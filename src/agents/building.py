from mesa import Agent


class Building(Agent):
    """Static obstacle covering exactly one grid cell."""
    def __init__(self, uid, pos, model):
        super().__init__(uid, model)
        self.pos = pos      # (x, y)

    def step(self):
        pass               # never moves
