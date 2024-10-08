import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

# Function to apply moving average
def moving_average(data, window_size=5):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

# Function to process and plot each csv file
def plot_csv_file(csv_file_path):
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path, header=None, names=["Episode", "Total Reward"])
    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return

    # Apply the moving average to the "Total Reward" column
    smoothed_rewards = moving_average(df["Total Reward"], window_size=5)

    # Adjust the episodes to match the length of the smoothed data
    episodes = df["Episode"][:len(smoothed_rewards)]

    # Plot the data
    plt.figure()
    plt.plot(episodes, smoothed_rewards, label="Smoothed Total Reward")
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.title(f"Smoothed Total Reward vs. Episode for {os.path.basename(csv_file_path)}")
    plt.legend()

    # Save the plot as a PNG file in the same directory as the CSV
    output_file_path = os.path.splitext(csv_file_path)[0] + ".png"
    plt.savefig(output_file_path)
    plt.close()
    print(f"Plot saved as {output_file_path}")

# Function to search for all python_cumulative_reward.csv files and create plots
def search_and_plot(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file == "python_cumulative_reward.csv":
                csv_file_path = os.path.join(root, file)
                plot_csv_file(csv_file_path)

# Argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot CSV files with smoothed reward data.")
    parser.add_argument("folder", help="Folder to search for python_cumulative_reward.csv files")
    args = parser.parse_args()

    # Search the folder and create plots
    search_and_plot(args.folder)
