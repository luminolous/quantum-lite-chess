# chess/board.py
from .piece import Piece, QuantumPiece
from .rules import Rules

class Board:
    def __init__(self):
        # 8x8 Grid menyimpan tuple (PieceObj, probability) atau None
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        self.q_pieces = [] # List of QuantumPiece obj
        self.move_log = []
        self._init_setup()

    def _init_setup(self):
        order = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for i, kind in enumerate(order):
            self.place_piece(0, i, Piece(kind, 'b'))
            self.place_piece(1, i, Piece('P', 'b'))
            self.place_piece(6, i, Piece('P', 'w'))
            self.place_piece(7, i, Piece(kind, 'w'))
        
        # Inisialisasi quantum state awal
        self.refresh_quantum_pieces()

    def place_piece(self, r, c, piece, prob=1.0):
        piece.prob = prob
        self.grid[r][c] = piece

    def get_piece(self, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return self.grid[r][c]
        return None

    def refresh_quantum_pieces(self):
        self.q_pieces.clear()
        for r in range(8):
            for c in range(8):
                p = self.get_piece(r, c)
                if p:
                    # Buat objek QuantumPiece baru buat ngelacak posisi ini
                    qp = QuantumPiece((r, c), p)
                    self.q_pieces.append(qp)

    def find_quantum_piece(self, r, c):
        """Mencari QuantumPiece yang relevan dengan koordinat"""
        for qp in self.q_pieces:
            for state_data in qp.qnum.values():
                if state_data[0] == (r, c):
                    return qp, list(qp.qnum.keys())[0] # Return key pertama found
        return None, None

    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end
        p = self.grid[sr][sc]
        self.grid[er][ec] = p
        self.grid[sr][sc] = None
        
        # Log
        self.move_log.append(f"{p.color}{p.kind}: ({sc},{sr})->({ec},{er})")

    def copy(self):
        """Buat salinan board untuk simulasi validasi moves"""
        new_board = Board()
        for r in range(8):
            for c in range(8):
                if self.grid[r][c]:
                    orig = self.grid[r][c]
                    new_board.grid[r][c] = Piece(orig.kind, orig.color, orig.prob)
        return new_board