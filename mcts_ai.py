import copy
import math
import random

from fuzzy import fuzzy_move_score
from minimax_ai import simulate_move


class MCTSNode:
    def __init__(
        self,
        game,
        player_index,
        root_player_index,
        parent=None,
        move=None
    ):
        self.game = game
        self.player_index = player_index
        self.root_player_index = root_player_index

        self.parent = parent
        self.move = move

        self.children = []

        self.visits = 0
        self.wins = 0.0

        player = game.players[player_index]
        self.untried_moves = game.legal_moves(player)

    def uct_score(self):
        if self.visits == 0:
            return float("inf")

        exploitation = self.wins / self.visits

        exploration = 1.41 * math.sqrt(
            math.log(self.parent.visits + 1) / self.visits
        )

        return exploitation + exploration

    def best_child(self):
        return max(
            self.children,
            key=lambda child: child.uct_score()
        )

    def expand(self):
        if not self.untried_moves:
            return None

        player = self.game.players[self.player_index]

        self.untried_moves.sort(
            key=lambda move: fuzzy_move_score(
                player,
                self.game.board.cells[move],
                move
            ),
            reverse=True
        )

        move = self.untried_moves.pop(0)

        new_game = simulate_move(
            self.game,
            self.player_index,
            move
        )

        child = MCTSNode(
            new_game,
            1 - self.player_index,
            self.root_player_index,
            self,
            move
        )

        self.children.append(child)

        return child


def mcts_rollout(game, root_player_index, max_steps=10):
    simulation = copy.deepcopy(game)

    steps = 0

    while not simulation.game_over and steps < max_steps:
        player = simulation.current_player()

        moves = simulation.legal_moves(player)

        if not moves:
            simulation.switch_turn()
            steps += 1
            continue

        scores = []

        for move in moves:
            score = fuzzy_move_score(
                player,
                simulation.board.cells[move],
                move
            )

            scores.append(score + 1)

        move = random.choices(
            moves,
            weights=scores,
            k=1
        )[0]

        simulation.move_player(player, move)

        if not simulation.game_over:
            simulation.switch_turn()

        steps += 1

    root_player = simulation.players[root_player_index]
    opponent = simulation.players[1 - root_player_index]

    if not root_player.alive:
        return 0.0

    if not opponent.alive:
        return 1.0

    if root_player.honey > opponent.honey:
        return 1.0

    if root_player.honey == opponent.honey:
        return 0.5

    return 0.0


def mcts_best_move(game, player, iterations=50):
    root_index = game.players.index(player)

    root = MCTSNode(
        copy.deepcopy(game),
        root_index,
        root_index
    )

    if not root.untried_moves:
        return None

    for _ in range(iterations):
        node = root

        while (
            not node.untried_moves
            and node.children
            and not node.game.game_over
        ):
            node = node.best_child()

        if node.untried_moves and not node.game.game_over:
            expanded = node.expand()

            if expanded is not None:
                node = expanded

        result = mcts_rollout(
            node.game,
            root_index
        )

        while node is not None:
            node.visits += 1
            node.wins += result
            node = node.parent

    if not root.children:
        return random.choice(game.legal_moves(player))

    best = max(
        root.children,
        key=lambda child: child.visits
    )

    return best.move