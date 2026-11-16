import math
import pygame

from config import (
    WIDTH,
    HEIGHT,
    ROWS,
    COLS,
    HEX_SIZE,
    BOARD_OFFSET_X,
    BOARD_OFFSET_Y,
    PANEL_X,
    PANEL_WIDTH,
    WHITE,
    BLACK,
    PHEROMONE_COLOR
)

from themes import get_theme


class UI:
    def __init__(self, screen):
        self.screen = screen

        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 15)
        self.medium_font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 48)

    def hex_center(self, row, col):
        horizontal_spacing = HEX_SIZE * math.sqrt(3)
        vertical_spacing = HEX_SIZE * 1.5

        x = BOARD_OFFSET_X + HEX_SIZE + col * horizontal_spacing

        if row % 2 == 1:
            x += horizontal_spacing / 2

        y = BOARD_OFFSET_Y + HEX_SIZE + row * vertical_spacing

        return int(x), int(y)

    def hex_points(self, center):
        x, y = center
        points = []

        for i in range(6):
            angle = math.radians(60 * i - 30)

            points.append((
                x + HEX_SIZE * math.cos(angle),
                y + HEX_SIZE * math.sin(angle)
            ))

        return points

    def point_in_polygon(self, point, polygon):
        x, y = point
        inside = False

        j = len(polygon) - 1

        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            if ((yi > y) != (yj > y)):
                test_x = (xj - xi) * (y - yi) / (yj - yi) + xi

                if x < test_x:
                    inside = not inside

            j = i

        return inside

    def get_clicked_hex(self, position):
        for row in range(ROWS):
            for col in range(COLS):
                center = self.hex_center(row, col)
                points = self.hex_points(center)

                if self.point_in_polygon(position, points):
                    return row, col

        return None

    def draw_text(self, text, position, font, color):
        image = font.render(text, True, color)
        self.screen.blit(image, position)

    def draw_board(self, game, theme_index):
        theme = get_theme(theme_index)

        current_player = game.current_player()
        legal_moves = game.legal_moves(current_player)

        for position, cell in game.board.cells.items():
            row, col = position

            center = self.hex_center(row, col)
            points = self.hex_points(center)

            color = theme["visited"] if cell.visited else theme["cell"]

            pygame.draw.polygon(self.screen, color, points)

            border_color = theme["border"]
            border_width = 2

            if position in legal_moves and not game.game_over:
                border_color = theme["legal_move"]
                border_width = 4

            pygame.draw.polygon(
                self.screen,
                border_color,
                points,
                border_width
            )

            if not cell.visited:
                self.draw_text(
                    f"H {cell.honey}",
                    (center[0] - 22, center[1] - 18),
                    self.small_font,
                    BLACK
                )

                self.draw_text(
                    f"B {cell.bees}",
                    (center[0] - 22, center[1] + 5),
                    self.small_font,
                    BLACK
                )

            for player in game.players:
                if (
                    player.position == position
                    and player.alive
                ):
                    pygame.draw.circle(
                        self.screen,
                        player.color,
                        (center[0], center[1] + 24),
                        13
                    )

                    pygame.draw.circle(
                        self.screen,
                        WHITE,
                        (center[0], center[1] + 24),
                        13,
                        2
                    )

    def draw_sidebar(self, game, theme_index):
        theme = get_theme(theme_index)

        pygame.draw.rect(
            self.screen,
            theme["panel"],
            (PANEL_X, 0, PANEL_WIDTH, HEIGHT)
        )

        self.draw_text(
            "MISSION HEXA",
            (PANEL_X + 70, 40),
            self.medium_font,
            theme["accent"]
        )

        y = 120

        for player in game.players:
            self.draw_text(
                player.name,
                (PANEL_X + 30, y),
                self.font,
                player.color
            )

            self.draw_text(
                f"Honey: {player.honey}",
                (PANEL_X + 30, y + 30),
                self.small_font,
                theme["text"]
            )

            self.draw_text(
                f"Position: {player.position}",
                (PANEL_X + 30, y + 55),
                self.small_font,
                theme["text"]
            )

            self.draw_text(
                f"Queen possibilities: {len(player.possible_queen_cells)}",
                (PANEL_X + 30, y + 80),
                self.small_font,
                theme["text"]
            )

            y += 140

        self.draw_text(
            f"Turn: {game.turn}",
            (PANEL_X + 30, y),
            self.font,
            theme["accent"]
        )

        self.draw_text(
            f"Current: {game.current_player().name}",
            (PANEL_X + 30, y + 35),
            self.small_font,
            theme["text"]
        )

        self.draw_text(
            game.message[:48],
            (PANEL_X + 30, HEIGHT - 80),
            self.small_font,
            theme["text"]
        )

        self.draw_text(
            "[R] Restart   [T] Theme",
            (PANEL_X + 30, HEIGHT - 45),
            self.small_font,
            theme["text"]
        )

    def draw_game(self, game, theme_index):
        theme = get_theme(theme_index)

        self.screen.fill(theme["background"])

        self.draw_board(game, theme_index)
        self.draw_sidebar(game, theme_index)

        if game.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))

            self.screen.blit(overlay, (0, 0))

            if game.winner:
                text = f"{game.winner.name} WINS!"
                color = game.winner.color
            else:
                text = "DRAW!"
                color = WHITE

            image = self.big_font.render(text, True, color)

            rect = image.get_rect(
                center=(WIDTH // 2, HEIGHT // 2)
            )

            self.screen.blit(image, rect)