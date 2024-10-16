import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse

def plot_probs(csv_file_path):
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return

    # Ensure the necessary columns are present
    required_columns = ['Episode', 'Step', 'Action Time', 'Prob1', 'Prob2', 'Prob3']
    if not all(col in df.columns for col in required_columns):
        print(f"File {csv_file_path} does not contain the required columns.")
        return

    # Sort data by Episode and Step for proper ordering
    df = df.sort_values(by=['Episode', 'Step'])

    # Plot 1: Three lines for Prob1, Prob2, and Prob3
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Prob1'], label="0", color='blue',alpha=0.6)
    plt.plot(df.index, df['Prob2'], label="1", color='green',alpha=0.6)
    plt.plot(df.index, df['Prob3'], label="2", color='red',alpha=0.6)
    plt.xlabel('Index (Episode and Step)')
    plt.ylabel('Probability')
    plt.ylim(-0.1,1.1)
    plt.title(f"Action Probabilities for {os.path.basename(csv_file_path)}")
    plt.legend()
    plt.tight_layout()

    # Save the plot to file
    plot1_file_path = os.path.splitext(csv_file_path)[0] + "_probs.png"
    plt.savefig(plot1_file_path)
    plt.close()
    print(f"Probabilities plot saved as {plot1_file_path}")

    # Plot 2: Single line for the sum of Prob2 + Prob3
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Prob2'] + df['Prob3'], label="1 OR 2", color='purple')
    plt.xlabel('Index (Episode and Step)')
    plt.ylabel('Sum of Prob2 and Prob3')
    plt.ylim(-0.1,1.1)
    plt.title(f"Sum of Prob2 + Prob3 for {os.path.basename(csv_file_path)}")
    plt.legend()
    plt.tight_layout()

    # Save the second plot to file
    plot2_file_path = os.path.splitext(csv_file_path)[0] + "_sum_probs.png"
    plt.savefig(plot2_file_path)
    plt.close()
    print(f"Sum of Prob2 + Prob3 plot saved as {plot2_file_path}")

def search_and_plot(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file == "actionsprobs.csv":
                csv_file_path = os.path.join(root, file)
                plot_probs(csv_file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Action Probabilities from CSV files.")
    parser.add_argument("folder", help="Folder to search for actionsprobs.csv files")
    args = parser.parse_args()

    # Search the folder and create plots
    search_and_plot(args.folder)
