from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from src.model.simulation import EvacuationModel

GRID_W = 110
GRID_H = 90

class ReportEnabledServer(ModularServer):
    _has_run = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None

    def launch(self, port=None):
        """
        Run model to completion before showing visualization
        """
        if not self._has_run:
            self.model = self.model_cls(**self.model_kwargs)
            self.model.run_model()
            self._has_run = True
        super().launch(port)

def agent_portrayal(agent):
    """
    sets size, shape and color
    """
    return {
        "Shape": "circle",
        "Color": agent.color,
        "Filled": "true",
        "r": 0.6,
        "Layer": 0
    }

grid = CanvasGrid(agent_portrayal, GRID_W, GRID_H, 700, 580) # grid with pixels

server = ReportEnabledServer( # GUI simulation
    EvacuationModel,
    [grid],
    "Evacuation Simulation",
    {"width": GRID_W, "height": GRID_H, "num_agents": 300, "pwd_ratio": 0.3}
)
