import random
import numpy as np
from scipy.ndimage import label
# from pathlib import Path
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
    def __init__(self, width, height, num_agents=20, pwd_ratio=0.089, active_areas=None): # data from IBGE
        super().__init__()
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
        flat_speed     = 2.5                # your emergency flat speed
        downhill_speed = 0.67               # average downhill speed

        # “slow‐down factor”
        base_speed = flat_speed * downhill_speed

        # PWD multipliers (fractions of base_speed)
        multipliers = {
            MobilityType.NON_PWD:    1.0,
            MobilityType.WHEELCHAIR: 0.8,
            MobilityType.BLIND:      0.7,
            MobilityType.CRUTCHES:   0.6,
        }

        # compute the real‐world seconds each PWD tick would take
        dt_list = [
            self.step_length / (base_speed * m)
            for m in multipliers.values()
        ]
        # pick the slowest (largest dt) so no one overshoots the clock
        self.dt = max(dt_list)            # seconds per tick (a call to step())

        self.time_per_step = (self.step_length / base_speed)

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

        pwd_types = [MobilityType.WHEELCHAIR, MobilityType.BLIND, MobilityType.CRUTCHES]

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
                        direction="up"
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
        """
        evacuees = [a for a in self.schedule.agents if isinstance(a, Evacuee)]
        if not evacuees:
            return True
        return all(
            a.evacuated or getattr(a, "impacted_by_landslide", False)
            for a in evacuees
        )

    def step(self):
        """
        Advance the model by one step, then stop if:
        1) 10 minute equivalent in step, or
        2) everybody's evacuated
        """
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

        landslides = [a for a in self.schedule.agents if isinstance(a, Landslide)]
        for evac in [a for a in self.schedule.agents if isinstance(a, Evacuee)]:
            if not evac.evacuated and not evac.impacted_by_landslide:
                for ls in landslides:
                    if evac.pos in ls.front:
                        evac.impacted_by_landslide = True
                        self.reporter.record_landslide_impact(evac)
                        evac.alive = False
                        break

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
        # pathfinding function
        # build a dynamic landslide-mask
        landslide_block = np.zeros_like(self.obstacle_mask, dtype=bool)
        for agent in self.schedule.agents:
            if isinstance(agent, Landslide):
                for (x, y) in agent.front:
                    landslide_block[y, x] = True

        # combine static obstacles + landslide blocks
        combined_obstacle = np.logical_or(self.obstacle_mask, landslide_block)

        # pass path_mask to favor cells on defined paths
        return a_star_path(
            self.grid,
            start,
            goal,
            path_mask=self.path_mask,
            obstacle_mask=combined_obstacle
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
