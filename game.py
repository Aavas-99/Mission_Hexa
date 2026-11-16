import random

from board import Board
from player import Player

from config import PLAYER1_COLOR, PLAYER2_COLOR


class MissionHexaGame:
    def __init__(self):
        self.board = Board()

        self.players = [
            Player("Player 1", PLAYER1_COLOR, True),
            Player("Player 2", PLAYER2_COLOR, True)
        ]

        self.current_index = 0
        self.turn = 0

        self.game_over = False
        self.winner = None

        self.message = "Mission Hexa started."

        self.initialize_players()

    def initialize_players(self):
        safe_positions = [
            position
            for position in self.board.cells
            if position != self.board.queen_position
        ]

        start1 = random.choice(safe_positions)
        safe_positions.remove(start1)

        start2 = random.choice(safe_positions)

        self.players[0].position = start1
        self.players[1].position = start2

        self.board.cells[start1].visited = True
        self.board.cells[start2].visited = True

        self.players[0].visited_cells.append(start1)
        self.players[1].visited_cells.append(start2)

        self.players[0].update_knowledge(self.board, start1)
        self.players[1].update_knowledge(self.board, start2)

    def current_player(self):
        return self.players[self.current_index]

    def other_player(self):
        return self.players[1 - self.current_index]

    def legal_moves(self, player):
        if not player.alive:
            return []

        moves = []

        for position in self.board.get_neighbors(player.position):
            cell = self.board.cells[position]

            if cell.visited:
                continue

            if player.honey < cell.bees:
                continue

            moves.append(position)

        return moves

    def move_player(self, player, position):
        if position not in self.legal_moves(player):
            return False

        cell = self.board.cells[position]

        player.position = position
        player.visited_cells.append(position)

        cell.visited = True

        # Entering the Queen Bee cell means instant death.
        if cell.has_queen:
            player.alive = False
            self.game_over = True
            self.winner = self.other_player()

            self.message = f"{player.name} entered the Queen Bee cell!"
            return True

        player.honey -= cell.bees
        player.honey += cell.honey

        pheromone = player.update_knowledge(self.board, position)

        if pheromone:
            pheromone_text = "Royal Pheromone detected!"
        else:
            pheromone_text = "No Royal Pheromone."

        self.message = (
            f"{player.name}: +{cell.honey} honey, "
            f"-{cell.bees} bee cost. {pheromone_text}"
        )

        return True

    def switch_turn(self):
        self.current_index = 1 - self.current_index

    def complete_turn(self):
        self.turn += 1

        self.board.update_environment(self.turn)

        self.switch_turn()
        self.check_game_over()

    def pass_turn(self):
        player = self.current_player()

        self.message = f"{player.name} has no legal moves and passes."

        self.turn += 1
        self.board.update_environment(self.turn)

        self.switch_turn()
        self.check_game_over()

    def check_game_over(self):
        if self.game_over:
            return

        player1_moves = self.legal_moves(self.players[0])
        player2_moves = self.legal_moves(self.players[1])

        if not player1_moves and not player2_moves:
            self.game_over = True

            if self.players[0].honey > self.players[1].honey:
                self.winner = self.players[0]
            elif self.players[1].honey > self.players[0].honey:
                self.winner = self.players[1]
            else:
                self.winner = None

            self.message = "Both players have no legal moves."