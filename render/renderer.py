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
        split_target1=None,
        player_color="w",
        thinking=False,
        game_over=False,
        result_str=None,
    ):
        if valid_moves is None:
            valid_moves = []

        # Background & board
        self.screen.blit(self.assets.background, (0, 0))

        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2
        self.screen.blit(self.assets.board_image, (x_off, y_off))

        # Highlight valid moves
        for (r, c) in valid_moves:
            color = Config.COLOR_HIGHLIGHT if quantum_mode else Config.COLOR_VALID_MOVE
            self._draw_rect(r, c, color, alpha=100, player_color=player_color)

        # Highlight split target A (split_target1)
        if split_target1 is not None:
            r, c = split_target1
            # Outline + soft fill
            self._draw_rect(r, c, Config.COLOR_SPLIT_ANCHOR, alpha=60, player_color=player_color)
            self._draw_rect(r, c, Config.COLOR_SPLIT_ANCHOR, width=6, player_color=player_color)
            self._draw_square_label(r, c, "A", player_color=player_color)

        # Highlight selected square
        if selected:
            self._draw_rect(selected[0], selected[1], Config.COLOR_SELECTED, width=4, player_color=player_color)

        # Draw pieces
        self._draw_pieces(board_obj, x_off, y_off, player_color=player_color)

        # HUD / instructions
        self._draw_hud(
            board_obj,
            quantum_mode=quantum_mode,
            selected=selected,
            split_target1=split_target1,
            player_color=player_color,
            thinking=thinking,
        )

        # Move log
        if hasattr(board_obj, "move_log"):
            self._draw_move_log(board_obj.move_log)

        # Thinking overlay
        if thinking:
            font = self.assets.fonts.get("small") or self.assets.fonts["default"]
            txt = font.render("Computer thinking...", True, (255, 255, 0))
            self.screen.blit(txt, (Config.WIDTH - 250, 20))

        if game_over and result_str:
            self._draw_game_over(result_str)

        pygame.display.update()

    def _draw_game_over(self, result_str):
        """Menggambar overlay hitam transparan dengan teks kemenangan."""
        # Dark overlay
        overlay = pygame.Surface((Config.WIDTH, Config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Tentukan teks
        title_font = self.assets.fonts.get("title") or self.assets.fonts["default"]
        sub_font = self.assets.fonts.get("default")
        
        msg = "GAME OVER"
        sub_msg = ""
        
        if result_str == "1-0":
            sub_msg = "WHITE WINS!"
            color = (100, 255, 100) # ijo
        elif result_str == "0-1":
            sub_msg = "BLACK WINS!"
            color = (255, 100, 100) # merah
        else:
            sub_msg = "DRAW / STALEMATE"
            color = (200, 200, 200) # abu

        # Render teks di tengah layar
        title_surf = title_font.render(msg, True, (255, 255, 255))
        sub_surf = title_font.render(sub_msg, True, color)
        
        cx, cy = Config.WIDTH // 2, Config.HEIGHT // 2
        
        self.screen.blit(title_surf, (cx - title_surf.get_width() // 2, cy - 80))
        self.screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, cy - 20))
        
        # Instruksi keluar
        hint = sub_font.render("Press ESC to Quit", True, (150, 150, 150))
        self.screen.blit(hint, (cx - hint.get_width() // 2, cy + 60))

    def _draw_hud(self, board_obj, *, quantum_mode: bool, selected, split_target1, player_color: str, thinking: bool):
        """Panel instruksi kecil biar user paham kontrol split."""
        font = self.assets.fonts.get("small") or self.assets.fonts["default"]

        # Deteksi giliran player (QuantumBoardAdapter punya turn_color)
        turn_color = getattr(board_obj, "turn_color", None)
        is_player_turn = (turn_color == player_color) if turn_color is not None else True

        lines = []
        if not quantum_mode:
            lines.append("Q: Quantum OFF (press Q to toggle)")
            if is_player_turn:
                lines.append("Click a piece, then click a target square")
        else:
            lines.append("Quantum ON (press Q to exit)")
            if thinking or (not is_player_turn):
                lines.append("Waiting for computer…")
            else:
                if selected is None:
                    lines.append("1) Click your piece to select")
                    lines.append("2) Normal move: click a highlighted square")
                    lines.append("3) Split: hold SHIFT + click target A, then click target B")
                else:
                    if split_target1 is None:
                        lines.append("Normal move: click a highlighted square")
                        lines.append("Split: hold SHIFT + click an EMPTY highlighted square to set target A")
                    else:
                        lines.append("Split target A selected (cyan). Now click target B")
                        lines.append("Tip: click elsewhere to cancel A")

        if not lines:
            return

        pad = 10
        w = 0
        h = 0
        rendered = []
        for t in lines:
            surf = font.render(t, True, (255, 255, 255))
            rendered.append(surf)
            w = max(w, surf.get_width())
            h += surf.get_height() + 4
        w += pad * 2
        h += pad * 2

        # Panel bg transparan
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        self.screen.blit(panel, (20, 20))

        y = 20 + pad
        for surf in rendered:
            self.screen.blit(surf, (20 + pad, y))
            y += surf.get_height() + 4

    def _draw_square_label(self, r, c, text: str, player_color="w"):
        """Label kecil di atas kotak (misal 'A' untuk split_target1)."""
        font = self.assets.fonts.get("split") or self.assets.fonts.get("small") or self.assets.fonts["default"]

        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2
        draw_r = 7 - r if player_color == "b" else r
        draw_c = 7 - c if player_color == "b" else c
        x = x_off + draw_c * Config.SQUARE_SIZE
        y = y_off + draw_r * Config.SQUARE_SIZE

        surf = font.render(text, True, (0, 0, 0))
        bg = pygame.Surface((surf.get_width() + 8, surf.get_height() + 4), pygame.SRCALPHA)
        bg.fill((255, 255, 255, 200))
        self.screen.blit(bg, (x + 6, y + 6))
        self.screen.blit(surf, (x + 10, y + 8))

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

                # Tampilkan probabilitas kalo quantum
                prob = getattr(p, "prob", 1.0)
                if prob < 1.0:
                    prob_txt = font.render(f"{int(prob * 100)}%", True, (255, 255, 255))
                    self.screen.blit(prob_txt, (x + 5, y + 5))

    def _draw_rect(self, r, c, color, alpha=255, width=0, player_color="w"):
        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2

        # Flip view buat black (samain dengan piece rendering)
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