import sys 

def enable_comparison_mode():
    """
    Enable win probability comparison mode by replacing the
    enhanced_win_probability module with win_probability.
    """
    # Import the standard modules first
    import switch_manager
    switch_manager.patch_switch_manager()
    
    print("Setting up win probability comparison mode...")
    
    # Now replace the evaluation module with our comparison module
    import win_probability
    sys.modules['evaluation'] = win_probability
    sys.modules['enhanced_win_probability'] = win_probability
    
    print("✓ Win probability comparison mode active!")
    print("All three methods (material, enhanced, engine) will be calculated and compared.")
    print("Results will be displayed after each move.")
    print("A CSV file and graph will be generated at the end of the game.")

if __name__ == "__main__":
    enable_comparison_mode()