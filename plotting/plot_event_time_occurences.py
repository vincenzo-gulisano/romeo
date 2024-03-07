import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os

def main(input_folder, output_pdf):
    # Paths to the input files
    eventtime_file = os.path.join(input_folder, 'eventtime.max.csv')
    episodes_file = os.path.join(input_folder, 'episodes.csv')
    
    # Read the CSV files
    eventtime_df = pd.read_csv(eventtime_file, header=None, names=['timestamp', 'event_time'])
    episodes_df = pd.read_csv(episodes_file)
    
    # Filter for start and end times of each episode
    starts_ends = episodes_df[episodes_df['event'].isin(['start', 'end'])]
    
    # Create a new DataFrame for filtered event times
    filtered_eventtimes = pd.DataFrame()
    
    for episode in episodes_df['episode'].unique():
        if episode in starts_ends['episode'].values:
            start_ts = starts_ends[(starts_ends['episode'] == episode) & (starts_ends['event'] == 'start')]['ts'].values[0]
            end_ts = starts_ends[(starts_ends['episode'] == episode) & (starts_ends['event'] == 'end')]['ts'].values[0]
      
            # Filter eventtime_df for the current episode's start/end range
            # and where event_time is not -1
            episode_events = eventtime_df[(eventtime_df['timestamp'] > start_ts) & 
                                        (eventtime_df['timestamp'] < end_ts) &
                                        (eventtime_df['event_time'] != -1)]
            filtered_eventtimes = pd.concat([filtered_eventtimes, episode_events])
    
    # Create a plot
    plt.figure(figsize=(10, 6))
    
    # Aggregate event_time occurrences and plot
    event_time_counts = filtered_eventtimes['event_time'].value_counts().sort_index()
    plt.plot(event_time_counts.index, event_time_counts.values)
    
    plt.xlabel('Event Time')
    plt.ylabel('Number of Occurrences')
    plt.title('Event Time Occurrences')
        
    # Adjusting X and Y limits
    plt.xlim(86400, 98028)
    plt.ylim(0, event_time_counts.values.max() + 10)

    # Adding vertical lines
    plt.axvline(x=86400 + 900, color='r', linestyle='--')
    plt.axvline(x=86400 + 9900, color='g', linestyle='--')

    # Save the plot to the specified PDF file
    plt.savefig(output_pdf)
    plt.close()

    # # Print the event_time_counts.index and values for the entry with the highest value
    # max_occurrences_index = event_time_counts.idxmax()
    # max_occurrences_value = event_time_counts.max()
    # print(f'Event Time with the highest occurrences: {max_occurrences_index}, Number of Occurrences: {max_occurrences_value}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CSV files and plot event times.')
    parser.add_argument('input_folder', type=str, help='Path to the input folder containing CSV files.')
    parser.add_argument('output_pdf', type=str, help='Name of the output PDF file for the plot.')
    
    args = parser.parse_args()
    
    main(args.input_folder, args.output_pdf)
