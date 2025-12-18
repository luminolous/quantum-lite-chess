# ai/bot.py
import random
import chess

from qlc.rules import Rules
from qlc.board import rc_to_square

class Bot:
    def __init__(self, color='b', seed=None):
        self.color = color  # 'w' or 'b'
        self.rng = random.Random(seed)

    def make_move(self, board_obj):
        if getattr(board_obj, "turn_color", None) != self.color:
            return
        if hasattr(board_obj, "is_game_over") and board_obj.is_game_over():
            return

        candidates = []
        want_color = chess.WHITE if self.color == "w" else chess.BLACK

        for r in range(8):
            for c in range(8):
                from_sq = rc_to_square(r, c)

                ok = False
                for br in getattr(board_obj, "branches", []):
                    b = br.board
                    p = b.piece_at(from_sq)
                    if p and p.color == want_color and p.color == b.turn:
                        ok = True
                        break
                if not ok:
                    continue

                valid = Rules.get_valid_moves(board_obj, r, c)
                for (rr, cc) in valid:
                    candidates.append(((r, c), (rr, cc)))

        if not candidates:
            return

        # chance split
        if self.rng.random() < 0.25:
            by_start = {}
            for s, e in candidates:
                by_start.setdefault(s, []).append(e)
            starts = [s for s, ds in by_start.items() if len(ds) >= 2]
            if starts:
                s = self.rng.choice(starts)
                d1, d2 = self.rng.sample(by_start[s], 2)
                if board_obj.split_piece(s, d1, d2):
                    return

        s, e = self.rng.choice(candidates)
        board_obj.apply_move(s, e)