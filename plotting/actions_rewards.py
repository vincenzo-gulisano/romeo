import os
import pandas as pd
import argparse

def find_reward_files(folder):
    # Walk through all directories and subdirectories recursively
    for root, _, files in os.walk(folder):
        for file in files:
            if file == 'rewards.actions.csv':
                file_path = os.path.join(root, file)
                process_reward_file(file_path)

def process_reward_file(file_path):
    # Read the CSV without headers (as per the problem statement)
    try:
        df = pd.read_csv(file_path, header=None, names=['ts', 'reward'])
        
        # Count the occurrences of each unique reward
        reward_counts = df['reward'].value_counts()
        
        # Print the full path and the occurrences of each reward
        print(f"{file_path}: {reward_counts}")
        print("\n")
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Count how many times each unique reward is opbserved for all files named rewards.csv in the given folder recursively")
    parser.add_argument('directory', type=str, help='Base folder containing the data.')
    
    args = parser.parse_args()
    
    find_reward_files(args.directory)
