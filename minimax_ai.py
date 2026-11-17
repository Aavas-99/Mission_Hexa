import copy

from fuzzy import fuzzy_move_score


def simulate_move(game, player_index, move):
    new_game = copy.deepcopy(game)

    player = new_game.players[player_index]
    cell = new_game.board.cells[move]

    player.position = move
    player.visited_cells.append(move)

    cell.visited = True

    if cell.has_queen:
        player.alive = False
        new_game.game_over = True
        new_game.winner = new_game.players[1 - player_index]

        return new_game

    player.honey -= cell.bees
    player.honey += cell.honey

    player.update_knowledge(new_game.board, move)

    new_game.current_index = 1 - player_index

    return new_game


def evaluate_state(game, ai_index):
    ai_player = game.players[ai_index]
    opponent = game.players[1 - ai_index]

    if not ai_player.alive:
        return -10000

    if not opponent.alive:
        return 10000

    score = ai_player.honey - opponent.honey

    ai_moves = game.legal_moves(ai_player)
    opponent_moves = game.legal_moves(opponent)

    score += (len(ai_moves) - len(opponent_moves)) * 3

    for move in ai_moves:
        score += 0.05 * fuzzy_move_score(
            ai_player,
            game.board.cells[move],
            move
        )

    for move in opponent_moves:
        score -= 0.05 * fuzzy_move_score(
            opponent,
            game.board.cells[move],
            move
        )

    return score


def minimax(game, depth, alpha, beta, maximizing, ai_index):
    if depth == 0 or game.game_over:
        return evaluate_state(game, ai_index)

    current_index = ai_index if maximizing else 1 - ai_index

    player = game.players[current_index]
    moves = game.legal_moves(player)

    if not moves:
        return evaluate_state(game, ai_index)

    if maximizing:
        best_value = -float("inf")

        for move in moves:
            new_game = simulate_move(game, current_index, move)

            value = minimax(
                new_game,
                depth - 1,
                alpha,
                beta,
                False,
                ai_index
            )

            best_value = max(best_value, value)
            alpha = max(alpha, best_value)

            if beta <= alpha:
                break

        return best_value

    best_value = float("inf")

    for move in moves:
        new_game = simulate_move(game, current_index, move)

        value = minimax(
            new_game,
            depth - 1,
            alpha,
            beta,
            True,
            ai_index
        )

        best_value = min(best_value, value)
        beta = min(beta, best_value)

        if beta <= alpha:
            break

    return best_value


def minimax_best_move(game, player, depth=2):
    moves = game.legal_moves(player)

    if not moves:
        return None

    player_index = game.players.index(player)

    best_move = None
    best_value = -float("inf")

    for move in moves:
        new_game = simulate_move(game, player_index, move)

        value = minimax(
            new_game,
            depth - 1,
            -float("inf"),
            float("inf"),
            False,
            player_index
        )

        if move in player.possible_queen_cells:
            value -= 500

        if value > best_value:
            best_value = value
            best_move = move

    return best_move