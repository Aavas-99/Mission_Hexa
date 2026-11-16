import pygame

from config import WIDTH, HEIGHT, FPS
from themes import THEMES

from game import MissionHexaGame
from ui import UI


def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    pygame.display.set_caption("Mission Hexa")

    clock = pygame.time.Clock()

    ui = UI(screen)

    game = MissionHexaGame()

    theme_index = 0

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game = MissionHexaGame()

                elif event.key == pygame.K_t:
                    theme_index = (theme_index + 1) % len(THEMES)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not game.game_over:
                    player = game.current_player()

                    clicked_cell = ui.get_clicked_hex(event.pos)

                    if clicked_cell in game.legal_moves(player):
                        game.move_player(player, clicked_cell)

                        if not game.game_over:
                            game.complete_turn()

        if not game.game_over:
            if not game.legal_moves(game.current_player()):
                game.pass_turn()

        ui.draw_game(game, theme_index)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()