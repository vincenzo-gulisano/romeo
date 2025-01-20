import pandas as pd
import argparse
import os

def add_episode_indicator(base_folder, log_file, csv_file):
    agent_resrouce = pd.read_csv(os.path.join(base_folder, csv_file))
    agent_log = os.path.join(base_folder, log_file)
    episode_starts = []
    current_episode = None

    # extract the starting timestamp for each episode
    with open(agent_log, 'r') as file:
        for line in file:
            # define the start of a new episode
            if 'starting episode' in line:
                current_episode = int(line.strip().split()[-1]) # extract episode number
                continue
            # capture the first timestamp of each episode
            if current_episode is not None and 'Got a new state/reward/extrainfo msg:' in line:
                timestamp = float(line.split('msg:')[1].strip())
                episode_starts.append(timestamp)
                current_episode = None # reset to ensure only the first timestamp per episode is captured
    # add a column to mark episode starts in the agent resource file
    agent_resrouce['episode_start'] = ''

    current_episode_index = 0
    for timestamp in episode_starts:
        for index, row in agent_resrouce.iterrows():
            if row['timestamp'] > timestamp:
                # mark the first row in agent resource after this log timestamp
                agent_resrouce.at[index, 'episode_start'] = f'episode {current_episode_index + 1}'
                current_episode_index += 1
                break
    
    # save the modified file with episode start markers
    output_file = os.path.join(base_folder, f'agent_resource_usage_episode.csv')
    agent_resrouce.to_csv(output_file, index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='indicate the start/end of the episode')
    parser.add_argument('base_folder', type=str, help='base folder')
    parser.add_argument('log_file', type=str, help='log file')
    parser.add_argument('csv_file', type=str, help='csv file')

    args = parser.parse_args()
    add_episode_indicator(args.base_folder, args.log_file, args.csv_file)