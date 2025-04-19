# Main file for Caesar's Chess

import pygame
import configuration 
import chess
from evaluation import calculate_win_probability
from plotting import plot_win_probabilities
from game_setup import initialize_game
from event_handler import EventHandler
from ai import HumanPlayer
import random
import os
import sys
import time
import asyncio

# Import settings screen
from settings_screen import SettingsScreen

# Enable enhanced win probability
try:
    from win_probability import update_win_probability
    update_win_probability()
except ImportError:
    print("Enhanced win probability not available.")

# Get the logger from the configuration
logger = configuration.logger
SEPARATOR = "---------------------------------------"

# Initialize Pygame
pygame.init()
logger.info("Pygame initialized.")
    
def main():
    # Show settings screen
    settings_screen = SettingsScreen()
    game_settings = settings_screen.run()
    
    # Extract settings
    switch_trigger_mode = game_settings['switch_trigger_mode']
    switch_mode = game_settings['switch_mode']
    game_mode = game_settings['game_mode']
    use_tokens = game_settings['use_tokens']
    random_token_moves = game_settings.get('random_token_moves')
    
    # Log selected settings
    logger.info(f"User selected switch trigger mode: {switch_trigger_mode}")
    logger.info(f"User selected switch mode: {switch_mode}")
    logger.info(f"User selected game mode: {game_mode}")
    logger.info(f"User selected token mechanics: {'Enabled' if use_tokens else 'Disabled'}")
    
    # Update configuration based on user input
    configuration.SWITCH_TRIGGER_MODE = switch_trigger_mode
    
    if switch_trigger_mode == "random_token":
        configuration.RANDOM_TOKEN_MOVES = random_token_moves
        print(f"Random token triggers set for moves: {configuration.RANDOM_TOKEN_MOVES}")
    
    # Initialize game components
    game, player_white, player_black, clock = initialize_game(
        use_tokens=use_tokens, 
        switch_mode=switch_mode, 
        mode=game_mode, 
        ai_type="UCI"
    )

    # Apply token setting to the game object
    game.use_tokens = use_tokens

    # Reinitialize tokens if enabled
    if game.use_tokens:
        game._initialize_tokens()

    # Create event handler
    event_handler = EventHandler(game)

    # Game state tracking
    game_over = False
    white_probabilities = []
    black_probabilities = []
    move_numbers = []

    # Main game loop
    logger.info("Starting main game loop.")
    while not game_over:
        # Handle events
        if event_handler.handle_events():
            break  # Quit if handle_events returns True
            
        # If the game is still running, execute AI move
        if not game_over and not game.is_switch_active:
            # Only get AI move if it's an AI's turn
            if game.board.turn == chess.WHITE and not isinstance(player_white, HumanPlayer):
                move = player_white.choose_move(game.board)
                if move:
                    time.sleep(1)
                    game.make_move(move)
                    logger.info(f"AI Move applied: {move.uci()}")
                    print(f"Move applied: {move.uci()}")
            elif game.board.turn == chess.BLACK and not isinstance(player_black, HumanPlayer):
                move = player_black.choose_move(game.board)
                if move:
                    time.sleep(1)
                    game.make_move(move)
                    logger.info(f"AI Move applied: {move.uci()}")
                    print(f"Move applied: {move.uci()}")

            # For human players, moves are handled by click events
            # so we don't need to do anything here

            # Calculate and log win probabilities after a move is made
            white_prob, black_prob = calculate_win_probability(game.board)
            logger.info(f"White win prob: {white_prob*100:.2f}%, Black win prob: {black_prob*100:.2f}%")
            print(f"White win prob: {white_prob*100:.2f}%, Black win prob: {black_prob*100:.2f}%")

            # Store probability data for later analysis
            white_probabilities.append(white_prob)
            black_probabilities.append(black_prob)
            move_numbers.append(game.move_count)

        # Update game state
        game_state, game_over = game.update()

        # Control game speed
        clock.tick(60)

        # Display final game state message if the game has ended
        if game_state:
            logger.info(f"Game over: {game_state}")
            print(f"Game over: {game_state}")
        if game_over:
            game.screen.fill((245, 235, 220))
            game.view.draw_game_state(game.screen, game_state)
    
    
    # Print switch statistics after game ends
    print(f"White pieces switched {game.switch_manager.white_switch_count} times")
    print(f"Black pieces switched {game.switch_manager.black_switch_count} times")
    print(f"Switch Move Numbers: {game.switch_manager.switch_move_numbers}")
    
    # Generate win probability plot
    plot_win_probabilities(move_numbers, white_probabilities, black_probabilities, game.switch_manager.switch_move_numbers)
    logger.info("Win probability plot generated.")
    print("Win probability plot generated.")

    # At the end of the function, add:
    try:
        from win_probability import shutdown
        shutdown()
    except ImportError:
        pass

# Run the game if the script is executed directly
# if __name__ == "__main__":
#     main()

asyncio.run(main())