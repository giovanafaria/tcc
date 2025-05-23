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
            "steps", "evacuated", "impacted_by_landslide",
            "final_pos", "time_spent"
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
            "end_time": None,
            "distance": 0,  # cumulative distance traveled
            "steps": 0,  # number of movement attempts
            "evacuated": False,  # success flag  # TODO: colocar tempo para a flag não necessariamente ser true sempre
            "impacted_by_landslide": False,
            "final_pos": None,  # add all fields with default values
            "time_spent": 0     # always equals as end_time, bc start_time = 0
        }
        self.data.append(entry)


    def record_movement(self, agent):
        """
        Update movement metrics
        """
        for entry in self.data:
            if entry["agent_id"] == agent.unique_id:
                entry["steps"] += 1
                dx = agent.pos[0] - entry["start_pos"][0]
                dy = agent.pos[1] - entry["start_pos"][1]
                entry["distance"] = (dx**2 + dy**2)**0.5  # euclidean distance > represent straight line distance (x grid cells)
                break

    def record_landslide_impact(self, agent):
        for entry in self.data:
            if entry["agent_id"] == agent.unique_id:
                entry["impacted_by_landslide"] = True
                entry["end_time"]  = self.model.schedule.steps
                entry["final_pos"] = agent.pos
                entry["time_spent"] = entry["end_time"] - entry["start_time"]
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

        for entry in self.data:
            if entry["end_time"] is None:
                agent = next(
                    (a for a in self.model.schedule.agents
                    if a.unique_id == entry["agent_id"]),
                    None
                )
                if agent is not None:
                    entry["end_time"]  = self.model.schedule.steps
                    entry["final_pos"] = agent.pos
                    entry["time_spent"] = entry["end_time"] - entry["start_time"]

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)  # making sure the dir is ok

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = reports_dir / f"evacuation_report_{timestamp}.csv"

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.header)
            writer.writeheader()
            writer.writerows(self.data)
        
        print(f'Report written to {filename}')