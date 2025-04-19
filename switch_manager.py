import chess
import random
import time
import pygame
from enum import Enum
from evaluation import calculate_win_probability
import configuration
import logging
import sys
from animation_handler import AnimationHandler
import gc

from win_probability import (
    calculate_win_probability_enhanced, 
    WIN_PROBABILITY_MODE,
    USE_ENGINE_FOR_SWITCHING,
    USE_ENGINE_FOR_DISPLAY,
    ENGINE_ANALYSIS_TIME,
    STABILITY_FACTOR_ENABLED,
    STABILITY_FACTOR_WEIGHT
)
from uci_engine import EngineManager

# Get the logger from configuration
logger = configuration.logger

class SwitchState(Enum):
    IDLE = "idle"
    ANIMATION = "animation"
    HIGHLIGHTING = "highlighting"
    SWITCHING = "switching"

class SwitchManager:
    """Handles all aspects of piece color switching in the chess game."""

    def __init__(self, board, animation_handler=None, game = None):
        self.board = board
        self.animation_handler = animation_handler
        self.game = game
        
        # Switch state
        self.is_active = False
        self.sequence_active = False
        self.state = SwitchState.IDLE
        self.last_switched_squares = []
        self.last_switched_color = None
        self.switched_pieces = set()
        self.switch_move_numbers = []
        self.switch_highlight_start_time = None
        
        # Access to promoted pieces info
        self.promoted_pieces = set()
        if game and hasattr(game, 'promoted_pieces'):
            self.promoted_pieces = game.promoted_pieces

        # Counters
        self.white_switch_count = 0
        self.black_switch_count = 0
        
        # Timer-based switching
        self.timer_start_time = pygame.time.get_ticks()
        self.COLOR_SWITCH_TIMER_EVENT = pygame.USEREVENT + 2
        
        # Initialize timer if needed
        if configuration.SWITCH_TRIGGER_MODE == "timer":
            pygame.time.set_timer(self.COLOR_SWITCH_TIMER_EVENT, configuration.SWITCH_TIMER_DURATION)
            logger.info(f"Timer-based switching initialized with duration: {configuration.SWITCH_TIMER_DURATION}ms")
            
        # Initialize enhanced evaluation
        self._initialize_enhanced_evaluation()

    def _initialize_enhanced_evaluation(self):
        """
        Initialize enhanced win probability evaluation if configured.
        Called during __init__ to ensure each instance uses the right evaluation method.
        """
        # Save the original method reference if not already saved
        if not hasattr(self, '_original_evaluate_probability_change'):
            self._original_evaluate_probability_change = self._evaluate_probability_change_safe
        
        # Replace with enhanced version only if configured to do so
        if WIN_PROBABILITY_MODE != "material":
            logger.info("Enhanced win probability evaluation enabled for switch manager")
            # The self is already bound to the instance methods, no need for a wrapper
            self._evaluate_probability_change_safe = self.evaluate_probability_change

    def evaluate_probability_change(self, board, piece, square):
        """
        Enhanced version of _evaluate_probability_change_safe that can use
        engine evaluation if configured to do so.
        """
        try:
            # Get engine if needed
            engine = None
            if WIN_PROBABILITY_MODE == "engine":
                engine_manager = EngineManager.get_instance()
                engine = engine_manager.get_engine()
            
            # First, calculate probabilities with the original board state
            original_white_prob, original_black_prob = calculate_win_probability_enhanced(
                board, 
                engine=engine,
                use_engine= USE_ENGINE_FOR_SWITCHING
            )
            
            # Create a temporary board copy for the simulation
            temp_board = board.copy()
            temp_piece = temp_board.piece_at(square)
            if temp_piece:
                temp_board.remove_piece_at(square)
                temp_board.set_piece_at(square, chess.Piece(temp_piece.piece_type, not temp_piece.color))
                
            # Calculate probabilities with the simulated change
            new_white_prob, new_black_prob = calculate_win_probability_enhanced(
                temp_board, 
                engine=engine,
                use_engine= USE_ENGINE_FOR_SWITCHING
            )
            
            # Return the absolute differences in probabilities
            return abs(new_white_prob - original_white_prob), abs(new_black_prob - original_black_prob)
        except Exception as e:
            logger.error(f"Error in enhanced probability calculation: {e}")
            # Fall back to original method
            return self._original_evaluate_probability_change(board, piece, square)

    def restore_original_evaluation(self):
        """
        Restore the original _evaluate_probability_change_safe method.
        """
        if hasattr(self, '_original_evaluate_probability_change'):
            self._evaluate_probability_change_safe = self._original_evaluate_probability_change
            logger.info("Restored original win probability evaluation for switch manager")

    def handle_switch_trigger(self):
            # Only check for timer-based switching if that mode is enabled and no switch sequence is active
            if configuration.SWITCH_TRIGGER_MODE == "timer" and not self.game.switch_sequence_active:
                time_elapsed = pygame.time.get_ticks() - self.game.timer_start_time
                remaining_time = max(0, (configuration.SWITCH_TIMER_DURATION - time_elapsed) // 1000)

                if remaining_time > 0:
                    # Update the countdown timer on the game window 
                    print(f"\rTime until switch: {remaining_time} seconds", end="")
                    sys.stdout.flush()
                elif remaining_time <= 0:
                    print("\n🔄 Timer-based switching triggered!")
                    self.game.find_switch_piece()  # Start the switch process
    
    def check_move_trigger(self, move_count):
        """Check if a move-based switch should be triggered."""
        if (not self.sequence_active and 
            move_count >= 10 and 
            (move_count - 10) % 5 == 0 and 
            move_count not in self.switch_move_numbers):
            logger.info(f"Move-based switch triggered at move {move_count}")
            return True
        return False
    
    def check_timer_trigger(self):
        """Check if a timer-based switch should be triggered."""
        if not self.sequence_active and not self.is_active:
            elapsed = pygame.time.get_ticks() - self.timer_start_time
            if elapsed >= configuration.SWITCH_TIMER_DURATION:
                self.timer_start_time = pygame.time.get_ticks()
                logger.info(f"Timer-based switch triggered after {elapsed}ms")
                return True
        return False

    def check_random_token_trigger(self, move_count):
        """Check if a random token-based switch should be triggered."""
        if (not self.sequence_active and 
            configuration.SWITCH_TRIGGER_MODE == "random_token" and
            hasattr(configuration, 'RANDOM_TOKEN_MOVES') and
            move_count in configuration.RANDOM_TOKEN_MOVES and
            move_count not in self.switch_move_numbers):
            logger.info(f"Random token-based switch triggered at move {move_count}")
            return True
        return False
    
    def restart_timer(self):
        """Restarts the switch timer."""
        self.timer_start_time = pygame.time.get_ticks()
        if configuration.SWITCH_TRIGGER_MODE == "timer":
            pygame.time.set_timer(self.COLOR_SWITCH_TIMER_EVENT, configuration.SWITCH_TIMER_DURATION)
            logger.debug(f"Switch timer restarted with duration: {configuration.SWITCH_TIMER_DURATION}ms")
   
    def find_switch_pieces(self, num_pieces=None):
        """Find pieces to switch based on the selected switch mode."""
        # Only proceed if a switch sequence isn't already active
        if self.sequence_active:
            logger.info("Switch sequence already in progress. Skipping.")
            return
        
        # Always use the game's switch_mode if available
        if num_pieces is None and hasattr(self, 'game') and hasattr(self.game, 'switch_mode'):
            num_pieces = self.game.switch_mode
        elif num_pieces is None:
            num_pieces = configuration.DEFAULT_SWITCH_MODE
            
        logger.info(f"Finding pieces to switch. Mode: {num_pieces} piece(s)")
        
        # Get eligible pieces
        eligible_pieces = self._get_eligible_pieces()
        if not eligible_pieces:
            logger.info("No eligible pieces found for switching.")
            return
        
        # Evaluate and select pieces
        best_squares = self._evaluate_switch_candidates(eligible_pieces, num_pieces)
        
        # IMPORTANT FIX: Check if any pieces were selected
        if not best_squares:
            logger.info("No suitable pieces selected after evaluation. Skipping switch entirely.")
            return
        
        # Store the selected squares and start the switch process
        self.last_switched_squares = best_squares
        logger.info(f"Selected for switching: {best_squares}")
        
        # Set state BEFORE starting animation
        self.sequence_active = True
        self.state = SwitchState.ANIMATION
        self.is_active = True
        
        # Start animation after state is set
        if self.animation_handler:
            self.animation_handler.start_animation()
        
        # Highlight each square for switching WITHOUT changing colors
        for square in best_squares:
            self._highlight_piece_for_switch(square)

        if hasattr(self, 'game'):
            self.sync_state_to_game(self.game)
            
        return best_squares 

    def switch_piece_color(self):
        """Execute the color switch on selected pieces."""
        logger.info(f"switch_piece_color triggered at time {time.time()}")

        # Store the current turn before executing the switch
        current_turn = self.board.turn
        
        # Ensure last_switched_squares is a list
        if not isinstance(self.last_switched_squares, list):
            self.last_switched_squares = [self.last_switched_squares]

        if not self.last_switched_squares:
            logger.info("No pieces selected to switch. Returning.")
            return

        # Track the color of the pieces being switched
        switched_colors = []
        
        # Process each square in the list
        for square in self.last_switched_squares:
            piece = self.board.piece_at(square)
            if not piece:
                logger.warning(f"No piece found at {square}. Skipping switch.")
                continue

            original_color = piece.color
            new_color = not piece.color
            piece_type = piece.piece_type
            
            # Remember the original color for each piece
            switched_colors.append(original_color)

            logger.debug(f"Switching piece at {square} from {original_color} to {new_color}")

            # Execute the actual switch
            self.board.remove_piece_at(square)
            new_piece = chess.Piece(piece_type, new_color)
            self.board.set_piece_at(square, new_piece)
            print(f"Switch occurs! Piece at square {square} changed from {original_color} to {new_color}")
            
            # Record the switch
            self.switch_move_numbers.append(self.move_count if hasattr(self, 'move_count') else -1)
            self.switched_pieces.add(square)

            # Update the switch counters
            if new_color == chess.WHITE:
                self.white_switch_count += 1
            else:
                self.black_switch_count += 1

            logger.info(f"Piece at square {square} changed color to {'white' if new_color else 'black'}")

        # After all pieces are switched, restore the original player's turn
        self.board.turn = current_turn
        
        # Update last_switched_color based on the original colors of all switched pieces
        # For single-piece switching, this will be the color of the piece that was switched
        if switched_colors:
            # When multiple pieces are switched, use the first one's color
            # This is important for the alternating pattern in single-piece mode
            self.last_switched_color = switched_colors[0]
            logger.info(f"Updated last_switched_color to {self.last_switched_color}")
                
        # Restart the timer if in timer mode
        if configuration.SWITCH_TRIGGER_MODE == "timer":
            self.restart_timer()
            
        logger.info("All selected pieces switched successfully")

        return True
    
    def _get_eligible_pieces(self):
        """Returns a list of non-king pieces that can be switched."""
        eligible_pieces = []
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if self._is_valid_switch_piece(piece, square):
                eligible_pieces.append((piece, square))
        return eligible_pieces

    def _evaluate_switch_candidates(self, pieces, num_pieces=2):
        logger.debug(f"evaluate_switch_candidates() called with num_pieces={num_pieces}")

        white_candidates = []
        black_candidates = []

        # Sort pieces by probability impact (lower impact is better)
        # We're using a copy of the board to avoid modifying the actual game state
        board_copy = self.board.copy()
        
        # Evaluate each piece's impact on a copy of the board
        piece_impacts = []
        for piece, square in pieces:
            # Evaluate impact using board copy
            impact = self._evaluate_probability_change_safe(board_copy, piece, square)
            piece_impacts.append((piece, square, sum(impact)))
        
        # Sort by impact
        sorted_pieces = sorted(piece_impacts, key=lambda x: x[2])
        
        # Convert back to original format
        sorted_pieces = [(p[0], p[1]) for p in sorted_pieces]

        # Separate pieces into white and black lists
        for piece, square in sorted_pieces:
            if piece.color == chess.WHITE:
                white_candidates.append(square)
            else:
                black_candidates.append(square)

        logger.debug(f"Initial White Candidates: {white_candidates}")
        logger.debug(f"Initial Black Candidates: {black_candidates}")
        
        # Filter out pieces that would cause check
        filtered_white_candidates = []
        filtered_black_candidates = []
        
        for square in white_candidates:
            if not self._would_cause_check(self.board, square):
                filtered_white_candidates.append(square)
            else:
                logger.debug(f"White piece at {square} filtered out to prevent check")
        
        for square in black_candidates:
            if not self._would_cause_check(self.board, square):
                filtered_black_candidates.append(square)
            else:
                logger.debug(f"Black piece at {square} filtered out to prevent check")
        
        white_candidates = filtered_white_candidates
        black_candidates = filtered_black_candidates
        
        logger.debug(f"Filtered White Candidates: {white_candidates}")
        logger.debug(f"Filtered Black Candidates: {black_candidates}")

        # Ensure we select exactly `num_pieces` pieces
        selected_squares = []

        if num_pieces == 2:
            if white_candidates and black_candidates:
                selected_squares.append(white_candidates[0])
                selected_squares.append(black_candidates[0])
            else:
                logger.info("Cannot find both white and black pieces for two-piece switching")
        else:  # Single piece mode
            # Simplified prioritization logic to strictly enforce alternating colors
            # If last switched piece was BLACK (or no previous switch), prioritize WHITE
            # If last switched piece was WHITE, prioritize BLACK
            prioritize_white = (self.last_switched_color == chess.BLACK or self.last_switched_color is None)
            
            logger.debug(f"Last switched color: {self.last_switched_color}")
            logger.info(f"Strictly prioritizing {'white' if prioritize_white else 'black'} pieces for switching")
            
            # STRICT ALTERNATING COLOR LOGIC:
            # Only select a piece if it matches the prioritized color
            if prioritize_white and white_candidates:
                selected_squares.append(white_candidates[0])
                logger.info(f"Selected white piece at {white_candidates[0]}")
            elif not prioritize_white and black_candidates:
                selected_squares.append(black_candidates[0])
                logger.info(f"Selected black piece at {black_candidates[0]}")
            else:
                logger.info(f"No eligible {'white' if prioritize_white else 'black'} pieces found. Skipping switch entirely.")
                # Return empty list to signal that no switch should occur

        logger.info(f"Final candidates selected: {selected_squares} (Mode: {num_pieces})")
        return selected_squares

    def _is_valid_switch_piece(self, piece, square):
        """Checks if a piece is eligible for switching."""
        if not piece or piece.piece_type == chess.KING:
            return False
        if square in self.switched_pieces:
            return False
        if self._is_piece_protected(piece, square):
            return False
            
        # Check if the piece is directly attacking the opponent's king
        if self._is_piece_attacking_king(square):
            logger.info(f"Piece at {square} is attacking opponent's king - not eligible for switch")
            return False
        
        # Check pawn position - prevent switching pawns at starting position or near promotion
        if piece.piece_type == chess.PAWN:
            rank = chess.square_rank(square)
            # White pawns on rank 1 (starting) or rank 6 (one step from promotion)
            # Black pawns on rank 6 (starting) or rank 1 (one step from promotion)
            if (piece.color == chess.WHITE and (rank == 1 or rank == 6)) or \
            (piece.color == chess.BLACK and (rank == 6 or rank == 1)):
                return False
        
        # Prevent switching promoted pieces
        if square in self.promoted_pieces:
            return False
                
        return True
    
    def _is_piece_protected(self, piece, square):
        """Checks if a piece is too close to the king or in a protected position."""
        king_square = self.board.king(piece.color)
        return chess.square_distance(square, king_square) <= 2

    def _is_piece_attacking_king(self, piece_square):
        """
        Checks if a piece at the given square is directly attacking the opponent's king.
        """
        piece = self.board.piece_at(piece_square)
        if not piece:
            return False
            
        opponent_color = not piece.color
        opponent_king_square = self.board.king(opponent_color)
        if not opponent_king_square:
            return False
            
        # Save original turn
        original_turn = self.board.turn
        
        # Set board to piece's turn so we can check its moves
        self.board.turn = piece.color
        
        # Check if this piece can attack the opponent's king
        is_attacking = False
        for move in self.board.legal_moves:
            if move.from_square == piece_square and move.to_square == opponent_king_square:
                is_attacking = True
                break
        
        # Restore original turn
        self.board.turn = original_turn
        
        return is_attacking

    def _would_cause_check(self, board, square):
            """Simulates a piece color switch and checks if it would cause check."""
            # Create a temporary board copy for simulation
            temp_board = board.copy()
            piece = temp_board.piece_at(square)
            if not piece:
                return False
                
            # Simulate the color switch
            temp_board.remove_piece_at(square)
            temp_board.set_piece_at(square, chess.Piece(piece.piece_type, not piece.color))
            
            # Check if the switch would put either king in check
            white_king_square = temp_board.king(chess.WHITE)
            black_king_square = temp_board.king(chess.BLACK)
            
            # Return True if either king would be in check
            return (white_king_square and temp_board.is_check()) or \
                (black_king_square and temp_board.turn == chess.BLACK and temp_board.is_check())

    def _evaluate_probability_change_safe(self, board, piece, square):
        """Evaluates the win probability change if a piece is switched without modifying the original board."""
        # First, calculate probabilities with the original board state
        original_white_prob, original_black_prob = calculate_win_probability(board)
        
        # Create a temporary board copy for the simulation
        temp_board = board.copy()
        temp_piece = temp_board.piece_at(square)
        if temp_piece:
            temp_board.remove_piece_at(square)
            temp_board.set_piece_at(square, chess.Piece(temp_piece.piece_type, not temp_piece.color))
            
        # Calculate probabilities with the simulated change
        new_white_prob, new_black_prob = calculate_win_probability(temp_board)
        
        # Return the absolute differences in probabilities
        return abs(new_white_prob - original_white_prob), abs(new_black_prob - original_black_prob)

    def _perform_piece_switch(self, square, new_color, simulate=False):
        """Switches a piece's color. If `simulate=True`, uses a copy of the board."""
        if simulate:
            # For simulation, use a temporary board copy
            temp_board = self.board.copy()
            piece = temp_board.piece_at(square)
            if not piece:
                return temp_board
                
            temp_board.remove_piece_at(square)
            temp_board.set_piece_at(square, chess.Piece(piece.piece_type, new_color))
            return temp_board
        else:
            # Actual switch on the real board
            piece = self.board.piece_at(square)
            if not piece:
                return
                
            self.board.remove_piece_at(square)
            self.board.set_piece_at(square, chess.Piece(piece.piece_type, new_color))
            
            # Get move count from game if available
            move_count = -1
            if hasattr(self, 'game'):
                move_count = self.game.move_count
            elif hasattr(self, 'move_count'):
                move_count = self.move_count
                
            self.switch_move_numbers.append(move_count)
            self.switched_pieces.add(square)
            self.last_switched_color = piece.color

    def _highlight_piece_for_switch(self, square):
        """Highlights a piece for switching and sets UI state."""
        # We're now tracking multiple squares, so adding to the list
        if square not in self.last_switched_squares:
            self.last_switched_squares.append(square)
            
        self.switch_highlight_start_time = time.time()

    def sync_state_to_game(self, game):
        """Sync switch manager state to the game object."""
        game.last_switched_squares = self.last_switched_squares
        game.switch_sequence_active = self.sequence_active
        game.is_switch_active = self.is_active
        game.switch_highlight_start_time = self.switch_highlight_start_time
        
        # Sync the state as well
        if hasattr(game, 'switch_manager'):
            game.switch_manager.state = self.state
        
        # Sync promoted pieces (ensure we have the latest)
        if hasattr(game, 'promoted_pieces'):
            self.promoted_pieces = game.promoted_pieces
        
        # If there's animation ongoing, make sure the game knows about it
        if self.animation_handler and self.animation_handler.active:
            game.caesar_move_active = True

# Add these functions outside the class to maintain the monkey-patching interface
def patch_switch_manager():
    """
    Keep this function for backward compatibility.
    It no longer needs to do anything as patching is now built-in.
    """
    logger.info("Switch manager patching is now built into SwitchManager initialization")
    return None

def restore_switch_manager():
    """
    Restore the original _evaluate_probability_change_safe method.
    This is now a wrapper around the instance method.
    """
    from switch_manager import SwitchManager
    
    # Find existing instances to restore
    instances = [obj for obj in gc.get_objects() if isinstance(obj, SwitchManager)]
    for instance in instances:
        instance.restore_original_evaluation()
    
    logger.info("Restored original win probability evaluation for all switch manager instances")
