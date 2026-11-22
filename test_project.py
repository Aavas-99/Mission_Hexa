import unittest
from unittest.mock import patch

from game import MissionHexaGame
from minimax_ai import MinimaxAI
from mcts_ai import MCTSAI
from ai_heuristics import best_future_honey_gain


class MissionHexaLogicTests(unittest.TestCase):
    def setUp(self):
        self.game = MissionHexaGame("human_human")

    def test_players_use_mode_specific_display_names(self):
        ai_game = MissionHexaGame("ai_vs_ai")
        self.assertEqual(
            [player.name for player in ai_game.players],
            ["Minimax", "MCTS"],
        )

        human_minimax = MissionHexaGame("human_minimax")
        self.assertEqual(
            [player.name for player in human_minimax.players],
            ["Human", "Minimax"],
        )

        human_mcts = MissionHexaGame("human_mcts")
        self.assertEqual(
            [player.name for player in human_mcts.players],
            ["Human", "MCTS"],
        )

    def test_move_metadata_tracks_actor_and_ai_reasoning(self):
        player = self.game.current_player()
        move = self.game.legal_moves(player)[0]
        self.assertTrue(self.game.move_player(player, move))
        self.assertIs(self.game.last_move_by, player)
        self.assertIsNone(self.game.last_move_reasoning)

        ai = MinimaxAI("easy")
        ai_move = ai.choose_move(self.game, player)
        self.assertIn(ai_move, self.game.legal_moves(player))
        self.assertIn("Selected", ai.last_reasoning)

        mcts = MCTSAI("easy")
        mcts_move = mcts.choose_move(self.game, player)
        self.assertIn(mcts_move, self.game.legal_moves(player))
        self.assertIn("Selected", mcts.last_reasoning)

    def test_starting_players_are_safe_and_distinct(self):
        p1, p2 = self.game.players
        self.assertIsNotNone(p1.position)
        self.assertIsNotNone(p2.position)
        self.assertNotEqual(p1.position, p2.position)
        self.assertNotEqual(p1.position, self.game.board.queen_position)
        self.assertNotEqual(p2.position, self.game.board.queen_position)

    def test_beliefs_exclude_cells_safely_visited_by_either_player(self):
        for player in self.game.players:
            for position, cell in self.game.board.cells.items():
                if cell.visited:
                    self.assertNotIn(
                        position, player.possible_queen_cells
                    )

    def test_cell_honey_and_bees_remain_constant_across_turns(self):
        initial_values = {
            position: (cell.honey, cell.bees)
            for position, cell in self.game.board.cells.items()
        }

        for _ in range(8):
            self.game.complete_turn()

        final_values = {
            position: (cell.honey, cell.bees)
            for position, cell in self.game.board.cells.items()
        }
        self.assertEqual(final_values, initial_values)

    def test_future_route_evaluation_rewards_a_profitable_followup(self):
        player = self.game.current_player()
        opponent = self.game.opponent(player)
        first_moves = [
            position
            for position in self.game.board.get_neighbors(player.position)
            if position != opponent.position
        ]
        if not first_moves:
            self.skipTest("No first step available")

        first = first_moves[0]
        second_moves = [
            position
            for position in self.game.board.get_neighbors(first)
            if position not in (player.position, opponent.position)
        ]
        if not second_moves:
            self.skipTest("No follow-up step available")
        second = second_moves[0]

        for cell in self.game.board.cells.values():
            cell.visited = True
        self.game.board.cells[first].visited = False
        self.game.board.cells[second].visited = False
        self.game.board.cells[first].honey = 2
        self.game.board.cells[first].bees = 1
        self.game.board.cells[second].honey = 21
        self.game.board.cells[second].bees = 1

        self.assertGreater(
            best_future_honey_gain(self.game, player, depth=2), 10
        )

    def test_queen_move_eliminates_mover_and_ends_game(self):
        player = self.game.current_player()
        alternatives = [
            position
            for position in self.game.board.get_neighbors(player.position)
            if position != self.game.players[1 - self.game.current_index].position
            and not self.game.board.cells[position].visited
        ]
        if len(alternatives) < 2:
            self.skipTest("Queen move needs an alternative legal move")

        move_position = alternatives[0]
        self.game.board.queen_position = move_position
        cell = self.game.board.cells[move_position]
        if cell.bees > player.honey:
            player.honey = cell.bees
        moved = self.game.move_player(player, move_position)

        self.assertTrue(moved)
        self.assertFalse(player.alive)
        self.assertTrue(self.game.game_over)
        self.assertIs(self.game.winner, self.game.opponent(player))

    def test_forced_queen_move_is_passed_repeatedly(self):
        player, opponent = self.game.players
        player.position = (0, 0)
        opponent.position = (7, 7)
        self.game.current_index = 0
        self.game.board.queen_position = (0, 1)

        for cell in self.game.board.cells.values():
            cell.visited = True
        self.game.board.cells[player.position].visited = True
        self.game.board.cells[opponent.position].visited = True
        self.game.board.cells[(0, 1)].visited = False
        self.game.board.cells[(7, 6)].visited = False
        self.game.board.cells[(6, 7)].visited = False
        self.game.board.cells[(6, 6)].visited = False

        self.assertEqual(self.game.legal_moves(player), [])
        self.game.pass_turn()
        self.assertEqual(self.game.current_player(), opponent)
        self.assertFalse(self.game.game_over)

        self.assertTrue(self.game.move_player(opponent, (7, 6)))
        self.game.complete_turn()
        self.assertEqual(self.game.current_player(), player)
        self.assertEqual(self.game.legal_moves(player), [])

        self.game.pass_turn()
        self.assertEqual(self.game.current_player(), opponent)
        self.assertFalse(self.game.game_over)

    def test_ai_vs_ai_ends_when_one_player_has_no_moves_and_awards_leader(self):
        game = MissionHexaGame("ai_vs_ai")
        player1, player2 = game.players
        player1.position = (0, 0)
        player2.position = (7, 7)
        game.current_index = 0
        game.board.queen_position = (3, 3)

        for cell in game.board.cells.values():
            cell.visited = True
        game.board.cells[(7, 6)].visited = False

        player1.honey = 10
        player2.honey = 11
        game.pass_turn()

        self.assertTrue(game.game_over)
        self.assertIs(game.winner, player2)
        self.assertIn("MCTS wins on honey", game.message)

    def test_ai_vs_ai_keeps_player2_playing_until_they_take_the_lead(self):
        game = MissionHexaGame("ai_vs_ai")
        player1, player2 = game.players
        player1.position = (0, 0)
        player2.position = (7, 7)
        game.current_index = 0
        game.board.queen_position = (3, 3)

        for cell in game.board.cells.values():
            cell.visited = True
        game.board.cells[(7, 6)].visited = False
        game.board.cells[(6, 6)].visited = False
        game.board.cells[(7, 6)].honey = 1
        game.board.cells[(7, 6)].bees = 1
        game.board.cells[(6, 6)].honey = 20
        game.board.cells[(6, 6)].bees = 1
        player1.honey = 15
        player2.honey = 10

        game.pass_turn()

        self.assertFalse(game.game_over)
        self.assertEqual(game.current_player(), player2)

        self.assertTrue(game.move_player(player2, (7, 6)))
        game.complete_turn()

        self.assertFalse(game.game_over)
        self.assertEqual(game.current_player(), player2)

        self.assertTrue(game.move_player(player2, (6, 6)))
        game.complete_turn()

        self.assertTrue(game.game_over)
        self.assertIs(game.winner, player2)

    def test_ai_vs_ai_tie_ends_if_player2_cannot_move(self):
        game = MissionHexaGame("ai_vs_ai")
        game.current_index = 0
        for cell in game.board.cells.values():
            cell.visited = True
        game.players[0].honey = game.players[1].honey = 10

        game.pass_turn()

        self.assertTrue(game.game_over)
        self.assertIsNone(game.winner)
        self.assertIn("draw", game.message.lower())

    def test_pass_turn_does_not_switch_when_moves_exist(self):
        player = self.game.current_player()
        original_index = self.game.current_index
        if not self.game.legal_moves(player):
            self.game.pass_turn()
            self.assertNotEqual(self.game.current_index, original_index)
        else:
            self.game.pass_turn()
            self.assertEqual(self.game.current_index, original_index)

    def test_safe_visit_records_a_pheromone_clue_for_the_visitor(self):
        player = self.game.current_player()
        opponent = self.game.opponent(player)
        safe_moves = [
            position
            for position in self.game.legal_moves(player)
            if position != self.game.board.queen_position
        ]
        if not safe_moves:
            self.skipTest("Current player has no safe legal move")

        position = safe_moves[0]
        self.assertTrue(self.game.move_player(player, position))
        self.assertIn(position, player.knowledge)
        self.assertIsInstance(player.knowledge[position], bool)
        self.assertNotIn(position, opponent.knowledge)

    def test_minimax_penalizes_a_known_possible_queen_position(self):
        player = self.game.players[0]
        player.possible_queen_cells = {player.position}
        self.assertGreater(
            MinimaxAI._queen_move_risk(player, player.position), 0
        )

    def test_minimax_uses_expected_value_for_a_possible_queen_move(self):
        player = self.game.current_player()
        move = self.game.legal_moves(player)[0]
        other_candidate = next(
            position
            for position, cell in self.game.board.cells.items()
            if not cell.visited and position != move
        )
        player.possible_queen_cells = {move, other_candidate}
        ai = MinimaxAI("easy")
        root_index = self.game.players.index(player)
        safe_value = 40.0
        queen_value = -10000 - self.game.opponent(player).honey

        with patch.object(ai, "_search", return_value=safe_value):
            value = ai._search_move(
                self.game,
                root_index,
                move,
                0,
                -float("inf"),
                float("inf"),
                root_index,
            )

        self.assertAlmostEqual(value, 0.5 * safe_value + 0.5 * queen_value)

    def test_minimax_alpha_beta_matches_exact_value_inside_narrow_window(self):
        player = self.game.current_player()
        opponent = self.game.opponent(player)
        player_moves = self.game.legal_moves(player)
        opponent_moves = self.game.legal_moves(opponent)
        if not player_moves or not opponent_moves:
            self.skipTest("Both players need legal moves")

        unvisited = [
            position
            for position, cell in self.game.board.cells.items()
            if not cell.visited
        ]
        player_extra = next(
            position for position in unvisited if position != player_moves[0]
        )
        opponent_extra = next(
            position
            for position in unvisited
            if position not in (opponent_moves[0], player_extra)
        )
        player.possible_queen_cells = {player_moves[0], player_extra}
        opponent.possible_queen_cells = {
            opponent_moves[0], opponent_extra
        }

        ai = MinimaxAI("medium")
        state = ai._copy_for_search(self.game)
        root_index = state.players.index(state.current_player())
        depth = 3
        exact = ai._search(
            state, depth, -float("inf"), float("inf"), root_index
        )
        bounded = ai._search(
            state, depth, exact - 0.01, exact + 0.01, root_index
        )

        self.assertAlmostEqual(bounded, exact)

    def test_search_ais_avoid_a_certain_queen_move_when_alternatives_exist(self):
        player = self.game.current_player()
        legal = self.game.legal_moves(player)
        if len(legal) < 2:
            self.skipTest("Current player needs two legal moves")

        queen_position = legal[0]
        self.game.board.queen_position = queen_position
        player.possible_queen_cells = {queen_position}
        safe_moves = set(legal) - {queen_position}

        minimax_move = MinimaxAI("easy").choose_move(self.game, player)
        mcts_move = MCTSAI("easy").choose_move(self.game, player)
        self.assertIn(minimax_move, safe_moves)
        self.assertIn(mcts_move, safe_moves)

    def test_search_clone_does_not_modify_original(self):
        clone = self.game.clone_for_search()
        self.assertTrue(clone.simulation_mode)
        self.assertIsNone(clone.board.queen_position)
        self.assertIsNotNone(self.game.board.queen_position)

    def test_minimax_search_updates_queen_beliefs_after_safe_simulated_move(self):
        player = self.game.current_player()
        move = self.game.legal_moves(player)[0]
        for observer in self.game.players:
            observer.possible_queen_cells.add(move)

        child = MinimaxAI("easy")._apply_move(
            self.game, self.game.players.index(player), move
        )

        for observer in child.players:
            self.assertNotIn(move, observer.possible_queen_cells)

    def test_mcts_search_updates_queen_beliefs_after_safe_simulated_move(self):
        player = self.game.current_player()
        move = self.game.legal_moves(player)[0]
        for observer in self.game.players:
            observer.possible_queen_cells.add(move)

        child = MCTSAI("easy")._apply_move(
            self.game, self.game.players.index(player), move
        )

        for observer in child.players:
            self.assertNotIn(move, observer.possible_queen_cells)

    def test_simulation_resolves_sampled_queen_position(self):
        player = self.game.current_player()
        candidates = [
            position
            for position in self.game.legal_moves(player)
            if not self.game.board.cells[position].visited
        ]
        if not candidates:
            self.skipTest("Current player has no legal moves")

        clone = self.game.clone_for_search()
        move = candidates[0]
        clone.board.queen_position = move
        moved_player = clone.current_player()
        self.assertTrue(clone.move_player(moved_player, move))
        self.assertTrue(clone.game_over)
        self.assertFalse(moved_player.alive)

    def test_both_search_algorithms_return_legal_moves(self):
        player = self.game.current_player()
        legal = self.game.legal_moves(player)
        if not legal:
            self.skipTest("Current player has no legal moves")

        minimax_move = MinimaxAI("easy").choose_move(self.game, player)
        mcts_move = MCTSAI("easy").choose_move(self.game, player)
        self.assertIn(minimax_move, legal)
        self.assertIn(mcts_move, legal)


if __name__ == "__main__":
    unittest.main()
