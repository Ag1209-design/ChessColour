import pygame
import time
import os
import configuration

# Get the logger
logger = configuration.logger

class AnimationHandler:
    """Handles all animations in the chess game, particularly Caesar's Move animation."""
    
    def __init__(self, game):
        self.game = game
        self.active = False
        self.start_time = None
        self.frame_index = 0

        # Confetti Animation Setup
        self.confetti_frames = self.load_confetti_frames()
        self.confetti_frame_index = 0
        self.caesar_start_time = None
        self.caesar_duration = 2  # Duration of the animation in seconds

    def start_animation(self):
        """Activates Caesar's Move animation."""
        self.active = True
        self.start_time = time.time()
        self.frame_index = 0
        self.caesar_start_time = time.time()
        
        # Set the game's caesar_move_active flag if it exists
        if hasattr(self.game, 'caesar_move_active'):
            self.game.caesar_move_active = True
            
        logger.info("Started Caesar's Move animation")

    def update_animation(self):
        """Updates animation frames and stops when done."""
        if self.active:
            elapsed_time = time.time() - self.start_time
            self.confetti_frame_index = int(elapsed_time * 10) % len(self.confetti_frames) if self.confetti_frames else 0
            
            # Only stop animation when duration is complete
            if elapsed_time > self.caesar_duration:
                logger.debug(f"Animation completed after {elapsed_time:.2f} seconds")
                self.stop_animation()
    
    def stop_animation(self):
        """Stops animation and resets state."""
        self.active = False
        
        # Reset the game's caesar_move_active flag if it exists
        if hasattr(self.game, 'caesar_move_active'):
            self.game.caesar_move_active = False
            
        logger.info("Stopped Caesar's Move animation")

    def load_confetti_frames(self):
        """Loads confetti animation frames from sprite sheet."""
        try:
            if not hasattr(self.game, 'assets_folder'):
                logger.warning("Game object has no assets_folder attribute")
                return []
                
            confetti_path = os.path.join(self.game.assets_folder, "spark_02.png")
            logger.debug(f"Loading confetti sprite sheet from: {confetti_path}")
            
            confetti_sheet = pygame.image.load(confetti_path).convert_alpha()
            num_rows, num_cols = 2, 4
            frame_width = confetti_sheet.get_width() // num_cols
            frame_height = confetti_sheet.get_height() // num_rows

            frames = []
            for row in range(num_rows):
                for col in range(num_cols):
                    frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    frame.blit(confetti_sheet, (0, 0), (col * frame_width, row * frame_height, frame_width, frame_height))
                    frames.append(pygame.transform.scale(frame, (self.game.screen_width, self.game.screen_height)))
            
            logger.info(f"Successfully loaded {len(frames)} confetti animation frames")
            return frames
        except FileNotFoundError:
            logger.error(f"Confetti sprite sheet not found: {confetti_path if 'confetti_path' in locals() else 'unknown path'}")
            return []
        except Exception as e:
            logger.error(f"Error loading confetti frames: {str(e)}")
            return []

    def draw_caesar_move_animation(self, screen):
        """Draws Caesar's Move animation with confetti."""
        if not self.active:
            return
            
        if self.confetti_frames and len(self.confetti_frames) > self.confetti_frame_index:
            confetti_frame = self.confetti_frames[self.confetti_frame_index]
            screen.blit(confetti_frame, (0, 0))

        # Draw "Caesar's Move" text if font is available
        if hasattr(self.game, 'font'):
            text = self.game.font.render("Caesar's Move", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.game.screen_width // 2, self.game.screen_height // 2))
            screen.blit(text, text_rect)

    def reset_animation(self):
        """Resets Caesar's Move animation."""
        self.active = False
        self.frame_index = 0
        self.start_time = None
        self.confetti_frame_index = 0
        
        # Reset the game's caesar_move_active flag if it exists
        if hasattr(self.game, 'caesar_move_active'):
            self.game.caesar_move_active = False
            
        logger.debug("Animation state reset")