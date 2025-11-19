from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalMooreGrid

from .agent import CleaningAgent, ChargingStation, DirtyCell, ObstacleAgent

class RoombaCleaningModel(Model):
    def __init__(self, width=25, height=25, num_dirty_cells=50, num_obstacles=20, max_steps=1000, seed=42):
        super().__init__(seed=seed)

        self.width = width
        self.height = height
        self.num_dirty_cells = num_dirty_cells
        self.num_obstacles = num_obstacles
        self.max_steps = max_steps
        self.seed = seed

        # Crear el grid con el generador de números aleatorios del modelo
        self.grid = OrthogonalMooreGrid([width, height], torus=False, random=self.random)

        # Métricas de la simulación
        self.dirty_cells_count = num_dirty_cells
        self.initial_dirty_cells = num_dirty_cells
        self.all_clean = False
        self.steps_to_clean = None
        self.total_movements = 0
        self.steps_count = 0  # Contador de pasos manual

        # Colocar la estación de carga en la posición (1, 1)
        charging_cell = self.grid[(1, 1)]
        self.charging_station = ChargingStation(self, cell=charging_cell)

        # Colocar obstáculos en posiciones aleatorias (evitando la posición de la estación)
        available_cells = [cell for cell in self.grid.empties.cells if cell.coordinate != (1, 1)]
        obstacle_cells = self.random.sample(available_cells, min(num_obstacles, len(available_cells)))

        for cell in obstacle_cells:
            ObstacleAgent(self, cell=cell)

        # Colocar celdas sucias en posiciones aleatorias (evitando obstáculos y estación)
        available_cells = [cell for cell in self.grid.empties.cells if cell.coordinate != (1, 1)]
        dirty_cells = self.random.sample(available_cells, min(num_dirty_cells, len(available_cells)))

        for cell in dirty_cells:
            DirtyCell(self, cell=cell)

        # Crear el agente de limpieza en la posición (1, 1) - mismo lugar que la estación
        self.cleaning_agent = CleaningAgent(self, cell=charging_cell, home_station=charging_cell)

        # Set up data collection
        model_reporters = {
            "Dirty Cells": lambda m: m.dirty_cells_count,
            "Battery": lambda m: m.cleaning_agent.battery,
        }

        self.datacollector = DataCollector(model_reporters)

        self.running = True

        # Collect initial data
        self.datacollector.collect(self)

    def step(self):
        """
        Advance the model by one step.
        """
        # Incrementar el contador de pasos
        self.steps_count += 1

        # Verificar si se alcanzó el máximo de pasos
        if self.steps_count >= self.max_steps:
            self.running = False
            return

        # Ejecutar el paso del agente
        self.cleaning_agent.step()

        # Actualizar métricas
        self.total_movements = self.cleaning_agent.movements

        # Verificar si todas las celdas están limpias
        if self.dirty_cells_count == 0 and not self.all_clean:
            self.all_clean = True
            self.steps_to_clean = self.steps_count
            self.running = False

        # Verificar si el agente se quedó sin batería y no puede regresar
        if self.cleaning_agent.battery <= 0 and not self.cleaning_agent.is_at_station():
            self.running = False

        # Collect data
        self.datacollector.collect(self)

