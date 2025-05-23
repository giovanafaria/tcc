from mesa import Agent
from src.agents.building import Building

class Landslide(Agent):
    def __init__(self, unique_id, model, mask, direction):
        super().__init__(unique_id, model)
        self.mask = mask
        self.direction = direction
        self.front = []  # current cells in the wave

    def step(self):
        next_front = []

        for (x, y) in self.front:
            if self.direction=="up":
                candidates = [
                    (x-1,y+1),(x,y+1),(x+1,y+1),
                    (x-1,y),(x+1,y)
                ]

            for nx, ny in candidates:
                if self.model.grid.out_of_bounds((nx, ny)):
                    continue

                pos = (nx, ny)

                cell_agents = self.model.grid.get_cell_list_contents([(nx, ny)])

                if any(isinstance(a, Landslide)
                       for a in self.model.grid.get_cell_list_contents([pos])):
                    continue

                for agent in cell_agents:
                    if isinstance(agent, Building):
                        agent.buried = True
                    elif hasattr(agent, "mobility_type"):  # evacuee
                        agent.evacuated = False
                        agent.alive = False

                        self.model.reporter.record_landslide_impact(agent)

                        if agent.unique_id in self.model.schedule._agents:
                            self.model.schedule.remove(agent)

                if (self.model.grid.is_cell_empty(pos, ignore_prohibited=True) and self.mask[ny, nx]):
                    self.force_place(pos)
                    next_front.append(pos)

        self.front = next_front

    def force_place(self, pos):
        x, y = pos
        self.pos = pos
        self.model.grid._grid[x][y] = self
