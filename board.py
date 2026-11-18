import random

from config import (
    ROWS, COLS, MIN_CELL_HONEY, MAX_CELL_HONEY,
    MIN_BEES, MAX_BEES, HONEY_UPDATE_INTERVAL,
    BEE_UPDATE_INTERVAL,
)
from hex_cell import HexCell


class Board:
    def __init__(self):
        self.cells = {}
        self.queen_position = None
        self.environment_turn = 0
        self.generate_board()

    def generate_board(self):
        self.cells = {}
        for row in range(ROWS):
            for col in range(COLS):
                self.cells[(row, col)] = HexCell(
                    row, col,
                    random.randint(MIN_CELL_HONEY, MAX_CELL_HONEY),
                    random.randint(MIN_BEES, MAX_BEES),
                )
        self.queen_position = random.choice(list(self.cells))
        self.environment_turn = 0

    def is_valid_position(self, position):
        return position in self.cells

    def get_neighbors(self, position):
        row, col = position
        if row % 2 == 0:
            offsets = [(-1, -1), (-1, 0), (0, -1),
                       (0, 1), (1, -1), (1, 0)]
        else:
            offsets = [(-1, 0), (-1, 1), (0, -1),
                       (0, 1), (1, 0), (1, 1)]
        result = []
        for dr, dc in offsets:
            candidate = (row + dr, col + dc)
            if candidate in self.cells:
                result.append(candidate)
        return result

    def get_random_safe_position(self, excluded_positions=None):
        excluded = set(excluded_positions or ())
        excluded.add(self.queen_position)
        choices = [p for p in self.cells if p not in excluded]
        if not choices:
            raise RuntimeError("No safe starting cells remain.")
        return random.choice(choices)

    def has_pheromone(self, position):
        """Call only on a cell just visited by a player."""
        if self.queen_position is None:
            return None
        return self.queen_position in self.get_neighbors(position)

    def update_environment(self):
        self.environment_turn += 1

        if (HONEY_UPDATE_INTERVAL > 0 and
                self.environment_turn % HONEY_UPDATE_INTERVAL == 0):
            for cell in self.cells.values():
                if not cell.visited:
                    cell.honey = max(
                        MIN_CELL_HONEY,
                        min(MAX_CELL_HONEY,
                            cell.honey + random.choice([-3, -2, -1, 1, 2, 3]))
                    )

        if (BEE_UPDATE_INTERVAL > 0 and
                self.environment_turn % BEE_UPDATE_INTERVAL == 0):
            for cell in self.cells.values():
                if not cell.visited:
                    cell.bees = max(
                        MIN_BEES,
                        min(MAX_BEES,
                            cell.bees + random.choice([-1, 1]))
                    )

    def get_cell(self, position):
        return self.cells.get(position)