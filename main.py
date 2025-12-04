# main.py
from app.game import Game

if __name__ == "__main__":
    # Entry point
    game_instance = Game()
    game_instance.start()