import pygame
import chess
import configuration
from switch_manager import SwitchState
from ai import HumanPlayer


# Get the logger from configuration
logger = configuration.logger

class EventHandler:
    """Handles all events in the chess game."""
    
    def __init__(self, game):
        self.game = game
    
    def handle_events(self):
        """Process all pygame events and return True if the game should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("Received QUIT event. Exiting game loop.")
                self.game.quit()
                return True  # Signal to quit
                    
            elif event.type == self.game.switch_manager.COLOR_SWITCH_TIMER_EVENT:
                if configuration.SWITCH_TRIGGER_MODE == "timer":
                    logger.debug("Timer event triggered")
                    # Only start switch sequence if one isn't already active
                    if not self.game.switch_sequence_active and not self.game.is_switch_active:
                        logger.info("Starting switch sequence from timer event")
                        self.game.switch_manager.find_switch_pieces(self.game.switch_mode)
                        # Reset timer for next cycle
                        self.game.timer_start_time = pygame.time.get_ticks()
                        pygame.time.set_timer(self.game.switch_manager.COLOR_SWITCH_TIMER_EVENT, 
                                        configuration.SWITCH_TIMER_DURATION)
                    
            # Only process mouse events if no switch or animation is active
            elif event.type == pygame.MOUSEBUTTONDOWN:
                
                    
                self.handle_mouse_click(event.pos)
                                
        return False  # Continue game   
    
    def handle_mouse_click(self, pos):
        """Handle mouse click events, including piece selection and move execution."""
        mouse_x, mouse_y = pos
        logger.debug(f"Mouse click detected at: x={mouse_x}, y={mouse_y}")
        
        # Check for switch button click if in player-triggered mode
        if (configuration.SWITCH_TRIGGER_MODE == "player" and 
            hasattr(self.game.view, "switch_button_rect") and 
            self.game.view.switch_button_rect.collidepoint(pos)):
            
            logger.info("Switch button clicked")
            # Only trigger switch if no switch sequence is already active
            if not self.game.switch_sequence_active and not self.game.is_switch_active:
                logger.info("Starting switch sequence from button click")
                self.game.switch_manager.find_switch_pieces(self.game.switch_mode)
            return
        
        # Handle token-related clicks
        if self.game.use_tokens:
            # Check for token clicks
            for token_x, token_y in self.game.white_tokens + self.game.black_tokens:
                distance = ((mouse_x - token_x) ** 2 + (mouse_y - token_y) ** 2) ** 0.5
                if distance <= 15:
                    # Handle token selection (cancel switch if in highlighting state)
                    if (self.game.switch_sequence_active and 
                        self.game.switch_manager.state == SwitchState.HIGHLIGHTING):
                        
                        # Find what color pieces are being switched
                        switch_color = None
                        if self.game.last_switched_squares:
                            for square in self.game.last_switched_squares:
                                piece = self.game.board.piece_at(square)
                                if piece:
                                    switch_color = piece.color
                                    logger.debug(f"Found piece color for switch: {switch_color}")
                                    break
                                
                        logger.debug(f"Switch color: {switch_color}, Token at ({token_x}, {token_y})")

                        # Token detection
                        is_white_token = (token_x, token_y) in self.game.white_tokens
                        is_black_token = (token_x, token_y) in self.game.black_tokens

                        # Check if token is unused
                        token_unused = (((token_x, token_y) not in self.game.used_white_tokens) if is_white_token else
                                    ((token_x, token_y) not in self.game.used_black_tokens))

                        logger.debug(f"Token color: {'white' if is_white_token else 'black'}, Unused: {token_unused}")

                        if token_unused:
                            # White token can cancel white piece switch
                            if is_white_token and switch_color is chess.WHITE:
                                logger.debug("Using white token to cancel white piece switch")
                                self.game.used_white_tokens.add((token_x, token_y))
                                self._cancel_switch()
                                self.game.token_highlight_color = (255, 0, 0)  # Red to indicate used
                                self.game.selected_token = None  # Reset token selection after use
                                logger.info("White token used to cancel switch of white piece")
                                pygame.display.flip()  # Update display
                                pygame.time.delay(500)  # Brief delay to show token use
                                return
                                
                            elif is_black_token and switch_color is chess.BLACK:
                                logger.debug("Using black token to cancel black piece switch")
                                self.game.used_black_tokens.add((token_x, token_y))
                                self._cancel_switch()
                                self.game.token_highlight_color = (255, 0, 0)  # Red to indicate used
                                self.game.selected_token = None  # Reset token selection after use
                                logger.info("Black token used to cancel switch of black piece")
                                pygame.display.flip()  # Update display
                                pygame.time.delay(500)  # Brief delay to show token use
                                return
                                                                                                
                    # Normal token selection (when not canceling a switch)
                    if self.game.selected_token == (token_x, token_y):
                        self.game.selected_token = None
                    else:
                        self.game.selected_token = (token_x, token_y)
                        # Add the token to highlighted tokens
                        self.game.highlighted_tokens = [(token_x, token_y)]
                        self.game.token_highlight_color = (0, 255, 0)  # Green highlight
                    logger.debug(f"Token selection changed: {self.game.selected_token}")
                    return  # Exit early since we handled a token click
        
        # Handle board clicks for piece selection and move execution
        # Check if click is within the chess board
        if mouse_x < self.game.screen_width and mouse_y < self.game.screen_height:
            # Find the square that was clicked
            col = mouse_x // self.game.square_size
            row = mouse_y // self.game.square_size
            clicked_square = chess.square(col, 7 - row)  # Convert to chess square
            
            logger.debug(f"Board click on square: {chess.square_name(clicked_square)}")
            
            # No switch should be active when making a move
            if not self.game.switch_sequence_active and not self.game.is_switch_active:
                # Player's turn check
                is_player_turn = (
                    (self.game.board.turn == chess.WHITE and isinstance(self.game.player_white, HumanPlayer)) or
                    (self.game.board.turn == chess.BLACK and isinstance(self.game.player_black, HumanPlayer))
                )
                
                if not is_player_turn:
                    logger.debug("Not player's turn. Ignoring click.")
                    return
                    
                # If a piece is already selected
                if self.game.selected_piece is not None:
                    # Check if the clicked square is a valid destination
                    valid_move = None
                    for move in self.game.valid_moves:
                        if move.to_square == clicked_square:
                            valid_move = move
                            break
                    
                    if valid_move:
                        # Execute the move
                        logger.info(f"Executing move: {valid_move.uci()}")
                        import time
                        self.game.make_move(valid_move)
                        # Reset selection
                        self.game.selected_piece = None
                        self.game.valid_moves = []
                        # Reset token selection when making a move
                        self.game.selected_token = None
                        self.game.highlighted_tokens = []
                        # Update the display to show the human move
                        self.game.update()
                        # Add a delay after human move is displayed, before AI responds
                        time.sleep(1)
                        return
                    
                    # Otherwise, check if they're clicking a different piece of their color
                    piece = self.game.board.piece_at(clicked_square)
                    if piece and piece.color == self.game.board.turn:
                        # Update the selection to the new piece
                        self.game.selected_piece = clicked_square
                        self.game.valid_moves = [move for move in self.game.board.legal_moves 
                                                if move.from_square == clicked_square]
                        logger.info(f"Selected new piece at {chess.square_name(clicked_square)}")
                        return
                    else:
                        # Clicking empty square or opponent's piece - deselect
                        self.game.selected_piece = None
                        self.game.valid_moves = []
                        logger.info("Piece deselected")
                        return
                
                # No piece selected yet - select a piece if it exists and is the player's color
                piece = self.game.board.piece_at(clicked_square)
                if piece and piece.color == self.game.board.turn:
                    self.game.selected_piece = clicked_square
                    # Find all legal moves for this piece
                    self.game.valid_moves = [move for move in self.game.board.legal_moves 
                                            if move.from_square == clicked_square]
                    logger.info(f"Selected piece at {chess.square_name(clicked_square)} with {len(self.game.valid_moves)} valid moves")
    
    def _cancel_switch(self):
        """Cancel an active piece color switch."""
        logger.info("Token used to cancel pending color switch")
        # Reset switch state
        self.game.switch_sequence_active = False
        self.game.is_switch_active = False
        self.game.switch_manager.sequence_active = False
        self.game.switch_manager.is_active = False
        self.game.switch_manager.state = SwitchState.IDLE
        self.game.last_switched_squares = []
        self.game.switch_manager.last_switched_squares = []
        # Reset animation if active
        if self.game.animation.active:
            self.game.animation.stop_animation()
        # Reset highlight timing
        self.game.switch_highlight_start_time = None
        self.game.switch_manager.switch_highlight_start_time = None
        # Update token state to show it's been used
        self.game.token_highlight_color = (255, 0, 0)  # Red to indicate used
        self.game.highlighted_tokens = []  # Clear the highlighted tokens list
        pygame.display.flip()  # Force a display update
        pygame.time.delay(500)  # Brief delay to show the token being used

def handle_token_interaction(game, event):
    """Legacy function for token selection interactions only if tokens are enabled."""
    # This is kept for backward compatibility
    if not game.use_tokens:
        return True

    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_x, mouse_y = event.pos
        logger.debug(f"Mouse click detected at: x={mouse_x}, y={mouse_y}")

        for token_x, token_y in game.white_tokens + game.black_tokens:
            distance = ((mouse_x - token_x) ** 2 + (mouse_y - token_y) ** 2) ** 0.5
            if distance <= 15:
                if game.selected_token is None:
                    game.selected_token = (token_x, token_y)
                    logger.debug(f"Token selected at: x={token_x}, y={token_y}")
                else:
                    game.selected_token = None
                    logger.debug("Token deselected.")
                return False
    return True

def handle_events(game):
    """Legacy event handling function for backward compatibility."""
    handler = EventHandler(game)
    return handler.handle_events()

def handle_switch_trigger(game):
    """Legacy function for timer-based switching trigger."""
    # Only check for timer-based switching if that mode is enabled and no switch sequence is active
    if configuration.SWITCH_TRIGGER_MODE == "timer" and not game.switch_manager.sequence_active:
        if game.switch_manager.check_timer_trigger():
            game.switch_manager.find_switch_pieces()

