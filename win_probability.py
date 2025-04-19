"""
Consolidated Win Probability Module for Caesar's Chess

This module combines functionality from:
- win_probability.py (core calculation functions)
- enhanced_win_probability.py (drop-in replacement)
- update_win_probability.py (patching logic)

The consolidated module maintains the same API and functionality
while simplifying the codebase.
"""

import chess
import math
import time
import importlib
import os
import sys
from functools import lru_cache
from configuration import logger
from evaluation import calculate_win_probability as original_probability
from evaluation import calculate_win_probability as material_based_probability

import time
import matplotlib.pyplot as plt
import numpy as np
import chess.engine

# Win Probability Configuration
WIN_PROBABILITY_MODE = "engine"  # Options: "material", "enhanced", "engine"

# Engine settings
USE_ENGINE_FOR_DISPLAY = True      # Use engine evaluation for display/plotting
USE_ENGINE_FOR_SWITCHING = False   # Use engine for switch candidate evaluation
ENGINE_ANALYSIS_TIME = 0.1         # Time in seconds for engine analysis

# Stability factor settings
STABILITY_FACTOR_ENABLED = True    # Apply stability factor to win probability
STABILITY_FACTOR_WEIGHT = 0.01     # Weight of the stability factor

# Cache settings
CACHE_ENABLED = True               # Enable caching of evaluations
CACHE_EXPIRY = 5                   # Cache expiry time in seconds

# -----------------------------------------------------------------------------
# Cache Management (from win_probability.py)
# -----------------------------------------------------------------------------

# Simple cache to avoid redundant calculations
_eval_cache = {}
_cache_expiry = 5  # seconds

def get_cached_eval(board_fen, default=None):
    """Get cached evaluation if available and not expired"""
    if board_fen in _eval_cache:
        timestamp, value = _eval_cache[board_fen]
        if time.time() - timestamp < _cache_expiry:
            return value
    return default

def set_cached_eval(board_fen, value):
    """Cache an evaluation with current timestamp"""
    _eval_cache[board_fen] = (time.time(), value)

# -----------------------------------------------------------------------------
# Core Calculation Functions (from win_probability.py)
# -----------------------------------------------------------------------------

def centipawn_to_probability(cp_score):
    """Convert centipawn score to win probability using sigmoid function"""
    return 1 / (1 + 10 ** (-cp_score / 400))

def count_vulnerable_pieces(board, color):
    """Count pieces that would be eligible for color switching"""
    count = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == color and piece.piece_type != chess.KING:
            # Basic check - exclude kings and consider all other pieces vulnerable
            # In a real implementation, you would use the same criteria as switch_manager
            count += 1
    return count

def apply_stability_factor(board, white_prob, black_prob):
    """Apply a stability factor based on vulnerability to color switches"""
    # Count pieces eligible for switching
    white_vulnerable = count_vulnerable_pieces(board, chess.WHITE)
    black_vulnerable = count_vulnerable_pieces(board, chess.BLACK)
    
    # Apply small penalty to probability based on vulnerability
    stability_factor = 0.01  # Small adjustment factor
    
    adjusted_white = white_prob * (1 - (white_vulnerable * stability_factor))
    adjusted_black = black_prob * (1 - (black_vulnerable * stability_factor))
    
    # Renormalize
    total = adjusted_white + adjusted_black
    if total > 0:
        return adjusted_white/total, adjusted_black/total
    else:
        return 0.5, 0.5

def calculate_win_probability_enhanced(board, engine=None, use_engine=True, stability_aware=True):
    """Enhanced win probability calculation that can use engine evaluation"""
    # Check cache first
    board_fen = board.fen()
    cached = get_cached_eval(board_fen)
    if cached:
        return cached
    
    # Try to use engine if available
    if engine and use_engine:
        try:
            result = engine.analyse(board, chess.engine.Limit(time=0.1), info=chess.engine.INFO_SCORE)
            if 'score' in result:
                score = result['score'].relative
                if score.is_mate():
                    # Handle mate scores
                    if score.mate() > 0:
                        white_prob, black_prob = 0.99, 0.01
                    else:
                        white_prob, black_prob = 0.01, 0.99
                else:
                    # Normal centipawn score
                    cp_score = score.score()
                    white_prob = centipawn_to_probability(cp_score)
                    black_prob = 1 - white_prob
            else:
                # Fall back to material evaluation
                white_prob, black_prob = original_probability(board)
        except Exception as e:
            # If engine analysis fails, use material evaluation
            print(f"Engine analysis failed: {e}")
            white_prob, black_prob = original_probability(board)
    else:
        # Use existing material-based evaluation
        white_prob, black_prob = original_probability(board)
    
    # Apply stability factor if requested
    if stability_aware:
        white_prob, black_prob = apply_stability_factor(board, white_prob, black_prob)
    
    # Cache the result
    result = (white_prob, black_prob)
    set_cached_eval(board_fen, result)
    
    return result

