import copy
import math

from ai_heuristics import (
    avoid_certain_queen_moves,
    best_future_honey_gain,
)
from config import (
    MINIMAX_DEPTH_EASY,
    MINIMAX_DEPTH_MEDIUM,
    MINIMAX_DEPTH_HARD,
    MINIMAX_DEPTH_WEAK,
    MINIMAX_DEPTH_STRONG,
)

class MinimaxAI:
    def __init__(self, difficulty="hard"):
        difficulty = difficulty.lower()
        if difficulty == "easy":
            self.depth = MINIMAX_DEPTH_EASY
        elif difficulty == "medium":
            self.depth = MINIMAX_DEPTH_MEDIUM
        else:
            self.depth = MINIMAX_DEPTH_HARD
        self.nodes_explored = 0
        self.pruned_branches = 0
        self.last_reasoning = None

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
            value = self._search_move(
                root,
                root_index,
                move,
                self.depth - 1,
                alpha,
                beta,
                root_index,
            )
            if value > best_value:
                best_value, best_move = value, move
            alpha = max(alpha, best_value)

        cell = game.board.cells[best_move]
        risk = self._queen_move_probability(player, best_move)
        risk_text = f"{risk:.0%} estimated queen risk" if risk else "no known queen risk"
        self.last_reasoning = (
            f"Selected {best_move} for its best depth-{self.depth} "
            f"evaluation. It offers {cell.honey - cell.bees:+d} net honey "
            f"with {risk_text}; searched {self.nodes_explored} positions."
        )
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
        moved = child.move_player(actor, move)
        if moved and not child.game_over:
            for observer in child.players:
                observer.update_possible_queen_cells(child.board)
            child.complete_turn()
        return child

    def _search_move(
        self, state, player_index, move, depth, alpha, beta, root_index
    ):
        actor = state.players[player_index]
        probability = self._queen_move_probability(actor, move)
        if probability == 1:
            return self._queen_terminal_value(
                state, player_index, root_index
            )

        child = self._apply_move(state, player_index, move)
        if probability == 0:
            return self._search(child, depth, alpha, beta, root_index)

        queen_value = self._queen_terminal_value(
            state, player_index, root_index
        )
        safe_probability = 1 - probability
        safe_alpha = (
            alpha - probability * queen_value
        ) / safe_probability
        safe_beta = (
            beta - probability * queen_value
        ) / safe_probability
        safe_value = self._search(
            child, depth, safe_alpha, safe_beta, root_index
        )
        return safe_probability * safe_value + probability * queen_value

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
                move_value = self._search_move(
                    state,
                    actor_index,
                    move,
                    depth - 1,
                    alpha,
                    beta,
                    root_index,
                )
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
            move_value = self._search_move(
                state,
                actor_index,
                move,
                depth - 1,
                alpha,
                beta,
                root_index,
            )
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
        my_moves = state.legal_moves(me)
        their_moves = state.legal_moves(other)

        # 1. Prioritize personal honey leadership
        score = 2.4 * float(me.honey) - 1.0 * float(other.honey)

        # 2. Rich future honey route harvesting
        score += 1.8 * best_future_honey_gain(state, me, depth=3) - 0.7 * best_future_honey_gain(state, other, depth=3)

        # 3. Available immediate move quality (surrounded by net-positive honey)
        if my_moves:
            score += 0.35 * sum(state.board.cells[p].honey - state.board.cells[p].bees for p in my_moves)

        # 4. Mobility control & anti-trapping
        score += 2.0 * len(my_moves) - 1.2 * len(their_moves)
        if not their_moves and other.alive:
            score += 35.0
        if not my_moves and me.alive:
            score -= 35.0

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

    @staticmethod
    def _queen_move_probability(player, position):
        candidates = player.possible_queen_cells
        if position in candidates and candidates:
            return 1.0 / len(candidates)
        return 0.0

    @staticmethod
    def _queen_terminal_value(state, actor_index, root_index):
        me = state.players[root_index]
        other = state.players[1 - root_index]
        if actor_index == root_index:
            return -10000 - other.honey
        return 10000 + me.honey

    def _terminal_value(self, state, root_index):
        me = state.players[root_index]
        other = state.players[1 - root_index]
        if state.winner is me:
            return 10000 + me.honey
        if state.winner is other:
            return -10000 - other.honey
        return me.honey - other.honey