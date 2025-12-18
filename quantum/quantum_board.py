# quantum/quantum_board.py
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Iterable
import math
import random

import chess  # python-chess


@dataclass
class Branch:
    board: chess.Board
    amp: complex  # amplitude (complex). Probability = |amp|^2


class QuantumBoard:
    """
    Quantum-lite chess engine:
    - Underlying rules/legality from python-chess.
    - Superposition of classical boards with complex amplitudes.
    - Interference happens when multiple branches merge into identical FEN.
    - Captures + "exclusion" (trying to move onto your own piece in some branches) => measurement (collapse).
    - Blocked-by-uncertainty (slide move) => controlled move: branch where legal moves, branch where illegal does null-move.
    """

    def __init__(
        self,
        fen: Optional[str] = None,
        *,
        seed: Optional[int] = None,
        max_branches: int = 64,
        eps_amp: float = 1e-12,
    ):
        self.rng = random.Random(seed)
        self.max_branches = int(max_branches)
        self.eps_amp = float(eps_amp)

        b = chess.Board(fen) if fen else chess.Board()
        self.branches: List[Branch] = [Branch(b, 1.0 + 0.0j)]
        self._normalize()

    @staticmethod
    def _prob(amp: complex) -> float:
        return (amp.real * amp.real) + (amp.imag * amp.imag)

    def _normalize(self) -> None:
        total = sum(self._prob(br.amp) for br in self.branches)
        if total <= 0:
            # fallback (klo semua amp 0)
            self.branches = [Branch(chess.Board(), 1.0 + 0.0j)]
            return
        scale = 1.0 / math.sqrt(total)
        for br in self.branches:
            br.amp *= scale

    def _merge_identical(self) -> None:
        buckets: Dict[str, complex] = defaultdict(complex)
        keep_board: Dict[str, chess.Board] = {}

        for br in self.branches:
            fen = br.board.fen()
            buckets[fen] += br.amp
            if fen not in keep_board:
                keep_board[fen] = br.board

        merged: List[Branch] = []
        for fen, amp in buckets.items():
            if abs(amp) > self.eps_amp:
                merged.append(Branch(keep_board[fen], amp))

        self.branches = merged
        self._normalize()

    def _prune(self) -> None:
        if len(self.branches) <= self.max_branches:
            return
        self.branches.sort(key=lambda br: self._prob(br.amp), reverse=True)
        self.branches = self.branches[: self.max_branches]
        self._normalize()

    def _post_step_cleanup(self) -> None:
        self._merge_identical()
        self._prune()
        self._merge_identical()

    # API buat UI / rendering
    def most_likely_board(self) -> chess.Board:
        return max(self.branches, key=lambda br: self._prob(br.amp)).board

    def turn(self) -> bool:
        # Pake cabang paling mungkin buat turn
        return self.most_likely_board().turn

    def square_distribution(self, square: int) -> Dict[Optional[str], float]:
        """
        Returns {piece_symbol or None: probability}.
        piece_symbol uses python-chess: 'P','p','K',... etc.
        """
        dist: Dict[Optional[str], float] = defaultdict(float)
        for br in self.branches:
            p = self._prob(br.amp)
            piece = br.board.piece_at(square)
            dist[piece.symbol() if piece else None] += p
        return dict(dist)

    def piece_probability(self, square: int) -> float:
        dist = self.square_distribution(square)
        return 1.0 - dist.get(None, 0.0)

    def legal_moves_distribution(self) -> Dict[str, float]:
        """
        Union of legal moves across branches: {uci: probability_mass}.
        """
        moves: Dict[str, float] = defaultdict(float)
        for br in self.branches:
            p = self._prob(br.amp)
            for mv in br.board.legal_moves:
                moves[mv.uci()] += p
        return dict(moves)

    # Coordinate helpers
    @staticmethod
    def rc_to_square(row: int, col: int) -> int:
        """
        If UI uses row=0 at TOP (rank 8) and col=0 at LEFT (file a).
        """
        file = col
        rank = 7 - row
        return chess.square(file, rank)

    @staticmethod
    def square_to_rc(square: int) -> Tuple[int, int]:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        row = 7 - rank
        col = file
        return row, col

    # Quantum operations
    def _copy_board(self, b: chess.Board) -> chess.Board:
        return b.copy(stack=False)

    def _push_or_null(self, b: chess.Board, mv: Optional[chess.Move]) -> None:
        if mv is None:
            b.push(chess.Move.null())
            return
        b.push(mv)

    def _collapse_to(self, keep_mask: List[bool]) -> None:
        kept = [br for br, keep in zip(self.branches, keep_mask) if keep]
        self.branches = kept if kept else self.branches  # safety
        self._normalize()

    def _measure_two_outcomes(
        self,
        mask_a: List[bool],
        mask_b: List[bool],
    ) -> str:
        """
        Choose outcome A or B based on total probability mass.
        Return "A" or "B" and collapses state accordingly.
        """
        p_a = sum(self._prob(br.amp) for br, keep in zip(self.branches, mask_a) if keep)
        p_b = sum(self._prob(br.amp) for br, keep in zip(self.branches, mask_b) if keep)

        if p_a <= 0 and p_b <= 0:
            return "NONE"

        r = self.rng.random() * (p_a + p_b)
        if r < p_a:
            self._collapse_to(mask_a)
            return "A"
        else:
            self._collapse_to(mask_b)
            return "B"

    # Classical move with quantum effects
    def apply_move(
        self,
        from_sq: int,
        to_sq: int,
        *,
        promotion: Optional[int] = None,
    ) -> bool:
        """
        Attempt a move (from,to) on the quantum state.

        Behavior:
        - Uses Board.find_move() per-branch (promotion defaults to queen for backrank pawn moves)
        - If move is legal in some branches and illegal in others:
            - If illegality is because target square has own piece => exclusion measurement/collapse.
            - Otherwise: controlled move => legal branches push(move), illegal branches push(null).
        - If capture is possible in some branches but not others => measurement on "capture happened" vs "not".
        """
        # Per branch move resolution
        legal_mv: List[Optional[chess.Move]] = [None] * len(self.branches)
        illegal_own: List[bool] = [False] * len(self.branches)
        capture_possible: List[bool] = [False] * len(self.branches)

        for i, br in enumerate(self.branches):
            b = br.board

            tgt = b.piece_at(to_sq)
            if tgt is not None and tgt.color == b.turn:
                illegal_own[i] = True
                continue

            try:
                mv = b.find_move(from_sq, to_sq, promotion=promotion) 
            except Exception:
                mv = None

            legal_mv[i] = mv
            if mv is not None:
                try:
                    capture_possible[i] = b.is_capture(mv)
                except Exception:
                    capture_possible[i] = False

        # Exclusion measurement: occupied by own vs not
        if any(illegal_own):
            mask_occ = illegal_own
            mask_free = [not x for x in illegal_own]
            outcome = self._measure_two_outcomes(mask_occ, mask_free)
            if outcome == "A":
                new_branches: List[Branch] = []
                for br in self.branches:
                    nb = self._copy_board(br.board)
                    self._push_or_null(nb, None)
                    new_branches.append(Branch(nb, br.amp))
                self.branches = new_branches
                self._post_step_cleanup()
                return True

            # Recompute arrays after collapse
            return self.apply_move(from_sq, to_sq, promotion=promotion)

        # Capture measurement if capture happens in some branches but not others
        if any(capture_possible) and not all(capture_possible):
            mask_cap = capture_possible
            mask_nocap = [not x for x in capture_possible]
            outcome = self._measure_two_outcomes(mask_cap, mask_nocap)
            # after collapse, recompute to execute consistently
            return self.apply_move(from_sq, to_sq, promotion=promotion)

        # Controlled move: legal branches do mv, illegal branches do null
        new_branches = []
        for br, mv in zip(self.branches, legal_mv):
            nb = self._copy_board(br.board)
            self._push_or_null(nb, mv) 
            new_branches.append(Branch(nb, br.amp))

        self.branches = new_branches
        self._post_step_cleanup()
        return True

    # Split move (superposition of two moves)
    def apply_split(
        self,
        from_sq: int,
        to_sq_a: int,
        to_sq_b: int,
        *,
        promotion: Optional[int] = None,
        phase_b: complex = 1j,
        require_noncapture: bool = True,
    ) -> bool:
        """
        Split move: same piece branches into two destinations (A and B).
        - amplitudes scaled by 1/sqrt(2); B also multiplied by phase_b (default i).
        - This is inspired by quantum chess split move + i-phase from iSWAP-style behavior. :contentReference[oaicite:10]{index=10}
        - Branches where split is not possible -> null move (turn still passes).
        """
        inv_sqrt2 = 1.0 / math.sqrt(2.0)
        out: List[Branch] = []

        for br in self.branches:
            b = br.board
            # If own piece occupies either target, treat as impossible split (null)
            for t in (to_sq_a, to_sq_b):
                tgt = b.piece_at(t)
                if tgt is not None and tgt.color == b.turn:
                    nb = self._copy_board(b)
                    self._push_or_null(nb, None)
                    out.append(Branch(nb, br.amp))
                    break
            else:
                # Try find legal moves
                try:
                    mv_a = b.find_move(from_sq, to_sq_a, promotion=promotion) 
                except Exception:
                    mv_a = None
                try:
                    mv_b = b.find_move(from_sq, to_sq_b, promotion=promotion) 
                except Exception:
                    mv_b = None

                if mv_a is None or mv_b is None:
                    nb = self._copy_board(b)
                    self._push_or_null(nb, None)
                    out.append(Branch(nb, br.amp))
                    continue

                if require_noncapture:
                    try:
                        if b.is_capture(mv_a) or b.is_capture(mv_b):
                            nb = self._copy_board(b)
                            self._push_or_null(nb, None)
                            out.append(Branch(nb, br.amp))
                            continue
                    except Exception:
                        pass

                # Create two child branches
                nb_a = self._copy_board(b)
                nb_b = self._copy_board(b)
                self._push_or_null(nb_a, mv_a)
                self._push_or_null(nb_b, mv_b)

                out.append(Branch(nb_a, br.amp * inv_sqrt2))
                out.append(Branch(nb_b, br.amp * inv_sqrt2 * phase_b))

        self.branches = out
        self._post_step_cleanup()
        return True