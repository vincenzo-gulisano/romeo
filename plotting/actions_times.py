import os
import pandas as pd
import argparse

def find_files_recursively(directory, filename):
    """Recursively find all files with a specific name in the directory."""
    episodes_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == filename:
                episodes_files.append(os.path.join(root, file))
    return episodes_files

def calculate_average_ts_diff(filepath):
    """Calculate the average ts difference for consecutive 'action' events in the same episode."""
    # Read the CSV file
    df = pd.read_csv(filepath)
    
    # Filter only events where the 'event' column starts with 'action'
    df_action = df[df['event'].str.startswith('action', na=False)]
    
    # # Calculate the average ts difference for consecutive 'action' events in the same episode
    # avg_ts_diff_per_episode = df_action.groupby('episode', group_keys=False).apply(
    #     lambda group: group['ts'].diff().dropna().mean()
    # )
    
    # Group by 'episode', but explicitly select the 'ts' column before applying the function
    avg_ts_diff_per_episode = df_action.groupby('episode')['ts'].apply(
        lambda group: group.diff().dropna().mean()
    )

    # Return the overall average ts difference across all episodes
    return avg_ts_diff_per_episode.mean()

def main(directory):
    # Search for all 'episodes.csv' files in the directory
    episodes_files = find_files_recursively(directory, 'episodes.csv')
    
    if not episodes_files:
        print(f"No 'episodes.csv' files found in directory {directory}.")
        return
    
    # Iterate through each file and calculate the average time difference for 'action' events
    for filepath in episodes_files:
        avg_ts_diff = calculate_average_ts_diff(filepath)
        # print(f"File: {filepath}")
        if pd.isna(avg_ts_diff):
            print("  No consecutive 'action' events found.")
        else:
            print(f"File: {filepath} - Average ts difference: {avg_ts_diff:.2f}")

if __name__ == "__main__":
   
    parser = argparse.ArgumentParser(description="Compute average inter action time for all files named episodes.csv in the given folder recursively")
    parser.add_argument('directory', type=str, help='Base folder containing the data.')
    
    args = parser.parse_args()
    
    main(args.directory)
