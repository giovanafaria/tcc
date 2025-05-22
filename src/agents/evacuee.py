from mesa import Agent
from src.mobility import MobilityType

class Evacuee(Agent):
    def __init__(self, unique_id, model, mobility_type=MobilityType.NON_PWD):
        """
        constructor for the agent
        """
        super().__init__(unique_id, model)
        self.mobility_type = mobility_type
        self.base_speed = mobility_type.speed
        self.color = mobility_type.color
        self.current_speed = self.base_speed
        self.path = []
        self.evacuation_started = False #flag to track evacuation start
        self.alive = True

        self.evacuated              = False
        self.impacted_by_landslide  = False

    def step(self):
        """
        method is run every simulation time step
        """
        if not self.alive:
            return

        if self.pos == self.model.safe_zone:
            # record evacuation = complete when reach safe zone
            if not hasattr(self, 'evacuated'):
                self.model.reporter.record_evacuation_end(self)
                self.evacuated = True
            return
        
        # start tracking at first movement attempt
        if not self.evacuation_started:
            self.model.reporter.record_evacuation_start(self)
            self.evacuation_started = True

        path = self.model.get_path(self.pos, self.model.safe_zone) # get the path from the current location to the safe zone

        if path and len(path) > 1:
            next_pos = path[1] # if there is a path still, take another step

            current_elev = self.model.get_elevation(self.pos)
            next_elev = self.model.get_elevation(next_pos)
            slope = next_elev - current_elev

            if self.mobility_type == MobilityType.WHEELCHAIR:
                slope_penalty = 1 + abs(slope) * 1.5  # wheelchairs are more affected
            elif self.mobility_type == MobilityType.BLIND or self.mobility_type == MobilityType.CRUTCHES:
                slope_penalty = 1 + abs(slope) * 0.8  # Blind or crutches less affected by slope but slower 
            else:
                slope_penalty = 1 + abs(slope) if slope > 0 else 1 # if its uphill, they maybe wont move as much?

            effective_speed = self.base_speed / slope_penalty

            if self.model.obstacle_mask[next_pos[1], next_pos[0]]:
                return          # blocked by building → stay this tick

            if self.model.grid.is_cell_empty(next_pos) and self.model.random.random() < effective_speed: # only move if next cell is empty
                self.model.grid.move_agent(self, next_pos)
                self.model.reporter.record_movement(self)

                if next_pos == self.model.safe_zone:
                    self.model.reporter.record_evacuation_end(self)
                    self.evacuated = True
