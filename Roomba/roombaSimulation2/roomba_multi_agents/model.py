from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid

from .agent import CleaningAgent, ChargingStation, DirtyCell, ObstacleAgent

class RoombaMultiAgentModel(Model):
    def __init__(self, num_agents=5, width=25, height=25, num_dirty_cells=100, num_obstacles=20, max_steps=2000, seed=42):
        super().__init__(seed=seed)

        self.num_agents = num_agents
        self.width = width
        self.height = height
        self.num_dirty_cells = num_dirty_cells
        self.num_obstacles = num_obstacles
        self.max_steps = max_steps
        self.seed = seed

        # Crear el grid con el generador de números aleatorios del modelo
        # Patrón de randomAgents y wolfSheep
        self.grid = OrthogonalMooreGrid([width, height], torus=False, random=self.random)

        # Métricas de la simulación
        self.dirty_cells_count = num_dirty_cells
        self.initial_dirty_cells = num_dirty_cells
        self.all_clean = False
        self.steps_to_clean = None
        self.steps_count = 0  # Contador de pasos manual

        # Lista para almacenar los agentes de limpieza
        self.cleaning_agents = []

        # Colocar obstáculos en posiciones aleatorias
        # Patrón de randomAgents para colocar obstáculos
        available_cells = [cell for cell in self.grid.empties.cells]
        obstacle_cells = self.random.sample(available_cells, min(num_obstacles, len(available_cells)))

        for cell in obstacle_cells:
            ObstacleAgent(self, cell=cell)

        # Colocar estaciones de carga en posiciones aleatorias (una por agente)
        # Patrón de wolfSheep para inicializar múltiples recursos (GrassPatch)
        available_cells = [cell for cell in self.grid.empties.cells]
        station_cells = self.random.sample(available_cells, min(num_agents, len(available_cells)))

        charging_stations = []
        for cell in station_cells:
            station = ChargingStation(self, cell=cell)
            charging_stations.append((station, cell))

        # Colocar celdas sucias en posiciones aleatorias (evitando obstáculos y estaciones)
        # Patrón de randomAgents
        available_cells = [cell for cell in self.grid.empties.cells]
        dirty_cells = self.random.sample(available_cells, min(num_dirty_cells, len(available_cells)))

        for cell in dirty_cells:
            DirtyCell(self, cell=cell)

        # Crear múltiples agentes de limpieza, cada uno en su estación inicial
        # Patrón de wolfSheep para crear múltiples Sheep/Wolf
        # Similar a: Sheep(model, ...) en un loop para initial_sheep
        for i, (station, cell) in enumerate(charging_stations):
            agent = CleaningAgent(self, cell=cell, home_station=cell)
            self.cleaning_agents.append(agent)

        # Set up data collection
        model_reporters = {
            "Cleaning Agents": lambda m: len(m.cleaning_agents),
            "Dirty Cells": lambda m: m.dirty_cells_count,
        }

        self.datacollector = DataCollector(model_reporters)

        self.running = True

        # Collect initial data
        self.datacollector.collect(self)

    def step(self):
        """
        Advance the model by one step.
        Estructura de wolfSheep.step()
        """
        # Incrementar el contador de pasos
        self.steps_count += 1

        # Verificar si se alcanzó el máximo de pasos
        if self.steps_count >= self.max_steps:
            self.running = False
            return

        # Ejecutar el paso de todos los agentes
        # Patrón de wolfSheep para ejecutar múltiples agentes
        # Usa shuffle para orden aleatorio (como wolfSheep)
        agents_shuffled = self.random.sample(self.cleaning_agents, len(self.cleaning_agents))
        for agent in agents_shuffled:
            agent.step()

        # Verificar si todas las celdas están limpias
        if self.dirty_cells_count == 0 and not self.all_clean:
            self.all_clean = True
            self.steps_to_clean = self.steps_count
            self.running = False

        # Verificar si todos los agentes se quedaron sin batería
        all_agents_dead = all(
            agent.battery <= 0 and not agent.is_at_any_station()
            for agent in self.cleaning_agents
        )
        if all_agents_dead:
            self.running = False

        # Collect data
        self.datacollector.collect(self)