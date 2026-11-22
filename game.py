import random

from board import Board
from player import Player
from config import PLAYER1_COLOR, PLAYER2_COLOR


class MissionHexaGame:
    def __init__(self, mode="human_minimax", difficulty="medium"):
        self.mode = mode
        self.difficulty = difficulty
        self.board = Board()

        if mode == "ai_vs_ai":
            p1_human, p2_human = False, False
            p1_ai, p2_ai = "minimax", "mcts"
            p1_name, p2_name = "Minimax", "MCTS"
        elif mode == "human_mcts":
            p1_human, p2_human = True, False
            p1_ai, p2_ai = None, "mcts"
            p1_name, p2_name = "Human", "MCTS"
        elif mode == "human_human":
            p1_human, p2_human = True, True
            p1_ai, p2_ai = None, None
            p1_name, p2_name = "Human 1", "Human 2"
        else:
            p1_human, p2_human = True, False
            p1_ai, p2_ai = None, "minimax"
            p1_name, p2_name = "Human", "Minimax"

        self.players = [
            Player(p1_name, PLAYER1_COLOR, p1_human, p1_ai),
            Player(p2_name, PLAYER2_COLOR, p2_human, p2_ai),
        ]

        self.current_index = random.randint(0, 1)
        self.turn = 0
        self.game_over = False
        self.winner = None
        self.message = "Find honey, avoid the hidden Queen Bee!"
        self.last_move_by = None
        self.last_move_reasoning = None
        self.simulation_mode = False
        self.last_clues = {}

        self.initialize_players()

    def initialize_players(self):
        first = self.board.get_random_safe_position()
        second = self.board.get_random_safe_position({first})

        for index, position in enumerate((first, second)):
            player = self.players[index]
            player.position = position
            player.visited_cells.append(position)

            cell = self.board.cells[position]
            cell.visited = True
            cell.owner = index

            player.observe_cell(self.board, position)

        for player in self.players:
            player.update_possible_queen_cells(self.board)

    def current_player(self):
        return self.players[self.current_index]

    def opponent(self, player):
        return self.players[1 - self.players.index(player)]

    def legal_moves(self, player):
        if player is None or not player.alive or player.position is None:
            return []

        result = []
        opponent = self.opponent(player)

        for position in self.board.get_neighbors(player.position):
            cell = self.board.cells[position]
            if cell.visited:
                continue
            if opponent.alive and position == opponent.position:
                continue
            if cell.bees > player.honey:
                continue
            result.append(position)

        if result == [self.board.queen_position]:
            return []

        return result

    def move_player(self, player, position):
        if self.game_over:
            return False
        if player not in self.players or position not in self.legal_moves(player):
            return False

        cell = self.board.cells[position]
        player.position = position
        player.visited_cells.append(position)
        cell.visited = True
        cell.owner = self.players.index(player)
        self.last_move_by = player
        self.last_move_reasoning = None

        if position == self.board.queen_position:
            player.alive = False
            self.game_over = True
            self.winner = self.opponent(player)
            self.message = (
                f"{player.name} found the Queen Bee and was eliminated! "
                f"{self.winner.name} wins."
            )
            return True

        player.honey -= cell.bees
        player.honey += cell.honey

        if not self.simulation_mode:
            clue = player.observe_cell(self.board, position)
            for observer in self.players:
                observer.update_possible_queen_cells(self.board)
            self.last_clues[player.name] = clue
            if clue:
                clue_text = "Royal pheromone detected nearby!"
            else:
                clue_text = "No royal pheromone detected."
            self.message = (
                f"{player.name}: paid {cell.bees} honey, collected "
                f"{cell.honey}. {clue_text}"
            )
        else:
            # Hypothetical visits do not reveal unknown pheromone data.
            self.message = f"{player.name} moved to {position}."

        return True

    def switch_turn(self):
        self.current_index = 1 - self.current_index

    def complete_turn(self):
        if self.game_over:
            return
        self.turn += 1
        self.switch_turn()
        self.check_game_over()

    def pass_turn(self):
        if self.game_over:
            return
        if self.legal_moves(self.current_player()):
            return
        if self.mode == "ai_vs_ai":
            self.check_game_over()
            return
        name = self.current_player().name
        self.message = f"{name} has no legal moves and passes."
        self.turn += 1
        self.switch_turn()
        self.check_game_over()

    def check_game_over(self):
        if self.game_over:
            return

        p1, p2 = self.players
        p1_has_moves = bool(self.legal_moves(p1))
        p2_has_moves = bool(self.legal_moves(p2))

        if self.mode == "ai_vs_ai":
            if not p1_has_moves and not p2_has_moves:
                self._finish_on_honey("Both players are stuck.")
            elif not p1_has_moves or not p2_has_moves:
                active = p1 if p1_has_moves else p2
                stuck = p2 if p1_has_moves else p1
                if active.honey > stuck.honey:
                    self._finish_on_honey(
                        f"{active.name} leads while {stuck.name} is stuck."
                    )
                else:
                    self.current_index = self.players.index(active)
                    self.message = (
                        f"{stuck.name} has no legal moves. "
                        f"{active.name} continues."
                    )
            return

        if not p1_has_moves and not p2_has_moves:
            self._finish_on_honey("Both players are stuck.")

    def _finish_on_honey(self, reason):
        p1, p2 = self.players
        self.game_over = True
        if p1.honey > p2.honey:
            self.winner = p1
            self.message = f"{reason} {p1.name} wins on honey!"
        elif p2.honey > p1.honey:
            self.winner = p2
            self.message = f"{reason} {p2.name} wins on honey!"
        else:
            self.winner = None
            self.message = f"{reason} The game is a draw!"

    def clone_for_search(self):
        """
        Search AIs use deepcopy and then enable simulation_mode.
        This helper is available for external experiments.
        """
        import copy
        clone = copy.deepcopy(self)
        clone.simulation_mode = True
        clone.board.queen_position = None
        return clone