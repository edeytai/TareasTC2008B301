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

    @property
    def neighbors(self):
        return self.cell.neighborhood.agents
    
    def __init__(self, model, cell, init_state=DEAD):
        """Create a cell, in the given state, at the given x, y position."""
        super().__init__(model)
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    def get_three_neighbors_above(self):
        """Obtiene los 3 vecinos de la fila superior: izquierda, centro, derecha"""
        x, y = self.x, self.y
        width = self.model.grid.dimensions[0]

        # Vecinos: (x-1,y+1), (x,y+1), (x+1,y+1) con wrap en x
        left_x = (x - 1) % width
        right_x = (x + 1) % width
        neighbor_y = y + 1

        # Si estamos en la fila superior, no hay vecinos arriba
        if neighbor_y >= self.model.grid.dimensions[1]:
            return None

        # Obtener los agentes en esas posiciones
        left = self.model.grid[(left_x, neighbor_y)].agents[0] if self.model.grid[(left_x, neighbor_y)].agents else None
        center = self.model.grid[(x, neighbor_y)].agents[0] if self.model.grid[(x, neighbor_y)].agents else None
        right = self.model.grid[(right_x, neighbor_y)].agents[0] if self.model.grid[(right_x, neighbor_y)].agents else None

        return (left, center, right)

    def determine_state(self):
        if self._next_state is not None:
            return

        upneighbors = self.get_three_neighbors_above()

        # Si no hay vecinos arriba (fila superior), mantener estado actual
        if upneighbors is None:
            self._next_state = self.state
            return

        left, center, right = upneighbors

        # Obtener estados de los vecinos (0 o 1)
        left_state = left.state if left else self.DEAD
        center_state = center.state if center else self.DEAD
        right_state = right.state if right else self.DEAD

        key = str(left_state) + str(center_state) + str(right_state)

        self._next_state = self.model.rule_table.get(key, self.DEAD)

    def assume_state(self):
        """Set the state to the new computed state -- computed in step()."""
        self.state = self._next_state

    def reset_next_state(self):
        self._next_state = None
