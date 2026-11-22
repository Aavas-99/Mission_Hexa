from config import INITIAL_HONEY


class Player:
    def __init__(self, name, color, is_human=True, ai_type=None):
        self.name = name
        self.color = color
        self.is_human = is_human
        self.ai_type = ai_type

        self.honey = INITIAL_HONEY
        self.position = None
        self.alive = True

        self.visited_cells = []
        self.knowledge = {}
        self.possible_queen_cells = set()

    def observe_cell(self, board, position):
        """
        Record the pheromone clue only for this visited cell.
        None means this is a search simulation with no hidden-world
        information available; it is not recorded as a negative clue.
        """
        clue = board.has_pheromone(position)
        if clue is None:
            return None
        self.knowledge[position] = clue
        self.update_possible_queen_cells(board)
        return clue

    def update_possible_queen_cells(self, board):
        possible = set(board.cells)
        for position, cell in board.cells.items():
            if cell.visited:
                possible.discard(position)

        for position, clue in self.knowledge.items():
            neighbors = set(board.get_neighbors(position))
            if clue:
                possible.intersection_update(neighbors)
            else:
                possible.difference_update(neighbors)

        self.possible_queen_cells = possible
