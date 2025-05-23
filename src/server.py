from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from src.model.simulation import EvacuationModel
from src.agents.building import Building
from src.agents.landslide import Landslide

GRID_W = 220
GRID_H = 180

class ReportEnabledServer(ModularServer):
    _has_run = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def launch(self, port=None):
        """
        Run model to completion before showing visualization
        """
        super().launch(port)

def agent_portrayal(agent):
    """
    sets size, shape and color
    """
    if agent is None:
        return None

    if isinstance(agent, Building):
        return {
            "Shape": "rect",
            "Color": "#555555",
            "Filled": "true",
            "Layer": 0,
            "w": 1, "h": 1
        }
    elif isinstance(agent, Landslide):
        return {
            "Shape": "rect",
            "Color": "#a52a2a",  # reddish-brown for landslide front
            "Filled": "true",
            "Layer": 1,
            "w": 1, "h": 1
        }
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
    {
     "width": GRID_W,
     "height": GRID_H,
     "num_agents": 50,
     "pwd_ratio": 0.089, # data from IBGE (2024)
     "active_areas": [1, 2]  # only shapefile x and y
     }  
)
