import copy
import math

from ai_heuristics import (
    avoid_certain_queen_moves,
    best_future_honey_gain,
)
from config import MINIMAX_DEPTH_WEAK, MINIMAX_DEPTH_STRONG

class MinimaxAI:
    def __init__(self, difficulty="strong"):
        difficulty = difficulty.lower()
        if difficulty == "easy":
            self.depth = 1
        elif difficulty == "medium":
            self.depth = MINIMAX_DEPTH_WEAK
        else:
            self.depth = MINIMAX_DEPTH_STRONG
        self.nodes_explored = 0
        self.pruned_branches = 0

    def choose_move(self, game, player):
        moves = avoid_certain_queen_moves(
            player, game.legal_moves(player)
        )
        if not moves:
            return None

        self.nodes_explored = 0
        self.pruned_branches = 0
        root_index = game.players.index(player)
        root = self._copy_for_search(game)

        ordered = sorted(moves, key=lambda p: self._move_order_score(
            player, game.board.cells[p], p
        ), reverse=True)

        best_move = ordered[0]
        best_value = -math.inf
        alpha, beta = -math.inf, math.inf

        for move in ordered:
            child = self._apply_move(root, root_index, move)
            value = self._search(
                child, self.depth - 1, alpha, beta, root_index
            )
            value -= self._queen_move_risk(player, move)
            if value > best_value:
                best_value, best_move = value, move
            alpha = max(alpha, best_value)

        return best_move

    def _copy_for_search(self, game):
        clone = copy.deepcopy(game)
        clone.simulation_mode = True
        clone.board.queen_position = None
        return clone

    def _apply_move(self, state, player_index, move):
        child = copy.deepcopy(state)
        child.simulation_mode = True
        child.board.queen_position = None
        actor = child.players[player_index]
        child.move_player(actor, move)
        if not child.game_over:
            child.complete_turn()
        return child

    def _search(self, state, depth, alpha, beta, root_index):
        self.nodes_explored += 1
        if state.game_over:
            return self._terminal_value(state, root_index)
        if depth <= 0:
            return self._evaluate(state, root_index)

        actor = state.current_player()
        actor_index = state.players.index(actor)
        moves = avoid_certain_queen_moves(
            actor, state.legal_moves(actor)
        )
        if not moves:
            child = copy.deepcopy(state)
            child.simulation_mode = True
            child.pass_turn()
            return self._search(
                child, depth - 1, alpha, beta, root_index
            )

        maximizing = actor_index == root_index
        moves.sort(
            key=lambda p: self._move_order_score(
                actor, state.board.cells[p], p
            ),
            reverse=maximizing,
        )
        if maximizing:
            value = -math.inf
            for move in moves:
                child = self._apply_move(state, actor_index, move)
                move_value = self._search(
                    child, depth - 1, alpha, beta, root_index
                ) - self._queen_move_risk(actor, move)
                value = max(
                    value,
                    move_value,
                )
                alpha = max(alpha, value)
                if beta <= alpha:
                    self.pruned_branches += 1
                    break
            return value

        value = math.inf
        for move in moves:
            child = self._apply_move(state, actor_index, move)
            move_value = self._search(
                child, depth - 1, alpha, beta, root_index
            ) + self._queen_move_risk(actor, move)
            value = min(
                value,
                move_value,
            )
            beta = min(beta, value)
            if beta <= alpha:
                self.pruned_branches += 1
                break
        return value

    def _evaluate(self, state, root_index):
        me = state.players[root_index]
        other = state.players[1 - root_index]
        score = float(me.honey - other.honey)

        my_moves = state.legal_moves(me)
        their_moves = state.legal_moves(other)
        score += 1.7 * (len(my_moves) - len(their_moves))
        score += 0.35 * (
            best_future_honey_gain(state, me)
            - best_future_honey_gain(state, other)
        )

        return score

    @staticmethod
    def _move_order_score(player, cell, position):
        return (
            cell.honey - cell.bees
            - MinimaxAI._queen_move_risk(player, position)
        )

    @staticmethod
    def _queen_move_risk(player, position):
        candidates = player.possible_queen_cells
        if position in candidates and candidates:
            return 10000.0 / len(candidates)
        return 0.0

    def _terminal_value(self, state, root_index):
        me = state.players[root_index]
        other = state.players[1 - root_index]
        if state.winner is me:
            return 10000 + me.honey
        if state.winner is other:
            return -10000 - other.honey
        return me.honey - other.honey