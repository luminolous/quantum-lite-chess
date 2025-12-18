# qlc/rules.py
"""
Move generation using python-chess.
Return format tetap: list of (r,c) tujuan.
"""
from __future__ import annotations
from .board import rc_to_square, square_to_rc


class Rules:
    @staticmethod
    def get_valid_moves(board_obj, r: int, c: int):
        from_sq = rc_to_square(r, c)

        dest = set()
        for br in getattr(board_obj, "branches", []):
            b = br.board
            p = b.piece_at(from_sq)
            if p is None or p.color != b.turn:
                continue

            for mv in b.legal_moves:
                if mv.from_square == from_sq:
                    dest.add(mv.to_square)

        return [square_to_rc(sq) for sq in dest]