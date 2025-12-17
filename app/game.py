# app/game.py
import pygame
import sys

from .config import Config
from .assets import AssetManager
from qlc.board import Board
from qlc.rules import Rules
from render.renderer import Renderer
from ai.bot import Bot


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption("Quantum Lite Chess")

        self.assets = AssetManager()
        self.assets.load_all()

        self.renderer = Renderer(self.screen, self.assets)
        self.board = Board()
        self.selected = None
        self.valid_moves = []
        self.player_color = 'w'
        self.bot = None
        self.quantum_mode = False

        self.split_target1 = None
        self.game_over = False

    def start(self):
        self._choose_side_menu()

        # White always starts in chess → kalau player pilih black, bot (white) move dulu.
        if self.player_color == "b":
            self._bot_turn()

        clock = pygame.time.Clock()

        while True:
            clock.tick(30)

            self.renderer.draw_game(
                self.board,
                selected=self.selected,
                valid_moves=self.valid_moves,
                quantum_mode=self.quantum_mode,
                player_color=self.player_color
            )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.quantum_mode = not self.quantum_mode
                        self.split_target1 = None
                        self.selected = None
                        self.valid_moves = []

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(pygame.mouse.get_pos())

    def _choose_side_menu(self):
        while True:
            self.screen.fill((0, 0, 0))
            text = self.assets.fonts['title'].render("Press W or B to choose side", True, (255, 255, 255))
            self.screen.blit(text, (80, Config.HEIGHT // 2 - 50))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.player_color = 'w'
                        self.bot = Bot('b')
                        return
                    elif event.key == pygame.K_b:
                        self.player_color = 'b'
                        self.bot = Bot('w')
                        return

    def _handle_click(self, pos):
        if self.game_over:
            return

        # python-chess enforce turn, jadi UI juga harus enforce
        if getattr(self.board, "turn_color", None) != self.player_color:
            return

        x_off = (Config.WIDTH - Config.BOARD_SIZE) // 2
        y_off = (Config.HEIGHT - Config.BOARD_SIZE) // 2

        mx, my = pos
        col = (mx - x_off) // Config.SQUARE_SIZE
        row = (my - y_off) // Config.SQUARE_SIZE

        r = 7 - row if self.player_color == 'b' else row
        c = 7 - col if self.player_color == 'b' else col
        if not (0 <= r < 8 and 0 <= c < 8):
            return

        # split: pick 2nd target
        if self.split_target1 is not None and self.selected is not None:
            if (
                (r, c) in self.valid_moves
                and (r, c) != self.split_target1
                and self.board.get_piece(r, c) is None
            ):
                ok = self.board.split_piece(self.selected, self.split_target1, (r, c))
                if ok:
                    self.selected = None
                    self.valid_moves = []
                    self.split_target1 = None
                    self._bot_turn()
                return

            if (r, c) != self.split_target1:
                self.split_target1 = None

        piece = self.board.get_piece(r, c)

        # attempt move
        if self.selected:
            if (r, c) in self.valid_moves:
                if self.quantum_mode and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    if self.board.get_piece(r, c) is None:
                        self.split_target1 = (r, c)
                    return

                status = self.board.apply_move(self.selected, (r, c))
                if status == "ok":
                    self.selected = None
                    self.valid_moves = []
                    self.split_target1 = None
                    self._bot_turn()
                return

            self.selected = None
            self.valid_moves = []
            self.split_target1 = None
            return

        # select piece
        if piece and piece.color == self.player_color:
            self.selected = (r, c)
            self.valid_moves = Rules.get_valid_moves(self.board, r, c)
            self.split_target1 = None

    def _bot_turn(self):
        while not self.game_over and self.bot and getattr(self.board, "turn_color", None) != self.player_color:
            self.renderer.draw_game(self.board, thinking=True, player_color=self.player_color)
            pygame.display.flip()
            pygame.time.delay(250)

            self.bot.make_move(self.board)

            if hasattr(self.board, "is_game_over") and self.board.is_game_over():
                self.game_over = True
                self.selected = None
                self.valid_moves = []
                self.split_target1 = None
                if hasattr(self.board, "result"):
                    self.board.move_log.append(f"GAME OVER: {self.board.result()}")