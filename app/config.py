# app/config.py
import os

class Config:
    # Screen settings
    WIDTH = 1024
    HEIGHT = 768
    FPS = 60
    
    # Board settings
    BOARD_SIZE = 512
    SQUARE_SIZE = BOARD_SIZE // 8
    
    # Paths
    ASSETS_PATH = r"assets\p1"
    BOARD_IMAGE_PATH = r"assets\boards\rect-8x8.svg"
    
    # Colors
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_HIGHLIGHT = (255, 255, 0)
    COLOR_VALID_MOVE = (144, 238, 144)
    COLOR_SELECTED = (255, 0, 0)
    
    # Fonts
    FONT_MAIN = "DejaVu Sans"