from mesa.discrete_space import CellAgent, FixedAgent

class CleaningAgent(CellAgent):
    def __init__(self, model, cell, home_station):
        super().__init__(model)
        self.cell = cell
        self.battery = 100  # Inicia con 100% de batería
        self.movements = 0
        self.home_station = home_station  # Conoce su estación inicial
        self.charging = False
        self.path_to_station = []  # Ruta calculada para regresar a la estación
        self.target_station = None  # Estación objetivo actual

    def needs_charging(self):
        """
        Determines if the agent needs to return to charging station.
        Returns True if battery is below 20% and not at any station.
        """
        return self.battery < 20 and not self.is_at_any_station()

    def is_at_any_station(self):
        """
        Checks if the agent is currently at ANY charging station.
        Patrón de wolfSheep para verificar si está en un recurso
        Similar a: grass_patch = next(obj for obj in self.cell.agents if isinstance(obj, GrassPatch))
        """
        # Busca si hay una estación de carga en la celda actual
        stations = [agent for agent in self.cell.agents if isinstance(agent, ChargingStation)]
        return len(stations) > 0

    def is_at_station(self):
        return self.is_at_any_station()

    def charge_battery(self):
        """
        Charges the battery by 5% per step when at ANY charging station.
        Patrón de wolfSheep.Sheep.feed()
        Similar a: if grass_patch.fully_grown: self.energy += self.energy_from_food
        """
        if self.is_at_any_station() and self.battery < 100:
            self.battery = min(100, self.battery + 5)  # Recarga 5% como Sheep come grass
            self.charging = True
        else:
            self.charging = False

    def clean_current_cell(self):
        """
        Cleans the current cell if it contains a DirtyCell agent.
        Returns True if cleaning was performed, False otherwise.
        Patrón de wolfSheep.Wolf.feed() para buscar y eliminar agentes
        """
        # Busca si hay una celda sucia en la posición actual
        dirty_agents = [agent for agent in self.cell.agents if isinstance(agent, DirtyCell)]
        if dirty_agents and self.battery > 0:
            # Elimina la celda sucia
            for dirty in dirty_agents:
                dirty.remove()
            self.battery -= 1  # Consumir 1% de batería por limpiar
            self.model.dirty_cells_count -= 1
            return True
        return False

    def find_nearest_station(self):
        """
        Uses BFS to find the nearest charging station (ANY station, not just home).
        Returns the cell containing the nearest station.
        BFS de wolfSheep para encontrar recursos
        Similar a cómo Sheep busca GrassPatch más cercano
        """
        from collections import deque

        # BFS para encontrar la estación más cercana
        queue = deque([(self.cell, 0)])  # (celda, distancia)
        visited = {self.cell}

        while queue:
            current, distance = queue.popleft()

            # Verificar si esta celda tiene una estación de carga
            stations = [agent for agent in current.agents if isinstance(agent, ChargingStation)]
            if stations:
                return current  # Retorna la celda con la estación más cercana

            # Explorar vecinos (evitando obstáculos)
            neighbors = current.neighborhood.select(
                lambda cell: not any(isinstance(agent, ObstacleAgent) for agent in cell.agents)
            )

            for neighbor in neighbors.cells:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1))

        return None  # No se encontró ninguna estación

    def find_path_to_station(self):
        """
        Uses BFS to find shortest path to nearest charging station.
        Returns list of cells representing the path.
        """
        # Primero encuentra la estación más cercana
        nearest_station_cell = self.find_nearest_station()

        if nearest_station_cell is None or nearest_station_cell == self.cell:
            return []

        self.target_station = nearest_station_cell

        from collections import deque

        # BFS para encontrar el camino más corto a esa estación
        queue = deque([(self.cell, [self.cell])])
        visited = {self.cell}

        while queue:
            current, path = queue.popleft()

            if current == nearest_station_cell:
                return path[1:]  # Excluir la celda actual

            # Explorar vecinos
            neighbors = current.neighborhood.select(
                lambda cell: not any(isinstance(agent, ObstacleAgent) for agent in cell.agents)
            )

            for neighbor in neighbors.cells:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []  # No se encontró camino

    def move_to_station(self):
        """
        Moves one step towards the nearest charging station following the calculated path.
        Returns True if movement was successful.
        """
        if not self.path_to_station:
            self.path_to_station = self.find_path_to_station()

        if self.path_to_station and self.battery > 0:
            next_cell = self.path_to_station.pop(0)
            self.cell = next_cell
            self.battery -= 1  # Consumir 1% por moverse
            self.movements += 1
            return True
        return False

    def move_to_dirty_cell(self):
        """
        Moves to a neighboring dirty cell if available, otherwise moves randomly.
        Returns True if movement was performed.
        Patrón de wolfSheep.Sheep.move() - buscar objetivo preferido
        """
        if self.battery <= 0:
            return False

        # Buscar celdas vecinas con suciedad (como Sheep busca grass)
        dirty_neighbors = self.cell.neighborhood.select(
            lambda cell: any(isinstance(agent, DirtyCell) for agent in cell.agents) and
                        not any(isinstance(agent, (ObstacleAgent, CleaningAgent)) for agent in cell.agents)
        )

        if dirty_neighbors.cells:
            # Moverse a una celda sucia (patrón de wolfSheep)
            self.cell = dirty_neighbors.select_random_cell()
            self.battery -= 1
            self.movements += 1
            return True
        else:
            # No hay celdas sucias cerca, moverse aleatoriamente (patrón de randomAgents)
            empty_neighbors = self.cell.neighborhood.select(
                lambda cell: not any(isinstance(agent, (ObstacleAgent, CleaningAgent)) for agent in cell.agents)
            )

            if empty_neighbors.cells:
                self.cell = empty_neighbors.select_random_cell()
                self.battery -= 1
                self.movements += 1
                return True

        return False

    def step(self):
        """
        Executes one step of the agent's behavior:
        1. If at any station and battery < 100%, charge
        2. If battery < 20% and not at station, return to nearest station
        3. If current cell is dirty, clean it
        4. Otherwise, move towards dirty cells or randomly
        """
        # Si está en cualquier estación y la batería no está llena, cargar
        if self.is_at_any_station() and self.battery < 100:
            self.charge_battery()
            return

        # Si la batería está baja, regresar a cargar
        if self.needs_charging():
            self.move_to_station()
            return

        # Si la celda actual está sucia, limpiarla
        if self.clean_current_cell():
            return

        # Moverse hacia celdas sucias o aleatoriamente
        self.move_to_dirty_cell()


class ChargingStation(FixedAgent):
    """
    Charging station where cleaning agents can recharge their battery.
    Patrón de randomAgents.ObstacleAgent y wolfSheep.GrassPatch
    """
    def __init__(self, model, cell):
        """
        Creates a new charging station.
        Args:
            model: Model reference
            cell: Reference to its position within the grid
        """
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass


class DirtyCell(FixedAgent):
    """
    Represents a dirty cell that needs to be cleaned.
    Patrón de FixedAgent de randomAgents
    """
    def __init__(self, model, cell):
        """
        Creates a new dirty cell.
        Args:
            model: Model reference
            cell: Reference to its position within the grid
        """
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass


class ObstacleAgent(FixedAgent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    Copiado literalmente de randomAgents
    """
    def __init__(self, model, cell):
        """
        Creates a new obstacle.
        Args:
            model: Model reference
            cell: Reference to its position within the grid
        """
        super().__init__(model)
        self.cell = cell

    def step(self):
        pass
