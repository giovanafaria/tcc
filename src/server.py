from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from src.model.simulation import EvacuationModel

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

grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500) # grid with pixels

server = ReportEnabledServer( # GUI simulation
    EvacuationModel,
    [grid],
    "Evacuation Simulation",
    {"width": 20, "height": 20, "num_agents": 30, "pwd_ratio": 0.3}
)
