from roomba_multi_agents.agent import CleaningAgent, ChargingStation, DirtyCell, ObstacleAgent
from roomba_multi_agents.model import RoombaMultiAgentModel

from mesa.visualization import (
    Slider,
    SolaraViz,
    make_space_component,
    make_plot_component,
)

from mesa.visualization.components import AgentPortrayalStyle

def roomba_portrayal(agent):
    """
    Defines how each agent is portrayed in the visualization.
    Estructura de randomAgents.random_portrayal
    """
    if agent is None:
        return

    portrayal = AgentPortrayalStyle(
        size=50,
        marker="o",
    )

    if isinstance(agent, CleaningAgent):
        # Color del agente basado en el nivel de batería
        if agent.charging:
            portrayal.color = "yellow"  # Amarillo cuando está cargando
        elif agent.battery > 50:
            portrayal.color = "green"  # Verde cuando tiene batería alta
        elif agent.battery > 20:
            portrayal.color = "orange"  # Naranja cuando tiene batería media
        else:
            portrayal.color = "red"  # Rojo cuando tiene batería baja
        portrayal.marker = "o"
        portrayal.size = 80
    elif isinstance(agent, ChargingStation):
        portrayal.color = "blue"
        portrayal.marker = "s"  # Cuadrado
        portrayal.size = 100
    elif isinstance(agent, DirtyCell):
        portrayal.color = "brown"
        portrayal.marker = "x"
        portrayal.size = 60
    elif isinstance(agent, ObstacleAgent):
        portrayal.color = "gray"
        portrayal.marker = "s"
        portrayal.size = 100

    return portrayal

def post_process(ax):
    """
    Post-processing of the visualization to maintain aspect ratio.
    """
    ax.set_aspect("equal")

def post_process_lines(ax):
    """
    Post-processing for line plots (patrón de wolfSheep)
    """
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.9))

lineplot_component = make_plot_component(
    {"Cleaning Agents": "tab:green", "Dirty Cells": "tab:brown"},
    post_process=post_process_lines,
)

# Configuración de parámetros de randomAgents y wolfSheep
model_params = {
    "seed": {
        "type": "InputText",
        "value": 42,
        "label": "Random Seed",
    },
    "num_agents": Slider("Number of cleaning agents", 5, 1, 20),  # 🔄 Como initial_sheep en wolfSheep
    "width": Slider("Grid width", 25, 10, 50),
    "height": Slider("Grid height", 25, 10, 50),
    "num_dirty_cells": Slider("Number of dirty cells", 100, 10, 300),
    "num_obstacles": Slider("Number of obstacles", 20, 0, 100),
    "max_steps": Slider("Maximum steps", 2000, 100, 5000),
}

# Create the model using the initial parameters from the settings
# Patrón de randomAgents y wolfSheep
model = RoombaMultiAgentModel(
    num_agents=model_params["num_agents"].value,
    width=model_params["width"].value,
    height=model_params["height"].value,
    num_dirty_cells=model_params["num_dirty_cells"].value,
    num_obstacles=model_params["num_obstacles"].value,
    max_steps=model_params["max_steps"].value,
    seed=model_params["seed"]["value"]
)

space_component = make_space_component(
    roomba_portrayal,
    draw_grid=True,
    post_process=post_process
)

page = SolaraViz(
    model,
    components=[space_component, lineplot_component],
    model_params=model_params,
    name="Roomba Cleaning Simulation - Multiple Agents",
)
