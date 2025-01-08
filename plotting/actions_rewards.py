import os
import pandas as pd
import argparse
import matplotlib.pyplot as plt

# Dictionary to keep track of reward counts for each file
reward_counts_per_file = {}

def find_reward_files(folder):
    # Walk through all directories and subdirectories recursively
    for root, _, files in os.walk(folder):
        for file in files:
            if file == 'rewards.actions.csv':
                file_path = os.path.join(root, file)
                process_reward_file_rewards_actions(file_path)
            if file == 'probs.csv':
                file_path = os.path.join(root, file)
                process_reward_file_probs_file(file_path)

def process_reward_file_rewards_actions(file_path):
    # Read the CSV without headers (as per the problem statement)
    try:
        df = pd.read_csv(file_path, header=None, names=['ts', 'reward'])
        
        # Count the occurrences of each unique reward
        reward_counts = df['reward'].value_counts()
        
        # Print the full path and the occurrences of each reward
        # print(f"{file_path}: {reward_counts}")
        # print("\n")
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def plot_reward_counts(output_path):
    
    # print(reward_counts_per_file)
    # Convert the reward counts dictionary into a DataFrame for easy plotting
    reward_counts_df = pd.DataFrame(reward_counts_per_file).fillna(0)
    
    # print(reward_counts_df)
    
    # Create a bar plot with grouped bars
    reward_counts_df.plot(kind='line', figsize=(12, 8), linestyle='None', marker='o')
    
    plt.title("Reward Counts Across Files")
    plt.xlabel("Reward")
    plt.ylabel("Count")
    plt.yscale("log")
    plt.legend(title="File", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # Save the single plot with all grouped bars
    plt.savefig(output_path)
    plt.close()
    print("Combined plot saved as combined_reward_counts.png")

def process_reward_file_probs_file(file_path):
    # Read the CSV without headers (as per the problem statement)
    try:
        df = pd.read_csv(file_path, header=None, names=['episode','step','prob0','prob1','prob2','entropy','entropy_ma','entropy_ma_ready','reward'])
        
        # Count the occurrences of each unique reward
        reward_counts = df['reward'].value_counts()
        
        # Define counts for the specific rewards and ranges
        specific_counts = {
            '-1': df[df['reward'] == -1].shape[0],
            '0': df[df['reward'] == 0].shape[0],
            '[25,30)': df[(df['reward'] >= 25) & (df['reward'] < 30)].shape[0],
            '[30,40)': df[(df['reward'] >= 30) & (df['reward'] < 40)].shape[0],
            '[40,50)': df[(df['reward'] >= 40) & (df['reward'] <= 50)].shape[0],
        }
        
        # Store the reward counts in a dictionary for later use
        reward_counts_per_file[file_path] = reward_counts
        
        # Print the full path and the occurrences of each reward
        print(f"{file_path}")
        print("Specific Reward Counts:")
        for reward, count in specific_counts.items():
            print(f"  {reward}: {count}")
        print("\n")
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Count how many times each unique reward is opbserved for all files named rewards.csv in the given folder recursively")
    parser.add_argument('directory', type=str, help='Base folder containing the data.')
    
    args = parser.parse_args()
    
    find_reward_files(args.directory)
    
    plot_reward_counts(os.path.join(args.directory, 'rewards.pdf'))
