from uci_engine import UCIEngine
from ai import HumanPlayer, AIPlayer
from game import ChessGame
from configuration import DEFAULT_SWITCH_MODE
import pygame
import chess

def initialize_game(use_tokens=True, switch_mode=DEFAULT_SWITCH_MODE, mode="AI vs AI", ai_type="UCI"):
    """Initializes the game with flexible player selection."""

    # Create game instance with correct switch mode
    game = ChessGame(use_tokens=use_tokens, switch_mode=switch_mode)
    game.switch_manager.game = game
    clock = pygame.time.Clock()

    # Initialize players based on selected mode
    if mode == "User vs AI":
        player_white = HumanPlayer(chess.WHITE)
        player_black = AIPlayer()  # Use UCI-based AI
    elif mode == "AI vs AI":
        player_white = AIPlayer()
        player_black = AIPlayer()
    elif mode == "User vs User":
        player_white = HumanPlayer(chess.WHITE)
        player_black = HumanPlayer(chess.BLACK)
    else:
        print("Invalid mode, defaulting to AI vs AI.")
        player_white = AIPlayer()
        player_black = AIPlayer()
    
    # Add player references to the game object
    game.player_white = player_white
    game.player_black = player_black

    return game, player_white, player_black, clock