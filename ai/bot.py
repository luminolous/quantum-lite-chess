# ai/bot.py
import random
from chess.rules import Rules

class Bot:
    def __init__(self, color):
        self.color = color
        self.quantum_chance = 0.25
        self.collapse_chance = 0.15

    def make_move(self, board_obj):
        """Melakukan langkah AI (Classical atau Quantum)"""
        my_pieces = []
        for r in range(8):
            for c in range(8):
                p = board_obj.get_piece(r, c)
                if p and p.color == self.color:
                    my_pieces.append((r, c))
        
        random.shuffle(my_pieces)

        # Coba measure/collapse musuh (strategi quantum)
        for r, c in my_pieces:
            qp, _ = board_obj.find_quantum_piece(r, c)
            if qp and len(qp.qnum) > 1 and random.random() < self.collapse_chance:
                qp.measure()
                board_obj.move_log.append("Bot: Collapse Triggered")
                return

        # Langkah normal atau split
        for r, c in my_pieces:
            moves = Rules.get_valid_moves(board_obj, r, c)
            if moves:
                # Try split move
                p = board_obj.get_piece(r, c)
                if random.random() < self.quantum_chance and p.prob == 1.0:
                    empty_sq = self._get_empty_squares(board_obj, (r,c))
                    if len(empty_sq) >= 2:
                        s1, s2 = random.sample(empty_sq, 2)
                        # Execute split (copy manual dlu)
                        board_obj.grid[s1[0]][s1[1]] = p
                        board_obj.grid[s1[0]][s1[1]].prob = 0.5
                        
                        board_obj.grid[s2[0]][s2[1]] = p
                        board_obj.grid[s2[0]][s2[1]].prob = 0.5
                        
                        board_obj.grid[r][c] = None
                        board_obj.move_log.append("Bot: Split Move")
                        return

                # Normal move
                move = random.choice(moves)
                board_obj.move_piece((r, c), move)
                return

    def _get_empty_squares(self, board, exclude_pos):
        res = []
        for r in range(8):
            for c in range(8):
                if not board.get_piece(r, c) and (r, c) != exclude_pos:
                    res.append((r, c))
        return res