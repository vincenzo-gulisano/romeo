import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np

def compute_entropy(prob1, prob2, prob3):
    # Compute entropy using the formula H = -sum(P * log(P))
    probs = np.array([prob1, prob2, prob3])
    # Avoid log(0) by only computing for non-zero probabilities
    entropy = -np.sum([p * np.log(p) for p in probs if p > 0])
    return entropy


def plot_probs_probs(csv_file_path):

    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path, names=['episode','step','prob0','prob1','prob2','entropy','entropy_ma','entropy_ma_ready','reward'])
    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return
    
    # Sort data by Episode and Step for proper ordering
    df = df.sort_values(by=['episode', 'step'])
    
    # Plot 1: Three lines for Prob1, Prob2, and Prob3
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['prob0'], label="0", color='blue',alpha=0.6)
    plt.plot(df.index, df['prob1'], label="1", color='green',alpha=0.6)
    plt.plot(df.index, df['prob2'], label="2", color='red',alpha=0.6)

    # Find episode indices for multiples of 20 starting from episode 21
    # This is because in these experiments the target network is updated
    # every 20 episodes
    last_episode = None
    episode_indices = []
    for idx, row in df.iterrows():
        if row['episode'] % 20 == 1 and row['episode'] != last_episode:
            episode_indices.append(idx)
            last_episode = row['episode']
    # print(episode_indices)

    # Plot vertical lines at these episode indices
    for idx in episode_indices:
        plt.axvline(x=idx, color='gray', linestyle='--', linewidth=0.5)

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
    plt.plot(df.index, df['prob1'] + df['prob2'], label="1 OR 2", color='purple')

    # Plot vertical lines at these episode indices
    for idx in episode_indices:
        plt.axvline(x=idx, color='gray', linestyle='--', linewidth=0.5)

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

    # Plot 3: Entropy over time
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['entropy'], label="Entropy", color='orange',alpha=0.6)
    plt.plot(df.index, df['entropy_ma'], label="Entropy", color='red')
        
    entropy_threshold = 0.6
    # Identify intervals where entropy moving average is below 0.6
    below_threshold = df['entropy_ma'] < entropy_threshold
    for i in range(len(below_threshold) - 1):
        if below_threshold[i] and not below_threshold[i - 1]:  # Start of interval
            start = df.index[i]
        elif below_threshold[i] and not below_threshold[i + 1]:  # End of interval
            end = df.index[i]
            plt.axvspan(start, end, color='lightgrey', alpha=0.3)  # Shaded background for interval

    # Plot vertical lines at these episode indices
    for idx in episode_indices:
        plt.axvline(x=idx, color='gray', linestyle='--', linewidth=0.5)

    plt.xlabel('Index (Episode and Step)')
    plt.ylabel('Entropy')
    plt.title(f"Entropy of Action Probabilities for {os.path.basename(csv_file_path)}")
    plt.legend()
    plt.tight_layout()

    # Save the third plot to file
    plot3_file_path = os.path.splitext(csv_file_path)[0] + "_entropy.png"
    plt.savefig(plot3_file_path)
    plt.close()
    print(f"Entropy plot saved as {plot3_file_path}")

def plot_probs_actionprobs(csv_file_path):
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

    # Compute entropy for each row in actions_df
    df['Entropy'] = df.apply(lambda row: compute_entropy(row['Prob1'], row['Prob2'], row['Prob3']), axis=1)

    # Plot 1: Three lines for Prob1, Prob2, and Prob3
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Prob1'], label="0", color='blue',alpha=0.6)
    plt.plot(df.index, df['Prob2'], label="1", color='green',alpha=0.6)
    plt.plot(df.index, df['Prob3'], label="2", color='red',alpha=0.6)

    # Find episode indices for multiples of 20 starting from episode 21
    last_episode = None
    episode_indices = []
    for idx, row in df.iterrows():
        if row['Episode'] % 20 == 1 and row['Episode'] != last_episode:
            episode_indices.append(idx)
            last_episode = row['Episode']
    # print(episode_indices)

    # Plot vertical lines at these episode indices
    for idx in episode_indices:
        plt.axvline(x=idx, color='gray', linestyle='--', linewidth=0.5)

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

    # Plot vertical lines at these episode indices
    for idx in episode_indices:
        plt.axvline(x=idx, color='gray', linestyle='--', linewidth=0.5)

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

    # Plot 3: Entropy over time
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Entropy'], label="Entropy", color='orange')
    
    # Plot vertical lines at these episode indices
    for idx in episode_indices:
        plt.axvline(x=idx, color='gray', linestyle='--', linewidth=0.5)

    plt.xlabel('Index (Episode and Step)')
    plt.ylabel('Entropy')
    plt.title(f"Entropy of Action Probabilities for {os.path.basename(csv_file_path)}")
    plt.tight_layout()

    # Save the third plot to file
    plot3_file_path = os.path.splitext(csv_file_path)[0] + "_entropy.png"
    plt.savefig(plot3_file_path)
    plt.close()
    print(f"Entropy plot saved as {plot3_file_path}")

def search_and_plot(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file == "probs.csv":
                csv_file_path = os.path.join(root, file)
                plot_probs_probs(csv_file_path)
            elif file == "actionsprobs.csv":
                csv_file_path = os.path.join(root, file)
                plot_probs_actionprobs(csv_file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Action Probabilities from CSV files.")
    parser.add_argument("folder", help="Folder to search for actionsprobs.csv files")
    args = parser.parse_args()

    # Search the folder and create plots
    search_and_plot(args.folder)
