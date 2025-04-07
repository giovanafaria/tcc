from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agent import Evacuee
from utils import a_star_path, load_elevation

import numpy as np

class EvacuationModel(Model):
    def __init__(self, width, height, num_agents=20, pwd_ratio=0.3):
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.safe_zone = (width - 1, height - 1)
        self.terrain = load_elevation(width, height)

        for i in range(num_agents):
            is_pwd = self.random.random() < pwd_ratio
            agent = Evacuee(i, self, is_pwd)
            x, y = self.random.randrange(width), self.random.randrange(height)
            while (x, y) == self.safe_zone:
                x, y = self.random.randrange(width), self.random.randrange(height)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)

    def step(self):
        self.schedule.step()

    def get_path(self, start, goal):
        return a_star_path(self.grid, start, goal)

    def get_elevation(self, pos):
        x, y = pos
        return self.terrain[y, x]
