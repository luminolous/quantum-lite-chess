class Rules:
    @staticmethod
    def get_valid_moves(board_obj, r, c):
        piece = board_obj.get_piece(r, c)
        if not piece: return []
        
        moves = []
        color = piece.color
        kind = piece.kind
        grid = board_obj.grid # Access raw grid for checking

        # Logic pawn
        if kind == 'P':
            direction = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1
            
            # Forward 1
            nr = r + direction
            if 0 <= nr < 8 and grid[nr][c] is None:
                moves.append((nr, c))
                # Forward 2
                if r == start_row and grid[r + 2*direction][c] is None:
                    moves.append((r + 2*direction, c))
            
            # Captures
            for dc in [-1, 1]:
                nr, nc = r + direction, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = grid[nr][nc]
                    if target and target.color != color:
                        moves.append((nr, nc))

        # Logic knight
        elif kind == 'N':
            offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
            for dr, dc in offsets:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = grid[nr][nc]
                    if not target or target.color != color:
                        moves.append((nr, nc))

        # Logic sliding pieces (B, R, Q)
        elif kind in ['B', 'R', 'Q']:
            directions = []
            if kind in ['B', 'Q']: directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            if kind in ['R', 'Q']: directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    target = grid[nr][nc]
                    if target is None:
                        moves.append((nr, nc))
                    elif target.color != color:
                        moves.append((nr, nc))
                        break
                    else:
                        break # Tabrak teman
                    nr += dr
                    nc += dc

        # Logic king
        elif kind == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        target = grid[nr][nc]
                        if not target or target.color != color:
                            moves.append((nr, nc))
                            
        return moves

    @staticmethod
    def is_in_check(board_obj, color):
        king_pos = None
        # Cari king
        for r in range(8):
            for c in range(8):
                p = board_obj.get_piece(r, c)
                if p and p.kind == 'K' and p.color == color:
                    king_pos = (r, c)
                    break
        if not king_pos: return True

        enemy_color = 'b' if color == 'w' else 'w'
        
        for r in range(8):
            for c in range(8):
                p = board_obj.get_piece(r, c)
                if p and p.color == enemy_color:
                    moves = Rules.get_valid_moves(board_obj, r, c)
                    if king_pos in moves:
                        return True
        return False