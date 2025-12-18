# qlc/board.py
"""
Board state backed by python-chess.

- Classical chess rules (legal moves, check rules, castling, en passant, promotion)
  are delegated to python-chess.
- Quantum "lite" behavior is modeled as a weighted set of classical branches (each
  branch is a chess.Board).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

import chess  # python-chess

from .piece import Piece

RC = Tuple[int, int]


@dataclass
class _Branch:
    board: chess.Board
    weight: float


def rc_to_square(r: int, c: int) -> chess.Square:
    """
    Convert internal (r,c) with r=0 at top (rank 8) into python-chess square index.
    python-chess: square(file_index, rank_index) where rank_index=0 is rank 1. :contentReference[oaicite:0]{index=0}
    """
    return chess.square(c, 7 - r)  # :contentReference[oaicite:1]{index=1}


def square_to_rc(sq: chess.Square) -> RC:
    """
    Convert python-chess square index into internal (r,c) with r=0 at top (rank 8).
    Uses square_file/square_rank. :contentReference[oaicite:2]{index=2}
    """
    file_idx = chess.square_file(sq)  # :contentReference[oaicite:3]{index=3}
    rank_idx = chess.square_rank(sq)  # :contentReference[oaicite:4]{index=4}
    return (7 - rank_idx, file_idx)


class Board:
    """
    API yang dipakai Game/Renderer/Bot (dibuat kompatibel):
      - get_piece(r,c) -> Piece|None  (Piece.prob dipakai renderer buat %)
      - apply_move((r1,c1),(r2,c2)) -> "ok"|"illegal"
      - split_piece((r,c), (r1,c1), (r2,c2)) -> bool
      - move_log: List[str]
      - turn_color: 'w'|'b'
      - is_game_over(), result()
    """
    def __init__(self, setup: bool = True, seed: int | None = None):
        self.rng = random.Random(seed)
        self.move_log: List[str] = []

        base = chess.Board() if setup else chess.Board(None)
        self.branches: List[_Branch] = [_Branch(base, 1.0)]
        self._normalize()

    @property
    def turn_color(self) -> str:
        # python-chess: chess.WHITE True, chess.BLACK False. :contentReference[oaicite:5]{index=5}
        return "w" if self._root().turn == chess.WHITE else "b"  # :contentReference[oaicite:6]{index=6}

    def is_game_over(self) -> bool:
        return self._root().is_game_over()  # :contentReference[oaicite:7]{index=7}

    def result(self) -> str:
        return self._root().result()  # :contentReference[oaicite:8]{index=8}

    def _root(self) -> chess.Board:
        return max(self.branches, key=lambda b: b.weight).board

    def _normalize(self) -> None:
        total = sum(b.weight for b in self.branches)
        if total <= 0:
            self.branches = [_Branch(self._root().copy(stack=True), 1.0)]  # :contentReference[oaicite:9]{index=9}
            return
        for b in self.branches:
            b.weight /= total

    def get_piece(self, r: int, c: int) -> Optional[Piece]:
        """
        Return piece "paling mungkin" di (r,c) dengan prob = total weight cabang
        yang punya piece type+color itu di square tsb.

        piece_at() dari python-chess. :contentReference[oaicite:10]{index=10}
        """
        sq = rc_to_square(r, c)
        dist: Dict[Tuple[str, str], float] = {}
        for br in self.branches:
            p = br.board.piece_at(sq)  # :contentReference[oaicite:11]{index=11}
            if p is None:
                continue
            color = "w" if p.color == chess.WHITE else "b"
            kind = p.symbol().upper()  # 'P','N','B','R','Q','K'
            dist[(color, kind)] = dist.get((color, kind), 0.0) + br.weight

        if not dist:
            return None

        (color, kind), prob = max(dist.items(), key=lambda kv: kv[1])
        return Piece(kind=kind, color=color, probability=prob)

    def apply_move(self, start: RC, end: RC) -> str:
        """
        Apply move normal. Legalitas move, check-rule, castling, en passant, dll,
        ditangani python-chess via find_move() + push(). :contentReference[oaicite:12]{index=12}

        Quantum-lite:
          - kalau legal hanya di sebagian cabang -> collapse ke cabang legal.
          - kalau capture di sebagian cabang dan non-capture di cabang lain -> sampling
            sukses capture berdasarkan massa probabilitas cabang capture (is_capture). :contentReference[oaicite:13]{index=13}
        """
        from_sq = rc_to_square(*start)
        to_sq = rc_to_square(*end)

        legal: List[Tuple[_Branch, chess.Move]] = []
        for br in self.branches:
            b = br.board
            try:
                mv = b.find_move(from_sq, to_sq)  # :contentReference[oaicite:14]{index=14}
            except Exception:
                continue

            piece = b.piece_at(from_sq)
            if piece is None or piece.color != b.turn:
                continue
            legal.append((br, mv))

        if not legal:
            return "illegal"

        cap: List[Tuple[_Branch, chess.Move]] = []
        ncap: List[Tuple[_Branch, chess.Move]] = []
        for br, mv in legal:
            if br.board.is_capture(mv):  # :contentReference[oaicite:15]{index=15}
                cap.append((br, mv))
            else:
                ncap.append((br, mv))

        if cap and ncap:
            p_cap = sum(br.weight for br, _ in cap) / sum(br.weight for br, _ in legal)
            if self.rng.random() < p_cap:
                chosen = cap
                self.move_log.append(f"CAPTURE-SUCCESS p={p_cap:.2f}")
            else:
                chosen = ncap
                self.move_log.append(f"CAPTURE-FAIL    p={p_cap:.2f}")
        else:
            chosen = cap or ncap

        new_branches: List[_Branch] = []
        for br, mv in chosen:
            b2 = br.board.copy(stack=True)  # :contentReference[oaicite:16]{index=16}
            b2.push(mv)  # :contentReference[oaicite:17]{index=17}
            new_branches.append(_Branch(b2, br.weight))

        self.branches = new_branches
        self._normalize()

        self.move_log.append(f"{chess.square_name(from_sq)}->{chess.square_name(to_sq)}")  # :contentReference[oaicite:18]{index=18}
        return "ok"

    def split_piece(self, start: RC, t1: RC, t2: RC) -> bool:
        """
        Split jadi superposisi 2 *quiet legal moves* (non-capture).
        """
        from_sq = rc_to_square(*start)
        to1 = rc_to_square(*t1)
        to2 = rc_to_square(*t2)

        new_branches: List[_Branch] = []
        for br in self.branches:
            b = br.board
            try:
                mv1 = b.find_move(from_sq, to1)  # :contentReference[oaicite:19]{index=19}
                mv2 = b.find_move(from_sq, to2)  # :contentReference[oaicite:20]{index=20}
            except Exception:
                continue

            piece = b.piece_at(from_sq)
            if piece is None or piece.color != b.turn:
                continue

            if b.is_capture(mv1) or b.is_capture(mv2):  # :contentReference[oaicite:21]{index=21}
                continue

            b1 = b.copy(stack=True); b1.push(mv1)  # :contentReference[oaicite:22]{index=22}
            b2 = b.copy(stack=True); b2.push(mv2)  # :contentReference[oaicite:23]{index=23}

            new_branches.append(_Branch(b1, br.weight * 0.5))
            new_branches.append(_Branch(b2, br.weight * 0.5))

        if not new_branches:
            return False

        self.branches = new_branches
        self._normalize()
        self.move_log.append(
            f"SPLIT {chess.square_name(from_sq)}->{chess.square_name(to1)} | {chess.square_name(to2)}"
        )  # :contentReference[oaicite:24]{index=24}
        return True