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
        Charges the battery by 5% per step when at a charging station OCCUPIED by this agent.
        Patrón de wolfSheep.Sheep.feed()
        Similar a: if grass_patch.fully_grown: self.energy += self.energy_from_food
        """
        station = self.get_current_station()
        # Solo cargar si estamos en una estación Y somos quienes la ocupan
        if station and station.occupied_by == self and self.battery < 100:
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
        Uses BFS to find the nearest AVAILABLE charging station (not occupied by another agent).
        Returns the cell containing the nearest available station.
        BFS de wolfSheep para encontrar recursos
        Similar a cómo Sheep busca GrassPatch más cercano
        """
        from collections import deque

        # BFS para encontrar la estación más cercana disponible
        queue = deque([(self.cell, 0)])  # (celda, distancia)
        visited = {self.cell}

        while queue:
            current, distance = queue.popleft()

            # Verificar si esta celda tiene una estación de carga disponible
            stations = [agent for agent in current.agents if isinstance(agent, ChargingStation)]
            if stations:
                station = stations[0]
                # Solo retornar si la estación está disponible o ya está ocupada por este agente
                if station.is_available() or station.occupied_by == self:
                    return current  # Retorna la celda con la estación más cercana disponible

            # Explorar vecinos (evitando obstáculos y estaciones ocupadas por otros)
            neighbors = current.neighborhood.select(
                lambda cell: not any(isinstance(agent, ObstacleAgent) for agent in cell.agents) and
                            not self.is_station_occupied_by_other(cell)
            )

            for neighbor in neighbors.cells:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, distance + 1))

        return None  # No se encontró ninguna estación disponible

    def find_path_to_station(self):
        """
        Uses BFS to find shortest path to nearest charging station.
        Returns list of cells representing the path.
        Avoids cells with stations occupied by other agents.
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

            # Explorar vecinos (evitando obstáculos y estaciones ocupadas por otros)
            neighbors = current.neighborhood.select(
                lambda cell: not any(isinstance(agent, ObstacleAgent) for agent in cell.agents) and
                            (cell == nearest_station_cell or not self.is_station_occupied_by_other(cell))
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
        # Verificar si tenemos una estación objetivo y si aún está disponible
        if self.target_station:
            stations = [agent for agent in self.target_station.agents if isinstance(agent, ChargingStation)]
            if stations:
                station = stations[0]
                # Si la estación objetivo está ocupada por otro, recalcular path
                if station.occupied_by is not None and station.occupied_by != self:
                    self.path_to_station = []
                    self.target_station = None

        if not self.path_to_station:
            self.path_to_station = self.find_path_to_station()

        if self.path_to_station and self.battery > 0:
            # Verificar la siguiente celda antes de moverse
            next_cell = self.path_to_station[0]  # Peek sin remover

            # Si la siguiente celda tiene una estación ocupada por otro, recalcular path
            if self.is_station_occupied_by_other(next_cell):
                self.path_to_station = []
                self.target_station = None
                return False

            # Liberar estación actual si estamos en una
            self.release_current_station()

            # Ahora sí moverse
            self.path_to_station.pop(0)
            self.cell = next_cell
            self.battery -= 1  # Consumir 1% por moverse
            self.movements += 1

            # Si llegamos a la estación objetivo, intentar ocuparla
            if self.is_at_any_station():
                self.occupy_current_station()

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

        # Liberar estación actual si estamos en una antes de moverse
        self.release_current_station()

        # Buscar celdas vecinas con suciedad (como Sheep busca grass)
        # Evitar obstáculos, otros agentes, y estaciones ocupadas por otros
        dirty_neighbors = self.cell.neighborhood.select(
            lambda cell: any(isinstance(agent, DirtyCell) for agent in cell.agents) and
                        not any(isinstance(agent, (ObstacleAgent, CleaningAgent)) for agent in cell.agents) and
                        not self.is_station_occupied_by_other(cell)
        )

        if dirty_neighbors.cells:
            # Moverse a una celda sucia (patrón de wolfSheep)
            self.cell = dirty_neighbors.select_random_cell()
            self.battery -= 1
            self.movements += 1
            return True
        else:
            # No hay celdas sucias cerca, moverse aleatoriamente (patrón de randomAgents)
            # Evitar obstáculos, otros agentes, y estaciones ocupadas por otros
            empty_neighbors = self.cell.neighborhood.select(
                lambda cell: not any(isinstance(agent, (ObstacleAgent, CleaningAgent)) for agent in cell.agents) and
                            not self.is_station_occupied_by_other(cell)
            )

            if empty_neighbors.cells:
                self.cell = empty_neighbors.select_random_cell()
                self.battery -= 1
                self.movements += 1
                return True

        return False

    def get_current_station(self):
        """
        Returns the charging station at the current cell, if any.
        """
        stations = [agent for agent in self.cell.agents if isinstance(agent, ChargingStation)]
        return stations[0] if stations else None

    def is_station_occupied_by_other(self, cell):
        """
        Checks if a cell has a charging station occupied by another agent.
        """
        stations = [agent for agent in cell.agents if isinstance(agent, ChargingStation)]
        if stations:
            station = stations[0]
            return station.occupied_by is not None and station.occupied_by != self
        return False

    def occupy_current_station(self):
        """
        Occupies the charging station at the current cell.
        """
        station = self.get_current_station()
        if station and station.is_available():
            station.occupy(self)

    def release_current_station(self):
        """
        Releases the charging station at the current cell if occupied by this agent.
        """
        station = self.get_current_station()
        if station and station.occupied_by == self:
            station.release()

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
            # Ocupar la estación si no está ocupada
            self.occupy_current_station()
            self.charge_battery()
            return

        # Si la batería está llena y está en una estación, liberarla antes de salir
        if self.is_at_any_station() and self.battery >= 100:
            self.release_current_station()

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
        self.occupied_by = None  # Referencia al agente que ocupa la estación

    def is_available(self):
        """
        Checks if the charging station is available (not occupied).
        """
        return self.occupied_by is None

    def occupy(self, agent):
        """
        Marks the station as occupied by a specific agent.
        """
        self.occupied_by = agent

    def release(self):
        """
        Releases the station, marking it as available.
        """
        self.occupied_by = None

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
