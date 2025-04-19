import chess
import random
from configuration import pawn_table, knight_table, bishop_table, rook_table, queen_table, king_table, king_endgame_table
from uci_engine import UCIEngine  # Import UCI engine wrapper

class AIPlayer:
    """Wrapper class to use a UCI chess engine as an AI player."""
    
    def __init__(self):
        self.engine = UCIEngine()  # Initialize UCI engine

    def choose_move(self, board):
        """Uses the UCI engine to get the best move."""
        return self.engine.choose_move(board)

    def close(self):
        """Closes the UCI engine process when the game ends."""
        self.engine.close()


# --- Evaluation Function ---
def evaluate_board(board):
    if board.is_checkmate():
        if board.turn == chess.WHITE:
            return float('-inf')  # Black wins
        else:
            return float('inf')   # White wins
    elif board.is_stalemate() or board.is_insufficient_material() or \
                 board.is_seventyfive_moves() or board.is_fivefold_repetition():  # ADD THESE CONDITIONS
        return 0  # Draw

    # Material Balance
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    material_balance = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                material_balance += value
            else:
                material_balance -= value

            # Piece-Square Table Adjustment
            if piece.piece_type == chess.PAWN:
                if piece.color == chess.WHITE:
                    material_balance += pawn_table[square]  # White's perspective
                else:
                    material_balance -= pawn_table[chess.square_mirror(square)] #Black's perspective
            elif piece.piece_type == chess.KNIGHT:
                if piece.color == chess.WHITE:
                    material_balance += knight_table[square]
                else:
                    material_balance -= knight_table[chess.square_mirror(square)]
            elif piece.piece_type == chess.BISHOP:
                if piece.color == chess.WHITE:
                    material_balance += bishop_table[square]
                else:
                    material_balance -= bishop_table[chess.square_mirror(square)]
            elif piece.piece_type == chess.ROOK:
                if piece.color == chess.WHITE:
                    material_balance += rook_table[square]
                else:
                    material_balance -= rook_table[chess.square_mirror(square)]
            elif piece.piece_type == chess.QUEEN:
                if piece.color == chess.WHITE:
                    material_balance += queen_table[square]
                else:
                    material_balance -= queen_table[chess.square_mirror(square)]
            elif piece.piece_type == chess.KING:
                # if board.is_endgame(): #DOES NOT EXIST SO IT WILL ERROR
                # We will assume is not the end game because I cannot add any new code!
                if len(board.piece_map()) <=15 : #Check middle game
                    if piece.color == chess.WHITE:
                        material_balance += king_endgame_table[square]
                    else:
                        material_balance -= king_endgame_table[chess.square_mirror(square)]
                else:
                    if piece.color == chess.WHITE:
                        material_balance += king_table[square]
                    else:
                        material_balance -= king_table[chess.square_mirror(square)]

            else:
                print(f"Unknown piece type: {piece.piece_type}") #ERROR CHECK

                # else:
                # if piece.color == chess.WHITE:
                # material_balance += king_table[square]
                # else:
                # material_balance -= king_table[chess.square_mirror(square)]

    # Piece Activity (Mobility)
    mobility_white = len(list(board.legal_moves))
    board.turn = chess.BLACK
    mobility_black = len(list(board.legal_moves))
    board.turn = chess.WHITE
    mobility = mobility_white - mobility_black

    # King Safety (Very basic - proximity to own pawns)
    king_safety_white = 0
    king_square = board.king(chess.WHITE)
    if king_square:
        for square in chess.SQUARES:
            if board.piece_at(square) and board.piece_at(square).piece_type == chess.PAWN and board.piece_at(square).color == chess.WHITE and chess.square_distance(square, king_square) <= 2:
                king_safety_white += 1

    king_safety_black = 0
    king_square = board.king(chess.BLACK)
    if king_square:
        for square in chess.SQUARES:
            if board.piece_at(square) and board.piece_at(square).piece_type == chess.PAWN and board.piece_at(square).color == chess.BLACK and chess.square_distance(square, king_square) <= 2:
                king_safety_black += 1

    king_safety = king_safety_white - king_safety_black

    # Weighted Sum of Factors
    evaluation = (material_balance +
                  0.1 * mobility +  # Reduced weight for mobility
                  0.2 * king_safety) # Reduced weight for king safety

    return evaluation

class HumanPlayer:
    """Handles human player input for move selection."""
    def __init__(self, color):
        self.color = color
        self.waiting_for_click = True

    def choose_move(self, board):
        """Returns None to indicate that the move will be made via clicks."""
        # This will signal the main loop to wait for click input
        return None
    