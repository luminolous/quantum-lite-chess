# chess/board.py
import random
from .piece import Piece

class Board:
    def __init__(self, setup=True):
        # 8x8 Grid menyimpan Piece atau None
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.move_log = []
        self._next_qid = 1  # untuk memberi ID superposisi (quantum-lite)

        if setup:
            self._init_setup()

    def _init_setup(self):
        order = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for i, kind in enumerate(order):
            self.place_piece(0, i, Piece(kind, 'b'))
            self.place_piece(1, i, Piece('P', 'b'))
            self.place_piece(6, i, Piece('P', 'w'))
            self.place_piece(7, i, Piece(kind, 'w'))

    # --- basic helpers ---
    def place_piece(self, r, c, piece, prob=1.0):
        piece.prob = float(prob)
        self.grid[r][c] = piece

    def get_piece(self, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return self.grid[r][c]
        return None

    def move_piece(self, start, end):
        """Move tanpa logika quantum (dipakai internal)."""
        sr, sc = start
        er, ec = end
        p = self.grid[sr][sc]
        self.grid[er][ec] = p
        self.grid[sr][sc] = None

    # --- quantum-lite primitives ---
    def _positions_by_qid(self, qid):
        pos = []
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.qid == qid:
                    pos.append((r, c, p))
        return pos

    def split_piece(self, start, end1, end2):
        """Split satu bidak menjadi 2 cabang (prob 0.5 + 0.5)."""
        sr, sc = start
        p = self.get_piece(sr, sc)
        if not p:
            return False

        (r1, c1), (r2, c2) = end1, end2
        if not (0 <= r1 < 8 and 0 <= c1 < 8 and 0 <= r2 < 8 and 0 <= c2 < 8):
            return False
        if (r1, c1) == (r2, c2):
            return False
        if self.get_piece(r1, c1) is not None:
            return False
        if self.get_piece(r2, c2) is not None:
            return False

        # hanya bisa split kalau masih klasik
        if p.qid is not None or p.prob < 1.0:
            return False

        qid = self._next_qid
        self._next_qid += 1

        p1 = p.clone(probability=0.5, qid=qid)
        p2 = p.clone(probability=0.5, qid=qid)

        # remove original
        self.grid[sr][sc] = None
        self.grid[r1][c1] = p1
        self.grid[r2][c2] = p2

        self.move_log.append(
            f"{p.color}{p.kind}: SPLIT ({sc},{sr})->({c1},{r1})&({c2},{r2})"
        )
        return True

    def collapse_at(self, r, c):
        """Collapse superposisi untuk bidak di (r,c) (jika ada)."""
        p = self.get_piece(r, c)
        if not p or p.qid is None:
            return None

        return self._collapse_qid(p.qid)

    def _collapse_qid(self, qid, forced_pos=None):
        """
        Collapse semua cabang dengan qid tertentu.
        - forced_pos: kalau diberikan, collapse dipaksa ke posisi itu (jika valid).
        Return posisi final (r,c).
        """
        entries = self._positions_by_qid(qid)
        if not entries:
            return None

        # template untuk reconstruct klasik
        template = entries[0][2]

        if forced_pos is not None:
            chosen = forced_pos
        else:
            weights = [max(0.0, float(p.prob)) for (_r, _c, p) in entries]
            total = sum(weights)
            if total <= 0:
                chosen = random.choice([(e[0], e[1]) for e in entries])
            else:
                rnd = random.uniform(0.0, total)
                cum = 0.0
                chosen = (entries[0][0], entries[0][1])
                for (rr, cc, _p), w in zip(entries, weights):
                    cum += w
                    if rnd <= cum:
                        chosen = (rr, cc)
                        break

        # hapus semua cabang lama
        for rr, cc, _p in entries:
            self.grid[rr][cc] = None

        # tempatkan versi klasik (qid=None, prob=1.0) di posisi final
        cr, cc = chosen
        self.grid[cr][cc] = Piece(template.kind, template.color, 1.0, qid=None)
        self.move_log.append(f"{template.color}{template.kind}: COLLAPSE -> ({cc},{cr})")
        return (cr, cc)

    def _attempt_capture_quantum(self, target_pos):
        """Coba tangkap bidak quantum di target_pos. Return (success, final_pos)."""
        tr, tc = target_pos
        target = self.get_piece(tr, tc)
        if not target or target.qid is None:
            return True, (tr, tc)  # bukan quantum

        qid = target.qid
        final_pos = self._collapse_qid(qid)  # collapse random dulu

        # setelah collapse, cek apakah target tetap di square yang diserang
        if final_pos == (tr, tc):
            # capture sukses: remove target klasik
            self.grid[tr][tc] = None
            return True, final_pos

        # capture gagal: target ternyata berada di square lain
        return False, final_pos

    def apply_move(self, start, end):
        """
        Move utama untuk game:
        - kalau attacker quantum: collapse dulu ke cabang yang dipilih
        - kalau target quantum dan diserang: target collapse dulu -> capture bisa gagal
        Return status string: "moved" | "captured" | "capture_failed"
        """
        sr, sc = start
        er, ec = end
        attacker = self.get_piece(sr, sc)
        if not attacker:
            return "capture_failed"

        # Kalau attacker quantum, collapse dulu ke cabang yang dipilih (start)
        if attacker.qid is not None:
            self._collapse_qid(attacker.qid, forced_pos=(sr, sc))
            attacker = self.get_piece(sr, sc)

        target = self.get_piece(er, ec)

        # Kalau target quantum, capture bisa gagal
        if target is not None and target.qid is not None:
            ok, _final = self._attempt_capture_quantum((er, ec))
            if not ok:
                # attacker tidak bergerak (turn tetap dianggap selesai oleh caller)
                return "capture_failed"
            # target sudah dihapus kalau ok (lihat _attempt_capture_quantum)
            self.move_piece((sr, sc), (er, ec))
            self.move_log.append(f"{attacker.color}{attacker.kind}: ({sc},{sr})->({ec},{er}) xQ")
            return "captured"

        # Capture normal
        if target is not None:
            self.move_piece((sr, sc), (er, ec))
            self.move_log.append(f"{attacker.color}{attacker.kind}: ({sc},{sr})->({ec},{er}) x")
            return "captured"

        # Move biasa
        self.move_piece((sr, sc), (er, ec))
        self.move_log.append(f"{attacker.color}{attacker.kind}: ({sc},{sr})->({ec},{er})")
        return "moved"

    def copy(self):
        """
        FIX: copy tidak boleh memanggil _init_setup() lagi.
        Ini dipakai untuk simulasi / validasi rules kalau diperlukan.
        """
        new_board = Board(setup=False)
        new_board._next_qid = self._next_qid
        for r in range(8):
            for c in range(8):
                orig = self.grid[r][c]
                if orig:
                    new_board.grid[r][c] = Piece(orig.kind, orig.color, orig.prob, orig.qid)
        # move_log biasanya tidak dibutuhkan untuk simulasi
        return new_board