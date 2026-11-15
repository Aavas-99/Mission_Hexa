import random

from config import HONEY_MIN, HONEY_MAX, BEE_MIN, BEE_MAX


class HexCell:
    def __init__(self, row, col):
        self.row = row
        self.col = col

        self.honey = random.randint(HONEY_MIN, HONEY_MAX)
        self.bees = random.randint(BEE_MIN, BEE_MAX)

        self.visited = False
        self.has_queen = False