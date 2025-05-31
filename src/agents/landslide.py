from mesa import Agent
from src.agents.building import Building
from src.agents.evacuee import Evacuee

class Landslide(Agent):
    def __init__(self, unique_id, model, mask, direction, cells_per_tick):
        """
        :param cells_per_tick: fractional grid cells the landslide moves per tick
        """
        super().__init__(unique_id, model)
        self.mask = mask
        self.direction = direction
        self.cells_per_tick = cells_per_tick
        self._accumulator = 0.0
        self.front = []
        self.visited = set()

    def step(self):
        # add fractional progress
        self._accumulator += self.cells_per_tick
        expansions = int(self._accumulator)
        if expansions < 1:
            return
        self._accumulator -= expansions

        # expansions one cell at a time
        for _ in range(expansions):
            new_front = []
            for (x, y) in self.front:
                if self.direction == "up":
                    candidates = [(x-1,y+1),(x,y+1),(x+1,y+1),(x-1,y),(x+1,y)]
                for nx, ny in candidates:
                    pos = (nx, ny)
                    if self.model.grid.out_of_bounds(pos):
                        continue
                    # must be on a valid landslide mask cell
                    if not self.mask[ny, nx]:
                        continue
                    if pos in self.visited:
                        continue
                    self.visited.add(pos)

                    # interact with any agents/buildings at pos
                    contents = self.model.grid.get_cell_list_contents([pos])
                    from src.agents.evacuee import Evacuee
                    for agent in contents:
                        if isinstance(agent, Building):
                            agent.buried = True
                        elif isinstance(agent, Evacuee):
                            agent.impacted_by_landslide = True
                            agent.alive = False
                            self.model.reporter.record_landslide_impact(agent)
                            if agent.unique_id in self.model.schedule._agents:
                                self.model.schedule.remove(agent)

                    # place landslide cell
                    if self.model.grid.is_cell_empty(pos, ignore_prohibited=True):
                        self.force_place(pos)
                        new_front.append(pos)

            self.front = new_front

    def force_place(self, pos):
        x, y = pos
        self.pos = pos
        self.model.grid._grid[x][y] = self
