import pygame
import os
import io
import sys
import cairosvg
from .config import Config

class AssetManager:
    def __init__(self):
        self.sprites = {}
        self.background = None
        self.board_image = None
        self.fonts = {}
        
    def load_all(self):
        """Load semua aset"""
        try:
            self._load_fonts()
            self._load_images()
            print("Assets loaded successfully.")
        except Exception as e:
            print(f"ERROR loading assets: {e}")
            sys.exit(1)

    def _load_fonts(self):
        self.fonts['default'] = pygame.font.SysFont(Config.FONT_MAIN, 32)
        self.fonts['title'] = pygame.font.SysFont(Config.FONT_MAIN, 42, bold=True)
        self.fonts['small'] = pygame.font.SysFont(Config.FONT_MAIN, 20)
        self.fonts['split'] = pygame.font.SysFont(Config.FONT_MAIN, 18, bold=True)

    def _load_images(self):
        # Load bg
        bg_path = os.path.join(Config.ASSETS_PATH, "bg.jpg")
        if os.path.exists(bg_path):
            img = pygame.image.load(bg_path)
            self.background = pygame.transform.scale(img, (Config.WIDTH, Config.HEIGHT))
        else:
            # Fallback klo gambar gaada
            self.background = pygame.Surface((Config.WIDTH, Config.HEIGHT))
            self.background.fill((50, 50, 50))

        # Load board svg
        self.board_image = self._load_svg(Config.BOARD_IMAGE_PATH, (Config.BOARD_SIZE, Config.BOARD_SIZE))

        # Load pieces svg
        piece_name_map = {"K": "king", "Q": "queen", "R": "rook", "B": "bishop", "N": "knight", "P": "pawn"}
        for color in ("w", "b"):
            for p_char, p_name in piece_name_map.items():
                filename = f"{p_name}-{color}.svg"
                path = os.path.join(Config.ASSETS_PATH, filename)
                self.sprites[f"{color}{p_char}"] = self._load_svg(path, (64, 64))

    def _load_svg(self, path, size):
        """Helper private untuk konversi SVG ke Surface."""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            
            png_bytes = cairosvg.svg2png(url=path, output_width=size[0], output_height=size[1])
            return pygame.image.load(io.BytesIO(png_bytes)).convert_alpha()
        except Exception as e:
            print(f"Warning: Failed to load {path}. Error: {e}")
            # Return surface transparan kosong buat fallback
            return pygame.Surface(size, pygame.SRCALPHA)