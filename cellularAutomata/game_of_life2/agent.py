# FixedAgent: Immobile agents permanently fixed to cells
from mesa.discrete_space import FixedAgent

class Cell(FixedAgent):
    """Represents a single ALIVE or DEAD cell in the simulation."""

    DEAD = 0
    ALIVE = 1

    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    @property
    def is_alive(self):
        return self.state == self.ALIVE

    def __init__(self, model, cell, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model)
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def determine_state(self):
        # Usar snapshot del modelo para actualización paralela
        snap = self.model.prev_state
        width = self.model.grid.dimensions[0]
        height = self.model.grid.dimensions[1]

        # Fila de arriba con wrap
        ny = (self.y - 1) % height
        # Vecinos izquierdo y derecho con wrap
        lx = (self.x - 1) % width
        rx = (self.x + 1) % width

        left = snap[ny][lx]
        right = snap[ny][rx]

        # Regla: XOR de left y right
        bit = left ^ right
        self._next_state = self.ALIVE if bit == 1 else self.DEAD

    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state
