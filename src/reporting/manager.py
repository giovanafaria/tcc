import csv
import time
from pathlib import Path

class ReportManager:
    def __init__(self, model):
        self.model = model
        # list to hold agent records
        self.data = []
        self.start_time = time.time()
        # columns definition for csv
        self.header = [
            "agent_id", "mobility_type", "start_pos",
            "start_time", "end_time", "distance",
            "steps", "evacuated", "final_pos", "time_spent"
        ]

    def record_evacuation_start(self, agent):
        """
        Initializes tracking when agent starts to move
        """
        entry = {
            "agent_id": agent.unique_id,  # Unique identifier
            "mobility_type": agent.mobility_type.name,  # Type as string
            "start_pos": agent.pos,  # Tuple like (x,y)
            "start_time": self.model.schedule.steps,  # Current step count
            "end_time": None,  # Will be filled later
            "distance": 0,  # Cumulative distance traveled
            "steps": 0,  # Number of movement attempts
            "evacuated": False,  # Success flag
            "final_pos": None,  # Add all fields with default values
            "time_spent": 0
        }
        self.data.append(entry)

    def record_evacuation_start(self, agent):
        entry = {
            "agent_id": agent.unique_id,
            "mobility_type": agent.mobility_type.name,
            "start_pos": agent.pos,
            "start_time": self.model.schedule.steps,
            "end_time": None,
            "distance": 0,
            "steps": 0,
            "evacuated": False,
            "final_pos": None,
            "time_spent": 0
        }
        self.data.append(entry)

    def record_movement(self, agent):  # THIS WAS MISSING
        """
        Update movement metrics
        """
        for entry in self.data:
            if entry["agent_id"] == agent.unique_id:
                entry["steps"] += 1
                dx = agent.pos[0] - entry["start_pos"][0]
                dy = agent.pos[1] - entry["start_pos"][1]
                entry["distance"] = (dx**2 + dy**2)**0.5
                break

    def record_evacuation_end(self, agent):
        """
        Ends data when agent reaches safe zone
        """
        for entry in self.data:
            if entry["agent_id"] == agent.unique_id:
                entry.update({
                    "end_time": self.model.schedule.steps,  # final step count
                    "evacuated": True,
                    "final_pos": agent.pos,  # safe zone position
                    "time_spent": self.model.schedule.steps - entry["start_time"]
                })

    def save_report(self):
        """
        Generates csv output file
        """
        if not any(entry["evacuated"] for entry in self.data):
            return
        
        reports_dir = Path("reports")

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = reports_dir / f"evacuation_report_{timestamp}.csv"

        valid_entries = [entry for entry in self.data if entry["evacuated"]]

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writeheader()
            writer.writerows(valid_entries)
            
            # process each agents data
            for entry in self.data:
                writer.writerow(entry)