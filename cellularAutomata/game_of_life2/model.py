from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Cell


class GameOfLife2(Model):
    """Autmata celular con actualizacion paralela usando snapshot."""

    def __init__(self, width=50, height=50, initial_fraction_alive=0.2, seed=None):
        """Crea el grid e inicializa todas las celdas aleatoriamente."""
        super().__init__(seed=seed)

        self.grid = OrthogonalMooreGrid((width, height), capacity=1, torus=True)

        # Inicializar todas las celdas aleatoriamente
        for cell in self.grid.all_cells:
            alive = 1 if self.random.random() < initial_fraction_alive else 0
            Cell(self, cell, init_state=alive)

        self.prev_state = None
        self.running = True

    def _take_snapshot(self):
        """Congela el estado actual en una matriz 2D."""
        width = self.grid.dimensions[0]
        height = self.grid.dimensions[1]
        snap = [[0]*width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                agents = self.grid[(x, y)].agents
                snap[y][x] = agents[0].state if agents else 0
        self.prev_state = snap

    def step(self):
        """Actualiza todas las celdas en paralelo usando snapshot."""
        # Tomar snapshot del estado actual
        self._take_snapshot()

        width = self.grid.dimensions[0]
        height = self.grid.dimensions[1]

        # Calcular el estado de cada celda
        for y in range(height):
            for x in range(width):
                cell = self.grid[(x, y)]
                if cell.agents:
                    cell.agents[0].determine_state()

        # Aplicar el nuevo estado
        for y in range(height):
            for x in range(width):
                cell = self.grid[(x, y)]
                if cell.agents:
                    cell.agents[0].assume_state()
