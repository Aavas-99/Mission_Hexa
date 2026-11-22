import copy
import math
import random

from ai_heuristics import avoid_certain_queen_moves, move_profit_score
from config import (
    MCTS_ITERATIONS_EASY,
    MCTS_ITERATIONS_MEDIUM,
    MCTS_ITERATIONS_HARD,
    MCTS_ITERATIONS_WEAK,
    MCTS_ITERATIONS_STRONG,
)


class MCTSNode:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.total_reward = 0.0
        self.untried_moves = (
            avoid_certain_queen_moves(
                state.current_player(),
                state.legal_moves(state.current_player()),
            )
            if not state.game_over else []
        )


class MCTSAI:
    """Monte Carlo Tree Search using UCT and random rollouts."""

    def __init__(self, difficulty="hard"):
        difficulty = difficulty.lower()
        if difficulty == "easy":
            self.iterations = MCTS_ITERATIONS_EASY
        elif difficulty == "medium":
            self.iterations = MCTS_ITERATIONS_MEDIUM
        else:
            self.iterations = MCTS_ITERATIONS_HARD
        self.exploration_constant = math.sqrt(2)
        self.rollout_depth = 16
        self.simulations_completed = 0
        self.last_reasoning = None

    def choose_move(self, game, player):
        legal = avoid_certain_queen_moves(
            player, game.legal_moves(player)
        )
        if not legal:
            return None
        if len(legal) == 1:
            position = legal[0]
            cell = game.board.cells[position]
            self.last_reasoning = (
                f"Selected the only safe move, {position}; it offers "
                f"{cell.honey - cell.bees:+d} net honey."
            )
            return position

        root_index = game.players.index(player)
        root_state = self._safe_copy(game)
        root = MCTSNode(root_state)
        self.simulations_completed = 0

        for _ in range(self.iterations):
            node = root

            # Selection
            while not node.untried_moves and node.children and not node.state.game_over:
                node = self._select_child(node, root_index)

            # Expansion
            if node.untried_moves and not node.state.game_over:
                move = self._pick_expansion_move(
                    node.untried_moves,
                    node.state,
                )
                node.untried_moves.remove(move)
                actor_index = node.state.current_index
                child_state = self._apply_move(node.state, actor_index, move)
                child = MCTSNode(child_state, node, move)
                node.children.append(child)
                node = child

            # Simulation and backpropagation
            reward = self._rollout(node.state, root_index)
            self.simulations_completed += 1
            while node is not None:
                node.visits += 1
                node.total_reward += reward
                node = node.parent

        if not root.children:
            return random.choice(legal)

        best_child = max(root.children, key=lambda child: child.visits)
        move = best_child.move
        cell = game.board.cells[move]
        average_score = best_child.total_reward / best_child.visits
        self.last_reasoning = (
            f"Selected {move}, the most-visited search option "
            f"({best_child.visits}/{self.simulations_completed} simulations; "
            f"average rollout score {average_score:+.2f}). It offers "
            f"{cell.honey - cell.bees:+d} net honey."
        )
        return move

    def _safe_copy(self, game):
        state = copy.deepcopy(game)
        state.simulation_mode = True
        state.board.queen_position = None
        return state

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

    def _rollout_step(self, state, player_index, move):
        actor = state.players[player_index]
        moved = state.move_player(actor, move)
        if moved and not state.game_over:
            for observer in state.players:
                observer.update_possible_queen_cells(state.board)
            state.complete_turn()

    def _select_child(self, node, root_index):
        maximizing = node.state.current_index == root_index
        best, best_value = None, -float("inf")

        for child in node.children:
            if child.visits == 0:
                return child
            exploitation = child.total_reward / child.visits
            if not maximizing:
                exploitation = -exploitation
            exploration = self.exploration_constant * math.sqrt(
                math.log(max(1, node.visits)) / child.visits
            )
            value = exploitation + exploration
            if value > best_value:
                best, best_value = child, value
        return best

    def _pick_expansion_move(self, moves, state=None):
        if state is None or len(moves) < 2:
            return random.choice(moves)
        actor = state.current_player()
        ranked = sorted(
            moves,
            key=lambda position: move_profit_score(
                state, actor, position
            ),
            reverse=True,
        )
        return random.choice(ranked[:min(3, len(ranked))])

    def _rollout(self, state, root_index):
        current = copy.deepcopy(state)
        current.simulation_mode = True
        current.board.queen_position = None
        if current.game_over:
            if current.winner is current.players[root_index]:
                return 1.0
            if current.winner is current.players[1 - root_index]:
                return -1.0
            return 0.0

        queen_candidates = set(
            current.players[root_index].possible_queen_cells
        )
        if not queen_candidates:
            queen_candidates = {
                position
                for position, cell in current.board.cells.items()
                if not cell.visited
            }

        if queen_candidates:
            sampled_queen = random.choice(tuple(queen_candidates))
            visited_candidate = current.board.cells[sampled_queen]
            if visited_candidate.visited:
                owner = visited_candidate.owner
                if owner is None:
                    return 0.0
                return -1.0 if owner == root_index else 1.0
            current.board.queen_position = sampled_queen

        for _ in range(self.rollout_depth):
            if current.game_over:
                break

            actor = current.current_player()
            moves = current.legal_moves(actor)

            if not moves:
                current.pass_turn()
                continue

            moves = avoid_certain_queen_moves(actor, moves)
            ranked = sorted(
                moves,
                key=lambda position: move_profit_score(
                    current, actor, position
                ),
                reverse=True,
            )
            if random.random() < 0.8:
                move = random.choice(ranked[:min(3, len(ranked))])
            else:
                move = random.choice(moves)

            self._rollout_step(
                current, current.current_index, move
            )

        me = current.players[root_index]
        opponent = current.players[1 - root_index]

        if current.game_over:
            if current.winner is me:
                return 1.0
            if current.winner is opponent:
                return -1.0
            return 0.0

        honey_component = math.tanh((me.honey - opponent.honey) / 20.0)
        mobility_component = math.tanh(
            (len(current.legal_moves(me)) -
             len(current.legal_moves(opponent))) / 3.0
        )
        return 0.85 * honey_component + 0.15 * mobility_component