# Function that maintains the same interface as the original
def calculate_win_probability_wrapper(board, use_enhanced=False, engine=None):
    """Wrapper function that maintains compatibility with the original interface"""
    if use_enhanced:
        return calculate_win_probability_enhanced(board, engine)
    else:
        return original_probability(board)

# -----------------------------------------------------------------------------
# Engine Manager Singleton (from enhanced_win_probability.py)
# -----------------------------------------------------------------------------

# Global engine manager instance
_engine_manager = None

def get_engine_manager():
    """Get or create the engine manager singleton"""
    global _engine_manager
    if _engine_manager is None:
        # Lazy import to avoid circular dependencies
        from uci_engine import EngineManager
        _engine_manager = EngineManager.get_instance()
    return _engine_manager

# -----------------------------------------------------------------------------
# Drop-in Replacement Main Function (from enhanced_win_probability.py)
# -----------------------------------------------------------------------------

def calculate_win_probability(board):
    """
    Drop-in replacement for the original calculate_win_probability function.
    
    This function maintains the exact same interface as the original but can
    provide enhanced functionality based on configuration settings.
    """
    
    mode = WIN_PROBABILITY_MODE
    
    if mode == "material":
        # Use the original material-based probability function
        return original_probability(board)
    
    elif mode == "enhanced" or mode == "engine":
        # Get engine if needed
        engine = None
        if mode == "engine":
            engine_manager = get_engine_manager()
            engine = engine_manager.get_engine()
        
        # Use the enhanced probability function
        return calculate_win_probability_enhanced(
            board,
            engine=engine,
            use_engine=(mode == "engine"),
            stability_aware=STABILITY_FACTOR_ENABLED
        )
    
    else:
        # Default to original method if mode is unrecognized
        return original_probability(board)

# -----------------------------------------------------------------------------
# Patching Functions (from update_win_probability.py)
# -----------------------------------------------------------------------------

def update_win_probability():
    """
    Update the win probability implementation to use the enhanced version.
    This preserves all original files and only modifies imports.
    """
    print("Updating win probability calculation...")
    
    try:
        # Import the switch manager and call its patch method directly
        import switch_manager
        switch_manager.patch_switch_manager()
        print("✓ SwitchManager patched successfully")
        
        # Override the evaluation module in sys.modules
        sys.modules['evaluation'] = sys.modules[__name__]
        print("✓ Win probability function replaced")
        
        print("\nEnhanced win probability is now active!")
        print("You can configure it by editing win_probability_config.py")
        
    except Exception as e:
        print(f"Error updating win probability: {str(e)}")
        print("The game will continue to use the original win probability calculation.")

# -----------------------------------------------------------------------------
# Cleanup Function (from enhanced_win_probability.py)
# -----------------------------------------------------------------------------

def shutdown():
    """Shutdown the engine when the application closes"""
    global _engine_manager
    if _engine_manager:
        _engine_manager.close()
        _engine_manager = None

# Add after the existing classes and functions in win_probability.py

