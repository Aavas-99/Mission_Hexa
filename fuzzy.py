def _low(x, a, b):
    if x <= a:
        return 1.0
    if x >= b:
        return 0.0
    return (b - x) / (b - a)


def _high(x, a, b):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    return (x - a) / (b - a)


def _medium(x, a, m, b):
    if x <= a or x >= b:
        return 0.0
    if x <= m:
        return (x - a) / (m - a)
    return (b - x) / (b - m)


def evaluate_move(player, cell, position=None, knowledge_player=None):
    """
    Mamdani-style rule activation with weighted-average defuzzification.
    Risk uses only the designated observer's already-known belief set.
    """
    if cell is None or cell.bees > player.honey:
        return 0.0

    observer = knowledge_player or player
    reward = cell.honey
    cost = cell.bees
    reserve = player.honey

    reward_high = _high(reward, 10, 25)
    reward_low = _low(reward, 5, 15)
    cost_low = _low(cost, 2, 6)
    cost_high = _high(cost, 4, 9)
    reserve_high = _high(reserve, 10, 25)
    reserve_low = _low(reserve, 4, 14)
    cost_medium = _medium(cost, 2, 5, 8)

    rules = [
        (min(reward_high, cost_low, reserve_high), 95),
        (min(reward_high, cost_low), 82),
        (min(reward_high, cost_medium), 62),
        (min(reward_low, cost_high), 28),
        (min(cost_high, reserve_low), 12),
    ]

    denominator = sum(strength for strength, _ in rules)
    score = (
        sum(strength * output for strength, output in rules) / denominator
        if denominator else 45.0
    )

    if position is not None and position in observer.possible_queen_cells:
        score -= 22.0

    return max(0.0, min(100.0, score))


def evaluate_position(player, board, knowledge_player=None):
    if player.position is None:
        return 0.0

    scores = []
    for position in board.get_neighbors(player.position):
        cell = board.cells[position]
        if cell.visited or cell.bees > player.honey:
            continue
        scores.append(
            evaluate_move(player, cell, position, knowledge_player)
        )

    return sum(scores) / len(scores) if scores else 0.0


def get_best_fuzzy_move(game, player):
    moves = game.legal_moves(player)
    if not moves:
        return None
    return max(
        moves,
        key=lambda pos: evaluate_move(
            player, game.board.cells[pos], pos
        )
    )
