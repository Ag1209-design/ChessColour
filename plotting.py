import matplotlib.pyplot as plt
import numpy as np

def plot_win_probabilities(move_numbers, white_probabilities, black_probabilities, switch_move_numbers):
    """Plots the win probabilities of a chess game over the number of moves.

    Args:
        move_numbers (list): List of move numbers.
        white_probabilities (list): List of white's win probabilities at each move.
        black_probabilities (list): List of black's win probabilities at each move.
        switch_move_numbers (list): List of move numbers where color switches occurred.
    """

    plt.figure(figsize=(12, 7))

    # Plot win probabilities
    plt.plot(move_numbers, white_probabilities, label='White Win Probability', color='tab:blue')
    plt.plot(move_numbers, black_probabilities, label='Black Win Probability', color='tab:orange')

    # Plot vertical lines for each move (optional)
    # for move_number in move_numbers:
    #     plt.axvline(x=move_number, color='black', linestyle='-', linewidth=0.5)

    # Add vertical lines to indicate color switches
    for switch_move in switch_move_numbers:
        plt.axvline(x=switch_move, color='red', linestyle='-', linewidth=0.8, label='Color Switch' if switch_move == switch_move_numbers[0] else "")

    # Calculate average win probabilities
    avg_white_prob = np.mean(white_probabilities)
    avg_black_prob = np.mean(black_probabilities)

    # Plot average win probabilities
    plt.axhline(y=avg_white_prob, color='blue', linestyle='-.', linewidth=1.2, label=f'Avg. White Win Prob: {avg_white_prob:.2f}')
    plt.axhline(y=avg_black_prob, color='orange', linestyle='-.', linewidth=1.2, label=f'Avg. Black Win Prob: {avg_black_prob:.2f}')

    plt.xlabel('Move Number')
    plt.ylabel('Win Probability')
    plt.title('Win Probability During Chess Game')
    plt.ylim(0, 1)
    plt.xlim(left=1)
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='upper left')
    plt.grid(True)
    plt.show()
    plt.close()