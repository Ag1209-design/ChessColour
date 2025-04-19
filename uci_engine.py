import chess.engine
import threading
import time
from configuration import UCI_ENGINE_PATH, logger

class UCIEngine:
    """Handles communication with a UCI chess engine (Stockfish, Lc0, etc.)."""
    
    def __init__(self):
        """Initializes the UCI chess engine from configuration.py."""
        self.engine_path = UCI_ENGINE_PATH  # Get path from config
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            print(f"UCI Engine started: {self.engine_path}")
        except FileNotFoundError:
            print(f"Error: UCI engine not found at {self.engine_path}. Ensure the path is correct.")
            self.engine = None

    def choose_move(self, board, time_limit=1.0):
        """Gets the best move from the UCI engine."""
        if self.engine:
            result = self.engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
        else:
            print("Error: UCI engine is not running.")
            return None

    def close(self):
        """Closes the UCI engine process."""
        if self.engine:
            self.engine.quit()
            print("UCI Engine closed.")

class EngineManager:
    """Manages a UCI engine instance for analysis"""
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one engine instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.engine = None
        self.engine_path = UCI_ENGINE_PATH
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the UCI engine"""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            logger.info(f"Analysis engine started: {self.engine_path}")
        except FileNotFoundError:
            logger.error(f"Error: UCI engine not found at {self.engine_path}. Win probability will use material evaluation.")
            self.engine = None
        except Exception as e:
            logger.error(f"Error initializing UCI engine: {str(e)}")
            self.engine = None
    
    def get_engine(self):
        """Get the engine instance, reinitializing if needed"""
        if self.engine is None:
            self._initialize_engine()
        return self.engine
    
    def analyse_position(self, board, time_limit=None):
        """Analyse a position using the UCI engine"""
        if time_limit is None:
            # Import ENGINE_ANALYSIS_TIME from win_probability instead of wp_config
            from win_probability import ENGINE_ANALYSIS_TIME
            time_limit = ENGINE_ANALYSIS_TIME
            
        engine = self.get_engine()
        if engine is None:
            return None
            
        try:
            result = engine.analyse(
                board, 
                chess.engine.Limit(time=time_limit),
                info=chess.engine.INFO_SCORE
            )
            return result
        except Exception as e:
            logger.error(f"Error during engine analysis: {str(e)}")
            return None
    
    def close(self):
        """Close the engine"""
        if self.engine:
            try:
                self.engine.quit()
                logger.info("Analysis engine closed.")
            except Exception as e:
                logger.error(f"Error closing engine: {str(e)}")
            finally:
                self.engine = None