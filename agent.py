from mesa import Agent

class Evacuee(Agent):
    def __init__(self, unique_id, model, is_pwd=False):
        super().__init__(unique_id, model)
        self.is_pwd = is_pwd
        self.speed = 0.4 if is_pwd else 1.0
        self.color = "red" if is_pwd else "blue"

    def step(self):
        if self.pos == self.model.safe_zone:
            return

        path = self.model.get_path(self.pos, self.model.safe_zone)
        if path and len(path) > 1:
            next_pos = path[1]
            current_elev = self.model.get_elevation(self.pos)
            next_elev = self.model.get_elevation(next_pos)
            slope = next_elev - current_elev
            slope_penalty = 1 + abs(slope) if slope > 0 else 1
            speed = self.speed / slope_penalty
            if self.model.random.random() < speed:
                self.model.grid.move_agent(self, next_pos)
