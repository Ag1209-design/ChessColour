Code file breakdown

Main:
Initialize game, manage main loop, handles user selections

Game:
Manage game state, move handling, switching mechanics, and animations

Event Handler:
Processes user inputs, token interactions, and timer-based events

Switch Handler:
All colour switch related events

Animation Handler:
Animations and visual related actions

UCI Engine:
Interfaces with Stockfish or other UCI chess engines for AI moves

Game Setup:
Configures players, AI, and initializes the chess game

Chess View:
Handles rendering the chessboard, pieces, and UI elements

Evaluation:
Calculates win probabilities and evaluates board positions

AI:
AI player logic using a UCI engine or custom evaluation

Plotting:
Generates graphs for win probability analysis

Configuration:
Stores game settings, logging setup, UI parameters, and piece evaluation tables

Win prob calculator:
Three modes - material, enhanced and engine to calculate win probability after every move
