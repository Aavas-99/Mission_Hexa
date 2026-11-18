class HexCell:
    def __init__(self, row, col, honey, bees):
        self.row = row
        self.col = col
        self.honey = honey
        self.bees = bees
        self.visited = False
        self.owner = None

    @property
    def position(self):
        return self.row, self.col

    def can_afford(self, honey_balance):
        return honey_balance >= self.bees

    def __repr__(self):
        return (
            f"HexCell({self.row}, {self.col}, honey={self.honey}, "
            f"bees={self.bees}, visited={self.visited})"
        )
