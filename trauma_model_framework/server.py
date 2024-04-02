import mesa

from .agents import SsAgent, Sugar
from .model import SugarscapeTMF

color_dic = {4: "#005C00", 3: "#008300", 2: "#00AA00", 1: "#00F800"}


def SsAgent_portrayal(agent):
    if agent is None:
        return

    if type(agent) is SsAgent:
        return {"Shape": "trauma_model_framework/resources/ant.png", "scale": 0.9, "Layer": 1}

    elif type(agent) is Sugar:
        color = color_dic[agent.amount] if agent.amount != 0 else "#D6F5D6"
        return {
            "Color": color,
            "Shape": "rect",
            "Filled": "true",
            "Layer": 0,
            "w": 1,
            "h": 1,
        }

    return {}


canvas_element = mesa.visualization.CanvasGrid(SsAgent_portrayal, 50, 50, 500, 500)
chart_element = mesa.visualization.ChartModule(
    [{"Label": "SsAgent", "Color": "#AA0000"}]
)

chart_element2 = mesa.visualization.ChartModule(
    [{"Label": "Trauma", "Color": "#000000"}]
)

server = mesa.visualization.ModularServer(
    SugarscapeTMF, [canvas_element, chart_element, chart_element2], "Basic Trauma Model Framework"
)
# server.launch()
