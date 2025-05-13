from pathlib import Path
from tornado.ioloop import IOLoop
from mesa import Model
from mesa.space import SingleGrid
from mesa.time import SimultaneousActivation
from src.agents.evacuee import Evacuee
from src.agents.building import Building
from src.mobility import MobilityType
from src.reporting.manager import ReportManager
from src.utils.pathfinding import a_star_path, load_elevation, load_paths

import numpy as np

class PartialMultiGrid(SingleGrid):
    def is_cell_empty(self, pos):
        """
        If position is the safe zone, it will be treated like its empty (unlimited capacity)
        """
        if pos == self.model.safe_zone:
            return True
        return super().is_cell_empty(pos)


class EvacuationModel(Model):
    def __init__(self, width, height, num_agents=20, pwd_ratio=0.3): # TODO: check which % is pwd 
        super().__init__()
        # grid and schedule initialization
        self.grid = PartialMultiGrid(width, height, torus=False) # creates the simulation space / single for one agent per cell
        self.grid.model = self # Attach the model instance so that safe_zone is accessible

        # env setup
        self.safe_zone = (0, height - 1)
        self.terrain = load_elevation(width, height) # TODO: load elevation info

        self.width  = width    # 110
        self.height = height   # 90

        raw_mask = np.load("data/processed/obstacle_mask.npy")
        self.obstacle_mask = np.flipud(raw_mask)

        uid = 10_000     # numbers above any evacuee id
        for y in range(height):
            for x in range(width):
                if self.obstacle_mask[y, x]:
                    b = Building(f"b{y}_{x}", (x, y), self)
                    uid += 1
                    self.grid.place_agent(b, (x, y)) # buildings are never scheduled

        # ─── timing parameters
        self.step_length = 2.0              # meters per grid‐move/step #TODO: pegar essa referencia
        self.target_time = 10 * 60          # total real‐world seconds = 600 s

        # base speeds (m/s)
        flat_speed     = 2.5                # your emergency flat speed
        downhill_speed = 0.67               # average downhill speed

        # Otherwise, if you want a “slow‐down factor”:
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

        # how many ticks until 600 s have elapsed?
        self.max_steps = int(self.target_time / self.dt)

        print(f'max steps: {self.max_steps}')

        # step counter
        self.current_step = 0
        # ────────────────────────────────────────────────────────

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
                if not self.grid.is_cell_empty((x, y)): # not occupied
                    continue
                break
            
            agent = Evacuee(i, self, mobility_type=mobility)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

    def all_agents_evacuated(self):
        """
        assumes each Evacuee sets self.evacuated=True onde it reaches safe_zone
        """
        return all(
            getattr(agent, "evacuated", False)
            for agent in self.schedule.agents
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

        # stop on time
        if self.current_step >= self.max_steps:
            real_time = self.current_step * self.dt
            print(f"Reached {self.current_step} steps (~{real_time:.1f}s) → stopping on time.")
            self.running = False

            # post simulation
            self.reporter.save_report()
            print('simulation complete!')

            IOLoop.current().stop()
            return

        # stop early if everybody is evacuated
        if all(getattr(agent, "evacuated", False) for agent in self.schedule.agents):
            print("All agents evacuated — stopping early.")
            self.running = False

            # post simulation
            self.reporter.save_report()
            print('simulation complete!')

            IOLoop.current().stop()
            return

    def get_path(self, start, goal):
        # pathfinding function
        # pass path_mask to favor cells on defined paths
        return a_star_path(self.grid, start, goal,
                   path_mask=self.path_mask,
                   obstacle_mask=self.obstacle_mask)

    def get_elevation(self, pos):
        # returns elevation at a specific location on the grid
        x, y = pos
        return self.terrain[y, x]
