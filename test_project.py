import unittest

from game import MissionHexaGame
from minimax_ai import MinimaxAI
from mcts_ai import MCTSAI
from ai_heuristics import best_future_honey_gain


class MissionHexaLogicTests(unittest.TestCase):
    def setUp(self):
        self.game = MissionHexaGame("human_human")

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
        if not alternatives:
            self.skipTest("No unvisited neighbor available for this random board")

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
