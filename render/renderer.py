# render/renderer.py
import pygame
from app.config import Config

class Renderer:
    def __init__(self, screen, assets):
        self.screen = screen
        self.assets = assets

    def draw_game(
        self,
        board_obj,
        selected=None,
        valid_moves=None,
        quantum_mode=False,
        player_color="w",
        thinking=False,
    ):
        if valid_moves is None:
            valid_moves = []

        # Background & board (pakai background asset yang sudah kamu load)
        self.screen.blit(self.assets.background, (0, 0))

        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2
        self.screen.blit(self.assets.board_image, (x_off, y_off))

        # Highlight valid moves
        for (r, c) in valid_moves:
            color = Config.COLOR_HIGHLIGHT if quantum_mode else Config.COLOR_VALID_MOVE
            self._draw_rect(r, c, color, alpha=100, player_color=player_color)

        # Highlight selected square
        if selected:
            self._draw_rect(selected[0], selected[1], Config.COLOR_SELECTED, width=4, player_color=player_color)

        # Draw pieces
        self._draw_pieces(board_obj, x_off, y_off, player_color=player_color)

        # Move log (kalau ada)
        if hasattr(board_obj, "move_log"):
            self._draw_move_log(board_obj.move_log)

        # Thinking overlay
        if thinking:
            font = self.assets.fonts.get("small") or self.assets.fonts["default"]
            txt = font.render("Computer thinking...", True, (255, 255, 0))
            self.screen.blit(txt, (Config.WIDTH - 250, 20))

        pygame.display.update()

    def _draw_pieces(self, board_obj, x_off, y_off, player_color="w"):
        font = self.assets.fonts.get("small") or self.assets.fonts["default"]

        for r in range(8):
            for c in range(8):
                p = board_obj.get_piece(r, c)
                if not p:
                    continue

                # Flip view buat black player
                draw_r = 7 - r if player_color == "b" else r
                draw_c = 7 - c if player_color == "b" else c

                x = x_off + draw_c * Config.SQUARE_SIZE
                y = y_off + draw_r * Config.SQUARE_SIZE

                img = self.assets.sprites.get(p.code)
                if img:
                    self.screen.blit(img, (x, y))

                # Tampilkan probabilitas kalau quantum-lite
                prob = getattr(p, "prob", 1.0)
                if prob < 1.0:
                    prob_txt = font.render(f"{int(prob * 100)}%", True, (255, 255, 255))
                    self.screen.blit(prob_txt, (x + 5, y + 5))

    def _draw_rect(self, r, c, color, alpha=255, width=0, player_color="w"):
        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2

        # Flip view buat black (samakan dengan piece rendering)
        draw_r = 7 - r if player_color == "b" else r
        draw_c = 7 - c if player_color == "b" else c

        x = x_off + draw_c * Config.SQUARE_SIZE
        y = y_off + draw_r * Config.SQUARE_SIZE
        rect = (x, y, Config.SQUARE_SIZE, Config.SQUARE_SIZE)

        if alpha < 255:
            s = pygame.Surface((Config.SQUARE_SIZE, Config.SQUARE_SIZE), pygame.SRCALPHA)
            s.set_alpha(alpha)
            s.fill(color)
            self.screen.blit(s, (x, y))
        else:
            pygame.draw.rect(self.screen, color, rect, width)

    def _draw_move_log(self, log):
        pygame.draw.rect(self.screen, (30, 30, 30), (Config.WIDTH - 200, 50, 180, 140))
        font = self.assets.fonts.get("small") or self.assets.fonts["default"]
        title = font.render("Log", True, (255, 255, 255))
        self.screen.blit(title, (Config.WIDTH - 190, 55))
        for i, txt in enumerate(log[-4:]):
            surf = font.render(str(txt), True, (200, 200, 200))
            self.screen.blit(surf, (Config.WIDTH - 190, 80 + i * 25))