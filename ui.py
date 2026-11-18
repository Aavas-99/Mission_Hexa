import math
import pygame

from config import (
    WIDTH, HEIGHT, ROWS, COLS, HEX_SIZE,
    BOARD_OFFSET_X, BOARD_OFFSET_Y, PANEL_X, PANEL_WIDTH,
    WHITE, BLACK, PHEROMONE_COLOR,
)
from themes import get_theme, THEMES


class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 19)
        self.small_font = pygame.font.SysFont("Arial", 15)
        self.medium_font = pygame.font.SysFont("Arial", 29)
        self.big_font = pygame.font.SysFont("Arial", 48)
        self.menu_buttons = {}

    def hex_center(self, row, col):
        spacing_x = HEX_SIZE * math.sqrt(3)
        spacing_y = HEX_SIZE * 1.5
        x = BOARD_OFFSET_X + HEX_SIZE + col * spacing_x
        if row % 2:
            x += spacing_x / 2
        y = BOARD_OFFSET_Y + HEX_SIZE + row * spacing_y
        return int(x), int(y)

    def hex_points(self, center):
        x, y = center
        return [
            (
                x + HEX_SIZE * math.cos(math.radians(60 * i - 30)),
                y + HEX_SIZE * math.sin(math.radians(60 * i - 30)),
            )
            for i in range(6)
        ]

    @staticmethod
    def point_in_polygon(point, polygon):
        x, y = point
        inside = False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if (yi > y) != (yj > y):
                test_x = (xj - xi) * (y - yi) / (yj - yi) + xi
                if x < test_x:
                    inside = not inside
            j = i
        return inside

    def get_clicked_hex(self, position):
        for row in range(ROWS):
            for col in range(COLS):
                if self.point_in_polygon(
                    position, self.hex_points(self.hex_center(row, col))
                ):
                    return row, col
        return None

    def draw_text(self, text, position, font=None, color=None):
        font = font or self.font
        color = color or WHITE
        image = font.render(str(text), True, color)
        self.screen.blit(image, position)

    def draw_button(self, rect, text, theme, key=None):
        pygame.draw.rect(
            self.screen, theme["button"], rect, border_radius=10
        )
        pygame.draw.rect(
            self.screen, theme["accent"], rect, 2, border_radius=10
        )
        image = self.font.render(text, True, theme["text"])
        self.screen.blit(image, image.get_rect(center=rect.center))
        if key:
            self.menu_buttons[key] = rect

    def draw_menu(self, theme_index, mode, difficulty, speed):
        theme = get_theme(theme_index)
        self.screen.fill(theme["background"])
        title = self.big_font.render("MISSION HEXA", True, theme["accent"])
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 135)))
        subtitle = self.font.render(
            "A hidden-Queen honeycomb strategy game",
            True, theme["text"]
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 190)))

        self.draw_text(
            "Choose a game mode", (565, 260), self.medium_font, theme["text"]
        )
        self.menu_buttons = {}
        options = [
            ("human_minimax", "Human vs Minimax AI"),
            ("human_mcts", "Human vs MCTS AI"),
            ("ai_vs_ai", "Minimax AI vs MCTS AI"),
            ("human_human", "Human vs Human"),
        ]
        for i, (key, label) in enumerate(options):
            self.draw_button(
                pygame.Rect(525, 315 + i * 65, 450, 48),
                label, theme, key
            )
            if mode == key:
                pygame.draw.rect(
                    self.screen, theme["legal_move"],
                    self.menu_buttons[key], 3, border_radius=10
                )

        self.draw_text(
            f"Difficulty: {difficulty.upper()}   [D to change]",
            (525, 600), self.font, theme["text"]
        )
        self.draw_text(
            f"AI speed: {speed}   [S to change]",
            (525, 635), self.font, theme["text"]
        )
        self.draw_text(
            f"Theme: {theme['name']}   [T to change]",
            (525, 670), self.font, theme["text"]
        )
        self.draw_text(
            "Click a mode to start. ESC exits.",
            (525, 735), self.small_font, theme["text"]
        )

    def draw_board(self, game, theme_index):
        theme = get_theme(theme_index)
        current = game.current_player()
        legal = set(game.legal_moves(current)) if not game.game_over else set()

        for position, cell in game.board.cells.items():
            center = self.hex_center(*position)
            points = self.hex_points(center)
            fill = theme["visited"] if cell.visited else theme["cell"]
            pygame.draw.polygon(self.screen, fill, points)

            border = theme["legal_move"] if position in legal else theme["border"]
            width = 4 if position in legal else 2
            pygame.draw.polygon(self.screen, border, points, width)

            if not cell.visited:
                self.draw_text(
                    f"H {cell.honey}",
                    (center[0] - 22, center[1] - 16),
                    self.small_font, BLACK
                )
                self.draw_text(
                    f"B {cell.bees}",
                    (center[0] - 22, center[1] + 4),
                    self.small_font, BLACK
                )
            elif cell.owner is not None:
                owner = game.players[cell.owner]
                label = "P1" if cell.owner == 0 else "P2"
                self.draw_text(
                    label,
                    (center[0] - 11, center[1] - 8),
                    self.small_font, WHITE
                )

            for player in game.players:
                if player.alive and player.position == position:
                    pygame.draw.circle(
                        self.screen, player.color,
                        (center[0], center[1] + 22), 12
                    )
                    pygame.draw.circle(
                        self.screen, WHITE,
                        (center[0], center[1] + 22), 12, 2
                    )

    def draw_sidebar(self, game, theme_index, difficulty, speed):
        theme = get_theme(theme_index)
        pygame.draw.rect(
            self.screen, theme["panel"],
            (PANEL_X, 0, PANEL_WIDTH, HEIGHT)
        )
        self.draw_text(
            "MISSION HEXA", (PANEL_X + 30, 32),
            self.medium_font, theme["accent"]
        )
        self.draw_text(
            f"Mode: {game.mode.replace('_', ' ').title()}",
            (PANEL_X + 28, 85), self.small_font, theme["text"]
        )

        y = 130
        for index, player in enumerate(game.players):
            pygame.draw.circle(
                self.screen, player.color, (PANEL_X + 38, y + 10), 9
            )
            self.draw_text(
                player.name + (" (AI)" if not player.is_human else " (Human)"),
                (PANEL_X + 58, y), self.font, player.color
            )
            self.draw_text(
                f"Honey: {player.honey}",
                (PANEL_X + 35, y + 31), self.small_font, theme["text"]
            )
            self.draw_text(
                f"Position: {player.position}",
                (PANEL_X + 35, y + 53), self.small_font, theme["text"]
            )
            self.draw_text(
                f"Cells visited: {len(player.visited_cells)}",
                (PANEL_X + 35, y + 75), self.small_font, theme["text"]
            )
            y += 135

        current = game.current_player()
        self.draw_text(
            f"Turn: {game.turn}", (PANEL_X + 30, y + 3),
            self.font, theme["accent"]
        )
        self.draw_text(
            f"Current: {current.name}", (PANEL_X + 30, y + 34),
            self.font, current.color
        )
        self.draw_text(
            f"Queen possibilities: {len(current.possible_queen_cells)}",
            (PANEL_X + 30, y + 67), self.small_font, theme["text"]
        )

        if current.knowledge:
            latest_position = list(current.knowledge)[-1]
            clue = current.knowledge[latest_position]
            clue_text = "Detected nearby" if clue else "Not detected"
            self.draw_text(
                f"Latest pheromone: {clue_text}",
                (PANEL_X + 30, y + 90), self.small_font,
                PHEROMONE_COLOR if clue else theme["text"]
            )

        self.draw_text(
            f"Difficulty: {difficulty.upper()}",
            (PANEL_X + 30, HEIGHT - 150), self.small_font, theme["text"]
        )
        self.draw_text(
            f"AI speed: {speed}",
            (PANEL_X + 30, HEIGHT - 127), self.small_font, theme["text"]
        )
        self.draw_text(
            "R Restart | T Theme | ESC Menu",
            (PANEL_X + 30, HEIGHT - 85), self.small_font, theme["text"]
        )
        self.draw_text(
            "D Difficulty | S Speed",
            (PANEL_X + 30, HEIGHT - 60), self.small_font, theme["text"]
        )
        self.draw_text(
            game.message[:48],
            (PANEL_X + 30, HEIGHT - 30), self.small_font, theme["accent"]
        )

    def draw_game(self, game, theme_index, difficulty="medium", speed="NORMAL"):
        theme = get_theme(theme_index)
        self.screen.fill(theme["background"])
        self.draw_board(game, theme_index)
        self.draw_sidebar(game, theme_index, difficulty, speed)

        if game.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))
            self.screen.blit(overlay, (0, 0))
            if game.winner:
                label = f"{game.winner.name} WINS!"
                color = game.winner.color
            else:
                label, color = "DRAW!", WHITE
            image = self.big_font.render(label, True, color)
            self.screen.blit(
                image, image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            )
            hint = self.font.render(
                "Press R to restart or ESC for menu",
                True, WHITE
            )
            self.screen.blit(
                hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 65))
            )