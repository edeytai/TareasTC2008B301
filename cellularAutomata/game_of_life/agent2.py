from mesa.discrete_space import FixedAgent

class Cell2(FixedAgent):
    DEAD = 0
    ALIVE = 1

    def __init__(self, model, cell, init_state=0):
        super().__init__(model)
        self.cell = cell
        self.pos = cell.coordinate
        self.state = init_state
        self._next_state = None

    @property
    def x(self):
        return self.cell.coordinate[0]

    @property
    def y(self):
        return self.cell.coordinate[1]

    def determine_state(self):
        # Usar snapshot para evitar mezclar pasos
        snap = self.model.prev_state
        w, h = self.model.width, self.model.height

        ny = self.y + self.model.ABOVE  # arriba respecto a convencion del modelo
        if ny < 0 or ny >= h:
            self._next_state = self.state
            return

        lx = max(self.x - 1, 0)
        cx = self.x
        rx = min(self.x + 1, w - 1)

        left = snap[ny][lx]
        center = snap[ny][cx]
        right = snap[ny][rx]

        key = f"{left}{center}{right}"
        bit = self.model.rule_table.get(key, 0)
        self._next_state = self.ALIVE if bit == 1 else self.DEAD

    def assume_state(self):
        if self._next_state is not None:
            self.state = self._next_state
            self._next_state = None
