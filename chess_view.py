import pygame
import chess
import os
import time
import math
import logging
import configuration

# Get the logger
logger = configuration.logger

SEPARATOR = "---------------------------------------"

class ChessView:
    def __init__(self, screen, screen_width, screen_height, assets_folder):
        logger.info(SEPARATOR)
        logger.info("Initializing ChessView...")

        """
        Initializes the ChessView object.

        Args:
            screen (pygame.Surface): The Pygame surface to draw on.
            screen_width (int): The width of the screen.
            screen_height (int): The height of the screen.
            assets_folder (str): The path to the folder containing the piece images.
        """
        self.screen = screen  # Now takes the screen as input
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.assets_folder = assets_folder
        self.square_size = self.screen_width // 8
        logger.debug(f"Screen dimensions: {screen_width}x{screen_height}, Square size: {self.square_size}")

        self.piece_images = self.load_images()  # Load images
        logger.info("Piece images loaded.")

        self.font = pygame.font.Font(os.path.join(self.assets_folder, "CinzelDecorative-Bold.ttf"), 60)
        self.font.set_bold(True)
        self.font_color = (0, 0, 0)
        logger.debug("Font initialized.")

        # Define the rectangle for the right column
        #pygame.draw.rect(screen, (93, 29, 63), (self.screen_width, 0, 200, self.screen_height), width = 2)
        logger.debug("Right column rectangle drawn.")

        self.switch_start_time = None  # Initialize switch_start_time
        self.is_switch_active = False  # Initialize is_switch_active
        self.switch_highlight_start_time = None
        logger.debug("Switch-related variables initialized.")

        self.caesar_move_active = False
        self.confetti_frame_index = 0
        self.caesar_start_time = None
        self.caesar_duration = 2  # Duration of the "Caesar's Move" animation in seconds
        logger.debug(f"Caesar's move animation duration set to: {self.caesar_duration} seconds")
        
    def load_images(self):
        logger.info(SEPARATOR)
        logger.info("Loading chess piece images...")
        """Loads and scales the chess piece images."""
        images = {}
        for piece in ["king", "queen", "rook", "bishop", "knight", "pawn"]:
            for color in ["w", "b"]:
                try:
                    image_name = f"{piece}_{color}.png"
                    image_path = os.path.abspath(os.path.join(self.assets_folder, image_name))
                    logger.debug(f"Trying to load image from: {image_path}")
                    loaded_image = pygame.image.load(image_path)
                    # Shrink to 80% of the square size
                    piece_size = int(self.square_size * 0.75)
                    scaled_image = pygame.transform.scale(loaded_image, (piece_size, piece_size))

                    images[f"{piece}_{color}"] = scaled_image
                    logger.info(f"Successfully loaded image: {image_name}")
                except FileNotFoundError as e:
                    logger.error(f"Could not load image at {image_path}. Error: {e}")
                    print(f"Could not load image at {image_path}. Error: {e}")

        logger.debug("Images dictionary:")
        for key, value in images.items():
            logger.debug(f"  {key}: {value}")
        logger.info("Images Loading Finished")
        logger.info(SEPARATOR)
        return images

    def draw_board(self, screen):
        """Draws the chessboard squares with algebraic notation (a-h, 1-8)."""
        logger.info(SEPARATOR)
        logger.info("Drawing the chessboard squares...")

        colors = [(238, 238, 210), (63, 82, 82)]  # Light and dark squares  # Light and dark squares
        font_size = int(self.square_size * 0.3)  # Adjust font size based on square size
        notation_font = pygame.font.Font(None, font_size)  # Use default font

        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                x = col * self.square_size
                y = row * self.square_size
                pygame.draw.rect(screen, color, (x, y, self.square_size, self.square_size))

                # Draw column labels (a-h) at the bottom of the board
                # Alternate label colors
                dark_color = (63, 82, 82)
                light_color = (246, 230, 202)

                # Column letters: bottom-right of the square
                if row == 7:
                    file_color = light_color if col % 2 == 0 else dark_color
                    file_label = notation_font.render(chr(ord('a') + col), True, file_color)
                    file_label_rect = file_label.get_rect(bottomright=(x + self.square_size - 5, y + self.square_size - 5))
                    screen.blit(file_label, file_label_rect)

                # Row numbers: top-left of the square
                if col == 0:
                    rank_color = dark_color if row % 2 == 0 else light_color
                    rank_label = notation_font.render(str(8 - row), True, rank_color)
                    screen.blit(rank_label, (x + 5, y + 5))

        logger.info("Finished Drawing ChessBoard")
        logger.info(SEPARATOR)
   
    def draw_pieces(self, screen, board, last_switched_squares, switch_highlight_start_time):
        logger.info(SEPARATOR)
        logger.info("Drawing the chess pieces on the board...")
        """Draws the chess pieces on the board."""

        if last_switched_squares is None:
            last_switched_squares = []  

        piece_names = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king",
        }
        logger.debug(f"Piece names: {piece_names}")

        # Ensure last_switched_squares is always a list
        if not isinstance(last_switched_squares, list):
            last_switched_squares = [last_switched_squares]  # Convert to list if it's an integer

        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7-row)  # Correct coordinate conversion
                piece = board.piece_at(square)
                if piece:
                    piece_name = piece_names[piece.piece_type]
                    piece_color = "w" if piece.color else "b"
                    image_key = f"{piece_name}_{piece_color}"
                    
                    image = self.piece_images[image_key]
                    image_rect = image.get_rect()
                    x = col * self.square_size + (self.square_size - image_rect.width) // 2
                    y = row * self.square_size + (self.square_size - image_rect.height) // 2
                
                    
                    if image_key in self.piece_images:
                        screen.blit(image, (x, y))
                        
                        # Apply highlighting if this square was switched recently
                        if square in last_switched_squares and switch_highlight_start_time is not None:
                            elapsed_time = time.time() - switch_highlight_start_time
                            glow_intensity = abs(math.sin(elapsed_time * 3)) * 127 + 128
                            glow_color = (255, 255, 0, int(glow_intensity))  # Added int cast for intensity
                            
                            glow_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                            pygame.draw.rect(glow_surface, glow_color, (0, 0, self.square_size, self.square_size))
                            
                            screen.blit(glow_surface, (col * self.square_size, row * self.square_size))
                            
                        # Highlight the selected piece
                        if hasattr(self, 'game') and hasattr(self.game, 'selected_piece') and square == self.game.selected_piece:
                            # Draw selection highlight (blue border around the square)
                            square_x = col * self.square_size
                            square_y = row * self.square_size
                            highlight_rect = pygame.Rect(square_x, square_y, self.square_size, self.square_size)
                            pygame.draw.rect(screen, (0, 0, 255), highlight_rect, 3)
                    elif not hasattr(self, "logged_missing_images"):
                        logger.warning(f"Image key {image_key} not found in piece_images.")
                        self.logged_missing_images = set()
                        self.logged_missing_images.add(image_key)                

        logger.info("Finished drawing the chess pieces on the board.")
        logger.info(SEPARATOR)

    def draw_captured_pieces(self, screen, white_captured_pieces, black_captured_pieces):
        logger.info(SEPARATOR)
        logger.info("Drawing the captured pieces on the side panel...")
        """Draws the captured pieces on the side panel."""
        captured_x_w = self.screen_width + 60
        captured_y_w = 20
        captured_x_b = self.screen_width + 120
        captured_y_b = 20
        size = 50
        piece_names = {
            chess.PAWN: "pawn",
            chess.KNIGHT: "knight",
            chess.BISHOP: "bishop",
            chess.ROOK: "rook",
            chess.QUEEN: "queen",
            chess.KING: "king",
        }
        logger.debug(f"Captured Piece names: {piece_names}")

        for piece in white_captured_pieces:
            piece_name = piece_names[piece.piece_type]
            piece_color = "w" if piece.color else "b"
            image_key = f"{piece_name}_{piece_color}"
            logger.debug(f"Drawing captured white piece: {piece_name} at {captured_x_w}, {captured_y_w}")

            if image_key in self.piece_images:
                image = pygame.transform.scale(self.piece_images[image_key], (size, size))
                screen.blit(image, (captured_x_w, captured_y_w))
                captured_y_w += size + 5
            else:
                logger.warning(f"Image key {image_key} not found in piece_images.")

        for piece in black_captured_pieces:
            piece_name = piece_names[piece.piece_type]
            piece_color = "w" if piece.color else "b"
            image_key = f"{piece_name}_{piece_color}"
            logger.debug(f"Drawing captured black piece: {piece_name} at {captured_x_b}, {captured_y_b}")

            if image_key in self.piece_images:
                image = pygame.transform.scale(self.piece_images[image_key], (size, size))
                screen.blit(image, (captured_x_b, captured_y_b))
                captured_y_b += size + 5
            else:
                logger.warning(f"Image key {image_key} not found in piece_images.")
        logger.info("Finished drawing the captured pieces on the side panel.")
        logger.info(SEPARATOR)

    def draw_tokens(self, screen, white_tokens, black_tokens, highlighted_tokens, token_highlight_color,
                used_white_tokens, used_black_tokens, selected_token):
        logger.info(SEPARATOR)
        logger.info("Drawing tokens on the side panel...")
        """Draws the tokens on the side panel."""

        # Draw white tokens
        for x, y in white_tokens:
            if (x, y) not in used_white_tokens:
                logger.debug(f"Drawing white token at {x}, {y}")
                pygame.draw.circle(screen, (255, 255, 255), (x, y), 15)  # White circle
                if (x, y) in highlighted_tokens and token_highlight_color:
                    logger.debug(f"Highlighting white token at {x}, {y} with color {token_highlight_color}")
                    pygame.draw.circle(screen, token_highlight_color, (x, y), 20, 3)
                if (x, y) == selected_token:  # Highlight selected token
                    pygame.draw.circle(screen, (0, 255, 0), (x, y), 22, 3)  # Green border
                    logger.debug(f"Drawing selected token highlight at {x}, {y}")
        # Draw black tokens with better visibility
        for x, y in black_tokens:
            if (x, y) not in used_black_tokens:
                # Use a dark gray instead of pure black for better visibility
                pygame.draw.circle(screen, (0, 0, 0), (x, y), 15)  # Dark gray circle
                # Add a white border for better visibility against the dark background
                pygame.draw.circle(screen, (255, 255, 255), (x, y), 15, 1)  # Light gray border
                
            else:
                # Draw "used" tokens with a gray color to indicate they're spent
                logger.debug(f"Drawing used white token at {x}, {y}")
                pygame.draw.circle(screen, (180, 180, 180), (x, y), 15)  # Gray circle
                pygame.draw.line(screen, (100, 100, 100), (x-10, y-10), (x+10, y+10), 3)  # X mark
                pygame.draw.line(screen, (100, 100, 100), (x+10, y-10), (x-10, y+10), 3)  # X mark
                
                # Add a pulsing effect if this token was just used (in highlighted_tokens list)
                if (x, y) in highlighted_tokens:
                    pulse_intensity = abs(math.sin(time.time() * 5)) * 127 + 128
                    pulse_color = (255, 0, 0, int(pulse_intensity))  # Pulsing red
                    pulse_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
                    pygame.draw.circle(pulse_surface, pulse_color, (20, 20), 18, 3)
                    screen.blit(pulse_surface, (x-20, y-20))

        
                
        logger.info("Finished drawing tokens on the side panel.")
        logger.info(SEPARATOR)
    def draw_game_state(self, screen, message):
        logger.info(SEPARATOR)
        logger.info("Drawing the game state message...")
        if message:
            logger.info(f"Drawing game state message: {message}")
            text = self.font.render(message, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen_width / 2 + 100, self.screen_height - 50))
            screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.delay(2000)  # Reduce the delay to 2 seconds
        logger.info("Finished drawing the game state message.")
        logger.info(SEPARATOR)

    def draw_check_message(self, screen, message):
        if message:
            logger.info(f"Drawing check message: {message}")
            
            # Set the font
            self.font = pygame.font.Font(os.path.join(self.assets_folder, "CinzelDecorative-Bold.ttf"), 36)
            self.font.set_bold(True)

            # Render the main text and measure it
            text_surface = self.font.render(message, True, (0, 0, 0))
            text_rect = text_surface.get_rect()

            # Padding and positioning
            padding = 5
            rect_width = text_rect.width + 2 * padding
            rect_height = text_rect.height + 2 * padding
            rect_x = (self.screen_width - rect_width) // 2
            rect_y = (self.screen_height - rect_height) // 2

            # Background rectangle
            background_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

            # Simulate drop shadow
            shadow_color = (28, 14, 21)  # #1C0E15
            shadow_offset_y = 5

            # Create a surface for shadow with alpha support
            shadow_surface = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)
            
            # Simulate a blur by drawing multiple offset shadows (basic Gaussian approximation)
            for i in range(1, 5):  # More layers = smoother shadow
                alpha = max(30 - i * 5, 10)  # Decrease alpha with each layer
                pygame.draw.rect(
                    shadow_surface,
                    (*shadow_color, alpha),
                    pygame.Rect(i, shadow_offset_y + i, rect_width, rect_height),
                    border_radius=10
                )

            # Blit shadow below the main rect
            screen.blit(shadow_surface, (rect_x, rect_y))

            # Draw the main rounded rectangle
            pygame.draw.rect(screen, (116, 36, 75), background_rect, border_radius=10)  # #74244B

            # Center text in the background rect
            text_rect.center = background_rect.center

            # Draw the text
            screen.blit(text_surface, text_rect)

        logger.info("Finished drawing the check message.")
        logger.info(SEPARATOR)



    def draw_timer(self, screen, timer_start_time, switch_sequence_active=False):
        """Displays the countdown timer on the game screen in the bottom-right corner.
        If switch_sequence_active is True, displays a message indicating a switch is in progress."""
        rect_width = 160
        rect_height = 40
        rect_x = self.screen_width + (200 - rect_width) // 2
        rect_y = 595  # Slightly above the move count rectangle (which is at 645)

        # Try loading Cormorant-Medium.ttf
        try:
            font_path = os.path.join(self.assets_folder, "Cormorant", "static", "Cormorant-Medium.ttf")
            if not os.path.exists(font_path):
                font_path = os.path.join(self.assets_folder, "Cormorant-Medium.ttf")  # fallback
            font = pygame.font.Font(font_path, 30)
        except Exception as e:
            logger.warning(f"Failed to load Cormorant-Medium.ttf: {e}")
            font = pygame.font.Font(None, 30)  # fallback

        if switch_sequence_active:
            timer_surface = font.render("SWITCH", True, (255, 255, 255))  # White text
        elif timer_start_time is not None:
            time_elapsed = pygame.time.get_ticks() - timer_start_time
            remaining_time = max(0, (configuration.SWITCH_TIMER_DURATION - time_elapsed) // 1000)  # ms to s
            timer_surface = font.render(f"SWITCH IN: {remaining_time}s", True, (255, 255, 255))  # White text
        else:
            return  # Nothing to draw if no timer active

        # Draw background rectangle behind the text
        pygame.draw.rect(screen, (116, 36, 75), (rect_x, rect_y, rect_width, rect_height), border_radius=6)

        # Center the text in the rectangle
        text_rect = timer_surface.get_rect(center=(rect_x + rect_width // 2, rect_y + rect_height // 2))
        screen.blit(timer_surface, text_rect)


    def draw_valid_moves(self, screen, valid_moves):
        """Draws indicators for valid moves on the board."""
        if not valid_moves:
            logger.warning("draw_valid_moves called with empty valid_moves list")
            return
            
        logger.debug(f"Drawing {len(valid_moves)} valid move indicators")
        
        # Draw a small circle on each valid destination square
        for move in valid_moves:
            to_square = move.to_square
            col = chess.square_file(to_square)
            row = 7 - chess.square_rank(to_square)  # Convert chess rank to screen coordinates
            
            # Calculate the center of the square
            center_x = col * self.square_size + self.square_size // 2
            center_y = row * self.square_size + self.square_size // 2
            
            try:
                # Draw different indicators based on whether the move is a capture
                if self.game.board.piece_at(to_square):  # Capture move
                    # Draw a red circle around the square
                    pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), 
                                    self.square_size // 4, 3)  # Red circle with 3px width
                else:
                    # Draw a green dot in the center of empty squares
                    pygame.draw.circle(screen, (0, 255, 0), (center_x, center_y), 
                                    self.square_size // 8)  # Solid green circle
            except Exception as e:
                logger.error(f"Error drawing move indicator: {e}")

    def draw_switch_button(self, screen):
        """Draws the color switch button if player-triggered switch mode is active."""
        # Only draw if player-triggered mode is active
        if configuration.SWITCH_TRIGGER_MODE != "player":
            return
            
        # Draw button in the right panel
        button_x = self.screen_width + 50
        button_y = 400
        button_width = 100
        button_height = 40
        
        # Store button position and dimensions for click detection
        self.switch_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        # Draw the button with a nice color
        pygame.draw.rect(screen, (70, 130, 180), self.switch_button_rect)
        
        # Add button text
        font = pygame.font.Font(None, 24)
        text = font.render("Switch Color", True, (255, 255, 255))
        text_rect = text.get_rect(center=(button_x + button_width // 2, button_y + button_height // 2))
        screen.blit(text, text_rect)
        
        logger.debug("Switch button drawn")