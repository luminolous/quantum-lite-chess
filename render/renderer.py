import pygame
from app.config import Config

class Renderer:
    def __init__(self, screen, assets):
        self.screen = screen
        self.assets = assets

    def draw_game(self, board_obj, selected=None, valid_moves=[], quantum_mode=False, player_color='w', thinking=False):
        # Background & board
        self.screen.blit(self.assets.background, (0, 0))
        
        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2
        self.screen.blit(self.assets.board_image, (x_off, y_off))

        # Highlight moves
        for r, c in valid_moves:
            color = Config.COLOR_HIGHLIGHT if quantum_mode else Config.COLOR_VALID_MOVE
            self._draw_rect(r, c, color, alpha=100)

        # Highlight selected
        if selected:
            self._draw_rect(selected[0], selected[1], Config.COLOR_SELECTED, width=4)

        # Draw pieces
        for r in range(8):
            for c in range(8):
                p = board_obj.get_piece(r, c)
                if p:
                    # Adjust view buat black player
                    draw_r = 7 - r if player_color == 'b' else r
                    draw_c = 7 - c if player_color == 'b' else c
                    
                    x = x_off + draw_c * Config.SQUARE_SIZE
                    y = y_off + draw_r * Config.SQUARE_SIZE
                    
                    img = self.assets.sprites.get(p.code)
                    if img:
                        self.screen.blit(img, (x, y))
                    
                    # 50% marker
                    if p.prob == 0.5:
                        txt = self.assets.fonts['split'].render("50%", True, (255, 0, 0))
                        self.screen.blit(txt, (x+5, y+5))

        # UI overlays
        if thinking:
            txt = self.assets.fonts['small'].render("Computer thinking...", True, (255, 255, 0))
            self.screen.blit(txt, (Config.WIDTH - 250, Config.HEIGHT - 30))

        self._draw_move_log(board_obj.move_log)

    def _draw_rect(self, r, c, color, width=0, alpha=255):
        # Helper untuk konversi koordinat grid ke pixel
        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2
        
        x = x_off + c * Config.SQUARE_SIZE
        y = y_off + r * Config.SQUARE_SIZE
        
        rect = (x, y, Config.SQUARE_SIZE, Config.SQUARE_SIZE)
        
        if alpha < 255:
            s = pygame.Surface((Config.SQUARE_SIZE, Config.SQUARE_SIZE))
            s.set_alpha(alpha)
            s.fill(color)
            self.screen.blit(s, (x, y))
        else:
            pygame.draw.rect(self.screen, color, rect, width)

    def _draw_move_log(self, log):
        pygame.draw.rect(self.screen, (30, 30, 30), (Config.WIDTH - 200, 50, 180, 140))
        title = self.assets.fonts['small'].render("Log", True, (255,255,255))
        self.screen.blit(title, (Config.WIDTH - 190, 55))
        for i, txt in enumerate(log[-4:]):
            surf = self.assets.fonts['small'].render(txt, True, (200,200,200))
            self.screen.blit(surf, (Config.WIDTH - 190, 80 + i*25))