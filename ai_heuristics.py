def avoid_certain_queen_moves(player, moves):
    candidates = player.possible_queen_cells
    if len(candidates) != 1:
        return list(moves)

    queen_cell = next(iter(candidates))
    safe_moves = [move for move in moves if move != queen_cell]
    return safe_moves or list(moves)


def best_future_honey_gain(game, player, depth=2, discount=0.5):
    if player.position is None or depth <= 0:
        return 0.0

    blocked = {
        position
        for position, cell in game.board.cells.items()
        if cell.visited
    }
    opponent = game.opponent(player)
    if opponent.alive and opponent.position is not None:
        blocked.add(opponent.position)

    if len(player.possible_queen_cells) == 1:
        blocked.add(next(iter(player.possible_queen_cells)))

    def search(position, honey, remaining, visited):
        if remaining == 0:
            return 0.0

        best = 0.0
        for next_position in game.board.get_neighbors(position):
            if next_position in visited:
                continue

            cell = game.board.cells[next_position]
            if cell.bees > honey:
                continue

            gain = cell.honey - cell.bees
            future = search(
                next_position,
                honey + gain,
                remaining - 1,
                visited | {next_position},
            )
            best = max(best, gain + discount * future)
        return best

    return search(player.position, player.honey, depth, blocked)


def move_profit_score(game, player, position):
    cell = game.board.cells[position]
    gain = cell.honey - cell.bees
    next_honey = player.honey + gain

    opponent = game.opponent(player)
    blocked = {
        position
        for position, visited_cell in game.board.cells.items()
        if visited_cell.visited
    }
    blocked.add(position)
    if opponent.alive and opponent.position is not None:
        blocked.add(opponent.position)

    if len(player.possible_queen_cells) == 1:
        blocked.add(next(iter(player.possible_queen_cells)))

    next_gain = 0
    for next_position in game.board.get_neighbors(position):
        if next_position in blocked:
            continue
        next_cell = game.board.cells[next_position]
        if next_cell.bees <= next_honey:
            next_gain = max(
                next_gain,
                next_cell.honey - next_cell.bees,
            )

    candidates = player.possible_queen_cells
    risk = (
        10000.0 / len(candidates)
        if position in candidates and candidates else 0.0
    )
    return gain + 0.5 * next_gain - risk
