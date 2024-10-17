import os
import pandas as pd
import argparse

def process_csv_file(csv_file_path):
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
    except Exception as e:
        print(f"Error reading {csv_file_path}: {e}")
        return None

    # Calculate cumulative sum of 'step' column
    df['cumulative_step'] = df['step'].cumsum()

    # Extract folder path and create output file path
    folder_path = os.path.dirname(csv_file_path)
    output_file_path = os.path.join(folder_path, 'episodes.steps.cumulative.csv')

    # Save 'episode' and 'cumulative_step' columns to the output file
    df[['episode', 'cumulative_step']].to_csv(output_file_path, index=False)

    print(f"Processed {csv_file_path}. Output saved to {output_file_path}")

def search_and_process(folder):
    for root, _, files in os.walk(folder):
        for file in files:
            if file == 'rewards.steps.csv':
                csv_file_path = os.path.join(root, file)
                process_csv_file(csv_file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process rewards.steps.csv files and create cumulative step CSV.")
    parser.add_argument("folder", help="Folder to search for rewards.steps.csv files")
    args = parser.parse_args()

    search_and_process(args.folder)
