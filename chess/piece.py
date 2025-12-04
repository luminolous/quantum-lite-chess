# chess/piece.py
import random

class Piece:
    """Representasi bidak klasik"""
    def __init__(self, kind, color, probability=1.0):
        self.kind = kind    # 'K', 'Q', dst
        self.color = color  # 'w', 'b'
        self.prob = probability

    @property
    def code(self):
        return f"{self.color}{self.kind}"

class QuantumPiece:
    """Menangani logika superposisi dan entanglement"""
    def __init__(self, pos, piece_obj):
        self.piece_data = piece_obj.code # Simpan kode misal 'wP'
        # states: key=state_id, value=[pos, probability]
        self.qnum = {'0': [pos, 1.0]} 
        self.ent = [] # Entanglement list
 
    def measure(self):
        """Melakukan pengukuran (Measurement/Collapse)"""
        total_prob = sum([val[1] for val in self.qnum.values()])
        if total_prob == 0: return None

        rnd = random.uniform(0, total_prob)
        cumulative = 0
        chosen_state = None
        
        for state, data in self.qnum.items():
            cumulative += data[1]
            if rnd <= cumulative:
                chosen_state = state
                break
        
        if chosen_state:
            final_pos = self.qnum[chosen_state][0]
            # Reset state jd klasik di posisi baru
            self.qnum.clear()
            self.ent.clear()
            self.qnum['0'] = [final_pos, 1.0]
            return final_pos
        return None

    def entangle_oneblock(self, my_state, target_pos, other_piece, other_state):
        """Logika entanglement"""
        x = self.qnum[my_state][1]
        y = other_piece.qnum[other_state][1]

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