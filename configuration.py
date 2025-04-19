import logging
import os
from datetime import datetime

# Debugging Toggle
DEBUG_MODE = True  # Set to False to disable debugging logs

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Generate a timestamped log file name
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")  # Format: YYYY-MM-DD_HH-MM-SS
LOG_FILE = os.path.join(LOG_DIR, f"chess_game_{timestamp}.log")

# Create a logger instance
logger = logging.getLogger(__name__)  # Use __name__ so the logger shows where the message came from in the logs
logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)  # Toggle debug level

# Create a file handler
file_handler = logging.FileHandler(LOG_FILE)

#Set it to the formatter as requested
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
#stream_handler.setFormatter(formatter)
#logger.addHandler(stream_handler)

# Example usage from the logging config file itself.
logger.info("This is an info message")
logger.debug("This is a debug message")  # Will be saved in the timestamped log & printed
logger.warning("This is a warning")
logger.error("This is an error")
logger.critical("This is critical")

# Game UI Settings
SCREEN_WIDTH = 700
SCREEN_HEIGHT = 700
SQUARE_SIZE = SCREEN_WIDTH // 8

# Default Game Settings
DEFAULT_SWITCH_MODE = 2  # 1 for single switch, 2 for two-piece switch

# Event Configuration
import pygame
COLOR_SWITCH_EVENT = pygame.USEREVENT + 1

# File Paths
ASSETS_FOLDER = "C:\\Users\\avani\\Documents\\Work\\Work_projects\\Internships\\Proxgy\\Caesars_chess\\assets2"

# --- Piece-Square Tables ---
pawn_table = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5,  5,  5,  5,  5,  5,  5,  5,
    1,  1,  2,  3,  3,  2,  1,  1,
    0.5,0.5,  1, 2.5, 2.5,  1, 0.5,0.5,
    0,  0,  0, 2.0, 2.0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0
]

knight_table = [
    -5, -4, -3, -3, -3, -3, -4, -5,
    -4, -2,  0,  0,  0,  0, -2, -4,
    -3,  0,  1, 1.5, 1.5,  1,  0, -3,
    -3,  0.5, 1.5, 2, 2, 1.5, 0.5, -3,
    -3,  0, 1.5, 2, 2, 1.5,  0, -3,
    -3,  0.5, 1, 1.5, 1.5,  1, 0.5, -3,
    -4, -2,  0,  0.5, 0.5,  0, -2, -4,
    -5, -4, -3, -3, -3, -3, -4, -5
]

bishop_table = [
    -2, -1, -1, -1, -1, -1, -1, -2,
    -1,  0,  0,  0,  0,  0,  0, -1,
    -1,  0,  0.5, 1, 1, 0.5,  0, -1,
    -1,  0.5, 0.5, 1, 1, 0.5, 0.5, -1,
    -1,  0, 1, 1, 1, 1,  0, -1,
    -1,  1, 1, 1, 1, 1, 1, -1,
    -1,  0.5,  0,  0,  0,  0, 0.5, -1,
    -2, -1, -1, -1, -1, -1, -1, -2
]

rook_table = [
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
     2,  2,  2,  2,  2,  2,  2,  2,
     3,  3,  3,  3,  3,  3,  3,  3
]

queen_table = [
    -3, -2, -2, -1, -1, -2, -2, -3,
    -2,  0,  0,  0,  0,  0,  0, -2,
    -2,  0,  0.5, 0.5, 0.5, 0.5,  0, -2,
    -1,  0, 0.5, 0.5, 0.5, 0.5,  0, -1,
    -1,  0, 0.5, 0.5, 0.5, 0.5,  0, -1,
    -2,  0, 0, 0, 0, 0,  0, -2,
    -2,  0,  0,  0,  0,  0,  0, -2,
    -3, -2, -2, -1, -1, -2, -2, -3
]

king_table = [
    -3, -4, -4, -5, -5, -4, -4, -3,
    -3, -4, -4, -5, -5, -4, -4, -3,
    -3, -4, -4, -5, -5, -4, -4, -3,
    -3, -4, -4, -5, -5, -4, -4, -3,
    -2, -3, -3, -4, -4, -3, -3, -2,
    -1, -2, -2, -2, -2, -2, -2, -1,
    2,  2,  0,  0,  0,  0,  2,  2,
    2,  3,  1,  0,  0,  1,  3,  2
]

# King wants to be close in the end game:
king_endgame_table = [
        -2, -1, -1, -1, -1, -1, -1, -2,
        -1,  0,  0,  0,  0,  0,  0, -1,
        -1,  0,  0.5, 1, 1, 0.5,  0, -1,
        -1,  0.5, 0.5, 1, 1, 0.5, 0.5, -1,
        -1,  0, 1, 1, 1, 1,  0, -1,
        -1,  1, 1, 1, 1, 1, 1, -1,
        -1,  0.5,  0,  0,  0,  0, 0.5, -1,
        -2, -1, -1, -1, -1, -1, -1, -2
    ]

# UCI Engine Path (Modify this to point to your preferred engine)
UCI_ENGINE_PATH = "C:\\Users\\avani\\Documents\\Work\\Work_projects\\Internships\\Proxgy\\Caesars_chess\\stockfish-windows-x86-64-avx2 (1)\\stockfish\stockfish-windows-x86-64-avx2.exe"

# User-selected switch trigger mode: "move" or "timer"
SWITCH_TRIGGER_MODE = "move"  # Default is move-based switching
SWITCH_TIMER_DURATION = 15000  # 15 seconds (in milliseconds)
RANDOM_TOKEN_MOVES = []  # Will contain three random move numbers

# Game Settings Screen 
# Font Settings
TITLE_FONT_SIZE = 44
HEADING_FONT_SIZE = 30
NORMAL_FONT_SIZE = 24