class WinProbabilityComparison:
    """Class to manage and compare different win probability calculations"""
    
    def __init__(self):
        from uci_engine import EngineManager
        self.engine_manager = EngineManager.get_instance()
        self.engine = self.engine_manager.get_engine()
        self.results = []
        
    def calculate_all_probabilities(self, board):
        """Calculate win probability using all three methods and return comparison"""
        
        # Start timing
        start_time = time.time()
        
        # 1. Material-based calculation
        material_white, material_black = material_based_probability(board)
        material_time = time.time() - start_time
        
        # 2. Enhanced calculation
        start_time = time.time()
        enhanced_white, enhanced_black = calculate_win_probability_enhanced(
            board, 
            engine=None, 
            use_engine=False,
            stability_aware=True
        )
        enhanced_time = time.time() - start_time
        
        # 3. Engine-based calculation (if available)
        engine_white, engine_black = None, None
        # Safely try engine evaluation
        engine_time = 0
        if self.engine:
            try:
                start_time = time.time()
                engine_white, engine_black = calculate_win_probability_enhanced(
                    board,
                    engine=self.engine,
                    use_engine=True,
                    stability_aware=True
                )
                engine_time = time.time() - start_time
            except Exception as e:
                logger.error(f"Engine evaluation failed: {e}")
                self.engine = None  # Disable engine after error
        
        # Store results for later analysis
        result = {
            "move": len(self.results) + 1,
            "fen": board.fen(),
            "material": {
                "white": material_white,
                "black": material_black,
                "time_ms": material_time * 1000
            },
            "enhanced": {
                "white": enhanced_white,
                "black": enhanced_black,
                "time_ms": enhanced_time * 1000
            },
            "engine": {
                "white": engine_white,
                "black": engine_black,
                "time_ms": engine_time * 1000 if engine_white else None
            }
        }
        self.results.append(result)
        
        # Log the comparison
        self._log_comparison(result)
        
        # Return all probabilities in a dictionary
        return {
            "material": (material_white, material_black),
            "enhanced": (enhanced_white, enhanced_black),
            "engine": (engine_white, engine_black) if engine_white else None
        }
    
    def _log_comparison(self, result):
        """Log the comparison results"""
        move = result["move"]
        
        material_w = result["material"]["white"] * 100
        material_b = result["material"]["black"] * 100
        material_time = result["material"]["time_ms"]
        
        enhanced_w = result["enhanced"]["white"] * 100
        enhanced_b = result["enhanced"]["black"] * 100
        enhanced_time = result["enhanced"]["time_ms"]
        
        engine_str = "N/A"
        if result["engine"]["white"]:
            engine_w = result["engine"]["white"] * 100
            engine_b = result["engine"]["black"] * 100
            engine_time = result["engine"]["time_ms"]
            engine_str = f"W:{engine_w:.1f}% B:{engine_b:.1f}% ({engine_time:.1f}ms)"
        
        # Print comparison to console
        print(f"\nMove {move} Win Probability Comparison:")
        print(f"  Material: W:{material_w:.1f}% B:{material_b:.1f}% ({material_time:.1f}ms)")
        print(f"  Enhanced: W:{enhanced_w:.1f}% B:{enhanced_b:.1f}% ({enhanced_time:.1f}ms)")
        print(f"  Engine  : {engine_str}")
        
        # Also log to file
        logger.info(f"Move {move} Win Probability Comparison:")
        logger.info(f"  Material: W:{material_w:.1f}% B:{material_b:.1f}% ({material_time:.1f}ms)")
        logger.info(f"  Enhanced: W:{enhanced_w:.1f}% B:{enhanced_b:.1f}% ({enhanced_time:.1f}ms)")
        logger.info(f"  Engine  : {engine_str}")
    
    def save_results(self, filename="win_probability_comparison.csv"):
        """Save all results to a CSV file for further analysis"""
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['move', 'material_white', 'material_black', 'material_time',
                         'enhanced_white', 'enhanced_black', 'enhanced_time',
                         'engine_white', 'engine_black', 'engine_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow({
                    'move': result['move'],
                    'material_white': result['material']['white'],
                    'material_black': result['material']['black'],
                    'material_time': result['material']['time_ms'],
                    'enhanced_white': result['enhanced']['white'],
                    'enhanced_black': result['enhanced']['black'],
                    'enhanced_time': result['enhanced']['time_ms'],
                    'engine_white': result['engine']['white'] if result['engine']['white'] else '',
                    'engine_black': result['engine']['black'] if result['engine']['black'] else '',
                    'engine_time': result['engine']['time_ms'] if result['engine']['time_ms'] else ''
                })
        
        print(f"\nWin probability comparison data saved to {filename}")
    
    def generate_comparison_plot(self, filename="win_probability_comparison.png"):
        """Generate a plot comparing the different win probability calculations"""
        try:
            moves = [r['move'] for r in self.results]
            
            # Material probabilities
            material_white = [r['material']['white'] for r in self.results]
            material_black = [r['material']['black'] for r in self.results]
            
            # Enhanced probabilities
            enhanced_white = [r['enhanced']['white'] for r in self.results]
            enhanced_black = [r['enhanced']['black'] for r in self.results]
            
            # Engine probabilities (if available)
            engine_white = []
            engine_black = []
            has_engine_data = False
            
            for r in self.results:
                if r['engine']['white'] is not None:
                    engine_white.append(r['engine']['white'])
                    engine_black.append(r['engine']['black'])
                    has_engine_data = True
                else:
                    # If we have some engine data but this move doesn't, use the last value
                    if has_engine_data and engine_white:
                        engine_white.append(engine_white[-1])
                        engine_black.append(engine_black[-1])
                    else:
                        engine_white.append(None)
                        engine_black.append(None)
            
            # Create plot
            plt.figure(figsize=(12, 8))
            
            # Plot material probabilities
            plt.plot(moves, material_white, 'b-', label='Material White', alpha=0.7)
            plt.plot(moves, material_black, 'r-', label='Material Black', alpha=0.7)
            
            # Plot enhanced probabilities
            plt.plot(moves, enhanced_white, 'b--', label='Enhanced White', alpha=0.7)
            plt.plot(moves, enhanced_black, 'r--', label='Enhanced Black', alpha=0.7)
            
            # Plot engine probabilities if available
            if has_engine_data:
                # Filter out None values
                valid_moves = []
                valid_engine_white = []
                valid_engine_black = []
                
                for i, val in enumerate(engine_white):
                    if val is not None:
                        valid_moves.append(moves[i])
                        valid_engine_white.append(engine_white[i])
                        valid_engine_black.append(engine_black[i])
                
                plt.plot(valid_moves, valid_engine_white, 'b:', label='Engine White', linewidth=2)
                plt.plot(valid_moves, valid_engine_black, 'r:', label='Engine Black', linewidth=2)
            
            plt.xlabel('Move Number')
            plt.ylabel('Win Probability')
            plt.title('Win Probability Comparison')
            plt.ylim(0, 1)
            plt.xlim(left=1)
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save plot
            plt.savefig(filename)
            plt.close()
            
            print(f"\nWin probability comparison plot saved to {filename}")
            
        except ImportError:
            print("Could not generate plot. Please install matplotlib with: pip install matplotlib")
        except Exception as e:
            print(f"Error generating plot: {str(e)}")

