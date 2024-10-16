import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

# Function to apply moving average
def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def read_csv_with_optional_header(csv_file_path):
    # Try reading the first row to check if it matches the expected header
    with open(csv_file_path, 'r') as file:
        first_line = file.readline().strip()

    # Define the expected header columns
    expected_columns = ['episode', 'step', 'total_reward']

    # Check if the first line matches the expected columns (assuming no extra whitespace)
    if first_line.split(",") == expected_columns:
        # If the first line matches, read the CSV normally
        df = pd.read_csv(csv_file_path)
    else:
        # If the first line doesn't match, treat it as having no header and assign column names
        df = pd.read_csv(csv_file_path, names=expected_columns)

    return df

# Function to process and plot each csv file
def plot_csv_file(base_folder,csv_file_path,max_step,max_reward):
    # Read the CSV file
    try:
        # df = pd.read_csv(csv_file_path)
        df = read_csv_with_optional_header(csv_file_path)

    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return
    
    # Extract the last two folders from the path to include in the title
    last_two_folders = os.path.join(*csv_file_path.split(os.sep)[-3:-1]).replace(os.sep, "_")

    # Exclude entries where 'step' is equal to 2
    df = df[df["step"] != 2]

    # Compute the average of all total rewards
    overall_average_reward = df["total_reward"].mean()
    overall_average_step = df["step"].mean()

    # Adjust the episodes
    episodes = df["episode"]

    # Plot the data
    plt.figure()
    # Plot actual values
    plt.plot(episodes, df["total_reward"], label="Actual Total Reward", color='blue', alpha=0.5)

    # Plot the overall average as a red horizontal line
    plt.axhline(y=overall_average_reward, color='red', linestyle='--', label="Average Total Reward")

    # Fit a line (linear regression) to minimize the square distance from each point
    # The `polyfit` function returns the slope and intercept of the best-fit line
    slope, intercept = np.polyfit(df["episode"], df["total_reward"], 1)

    # Calculate the values for the regression line
    regression_line = slope * df["episode"] + intercept
    
    # Plot the overall average as a red horizontal line
    plt.plot(df["episode"], regression_line, color='green', linestyle='-', label="Best-Fit Line")

    # Set y-axis limits
    plt.ylim(0, max_reward)

    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.title(f"Total Reward and Overall Average for {os.path.basename(csv_file_path)}")
    plt.legend()

    # Set the title with the last two folders
    plt.title(f"{last_two_folders}")

    # Save the plot as a PNG file in the same directory as the CSV
    output_file_path = os.path.join(base_folder, last_two_folders +  ".reward.png")
    # os.path.splitext(csv_file_path)[0] + ".png"
    plt.savefig(output_file_path)
    plt.close()
    print(f"Plot saved as {output_file_path}")

    # Plot the data
    plt.figure()
    # Plot actual values
    plt.plot(episodes, df["step"], label="Actual Steps", color='blue', alpha=0.5)

    # Plot the overall average as a red horizontal line
    plt.axhline(y=overall_average_step, color='red', linestyle='--', label="Average Total Step")

    # Fit a line (linear regression) to minimize the square distance from each point
    # The `polyfit` function returns the slope and intercept of the best-fit line
    slope, intercept = np.polyfit(df["episode"], df["step"], 1)

    # Calculate the values for the regression line
    regression_line = slope * df["episode"] + intercept
    
    # Plot the overall average as a red horizontal line
    plt.plot(df["episode"], regression_line, color='green', linestyle='-', label="Best-Fit Line")


    # Set y-axis limits
    plt.ylim(0, max_step)

    plt.xlabel("Episode")
    plt.ylabel("Total Steps")
    plt.title(f"Total Steps and Overall Average for {os.path.basename(csv_file_path)}")
    plt.legend()

    # Set the title with the last two folders
    plt.title(f"{last_two_folders}")

    # Save the plot as a PNG file in the same directory as the CSV
    output_file_path = os.path.join(base_folder, last_two_folders +  ".steps.png")
    # os.path.splitext(csv_file_path)[0] + ".png"
    plt.savefig(output_file_path)
    plt.close()
    print(f"Plot saved as {output_file_path}")

# Function to search for all python_cumulative_reward.csv files and create plots
def search_and_plot(folder,max_step,max_reward):
    for root, _, files in os.walk(folder):
        for file in files:
            if file == "step_tot_reward.csv" or file == "rewards.steps.csv":
                csv_file_path = os.path.join(root, file)
                plot_csv_file(folder,csv_file_path,max_step,max_reward)

# Argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot CSV files with smoothed reward data.")
    parser.add_argument("folder", help="Folder to search for python_cumulative_reward.csv files")
    parser.add_argument("max_step", help="max_step")
    parser.add_argument("max_reward", help="max_reward")
    args = parser.parse_args()

    # Search the folder and create plots
    search_and_plot(args.folder,int(args.max_step),int(args.max_reward))
