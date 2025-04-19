"""
Setup script for Caesar's Chess
Installs required packages for the game.
"""

import subprocess
import sys
import os

def check_pygame():
    """Check if pygame is installed, install if not."""
    try:
        import pygame
        print("✓ Pygame is already installed.")
        return True
    except ImportError:
        print("Pygame not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
            print("✓ Pygame installed successfully.")
            return True
        except Exception as e:
            print(f"Error installing Pygame: {e}")
            return False

def check_chess():
    """Check if python-chess is installed, install if not."""
    try:
        import chess
        print("✓ Python-chess is already installed.")
        return True
    except ImportError:
        print("Python-chess not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-chess"])
            print("✓ Python-chess installed successfully.")
            return True
        except Exception as e:
            print(f"Error installing Python-chess: {e}")
            return False

def check_matplotlib():
    """Check if matplotlib is installed, install if not."""
    try:
        import matplotlib
        print("✓ Matplotlib is already installed.")
        return True
    except ImportError:
        print("Matplotlib not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
            print("✓ Matplotlib installed successfully.")
            return True
        except Exception as e:
            print(f"Error installing Matplotlib: {e}")
            return False

def check_files():
    """Check if required files are present."""
    required_files = [
        "settings_screen.py",
        "launcher.py",
        "configuration.py",
        "game.py",
        "chess_view.py",
        "event_handler.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("✓ All required files are present.")
    return True

def main():
    """Main function to check and install requirements."""
    print("Caesar's Chess Setup")
    print("===================")
    print("Checking requirements...")
    
    # Check and install required packages
    pygame_ok = check_pygame()
    chess_ok = check_chess()
    matplotlib_ok = check_matplotlib()
    
    # Check required files
    files_ok = check_files()
    
    # Summary
    if pygame_ok and chess_ok and matplotlib_ok and files_ok:
        print("\nAll requirements satisfied!")
        print("You can now run the game with: python launcher.py")
    else:
        print("\nSome requirements are missing.")
        print("Please fix the issues above before running the game.")

if __name__ == "__main__":
    main()

from setuptools import setup, find_packages

setup(
    name="chess_game",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pygame",
        "python-chess",
        "matplotlib",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "chess-game=chess_game.main:main",
        ]
    },
)
