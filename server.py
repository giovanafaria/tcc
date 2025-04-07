from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from model import EvacuationModel

def agent_portrayal(agent):
    return {"Shape": "circle", "Color": agent.color, "r": 0.6, "Layer": 0}

grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

server = ModularServer(
    EvacuationModel,
    [grid],
    "Evacuation Simulation",
    {"width": 20, "height": 20, "num_agents": 30, "pwd_ratio": 0.3}
)
