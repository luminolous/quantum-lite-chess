# chess/piece.py
import random

class Piece:
    """Representasi bidak klasik (dan versi 'lite' untuk quantum split)."""
    def __init__(self, kind, color, probability=1.0, qid=None):
        self.kind = kind    # 'K', 'Q', dst
        self.color = color  # 'w', 'b'
        self.prob = float(probability)
        self.qid = qid      # None -> klasik, int -> bagian dari superposisi

    @property
    def code(self):
        return f"{self.color}{self.kind}"

    @property
    def is_quantum(self):
        return self.qid is not None and self.prob < 1.0

    def clone(self, *, probability=None, qid=None):
        """Clone bidak (hindari shared-reference saat split)."""
        return Piece(
            self.kind,
            self.color,
            self.prob if probability is None else float(probability),
            self.qid if qid is None else qid,
        )

class QuantumPiece:
    """Menangani logika superposisi dan entanglement"""
    def __init__(self, pos, piece_obj):
        self.piece_data = piece_obj.code # Simpan kode misal 'wP'
        # states: key=state_id, value=[pos, probability]
        self.qnum = {'0': [pos, 1.0]} 
        self.ent = [] # Entanglement list
 
    def measure(self):
        """Collapse probabilitas ke satu state"""
        total_prob = sum(state[1] for state in self.qnum.values())
        rand = random.random() * total_prob
        cum = 0.0
        chosen_state = None

        for st_id, (p, prob) in self.qnum.items():
            cum += prob
            if rand <= cum:
                chosen_state = st_id
                break

        # Collapse: set chosen state=1.0, others=0
        final_pos = self.qnum[chosen_state][0]
        for st_id in self.qnum:
            self.qnum[st_id][1] = 1.0 if st_id == chosen_state else 0.0
        return final_pos

    def entangle_oneblock(self, other_piece, target_pos):
        """Simple entanglement example: handle transitions, update ent list"""
        # This method is for demonstration; can be expanded.
        x = self.qnum['0'][1]
        y = other_piece.qnum['0'][1]

        # Example: split state into 2. Weighted by x,y
        my_state = '0'
        other_state = '0'

        a = x * y
        b = x * (1 - y)

        # Update probabilities
        self.qnum[my_state + '0'] = [self.qnum[my_state][0], a]
        self.qnum[my_state + '1'] = [target_pos, b]
        del self.qnum[my_state]

        last_state = other_state[:-1] + str(int(not int(other_state[-1])))

        other_piece.ent.append((self, my_state + '1', other_state))
        other_piece.ent.append((self, my_state + '0', last_state))
        
        self.ent.append((other_piece, other_state, my_state + '1'))
        self.ent.append((other_piece, last_state, my_state + '0'))