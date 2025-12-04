# app/game.py
import pygame
import sys
from .config import Config
from .assets import AssetManager
from chess.board import Board
from chess.rules import Rules
from render.renderer import Renderer
from ai.bot import Bot

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption("Quantum Chess - OOP Project")
        self.clock = pygame.time.Clock()
        
        # Init subsystems
        self.assets = AssetManager()
        self.assets.load_all()
        
        self.renderer = Renderer(self.screen, self.assets)
        self.board = Board()
        
        self.selected = None
        self.valid_moves = []
        self.player_color = 'w' # Default
        self.bot = None
        self.quantum_mode = False
        self.game_over = False

    def start(self):
        self._welcome_screen()
        choice = self._side_selection()
        self.player_color = choice
        self.bot = Bot('b' if choice == 'w' else 'w')
        
        self._game_loop()

    def _welcome_screen(self):
        self.screen.blit(self.assets.background, (0,0))
        txt = self.assets.fonts['title'].render("Quantum Chess", True, (255,255,255))
        self.screen.blit(txt, (120, 300))
        pygame.display.flip()
        self._wait_key()

    def _side_selection(self):
        self.screen.blit(self.assets.background, (0,0))
        txt = self.assets.fonts['title'].render("Press W (White) or B (Black)", True, (255,255,255))
        self.screen.blit(txt, (100, 300))
        pygame.display.flip()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w: return 'w'
                    if event.key == pygame.K_b: return 'b'

    def _wait_key(self):
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN: waiting = False
                if event.type == pygame.QUIT: sys.exit()

    def _handle_click(self, pos):
        if self.game_over: return
        
        # Convert mouse to grid
        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2
        
        col = (pos[0] - x_off) // Config.SQUARE_SIZE
        row = (pos[1] - y_off) // Config.SQUARE_SIZE
        
        # Adjust for player perspective
        r = 7 - row if self.player_color == 'b' else row
        c = 7 - col if self.player_color == 'b' else col
        
        if not (0 <= r < 8 and 0 <= c < 8): return

        # Logic selection & move
        piece = self.board.get_piece(r, c)
        
        # Move ke ktak valid
        if (r, c) in self.valid_moves and self.selected:
            self.board.move_piece(self.selected, (r, c))
            self.selected = None
            self.valid_moves = []
            
            # Bot turn trigger
            self._bot_turn()
            return

        # Select piece
        if piece and piece.color == self.player_color:
            self.selected = (r, c)
            self.valid_moves = Rules.get_valid_moves(self.board, r, c)

    def _bot_turn(self):
        # Render 'Thinking' state
        self.renderer.draw_game(self.board, thinking=True)
        pygame.display.flip()
        pygame.time.delay(500)
        
        self.bot.make_move(self.board)

    def _game_loop(self):
        running = True
        while running:
            self.clock.tick(Config.FPS)
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_click(pygame.mouse.get_pos())
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.quantum_mode = not self.quantum_mode
            
            # Render
            self.renderer.draw_game(
                self.board, 
                self.selected, 
                self.valid_moves, 
                self.quantum_mode, 
                self.player_color
            )
            pygame.display.flip()
            
        pygame.quit()