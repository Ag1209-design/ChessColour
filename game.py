import pygame
import chess
import random
import time
import configuration
import os
from chess_view import ChessView
from evaluation import calculate_win_probability
from animation_handler import AnimationHandler
from switch_manager import SwitchManager
from event_handler import EventHandler
import sys
from switch_manager import SwitchState

# Get the logger
logger = configuration.logger
SEPARATOR = "---------------------------------------"

class ChessGame:
    def __init__(self, use_tokens=True, switch_mode=2):
        self.switch_mode = switch_mode
        logger.info(f"ChessGame initialized with switch_mode={self.switch_mode}")
        
        # Set up screen dimensions
        from configuration import SCREEN_WIDTH, SCREEN_HEIGHT, SQUARE_SIZE
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.square_size = SQUARE_SIZE
        
        # Initialize tokens if enabled
        self.use_tokens = use_tokens
        if self.use_tokens:
            self._initialize_tokens()
        else:
            self.white_tokens = []
            self.black_tokens = []
            
        # Always initialize token-related variables regardless of whether tokens are enabled
        self.selected_token = None
        self.token_highlight_color = None
        self.highlighted_tokens = []
        self.used_white_tokens = set()
        self.used_black_tokens = set()
            
        logger.info("Initializing ChessGame...")
        pygame.init()
        logger.info("Pygame modules initialized.")
        
        # Path to assets folder
        from configuration import ASSETS_FOLDER
        self.assets_folder = ASSETS_FOLDER
        
        # Initialize game window
        self.screen = pygame.display.set_mode((self.screen_width + 200, self.screen_height))
        pygame.display.set_caption("Caesar's Chess")
        logger.info("Game display window initialized.")
        
        # Initialize the chess board
        self.board = chess.Board()
        logger.info("Chess board initialized.")
        
        # Lists to track captured pieces
        self.white_captured_pieces = []
        self.black_captured_pieces = []
        
        # Initialize font
        self.font = pygame.font.Font(None, 72)
        self.font.set_bold(True)
        self.font_color = (0, 0, 0)
        
        # Game state variables
        self.move_count = 0
        self.selected_token = None
        self.token_highlight_color = None
        self.highlighted_tokens = []
        self.used_white_tokens = set()
        self.used_black_tokens = set()
        self.promoted_pawns = set()
        self.promoted_pieces = set()
        self.switch_sequence_active = False
        self.is_switch_active = False
        self.last_switched_squares = []
        self.pending_switch = False
        
        # Initialize the right column
        self.right_column_rect = pygame.Rect(self.screen_width, 0, 200, self.screen_height)
        
        # Initialize components
        self.animation = AnimationHandler(self)
        self.switch_manager = SwitchManager(self.board, self.animation, self)
        self.event_handler = EventHandler(self)
        self.view = ChessView(self.screen, self.screen_width, self.screen_height, self.assets_folder)
        
        # Caesar move animation control
        self.caesar_move_active = False
        
        # Timer-based switch initialization
        self.timer_start_time = pygame.time.get_ticks()
        self.COLOR_SWITCH_TIMER_EVENT = pygame.USEREVENT + 2
        if configuration.SWITCH_TRIGGER_MODE == "timer":
            pygame.time.set_timer(self.COLOR_SWITCH_TIMER_EVENT, configuration.SWITCH_TIMER_DURATION)
            logger.info(f"Timer mode activated: {configuration.SWITCH_TIMER_DURATION} ms interval")

        self.selected_piece = None
        self.valid_moves = []
        
    def _initialize_tokens(self):
        """Initialize token positions for the game."""
        token_spacing = 40
        self.white_tokens = []
        self.black_tokens = []

        # Position black tokens
        start_x_black = self.screen_width + 40
        start_y_black = 40
        for i in range(3):
            self.black_tokens.append((start_x_black, start_y_black + i * token_spacing))

        # Position white tokens
        start_x_white = self.screen_width + 40
        start_y_white = self.screen_height - 170
        for i in range(3):
            self.white_tokens.append((start_x_white, start_y_white + i * token_spacing))
        
        logger.debug("Tokens initialized")
    
    def get_game_state(self):
        """Check the game state for win conditions, draws, etc."""
        # Flags to track if kings are present on the board
        white_king_present = False
        black_king_present = False
        game_over = False

        # Check for kings
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                if piece.piece_type == chess.KING and piece.color == chess.WHITE:
                    white_king_present = True
                elif piece.piece_type == chess.KING and piece.color == chess.BLACK:
                    black_king_present = True

        # If a king is missing, the game is over
        if not white_king_present:
            logger.info("White king missing. Black wins by capture.")
            return "Checkmate! Black wins", True
        if not black_king_present:
            logger.info("Black king missing. White wins by capture.")
            return "Checkmate! White wins", True

        # Check for standard chess endgame conditions
        if self.board.is_checkmate():
            if self.board.turn == chess.WHITE:
                logger.info("Checkmate. Black wins (white's turn).")
                return "Checkmate! Black wins", True
            else:
                logger.info("Checkmate. White wins (black's turn).")
                return "Checkmate! White wins", True
        elif self.board.is_stalemate():
            logger.info("Stalemate. Draw.")
            return "Stalemate! Draw", True
        elif self.board.is_insufficient_material():
            logger.info("Insufficient Material. Draw.")
            return "Insufficient Material! Draw", True
        elif self.board.is_seventyfive_moves():
            logger.info("75-moves rule. Draw.")
            return "75-moves rule! Draw", True
        elif self.board.is_fivefold_repetition():
            logger.info("Five-fold repetition. Draw.")
            return "Five-fold repetition! Draw", True
        elif self.board.is_check():
            player = "White" if self.board.turn == chess.WHITE else "Black"
            logger.info(f"{player} king is in check.")
            return f"{player} King in Check!", False
        else:
            # Game is still ongoing
            return None, False
    
    def handle_switch_sequence(self):
        """Handle the state transitions in the switch sequence."""
        now = time.time()
        
        if self.switch_sequence_active:
            # Log the current state for debugging
            logger.debug(f"Switch sequence active: State={self.switch_manager.state}, Animation active={self.animation.active}")
            
            # When a switch sequence first becomes active, pause the timer event
            if self.switch_manager.state == SwitchState.ANIMATION and configuration.SWITCH_TRIGGER_MODE == "timer":
                # Pause the timer event during the switch sequence
                pygame.time.set_timer(self.COLOR_SWITCH_TIMER_EVENT, 0)  # Setting to 0 disables the timer
                logger.debug("Timer paused during switch sequence")
                
            if self.animation.active:
                # Animation is still playing, just wait
                return
                        
            elif self.switch_manager.state == SwitchState.ANIMATION:
                # Animation just finished, transition to highlighting state
                logger.info("Animation complete, moving to highlighting state")
                self.switch_manager.state = SwitchState.HIGHLIGHTING
                # Set a time for highlighting to be visible (5 seconds)
                self.highlight_end_time = now + 5.0
                
            elif self.switch_manager.state == SwitchState.HIGHLIGHTING:
                # Check if highlighting period is over
                if hasattr(self, 'highlight_end_time') and now > self.highlight_end_time:
                    logger.info("Highlighting period complete, executing switch")
                    self.switch_manager.state = SwitchState.SWITCHING
                    # Execute the switch exactly once
                    self.switch_piece_color()
                    # Log that the switch has been completed
                    logger.info("Switch completed at " + str(now))
                    
                    # IMPORTANT FIX: Completely reset all state flags
                    self._reset_switch_state()
                    
                    # Reset the timer for the next cycle if needed
                    if configuration.SWITCH_TRIGGER_MODE == "timer":
                        self.timer_start_time = pygame.time.get_ticks()
                        pygame.time.set_timer(self.COLOR_SWITCH_TIMER_EVENT, configuration.SWITCH_TIMER_DURATION)
                        logger.info("Timer reset for next switch cycle")
                    logger.info("Switch sequence completed and state reset with cleared highlighting")

    # Add this new helper method to ensure complete state reset
    def _reset_switch_state(self):
        """Reset all switch-related state completely"""
        # Reset all state flags in game
        self.switch_manager.state = SwitchState.IDLE
        self.switch_sequence_active = False
        self.is_switch_active = False
        self.pending_switch = False
        
        # Clear highlighted squares
        self.last_switched_squares = []
        
        # Ensure this gets synchronized to the switch manager
        self.switch_manager.sequence_active = False
        self.switch_manager.is_active = False
        self.switch_manager.last_switched_squares = []
        
        # Reset highlight timing
        self.switch_highlight_start_time = None
        self.switch_manager.switch_highlight_start_time = None
        
        logger.info("All switch state completely reset")

    # Replace the check_animation_completion method with this simplified version
    def check_animation_completion(self):
        """Check if animation is complete and update state accordingly."""
        # Now we just check if the animation is complete
        # The actual state transitions are handled in handle_switch_sequence
        pass  # No need to do anything here, state is managed in handle_switch_sequence

    def update(self):
        # Process events and get game state
        game_state, game_over = self.get_game_state()
        
        # Handle switch sequence state transitions BEFORE rendering
        self.handle_switch_sequence()
        
        # Sync game state with switch manager
        self.switch_manager.move_count = self.move_count
        
        # Update animations AFTER handling switch sequence
        self.animation.update_animation()
        
        # Update flags from switch manager
        self.last_switched_squares = self.switch_manager.last_switched_squares
        self.switch_sequence_active = self.switch_manager.sequence_active
        self.is_switch_active = self.switch_manager.is_active
        
        # IMPORTANT FIX: Only check for triggers if no switch is active or pending
        # This prevents additional triggers during or immediately after a switch
        if not self.switch_sequence_active and not self.is_switch_active and not hasattr(self, 'pending_switch'):
            # Check for move-based or random token-based switch triggers
            if (configuration.SWITCH_TRIGGER_MODE == "move" and
                self.switch_manager.check_move_trigger(self.move_count)):
                self.switch_manager.find_switch_pieces(self.switch_mode)
            elif (configuration.SWITCH_TRIGGER_MODE == "random_token" and
                self.switch_manager.check_random_token_trigger(self.move_count)):
                self.switch_manager.find_switch_pieces(self.switch_mode)

        # Handle any pending switches set by make_move
        if hasattr(self, 'pending_switch') and self.pending_switch and not self.switch_sequence_active:
            self.find_switch_piece()
            self.pending_switch = False

        # Render the screen
        self.screen.fill((0, 0, 0))  # Clear screen
        pygame.draw.rect(self.screen, (63, 82, 82), self.right_column_rect)
        pygame.draw.rect(self.screen, (60, 60, 60), self.right_column_rect, width=1)
        
        # Ensure the view has a reference to the game
        self.view.game = self
        
        if self.animation.active:
            self.animation.draw_caesar_move_animation(self.screen)
        else:
            # Draw game elements
            self.view.draw_board(self.screen)
        
            if hasattr(self.view, "draw_pieces"):
                self.view.draw_pieces(
                    self.screen, 
                    self.board, 
                    self.last_switched_squares, 
                    self.switch_manager.switch_highlight_start_time
                )
                
                # Draw valid move indicators when a piece is selected
                if self.selected_piece is not None:
                    # Double-check that we have valid moves for this piece
                    if not self.valid_moves:
                        # Recalculate valid moves if the list is empty
                        self.valid_moves = [move for move in self.board.legal_moves 
                                        if move.from_square == self.selected_piece]
                        if not self.valid_moves:
                            logger.warning(f"No valid moves for selected piece at {self.selected_piece}")
                            # If still no valid moves, deselect the piece
                            self.selected_piece = None
                    else:
                        # Draw the valid moves
                        self.view.draw_valid_moves(self.screen, self.valid_moves)
            else:
                logger.error("Error: draw_pieces() not found in ChessView!")
                
            # Draw countdown timer for timer-based switching
            if configuration.SWITCH_TRIGGER_MODE == "timer":
                self.view.draw_timer(self.screen, self.timer_start_time, self.switch_sequence_active)

            # Draw captured pieces and tokens
            self.view.draw_captured_pieces(self.screen, self.white_captured_pieces, self.black_captured_pieces)

            # After drawing tokens
            self.view.draw_tokens(
                self.screen, 
                self.white_tokens, 
                self.black_tokens, 
                self.highlighted_tokens, 
                self.token_highlight_color,
                self.used_white_tokens, 
                self.used_black_tokens, 
                self.selected_token
            )

            # Draw switch button if in player-triggered mode
            if hasattr(self.view, "draw_switch_button"):
                self.view.draw_switch_button(self.screen)
            
            # Load Cormorant-Medium.ttf
            try:
                move_font_path = os.path.join(self.assets_folder, "Cormorant", "static", "Cormorant-Medium.ttf")
                if not os.path.exists(move_font_path):
                    move_font_path = os.path.join(self.assets_folder, "Cormorant-Medium.ttf")  # fallback
                move_font = pygame.font.Font(move_font_path, 28)
            except Exception as e:
                logger.warning(f"Failed to load Cormorant-Medium.ttf: {e}")
                move_font = pygame.font.Font(None, 24)  # fallback

            move_text = move_font.render(f"MOVE: {self.move_count}", True, (255, 255, 255))

            # Centrally aligned rectangle in right panel
            rect_width = 160
            rect_height = 40
            rect_x = self.screen_width + (200 - rect_width) // 2
            rect_y = 645

            pygame.draw.rect(self.screen, (49, 65, 64), (rect_x, rect_y, rect_width, rect_height), border_radius=6)

            # Center the text in the rectangle
            text_rect = move_text.get_rect(center=(rect_x + rect_width // 2, rect_y + rect_height // 2))
            self.screen.blit(move_text, text_rect)


            # Display random token move numbers if that mode is active
            if configuration.SWITCH_TRIGGER_MODE == "random_token" and hasattr(configuration, 'RANDOM_TOKEN_MOVES'):
                token_font = pygame.font.Font(None, 28)  # Smaller font to fit all numbers
                token_text = token_font.render(f"Random: {', '.join(map(str, configuration.RANDOM_TOKEN_MOVES))}", True, (255, 255, 255)) 
                #self.screen.blit(token_text, (self.screen_width + 20, 600))
            
            # Display check message if king is in check but game is not over
            if game_state and not game_over and "Check" in game_state:
                self.view.draw_check_message(self.screen, game_state)

        pygame.display.flip()
        return game_state, game_over

    def make_move(self, move):
        """Execute a chess move on the board."""
        logger.info(f"Attempting to make move: {move.uci()}")
        
        if move in self.board.legal_moves:
            logger.debug(f"Move is legal.")
            
            # Check for capture
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                logger.info(f"Piece captured: {captured_piece}")
                if captured_piece.color == chess.WHITE:
                    self.white_captured_pieces.append(captured_piece)
                else:
                    self.black_captured_pieces.append(captured_piece)
            
            # Check for promotion
            is_promotion = False
            piece = self.board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                if ((piece.color == chess.WHITE and chess.square_rank(move.to_square) == 7) or 
                    (piece.color == chess.BLACK and chess.square_rank(move.to_square) == 0)):
                    is_promotion = True
                    logger.info("Pawn promotion detected.")
            
            # Handle promotion
            if is_promotion:
                promotion_choice = self.get_promotion_choice(move.to_square)
                if promotion_choice:
                    promotion_move = chess.Move(move.from_square, move.to_square, promotion=promotion_choice)
                    self.board.push(promotion_move)
                    logger.info(f"Promotion move executed: {promotion_move.uci()}")
                    self.promoted_pawns.add(move.to_square)
                    self.promoted_pieces.add(move.to_square)
            else:
                # Normal move
                self.board.push(move)
                logger.info(f"Normal move executed: {move.uci()}")

            self.move_count += 1
            self.switch_manager.move_count = self.move_count
            
            # FIX: Make the move trigger logic safer by checking if a switch is already active
            if (configuration.SWITCH_TRIGGER_MODE == "move" and 
                self.move_count >= 10 and 
                (self.move_count - 10) % 5 == 0 and 
                not self.switch_sequence_active and
                not self.is_switch_active):
                
                # Only set pending_switch if no switch is currently active
                logger.info(f"Move-based switching triggered at move {self.move_count}")
                self.pending_switch = True
                # Make sure we actually have this attribute
                if not hasattr(self, 'pending_switch'):
                    setattr(self, 'pending_switch', True)
            
            return True
        else:
            logger.warning(f"Illegal move attempted: {move.uci()}")
            return False
    
    def get_promotion_choice(self, square):
        """Display UI for promotion choices and return the selected piece type."""
        logger.info(f"Getting promotion choice for square: {square}")
        choices = ["queen", "rook", "bishop", "knight"]
        piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        choice_images = []
        
        # Get piece images
        for choice in choices:
            image_key = f"{choice}_{'w' if self.board.turn == chess.WHITE else 'b'}"
            if image_key in self.view.piece_images:
                image = pygame.transform.scale(self.view.piece_images[image_key], (50, 50))
                choice_images.append(image)
            else:
                logger.warning(f"Image {image_key} not loaded. Using placeholder.")
                choice_images.append(pygame.Surface((50, 50)))
        
        selected_piece = None
        
        # UI loop for promotion selection
        while selected_piece is None:
            self.screen.fill((30, 30, 30))
            self.view.draw_board(self.screen)
            self.view.draw_pieces(self.screen, self.board, self.last_switched_squares,
                                self.switch_manager.switch_highlight_start_time)
            
            # Display promotion choices
            for i, image in enumerate(choice_images):
                rect = image.get_rect(center=(self.screen_width / 4 + i * 100, self.screen_height / 2))
                self.screen.blit(image, rect)
                
                # Highlight on hover
                mouse_pos = pygame.mouse.get_pos()
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 3)
            
            pygame.display.flip()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    logger.info("Promotion selection interrupted, Pygame quit.")
                    return None
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for i, image in enumerate(choice_images):
                        rect = image.get_rect(center=(self.screen_width / 4 + i * 100, self.screen_height / 2))
                        if rect.collidepoint(mouse_pos):
                            selected_piece = i
                            logger.info(f"Selected piece index: {selected_piece} ({choices[selected_piece]})")
                            break
        
        return piece_types[selected_piece]
    
    def find_switch_piece(self):
        """Wrapper for switch_manager's find_switch_pieces."""
        return self.switch_manager.find_switch_pieces(self.switch_mode)
    
    def switch_piece_color(self):
        """Wrapper for switch_manager's switch_piece_color."""
        return self.switch_manager.switch_piece_color()
    
    def setup_castling_test(self, color):
        """Set up a test scenario for castling."""
        logger.info(f"Setting up castling test for {color}")
        
        # Clear the board
        self.board.clear()
        
        if color == chess.WHITE:
            # Set up white pieces
            self.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            self.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
            self.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
            self.board.turn = chess.WHITE
            self.board.castling_rights = chess.BB_H1 | chess.BB_A1
        else:
            # Set up black pieces
            self.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            self.board.set_piece_at(chess.H8, chess.Piece(chess.ROOK, chess.WHITE))
            self.board.set_piece_at(chess.A8, chess.Piece(chess.ROOK, chess.WHITE))
            self.board.turn = chess.BLACK
            self.board.castling_rights = chess.BB_H8 | chess.BB_A8
        
        logger.debug(f"Castling test setup complete. Legal moves: {[move.uci() for move in self.board.legal_moves]}")
    
    def delay_for_highlight(self):
        """Introduce a delay for highlighting after an update."""
        self.update()
    
    def quit(self):
        """Properly quit the game."""
        pygame.quit()
        sys.exit()