# Singleton instance
_comparison_instance = None

def get_comparison_instance():
    """Get or create the comparison singleton"""
    global _comparison_instance
    if _comparison_instance is None:
        _comparison_instance = WinProbabilityComparison()
    return _comparison_instance

def calculate_win_probability(board):
    """
    Drop-in replacement for the original calculate_win_probability function
    that also performs comparison of all methods.
    
    Returns the probability from the currently configured method.
    """
    # Get the comparison instance
    comparison = get_comparison_instance()
    
    # Calculate and compare all methods
    all_probabilities = comparison.calculate_all_probabilities(board)
    
    # Return the value from the configured method
    mode = WIN_PROBABILITY_MODE
    if mode == "material" or mode not in all_probabilities:
        return all_probabilities["material"]
    elif mode == "enhanced":
        return all_probabilities["enhanced"]
    elif mode == "engine" and all_probabilities["engine"]:
        return all_probabilities["engine"]
    else:
        return all_probabilities["enhanced"]  # Fallback

def save_comparison_data():
    """Save the comparison data to CSV and generate a plot"""
    comparison = get_comparison_instance()
    comparison.save_results()
    comparison.generate_comparison_plot()

def shutdown():
    """Shutdown the engine when the application closes"""
    global _comparison_instance
    if _comparison_instance:
        _comparison_instance.engine_manager.close()

# For backward compatibility with the previous files
def update_win_probability():
    """Function for backward compatibility with the previous setup"""
    print("Win probability module initialized with comparison functionality")
    return True
# -----------------------------------------------------------------------------
# Auto-execute update if run as a script
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    update_win_probability()

