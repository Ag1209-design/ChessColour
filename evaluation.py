import chess
import math
from configuration import pawn_table, knight_table, bishop_table, rook_table, queen_table, king_table, king_endgame_table

def calculate_win_probability(board):
    """Calculates the probability of winning for white and black,
    incorporating piece-square tables."""

    white_score = 0
    black_score = 0
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0  # King doesn't directly contribute to material score
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            if piece.color == chess.WHITE:
                white_score += value
                # PST adjustments
                if piece.piece_type == chess.PAWN:
                    white_score += pawn_table[square]
                elif piece.piece_type == chess.KNIGHT:
                    white_score += knight_table[square]
                elif piece.piece_type == chess.BISHOP:
                    white_score += bishop_table[square]
                elif piece.piece_type == chess.ROOK:
                    white_score += rook_table[square]
                elif piece.piece_type == chess.QUEEN:
                    white_score += queen_table[square]
                elif piece.piece_type == chess.KING:
                     white_score += king_table[square]
            else:
                black_score += value
                # PST adjustments (mirror for black)
                if piece.piece_type == chess.PAWN:
                    black_score += pawn_table[chess.square_mirror(square)]
                elif piece.piece_type == chess.KNIGHT:
                    black_score += knight_table[chess.square_mirror(square)]
                elif piece.piece_type == chess.BISHOP:
                    black_score += bishop_table[chess.square_mirror(square)]
                elif piece.piece_type == chess.ROOK:
                    black_score += rook_table[chess.square_mirror(square)]
                elif piece.piece_type == chess.QUEEN:
                    black_score += queen_table[chess.square_mirror(square)]
                elif piece.piece_type == chess.KING:
                     black_score += king_table[square]

    # Normalize scores and handle the case if both are zero.
    if white_score == 0 and black_score == 0:
        return 0.5, 0.5

    total_score = white_score + black_score
    
    #Check if the score is equal to 0
    if total_score ==0:
        return 0.5, 0.5
    
    total_score = white_score + black_score
    normalized_white_score = white_score / total_score
    normalized_black_score = black_score / total_score

    # Use a logistic function for probability, ensuring it's between 0 and 1
    white_prob = 1 / (1 + math.exp(-5 * (normalized_white_score - 0.5)))  # Adjust scaling factor for sensitivity
    black_prob = 1 - white_prob

    return white_prob, black_prob