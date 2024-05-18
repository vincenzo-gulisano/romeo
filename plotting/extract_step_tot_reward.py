import re
import csv
import argparse
import os

def extract_data(base_folder):
    log_file_path = os.path.join(base_folder, 'python_agent.log') 
    output_csv_path = os.path.join(base_folder, 'step_tot_reward_14.csv')

    episode_pattern = re.compile(r'Episode (\d+), Step (\d+), This episode has finished\.\nEpisode \1, Total Time:.*Total Reward: (-?\d+)')

    # Prepare to write to the CSV file
    with open(output_csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['episode', 'step', 'total_reward'])  # Write header

        # Open and read the log file
        with open(log_file_path, 'r') as log_file:
            log_content = log_file.read()
            matches = episode_pattern.findall(log_content)
            for match in matches:
                episode, step, total_reward = match
                writer.writerow([episode, step, total_reward])  # Write each match to the CSV

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract episode data from log file and write to CSV.")
    parser.add_argument('base_folder', type=str, help='Path to the base folder')
    args = parser.parse_args()

    extract_data(args.base_folder)
