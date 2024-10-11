import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

# Function to apply moving average
def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

# Function to process and plot each csv file
def plot_csv_file(csv_file_path):
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return
    
    # Extract the last two folders from the path to include in the title
    last_two_folders = os.path.join(*csv_file_path.split(os.sep)[-3:-1])

    # Exclude entries where 'step' is equal to 2
    df = df[df["step"] != 2]

    # Compute the average of all total rewards
    overall_average = df["total_reward"].mean()

    # Adjust the episodes
    episodes = df["episode"]

    # Plot the data
    plt.figure()
    # Plot actual values
    plt.plot(episodes, df["total_reward"], label="Actual Total Reward", color='blue', alpha=0.5)

    # Plot the overall average as a red horizontal line
    plt.axhline(y=overall_average, color='red', linestyle='--', label="Average Total Reward")

    # Set y-axis limits
    plt.ylim(0, 300)

    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.title(f"Total Reward and Overall Average for {os.path.basename(csv_file_path)}")
    plt.legend()

    # Set the title with the last two folders
    plt.title(f"{last_two_folders}")

    # Save the plot as a PNG file in the same directory as the CSV
    output_file_path = os.path.splitext(csv_file_path)[0] + ".png"
    plt.savefig(output_file_path)
    plt.close()
    print(f"Plot saved as {output_file_path}")

# Function to search for all python_cumulative_reward.csv files and create plots
def search_and_plot(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file == "rewards.steps.csv":
                csv_file_path = os.path.join(root, file)
                plot_csv_file(csv_file_path)

# Argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot CSV files with smoothed reward data.")
    parser.add_argument("folder", help="Folder to search for python_cumulative_reward.csv files")
    args = parser.parse_args()

    # Search the folder and create plots
    search_and_plot(args.folder)
