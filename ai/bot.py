# ai/bot.py
import random
from chess.rules import Rules

class Bot:
    def __init__(self, color):
        self.color = color
        self.quantum_chance = 0.25
        self.collapse_chance = 0.15

    def make_move(self, board_obj):
        """Melakukan langkah AI (Classical atau Quantum-lite)."""
        my_pieces = []
        for r in range(8):
            for c in range(8):
                p = board_obj.get_piece(r, c)
                if p and p.color == self.color:
                    my_pieces.append((r, c))

        random.shuffle(my_pieces)

        for r, c in my_pieces:
            p = board_obj.get_piece(r, c)
            if not p:
                continue

            moves = Rules.get_valid_moves(board_obj, r, c)
            if not moves:
                continue

            # Quantum split hanya kalau piece klasik (prob=1 & bukan quantum)
            if p.qid is None and p.prob == 1.0 and random.random() < self.quantum_chance:
                empty_sq = self._get_empty_squares(board_obj, (r, c))
                if len(empty_sq) >= 2:
                    s1, s2 = random.sample(empty_sq, 2)
                    if board_obj.split_piece((r, c), s1, s2):
                        board_obj.move_log.append("Bot: Split Move")
                        return

            # Normal move (capture quantum bisa gagal)
            move = random.choice(moves)
            status = board_obj.apply_move((r, c), move)
            if status == "capture_failed":
                # Turn tetap dianggap selesai (lite). Bisa kamu ubah kalau mau retry.
                board_obj.move_log.append("Bot: Capture Failed")
            return

    def _get_empty_squares(self, board, exclude_pos):
        res = []
        for r in range(8):
            for c in range(8):
                if not board.get_piece(r, c) and (r, c) != exclude_pos:
                    res.append((r, c))
        return res