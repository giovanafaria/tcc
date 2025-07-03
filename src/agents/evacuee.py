from mesa import Agent
from src.mobility import MobilityType

class Evacuee(Agent):
    def __init__(self, unique_id, model, mobility_type=MobilityType.NON_PWD):
        """
        constructor for the agent
        """
        super().__init__(unique_id, model)
        self.mobility_type = mobility_type
        self.base_speed = float(getattr(mobility_type, 'speed', 1.0)) 
        self.color = getattr(mobility_type, 'color', "#FFFFFF")

        self.evacuation_started     = False
        self.alive = True
        self.evacuated              = False
        self.impacted_by_landslide  = False
        self.stuck = False

        self.stuck_counter = 0
        self.previous_pos = None
        # max steps an agent tries to move into a landslide before being marked stuck
        self.max_stuck_threshold = 40   # will use more than n of steps for no landslide and 200 for activate areas

    def step(self):
        """
        method is run every simulation time step
        """
        if not self.alive or self.stuck or self.evacuated:
            return

        if self.pos == self.model.safe_zone:
            if not self.evacuated:
                self.model.reporter.record_evacuation_end(self)
                self.evacuated = True
            return

        if not self.evacuation_started:
            self.model.reporter.record_evacuation_start(self)
            self.evacuation_started = True

        # check if pos changed
        if self.previous_pos is not None and self.pos == self.previous_pos:
            pass
        else:
            self.stuck_counter = 0
        self.previous_pos = self.pos

        moved_this_step = False
        path = self.model.get_path(self.pos, self.model.safe_zone)

        if path and len(path) > 1:
            next_pos = path[1]

            current_elev = self.model.get_elevation(self.pos)
            next_elev = self.model.get_elevation(next_pos)
            slope = next_elev - current_elev

            uphill_factor = 2.45   # 0,58 m/s to non pwd
            downhill_factor = 2.0  # universal — gives 0.67 m/s baseline (QU et al., 2014)

            if slope > 0: slope_penalty = 1 + slope * uphill_factor
            elif slope < 0: slope_penalty = 1 + abs(slope) * downhill_factor
            else: slope_penalty = 1 # flat terrain
            
            effective_speed = self.model.base_speed * self.base_speed / slope_penalty

            is_next_cell_building = self.model.obstacle_mask[next_pos[1], next_pos[0]]
            passes_speed_check = self.model.random.random() < max(effective_speed, 0.75) # prob of moving never lower than 98%

            if not is_next_cell_building:
                if passes_speed_check:
                    if self.model.grid.is_cell_empty(next_pos):
                        # cell is completely empty, can move
                        self.model.grid.move_agent(self, next_pos)
                        self.model.reporter.record_movement(self)
                        moved_this_step = True
                        if next_pos == self.model.safe_zone:
                            if not self.evacuated:
                                self.model.reporter.record_evacuation_end(self)
                                self.evacuated = True
                    else:
                        from src.agents.landslide import Landslide
                        contents = self.model.grid.get_cell_list_contents([next_pos])
                        if any(isinstance(agent, Landslide) for agent in contents):
                            reason_for_not_moving_is_landslide_block = True

        if moved_this_step:
            self.stuck_counter = 0
        elif self.previous_pos is not None and self.pos == self.previous_pos:
            self.stuck_counter += 1

        if not self.stuck and self.stuck_counter >= self.max_stuck_threshold:
            self.stuck = True
            print(f'Agent {self.unique_id} at {self.pos} is now STUCK after {self.stuck_counter} attempts to move into a landslide (Threshold: {self.max_stuck_threshold}).')
            if hasattr(self.model.reporter, 'record_agent_stuck'):
                self.model.reporter.record_agent_stuck(self)