from mesa import Model
from mesa.discrete_space import OrthogonalMooreGrid
from .agent import Cell


class ConwaysGameOfLife(Model):
    """Autmata celular 1D con actualizacion fila por fila."""

    def __init__(self, width=50, height=50, initial_fraction_alive=0.2, seed=None):
        """Crea el grid y inicializa la fila superior aleatoriamente."""
        super().__init__(seed=seed)

        # Tabla
        self.rule_table = {
            "111": 0, "110": 1, "101": 0, "100": 1,
            "011": 1, "010": 0, "001": 1, "000": 0
        }

        self.grid = OrthogonalMooreGrid((width, height), capacity=1, torus=False)

        # Inicializar todas las celdas como DEAD
        for cell in self.grid.all_cells:
            Cell(self, cell, init_state=Cell.DEAD)

        # Inicializar solo la fila superior (y = height-1) aleatoriamente
        for x in range(width):
            cell = self.grid[(x, height - 1)]
            agent = cell.agents[0]
            if self.random.random() < initial_fraction_alive:
                agent.state = Cell.ALIVE

        # Fila actual que se este procesando (comenzando desde height-2)
        self.current_row = height - 2

        self.running = True

    def step(self):
        """Actualiza una fila por paso, de arriba hacia abajo."""
        # Si ya procesamos todas las filas, detener
        if self.current_row < 0:
            self.running = False
            return

        width = self.grid.dimensions[0]

        # Reiniciar _next_state para las celdas de esta fila
        for x in range(width):
            cell = self.grid[(x, self.current_row)]
            if cell.agents:
                cell.agents[0].reset_next_state()

        # Calcular el estado de cada celda en la fila actual
        for x in range(width):
            cell = self.grid[(x, self.current_row)]
            if cell.agents:
                cell.agents[0].determine_state()

        # Aplicar el nuevo estado
        for x in range(width):
            cell = self.grid[(x, self.current_row)]
            if cell.agents:
                cell.agents[0].assume_state()

        # Avanzar a la siguiente fila
        self.current_row -= 1
