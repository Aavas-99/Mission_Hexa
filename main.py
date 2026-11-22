import sys
import pygame

from config import WIDTH, HEIGHT, FPS, SPEED_VALUES
from themes import THEMES
from game import MissionHexaGame
from minimax_ai import MinimaxAI
from mcts_ai import MCTSAI
from ui import UI


def create_ai(player, difficulty, ai_vs_ai=False):
    if player.ai_type == "minimax":
        return MinimaxAI("hard" if ai_vs_ai else difficulty)
    if player.ai_type == "mcts":
        return MCTSAI("easy" if ai_vs_ai else difficulty)
    return None


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mission Hexa")
    clock = pygame.time.Clock()
    ui = UI(screen)

    theme_index = 0
    difficulty = "medium"
    difficulty_options = ["easy", "medium", "hard"]
    difficulty_index = 1
    speed_options = ["SLOW", "NORMAL", "FAST"]
    speed_index = 1
    speed = speed_options[speed_index]

    mode = "human_minimax"
    game = None
    ai_players = {}
    ai_timer = 0.0
    menu = True
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if menu:
                        running = False
                    else:
                        menu = True

                elif event.key == pygame.K_t:
                    theme_index = (theme_index + 1) % len(THEMES)

                elif event.key == pygame.K_d:
                    difficulty_index = (
                        difficulty_index + 1
                    ) % len(difficulty_options)
                    difficulty = difficulty_options[difficulty_index]

                elif event.key == pygame.K_s:
                    speed_index = (speed_index + 1) % len(speed_options)
                    speed = speed_options[speed_index]

                elif event.key == pygame.K_r and not menu:
                    game = MissionHexaGame(mode, difficulty)
                    ai_players = {
                        i: create_ai(player, difficulty, mode == "ai_vs_ai")
                        for i, player in enumerate(game.players)
                        if not player.is_human
                    }
                    ai_timer = 0.0

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu:
                    for key, rect in ui.menu_buttons.items():
                        if rect.collidepoint(event.pos):
                            mode = key
                            game = MissionHexaGame(mode, difficulty)
                            ai_players = {
                                i: create_ai(player, difficulty, mode == "ai_vs_ai")
                                for i, player in enumerate(game.players)
                                if not player.is_human
                            }
                            ai_timer = 0.0
                            menu = False
                            break
                elif game and not game.game_over:
                    player = game.current_player()
                    if player.is_human:
                        position = ui.get_clicked_hex(event.pos)
                        if position in game.legal_moves(player):
                            moved = game.move_player(player, position)
                            if moved and not game.game_over:
                                game.complete_turn()
                            ai_timer = 0.0

        if menu:
            ui.draw_menu(theme_index, mode, difficulty, speed)
        else:
            if game and not game.game_over:
                player = game.current_player()

                if not game.legal_moves(player):
                    game.pass_turn()
                    ai_timer = 0.0

                elif not player.is_human:
                    ai_timer += dt
                    delay = SPEED_VALUES[speed]
                    if ai_timer >= delay:
                        ai = ai_players.get(game.current_index)
                        move = ai.choose_move(game, player) if ai else None

                        if move is not None and move in game.legal_moves(player):
                            moved = game.move_player(player, move)
                            if moved:
                                game.last_move_reasoning = ai.last_reasoning
                            if moved and not game.game_over:
                                game.complete_turn()
                        else:
                            game.pass_turn()

                        ai_timer = 0.0

            ui.draw_game(game, theme_index, difficulty, speed)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()