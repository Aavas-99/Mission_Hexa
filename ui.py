import math
import pygame

from config import (
    WIDTH, HEIGHT, ROWS, COLS, HEX_SIZE,
    BOARD_OFFSET_X, BOARD_OFFSET_Y, PANEL_X, PANEL_WIDTH,
    WHITE, BLACK, PHEROMONE_COLOR,
)
from themes import get_theme, THEMES

HEADER_HEIGHT = 78
PANEL_TOP = HEADER_HEIGHT + 10
CARD_RADIUS = 16

FONT_STACK = ["Segoe UI", "Arial", "Helvetica", "sans-serif"]


class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(FONT_STACK, 18)
        self.small_font = pygame.font.SysFont(FONT_STACK, 14)
        self.tiny_font = pygame.font.SysFont(FONT_STACK, 12)
        self.medium_font = pygame.font.SysFont(FONT_STACK, 26, bold=True)
        self.big_font = pygame.font.SysFont(FONT_STACK, 50, bold=True)
        self.title_font = pygame.font.SysFont(FONT_STACK, 66, bold=True)
        self.num_font = pygame.font.SysFont(FONT_STACK, 30, bold=True)
        self.cell_font = pygame.font.SysFont(FONT_STACK, 15, bold=True)
        self.menu_buttons = {}
        self._gradient_cache = {}
        self._disc_cache = {}
        self._ring_cache = {}

    # ------------------------------------------------------------------ #
    # helpers                                                             #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _mix(c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def _fill_gradient(self, top_color, bottom_color):
        key = (tuple(top_color), tuple(bottom_color))
        if key not in self._gradient_cache:
            column = pygame.Surface((1, HEIGHT))
            for y in range(HEIGHT):
                t = y / max(1, HEIGHT - 1)
                column.set_at((0, y), self._mix(top_color, bottom_color, t))
            self._gradient_cache[key] = pygame.transform.scale(
                column, (WIDTH, HEIGHT)
            )
        self.screen.blit(self._gradient_cache[key], (0, 0))

    def _disc(self, color, radius, alpha=255):
        radius = max(1, int(radius))
        alpha = max(0, min(255, int(alpha)))
        key = (tuple(color), radius, alpha)
        if key not in self._disc_cache:
            d = radius * 2
            surf = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (radius, radius), radius)
            self._disc_cache[key] = surf
        return self._disc_cache[key]

    def _hex_ring(self, color, radius, width, alpha):
        radius = int(radius)
        key = (tuple(color), radius, width, alpha)
        if key not in self._ring_cache:
            d = (radius + width) * 2 + 4
            surf = pygame.Surface((d, d), pygame.SRCALPHA)
            pts = self.hex_points((d // 2, d // 2), radius)
            pygame.draw.polygon(surf, (*color, alpha), pts, width)
            self._ring_cache[key] = surf
        return self._ring_cache[key]

    @staticmethod
    def _muted(theme):
        return theme.get(
            "muted", UI._mix(theme["text"], theme["background"], 0.4)
        )

    # ------------------------------------------------------------------ #
    # geometry (unchanged interface, used by main.py mouse handling)      #
    # ------------------------------------------------------------------ #
    def hex_center(self, row, col):
        spacing_x = HEX_SIZE * math.sqrt(3)
        spacing_y = HEX_SIZE * 1.5
        x = BOARD_OFFSET_X + HEX_SIZE + col * spacing_x
        if row % 2:
            x += spacing_x / 2
        y = BOARD_OFFSET_Y + HEX_SIZE + row * spacing_y
        return int(x), int(y)

    def hex_points(self, center, size=HEX_SIZE):
        x, y = center
        return [
            (
                x + size * math.cos(math.radians(60 * i - 30)),
                y + size * math.sin(math.radians(60 * i - 30)),
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

    # ------------------------------------------------------------------ #
    # text & buttons                                                      #
    # ------------------------------------------------------------------ #
    def draw_text(self, text, position, font=None, color=None,
                  center=None, shadow=False):
        font = font or self.font
        color = WHITE if color is None else color
        image = font.render(str(text), True, color)
        rect = image.get_rect()
        if center is not None:
            rect.center = center
        else:
            rect.topleft = position
        if shadow:
            shade = font.render(str(text), True, (0, 0, 0))
            self.screen.blit(
                shade, shade.get_rect(
                    center=(rect.centerx + 2, rect.centery + 2)
                )
            )
        self.screen.blit(image, rect)
        return rect

    def draw_button(self, rect, text, theme, key=None,
                    selected=False, hovered=False):
        shadow = rect.move(0, 4)
        pygame.draw.rect(
            self.screen,
            self._mix(theme["background"], (0, 0, 0), 0.5),
            shadow, border_radius=13,
        )
        fill = theme["button_hover"] if hovered else theme["button"]
        pygame.draw.rect(self.screen, fill, rect, border_radius=13)
        border = (
            theme["accent"] if selected
            else self._mix(theme["border"], theme["text"], 0.25)
        )
        pygame.draw.rect(
            self.screen, border, rect, 3 if selected else 2, border_radius=13
        )
        if selected:
            bar = pygame.Rect(
                rect.x + 12, rect.y + 13, 5, rect.height - 26
            )
            pygame.draw.rect(
                self.screen, theme["legal_move"], bar, border_radius=3
            )
        image = self.font.render(text, True, theme["text"])
        self.screen.blit(image, image.get_rect(center=rect.center))
        if key:
            self.menu_buttons[key] = rect

    def _key_hint(self, x, y, key, label, theme):
        muted = self._muted(theme)
        kw = max(34, self.tiny_font.size(key)[0] + 18)
        chip = pygame.Rect(x, y, kw, 22)
        pygame.draw.rect(
            self.screen,
            self._mix(theme["button"], (255, 255, 255), 0.07),
            chip, border_radius=6,
        )
        pygame.draw.rect(
            self.screen,
            self._mix(theme["accent"], theme["panel"], 0.55),
            chip, 1, border_radius=6,
        )
        self.draw_text(key, (0, 0), self.tiny_font, theme["accent"],
                       center=chip.center)
        self.draw_text(label, (chip.right + 8, chip.y + 2),
                       self.small_font, theme["text"])

    # ------------------------------------------------------------------ #
    # main menu                                                           #
    # ------------------------------------------------------------------ #
    def draw_menu(self, theme_index, mode, difficulty, speed):
        theme = get_theme(theme_index)
        muted = self._muted(theme)
        self._fill_gradient(
            theme["background"],
            self._mix(theme["background"], BLACK, 0.45),
        )
        mouse = pygame.mouse.get_pos()

        # ambient hexagon rings
        for cx, cy, r, w, a in [
            (1255, 150, 170, 3, 42), (1330, 330, 90, 2, 30),
            (210, 750, 200, 3, 36), (330, 640, 80, 2, 26),
            (760, 55, 55, 2, 28),
        ]:
            ring = self._hex_ring(theme["accent"], r, w, a)
            self.screen.blit(
                ring, (cx - ring.get_width() // 2, cy - ring.get_height() // 2)
            )

        # title with soft glow
        glow = self.title_font.render(
            "MISSION HEXA",
            True, self._mix(theme["accent"], theme["background"], 0.35),
        )
        self.screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + 4, 142)))
        title = self.title_font.render("MISSION HEXA", True, theme["accent"])
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 135)))
        subtitle = self.font.render(
            "A hidden-Queen honeycomb strategy game",
            True, self._mix(theme["text"], theme["background"], 0.15),
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 198)))
        self.draw_text(
            "C H O O S E   A   G A M E   M O D E", (0, 0),
            self.tiny_font, muted, center=(WIDTH // 2, 252),
        )

        # mode buttons
        self.menu_buttons = {}
        options = [
            ("human_minimax", "Human vs Minimax AI"),
            ("human_mcts", "Human vs MCTS AI"),
            ("ai_vs_ai", "Minimax AI vs MCTS AI"),
            ("human_human", "Human vs Human"),
        ]
        bx = WIDTH // 2 - 230
        for i, (key, label) in enumerate(options):
            rect = pygame.Rect(bx, 286 + i * 74, 460, 56)
            hovered = rect.collidepoint(mouse)
            self.draw_button(
                rect, label, theme, key,
                selected=(mode == key), hovered=hovered,
            )

        # settings chips
        chips = [
            ("DIFFICULTY", difficulty.upper(), "D"),
            ("AI SPEED", speed, "S"),
            ("THEME", theme["name"].upper(), "T"),
        ]
        cw, chh, gap = 292, 66, 24
        total = cw * 3 + gap * 2
        x0 = WIDTH // 2 - total // 2
        for i, (label, value, hotkey) in enumerate(chips):
            rect = pygame.Rect(x0 + i * (cw + gap), 606, cw, chh)
            pygame.draw.rect(
                self.screen,
                self._mix(theme["panel"], (255, 255, 255), 0.03),
                rect, border_radius=14,
            )
            pygame.draw.rect(
                self.screen,
                self._mix(theme["accent"], theme["panel"], 0.55),
                rect, 1, border_radius=14,
            )
            self.draw_text(label, (rect.x + 18, rect.y + 9),
                           self.tiny_font, muted)
            self.draw_text(value, (rect.x + 18, rect.y + 28),
                           self.font, theme["text"])
            tag = pygame.Rect(rect.right - 42, rect.y + 8, 26, 20)
            pygame.draw.rect(self.screen, theme["button"], tag, border_radius=5)
            self.draw_text(hotkey, (0, 0), self.tiny_font, theme["accent"],
                           center=tag.center)

        self.draw_text(
            "Click a mode to start  •  ESC exits", (0, 0),
            self.small_font, muted, center=(WIDTH // 2, 714),
        )

    # ------------------------------------------------------------------ #
    # in-game screens                                                     #
    # ------------------------------------------------------------------ #
    def _draw_header(self, game, theme):
        muted = self._muted(theme)
        bar = pygame.Rect(16, 14, WIDTH - 32, HEADER_HEIGHT - 14)
        pygame.draw.rect(
            self.screen,
            self._mix(theme["panel"], (255, 255, 255), 0.02),
            bar, border_radius=14,
        )
        pygame.draw.rect(
            self.screen,
            self._mix(theme["accent"], theme["panel"], 0.55),
            bar, 1, border_radius=14,
        )
        title = self.medium_font.render("MISSION HEXA", True, theme["accent"])
        self.screen.blit(title, title.get_rect(midleft=(bar.x + 24, bar.centery)))

        current = game.current_player()
        if game.game_over:
            status, color = "GAME OVER", theme["accent"]
        else:
            status = f"TURN {game.turn}  •  {current.name.upper()} TO MOVE"
            color = current.color
        img = self.font.render(status, True, color)
        self.screen.blit(img, img.get_rect(center=(bar.centerx + 30, bar.centery)))

        msg = (game.message or "")[:46]
        mimg = self.small_font.render(msg, True, muted)
        self.screen.blit(mimg, mimg.get_rect(midright=(bar.right - 24, bar.centery)))

    def draw_board(self, game, theme_index):
        theme = get_theme(theme_index)
        current = game.current_player()
        legal = (
            set(game.legal_moves(current))
            if not game.game_over else set()
        )
        pulse = (math.sin(pygame.time.get_ticks() / 260.0) + 1.0) / 2.0

        # honeycomb watermark behind the board
        c0 = self.hex_center(0, 0)
        c1 = self.hex_center(ROWS - 1, COLS - 1)
        bcx, bcy = (c0[0] + c1[0]) // 2, (c0[1] + c1[1]) // 2
        ring = self._hex_ring(theme["accent"], 350, 3, 16)
        self.screen.blit(
            ring, (bcx - ring.get_width() // 2, bcy - ring.get_height() // 2)
        )

        # pulsing glow under legal moves
        glow_alpha = 70 + int(pulse * 80)
        for position in legal:
            cx, cy = self.hex_center(*position)
            glow = self._hex_ring(
                theme["legal_move"], HEX_SIZE + 5, 7, glow_alpha
            )
            self.screen.blit(
                glow, (cx - glow.get_width() // 2, cy - glow.get_height() // 2)
            )

        honey_text = (112, 66, 4)
        for position, cell in game.board.cells.items():
            center = self.hex_center(*position)
            points = self.hex_points(center)
            fill = theme["visited"] if cell.visited else theme["cell"]
            pygame.draw.polygon(self.screen, fill, points)
            inner_fill = self._mix(
                fill, WHITE, 0.12 if not cell.visited else 0.05
            )
            pygame.draw.polygon(
                self.screen, inner_fill,
                self.hex_points(center, HEX_SIZE * 0.78),
            )

            is_legal = position in legal
            border = theme["legal_move"] if is_legal else theme["border"]
            pygame.draw.polygon(
                self.screen, border, points, 3 if is_legal else 2
            )

            if not cell.visited:
                self.draw_text(
                    f"H{cell.honey}", (0, 0), self.cell_font, honey_text,
                    center=(center[0], center[1] - 10),
                )
                self.draw_text(
                    f"B{cell.bees}", (0, 0), self.small_font, BLACK,
                    center=(center[0], center[1] + 11),
                )
            elif cell.owner is not None:
                clue = game.players[cell.owner].knowledge.get(position)
                marker = "+" if clue is True else "-" if clue is False else ""
                label = f"P{cell.owner + 1}{marker}"
                label_color = PHEROMONE_COLOR if clue is True else WHITE
                self.draw_text(
                    label, (0, 0), self.cell_font, label_color, center=center
                )

            for player in game.players:
                if player.alive and player.position == position:
                    px, py = center[0], center[1] + 22
                    gr = 18 + int(pulse * 3)
                    self.screen.blit(
                        self._disc(player.color, gr, 60), (px - gr, py - gr)
                    )
                    pygame.draw.circle(self.screen, player.color, (px, py), 12)
                    pygame.draw.circle(self.screen, WHITE, (px, py), 12, 2)
                    if not game.game_over and current is player:
                        pygame.draw.circle(self.screen, WHITE, (px, py), 16, 2)

    def draw_sidebar(self, game, theme_index, difficulty, speed):
        theme = get_theme(theme_index)
        muted = self._muted(theme)
        panel_alt = theme.get("panel_alt", theme["panel"])
        panel = pygame.Rect(
            PANEL_X + 10, PANEL_TOP,
            PANEL_WIDTH - 26, HEIGHT - PANEL_TOP - 16,
        )
        pygame.draw.rect(
            self.screen,
            self._mix(theme["panel"], BLACK, 0.35),
            panel.move(0, 4), border_radius=CARD_RADIUS,
        )
        pygame.draw.rect(self.screen, theme["panel"], panel, border_radius=CARD_RADIUS)
        pygame.draw.rect(
            self.screen,
            self._mix(theme["accent"], theme["panel"], 0.5),
            panel, 1, border_radius=CARD_RADIUS,
        )
        x = panel.x + 18
        w = panel.width - 36

        # mode chip
        chip = pygame.Rect(x, panel.y + 16, w, 32)
        pygame.draw.rect(
            self.screen, self._mix(panel_alt, WHITE, 0.02), chip, border_radius=9
        )
        self.draw_text("MODE", (chip.x + 14, chip.y + 8), self.tiny_font, muted)
        mode_value = self.small_font.render(
            game.mode.replace("_", " ").title(), True, theme["accent"]
        )
        self.screen.blit(
            mode_value, mode_value.get_rect(midright=(chip.right - 14, chip.centery))
        )

        # player cards
        y = chip.bottom + 14
        for player in game.players:
            card = pygame.Rect(x, y, w, 116)
            pygame.draw.rect(self.screen, panel_alt, card, border_radius=12)
            pygame.draw.rect(self.screen, player.color, card, 2, border_radius=12)
            pygame.draw.circle(
                self.screen, player.color, (card.x + 24, card.y + 24), 8
            )
            pygame.draw.circle(
                self.screen, WHITE, (card.x + 24, card.y + 24), 8, 1
            )
            self.draw_text(
                player.name, (card.x + 40, card.y + 12),
                self.font, theme["text"]
            )
            kind = "HUMAN" if player.is_human else "AI"
            kind_img = self.tiny_font.render(kind, True, muted)
            self.screen.blit(
                kind_img, kind_img.get_rect(midright=(card.right - 14, card.y + 24))
            )
            if not player.alive:
                dead = self.small_font.render("ELIMINATED", True, PHEROMONE_COLOR)
                self.screen.blit(
                    dead, dead.get_rect(midright=(card.right - 14, card.y + 46))
                )
            self.draw_text(
                "HONEY", (card.x + 16, card.y + 46), self.tiny_font, muted
            )
            self.draw_text(
                str(player.honey), (card.x + 16, card.y + 62),
                self.num_font, player.color
            )
            info = (
                f"Pos {player.position}  •  "
                f"Visited {len(player.visited_cells)}"
            )
            self.draw_text(
                info, (card.x + 16, card.y + 94), self.small_font, theme["text"]
            )
            y = card.bottom + 12

        # queen radar
        sec = y + 10
        self.draw_text("QUEEN RADAR", (x, sec), self.tiny_font, theme["accent"])
        current = game.current_player()
        n = len(current.possible_queen_cells)
        self.draw_text(
            f"{current.name}: {n} possible hideout"
            + ("s" if n != 1 else ""),
            (x, sec + 18), self.small_font, theme["text"]
        )
        bar_bg = pygame.Rect(x, sec + 44, w, 10)
        pygame.draw.rect(
            self.screen,
            self._mix(theme["panel"], BLACK, 0.3),
            bar_bg, border_radius=5,
        )
        if n:
            fillw = max(6, int(w * n / float(ROWS * COLS)))
            pygame.draw.rect(
                self.screen, PHEROMONE_COLOR,
                pygame.Rect(x, sec + 44, fillw, 10), border_radius=5,
            )

        clue_rect = pygame.Rect(x, sec + 66, w, 34)
        pygame.draw.rect(self.screen, panel_alt, clue_rect, border_radius=10)
        if current.knowledge:
            latest = list(current.knowledge)[-1]
            clue = current.knowledge[latest]
            clue_text = (
                "Pheromone: detected nearby!"
                if clue else "Pheromone: nothing detected"
            )
            clue_color = PHEROMONE_COLOR if clue else muted
        else:
            clue_text = "No pheromone clues yet"
            clue_color = muted
        self.draw_text(
            clue_text, (0, 0), self.small_font, clue_color,
            center=clue_rect.center
        )

        # controls
        cy = clue_rect.bottom + 24
        self.draw_text("CONTROLS", (x, cy), self.tiny_font, theme["accent"])
        hints = [
            ("R", "Restart"), ("T", "Theme"), ("D", "Difficulty"),
            ("S", "Speed"), ("ESC", "Menu"),
        ]
        for i, (key, label) in enumerate(hints):
            hx = x + (i % 2) * (w // 2 + 6)
            hy = cy + 22 + (i // 2) * 30
            self._key_hint(hx, hy, key, label, theme)

        footer = (
            f"Theme {theme['name']}  •  "
            f"{difficulty.upper()}  •  {speed}"
        )
        self.draw_text(
            footer, (0, 0), self.tiny_font, muted,
            center=(panel.centerx, panel.bottom - 18),
        )

    def _draw_game_over(self, game, theme):
        muted = self._muted(theme)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        card = pygame.Rect(0, 0, 560, 300)
        card.center = (WIDTH // 2, HEIGHT // 2)
        pygame.draw.rect(
            self.screen,
            self._mix(theme["panel"], BLACK, 0.4),
            card.move(0, 6), border_radius=22,
        )
        pygame.draw.rect(self.screen, theme["panel"], card, border_radius=22)
        pygame.draw.rect(
            self.screen, theme["accent"], card, 2, border_radius=22
        )

        if game.winner:
            label, color = f"{game.winner.name} WINS!", game.winner.color
        else:
            label, color = "IT'S A DRAW!", WHITE
        self.draw_text(
            label, (0, 0), self.big_font, color,
            center=(card.centerx, card.y + 78), shadow=True,
        )
        pygame.draw.line(
            self.screen,
            self._mix(theme["accent"], theme["panel"], 0.5),
            (card.x + 60, card.y + 128), (card.right - 60, card.y + 128), 1,
        )
        p1, p2 = game.players
        score = (
            f"Honey    {p1.name}: {p1.honey}"
            f"     •     {p2.name}: {p2.honey}"
        )
        self.draw_text(
            score, (0, 0), self.font, theme["text"],
            center=(card.centerx, card.y + 162),
        )
        hint = "Press R to play again  •  ESC for menu"
        self.draw_text(
            hint, (0, 0), self.small_font, muted,
            center=(card.centerx, card.y + 212),
        )

    def draw_game(self, game, theme_index, difficulty="medium", speed="NORMAL"):
        theme = get_theme(theme_index)
        self._fill_gradient(
            theme["background"],
            self._mix(theme["background"], BLACK, 0.45),
        )
        self._draw_header(game, theme)
        self.draw_board(game, theme_index)
        self.draw_sidebar(game, theme_index, difficulty, speed)
        if game.game_over:
            self._draw_game_over(game, theme)