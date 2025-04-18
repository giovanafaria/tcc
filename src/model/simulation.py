from pathlib import Path
from mesa import Model
from mesa.space import SingleGrid
from mesa.time import SimultaneousActivation
from src.agents.evacuee import Evacuee
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
        # grid and schedule initialization
        self.grid = PartialMultiGrid(width, height, torus=False) # creates the simulation space / single for one agent per cell
        self.grid.model = self # Attach the model instance so that safe_zone is accessible
        self.schedule = SimultaneousActivation(self) # prepares the schedule: who moves and when (agents)
        self.running = True # control flag (mesa)

        # env setup
        self.safe_zone = (width - 1, height - 1) # TODO: define safe zone
        self.terrain = load_elevation(width, height) # TODO: load elevation info

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
            x, y = self.random.randrange(width), self.random.randrange(height)
            while (x, y) == self.safe_zone or not self.grid.is_cell_empty((x,y)):
                x, y = self.random.randrange(width), self.random.randrange(height)
            
            agent = Evacuee(i, self, mobility_type=mobility)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

    def step(self):
        """
        Advance the model by one step
        """
        # everyone takes their action
        self.schedule.step()

        # check is there is still people to evacuate TODO: quando implementar tempo isso vai ser só p calcular quem nao conseguiu chegar
        self.running = any(
            not hasattr(agent, 'evacuated')
            for agent in self.schedule.agents
        ) # auto update in the running state

    def run_model(self):
        while self.running:
            self.step()

        # post simulation
        self.reporter.save_report()
        print('simulation complete!')

    def get_path(self, start, goal):
        # pathfinding function
        # pass path_mask to favor cells on defined paths
        return a_star_path(self.grid, start, goal, self.path_mask)

    def get_elevation(self, pos):
        # returns elevation at a specific location on the grid
        x, y = pos
        return self.terrain[y, x]
