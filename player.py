from config import INITIAL_HONEY


class Player:
    def init(self, name, color, is_human=True):
        self.name = name
        self.color = color
        self.is_human = is_human

        self.honey = INITIAL_HONEY
        self.position = None
        self.alive = True

        self.visited_cells = []

        self.knowledge = {}
        self.possible_queen_cells = set()

    def update_knowledge(self, board, position):
        pheromone = board.has_pheromone(position)

        self.knowledge[position] = pheromone
        self.update_possible_queen_cells(board)

        return pheromone

    def update_possible_queen_cells(self, board):
        possible = set(board.cells.keys())

        for position in self.knowledge:
            possible.discard(position)

        for position, pheromone in self.knowledge.items():
            neighbors = set(board.get_neighbors(position))

            if pheromone:
                possible = possible.intersection(neighbors)
            else:
                possible = possible.difference(neighbors)

        self.possible_queen_cells = possible