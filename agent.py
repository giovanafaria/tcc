from mesa import Agent

class Evacuee(Agent):
    def __init__(self, unique_id, model, is_pwd=False):
        """
        constructor for the agent
        """
        super().__init__(unique_id, model)
        self.is_pwd = is_pwd  # move slower and it is red
        self.speed = 0.4 if is_pwd else 1.0
        self.color = "red" if is_pwd else "blue"

    def step(self):
        """
        method is run every simulation time step
        """
        if self.pos == self.model.safe_zone:
            # if they reached safe zone, stop
            return

        path = self.model.get_path(self.pos, self.model.safe_zone) # get the path from the current location to the safe zone

        if path and len(path) > 1:
            next_pos = path[1] # if there is a path still, take another step

            current_elev = self.model.get_elevation(self.pos)
            next_elev = self.model.get_elevation(next_pos)
            slope = next_elev - current_elev
            slope_penalty = 1 + abs(slope) if slope > 0 else 1 # if its uphill, they maybe wont move as much?

            speed = self.speed / slope_penalty
            if self.model.random.random() < speed: # random: the steeper the slope, the lower the chance to move (maybe change to move slower anyway)
                self.model.grid.move_agent(self, next_pos)
