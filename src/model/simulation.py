import random
import numpy as np
from scipy.ndimage import label
from tornado.ioloop import IOLoop
from mesa import Model
from mesa.space import SingleGrid
from mesa.time import SimultaneousActivation
from src.agents.evacuee import Evacuee
from src.agents.building import Building
from src.agents.landslide import Landslide
from src.mobility import MobilityType
from src.reporting.manager import ReportManager
from src.utils.pathfinding import a_star_path, load_elevation, load_paths

class PartialMultiGrid(SingleGrid):
    def is_cell_empty(self, pos, ignore_prohibited=False):
        """
        If position is the safe zone, it will be treated like its empty (unlimited capacity).
        Also, never allow prohibited cells.
        """
        # always allow safe zone
        if pos == self.model.safe_zone:
            return True
        
        # prohibited cells (a triangle)
        if not ignore_prohibited and pos in getattr(self.model, "prohibited", ()):
            return False
        
        # normal cells
        return super().is_cell_empty(pos)


class EvacuationModel(Model):
    def __init__(
        self,
        width,
        height,
        num_agents=20,
        pwd_ratio=0.089, # data from IBGE
        active_areas=None,
        enable_landslide=True
        ): 
        super().__init__()

        self.enable_landslide = enable_landslide

        # grid and schedule initialization
        self.grid = PartialMultiGrid(width, height, torus=False) # creates the simulation space / single for one agent per cell
        self.grid.model = self # Attach the model instance so that safe_zone is accessible

        # env setup
        self.safe_zone = (0, height - 1)
        self.terrain = load_elevation(width, height) # TODO: load elevation info
        self.width  = width    # 220
        self.height = height   # 180

        raw_mask = np.load("data/processed/obstacle_mask.npy")
        self.obstacle_mask = np.flipud(raw_mask)

        uid = 10_000     # numbers above any evacuee id
        for y in range(height):
            for x in range(width):
                if self.obstacle_mask[y, x]:
                    b = Building(f"b{y}_{x}", (x, y), self)
                    uid += 1
                    self.grid.place_agent(b, (x, y)) # buildings are never scheduled

        # adding 'prohibited' cells (actually, they are hills and agents wouldnt be there in a normal situation)
        leg_left = 70 # length of the edges that will build the triangle
        leg_right = 50
        self.prohibited = {
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x + y < leg_left)                      # bottom‐left
                or ((self.width - 1 - x) + y < leg_right)    # bottom‐right
        }

        # ─── timing parameters
        self.step_length = 1.0              # meters per grid‐move/step
        self.target_time = 10 * 60          # total real‐world seconds = 600 s

        # base speeds (m/s)
        self.base_speed     = 1.5               # your emergency flat speed

        # compute the real‐world seconds each PWD tick would take (slowest agent)
        dt_list = [
            self.step_length / (self.base_speed * mt.speed)
            for mt in MobilityType
        ]
        # pick the slowest (largest dt) so no one overshoots the clock
        self.dt = max(dt_list)            # seconds per tick (a call to step())

        self.time_per_step = (self.step_length / self.base_speed)

        # how many ticks until 600 s have elapsed?
        self.max_steps = int(self.target_time / self.time_per_step)

        print(f'max steps: {self.max_steps}')

        # step counter
        self.current_step = 0
        self.schedule = SimultaneousActivation(self) # prepares the schedule: who moves and when (agents)
        self.running = True # control flag (mesa)

        shapefile_path = "data/raw/Caminho.shp"
        self.path_mask = load_paths(width, height, shapefile_path)

        # reporting system
        self.reporter = ReportManager(self)

        pwd_types = [MobilityType.MOTOR, MobilityType.VISUAL, MobilityType.INTELLECTUAL]

        for i in range(num_agents):
            # if they are pwd, place them randomly, add to the grid and schedule
            if self.random.random() < pwd_ratio:
                mobility = self.random.choice(pwd_types)
            else:
                mobility = MobilityType.NON_PWD

            # agent creation code
            while True:
                x, y = self.random.randrange(width), self.random.randrange(height)

                if (x, y) == self.safe_zone:            # not the safe zone
                    continue
                if self.obstacle_mask[y, x]:            # not inside building
                    continue
                if (x, y) in self.prohibited:
                    continue
                if not self.grid.is_cell_empty((x, y)): # not occupied
                    continue
                break
            
            agent = Evacuee(i, self, mobility_type=mobility)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

        # landslide configs
        if self.enable_landslide:
            mask_files = [
                "data/processed/landslide_mask_1.npy",
                "data/processed/landslide_mask_2.npy",
                "data/processed/landslide_mask_3.npy",
            ]
            self.landslide_masks = [
                np.flipud(np.load(fp)) for fp in mask_files
            ]
            # if user didnt specify activate all
            self.active_areas = (
                active_areas
                if active_areas is not None
                else list(range(len(self.landslide_masks)))
            )

            # landslide timing / velocity
            self.landslide_speed         = 5.25  # m/s  
            self.ls_cells_per_tick = (
                self.landslide_speed * self.base_speed
                / self.step_length
            )

            self.impacted_by_landslide = False

            lid = 10000
            for idx, mask in enumerate(self.landslide_masks):
                if idx not in self.active_areas:
                    continue
                # label components inside this shapefile (usually 1, but safe)
                labeled, n_comp = label(mask)
                for comp in range(1, n_comp+1):
                    coords = np.argwhere(labeled == comp)
                    base_row = coords[:,0].min()
                    base_front = [
                        (col, base_row) for (row,col) in coords
                        if row == base_row
                    ]
                    wave = Landslide(
                        unique_id=f"ls_{idx}_{comp}",
                        model=self,
                        mask=self.landslide_masks[idx],
                        direction="up",
                        cells_per_tick=self.ls_cells_per_tick
                    )
                    wave.front = base_front
                    for pos in base_front:
                        wave.force_place(pos)
                    self.schedule.add(wave)
                    lid += 1
        else:
            self.landslide_masks = []
            self.active_areas = []

        # reporting system 
        self.reporter = ReportManager(self)

        # thresholds (in seconds) at which to auto-save intermediate reports
        self._report_thresholds = {
            60:  "minute_1",
            180: "minute_3",
            300: "minute_5",
        }
        self._reports_saved = set()   # to avoid duplicates

    def all_agents_done(self):
        """
        assumes each Evacuee sets self.evacuated=True once it reaches safe_zone
        or sets self.impacted_by_landslide=True once landslide hits it
        or sets self.stuck=True when no path is available for too long
        """
        evacuees = [a for a in self.schedule.agents if isinstance(a, Evacuee)]
        if not evacuees:
            return True
        return all(
            a.evacuated
            or getattr(a, "impacted_by_landslide", False)
            or getattr(a, "stuck", False)
            for a in evacuees
        )

    def step(self):
        """
        Advance the model by one step, then stop if:
        1) 10 minute equivalent in step, or
        2) everybody's evacuated
        """
        # build a dynamic landslide-mask
        landslide_block = np.zeros_like(self.obstacle_mask, dtype=bool)
        for agent_obj in self.schedule.agents:
            if isinstance(agent_obj, Landslide):
                for (x, y) in agent_obj.front:
                    if 0 <= x < self.width and 0 <= y < self.height:
                        landslide_block[y, x] = True
        # combine static obstacles + landslide blocks
        self.current_step_combined_obstacle_mask = np.logical_or(self.obstacle_mask, landslide_block)

        # everyone takes their action
        self.schedule.step()
        self.current_step += 1

        # compute the real time so far
        elapsed = self.current_step * self.time_per_step
        for secs, folder in self._report_thresholds.items():
            if elapsed >= secs and secs not in self._reports_saved:
                self._reports_saved.add(secs)
                print(f"Reached ~{int(elapsed)}s → saving report for {folder}")
                self.reporter.save_report(folder)

        # stop early if everybody is evacuated
        if self.all_agents_done():
            print("All agents evacuated or impacted by landslide — stopping early.")
            self.running = False

            # post simulation
            self.reporter.save_report("all_done")
            print('simulation complete!')

            IOLoop.current().stop()
            return

        # stop on time
        if self.current_step >= self.max_steps:
            real_time = self.current_step * self.dt
            print(f"Reached {self.current_step} steps (~{real_time:.1f}s) → stopping on time.")
            self.running = False

            # post simulation
            self.reporter.save_report("all_done")
            print('simulation complete!')

            IOLoop.current().stop()
            return

    def get_path(self, start, goal):
        """
        Compute an A* path avoiding both static buildings buildings
        and any cells currently occupied by landslide front(s)
        """
        # pass path_mask to favor cells on defined paths
        return a_star_path(
            self.grid,
            start,
            goal,
            path_mask=self.path_mask,
            obstacle_mask=self.current_step_combined_obstacle_mask # Uses the precomputed mask
        )

    def get_elevation(self, pos):
        # returns elevation at a specific location on the grid
        x, y = pos
        return self.terrain[y, x]
    
    def force_place_agent(self, agent, pos):
        # Direct low-level assignment to force agent placement
        x, y = pos
        agent.pos = pos
        self.grid._grid[x][y] = agent
