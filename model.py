from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agent import Evacuee
from utils import a_star_path, load_elevation

import numpy as np

class EvacuationModel(Model):
    def __init__(self, width, height, num_agents=20, pwd_ratio=0.3): # TODO: check which % is pwd 
        self.grid = MultiGrid(width, height, torus=False) # creates the simulation space
        self.schedule = SimultaneousActivation(self) # prepares the schedule: who moves and when (agents)
        self.safe_zone = (width - 1, height - 1) # TODO: define safe zone
        self.terrain = load_elevation(width, height) # TODO: load elevation info

        for i in range(num_agents):
            # if they are pwd, place them randomly, add to the grid and schedule
            is_pwd = self.random.random() < pwd_ratio
            agent = Evacuee(i, self, is_pwd)
            x, y = self.random.randrange(width), self.random.randrange(height)
            while (x, y) == self.safe_zone:
                x, y = self.random.randrange(width), self.random.randrange(height)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

    def step(self):
        # everyone takes their action
        self.schedule.step()

    def get_path(self, start, goal):
        # pathfinding function
        return a_star_path(self.grid, start, goal)

    def get_elevation(self, pos):
        # returns elevation at a specific location on the grid
        x, y = pos
        return self.terrain[y, x]
