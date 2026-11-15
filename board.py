import random

from config import (
    ROWS,
    COLS,
    MIN_CELL_HONEY,
    MAX_CELL_HONEY,
    MIN_BEES,
    MAX_BEES,
    HONEY_UPDATE_INTERVAL,
    BEE_UPDATE_INTERVAL
)

from hex_cell import HexCell


class Board:
    def __init__(self):
        self.cells = {}

        for row in range(ROWS):
            for col in range(COLS):
                self.cells[(row, col)] = HexCell(row, col)

        self.queen_position = None
        self.place_queen()

    def place_queen(self):
        self.queen_position = random.choice(list(self.cells.keys()))
        self.cells[self.queen_position].has_queen = True

    def get_neighbors(self, position):
        row, col = position

        if row % 2 == 0:
            directions = [
                (-1, 0),
                (-1, -1),
                (0, -1),
                (0, 1),
                (1, 0),
                (1, -1)
            ]
        else:
            directions = [
                (-1, 0),
                (-1, 1),
                (0, -1),
                (0, 1),
                (1, 0),
                (1, 1)
            ]

        neighbors = []

        for dr, dc in directions:
            new_position = (row + dr, col + dc)

            if new_position in self.cells:
                neighbors.append(new_position)

        return neighbors

    def has_pheromone(self, position):
        return self.queen_position in self.get_neighbors(position)

    def update_environment(self, turn):
        if turn % HONEY_UPDATE_INTERVAL == 0:
            for cell in self.cells.values():
                if cell.visited or cell.has_queen:
                    continue

                if random.random() < 0.55:
                    change = random.randint(-5, 5)

                    cell.honey = max(
                        MIN_CELL_HONEY,
                        min(MAX_CELL_HONEY, cell.honey + change)
                    )

        if turn % BEE_UPDATE_INTERVAL == 0:
            for cell in self.cells.values():
                if cell.visited or cell.has_queen:
                    continue

                if random.random() < 0.50:
                    change = random.choice([-2, -1, 0, 1, 2])

                    cell.bees = max(
                        MIN_BEES,
                        min(MAX_BEES, cell.bees + change)
                    )