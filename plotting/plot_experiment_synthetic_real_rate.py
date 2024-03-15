import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import plotly.tools as tls

def plot_files_in_folder(folder):

    valid_csv_files = []

    csv_files_to_process = ['injectionrate.rate.csv','throughput.count.csv','CPU-in.average.csv','CPU-agg.average.csv','CPU-out.average.csv','outrate.rate.csv','latency.average.csv','ratio.percent.csv','eventtime.max.csv']

    for file in csv_files_to_process:
        file_path = os.path.join(folder, file)
        try:
            df = pd.read_csv(file_path)
            # Check if the CSV file has exactly 2 columns and contains numerical values
            if len(df.columns) == 2 and all(df.applymap(lambda x: isinstance(x, (int, float))).all(axis=1)):
                print(file_path,'is a valid file path')
                valid_csv_files.append(file_path)
            else:
                print(file_path,'is not a valid file path')
        except pd.errors.EmptyDataError:
            pass  # Handle empty CSV files

    if not valid_csv_files:
        print("No valid CSV files found in the folder.")
        return

    # Read episodes.csv
    # episodes_path = os.path.join(folder, 'episodes.csv')
    # episodes_df = pd.read_csv(episodes_path)

    # highest_episode = episodes_df['episode'].max()

    print('Computing the minimum value of the first column among all files...')
    min_value = min(pd.read_csv(file).iloc[:, 0].min() for file in valid_csv_files)
    # min_value = min(min_value,episodes_df.iloc[:, 0].min())
    print('...',min_value)

    # episodes_df['ts'] -= min_value

    # Set the size of the figure
    fig1, ax1 = plt.subplots(len(valid_csv_files),1,figsize=(10, len(valid_csv_files)*2), sharex=True)

    # Plot each valid CSV file
    for i,file_path in enumerate(valid_csv_files):
        df = pd.read_csv(file_path)
        x_label = 'Time (s)'
        y_label = os.path.splitext(os.path.basename(file_path))[0]
        
        # Adjust the values by subtracting the minimum value
        df.iloc[:, 0] -= min_value

        # Plotting for fig 1
        ax1[i].plot(df.iloc[:, 0], df.iloc[:, 1].replace(-1, np.nan), label=y_label)
        ax1[i].set_xlabel(x_label)
        # ax1[i].set_xlim([0,7200])
        ax1[i].set_ylabel(y_label)
        # plt.yscale('log')
        
        # Add vertical lines for each ts in episodes.csv
        # if print_global_events:
        #     for index, row in episodes_df.iterrows():
        #         if row['event']=='start' or row['event']=='end':
        #             ax1[i].axvline(row['ts'], linestyle='--', color='red')
        #             ax1[i].text(row['ts'], (df.iloc[:, 1].min()+df.iloc[:, 1].max())/2, f"{row['episode']}: {row['event']}", rotation=90, color='red')

        if i==0:
            ax1[i].set_title(f'Plot for {os.path.basename(file_path)}')

    # Create a subfolder for each unique episode value
    # episode_folder = os.path.join(folder, 'eps')
    # os.makedirs(episode_folder, exist_ok=True)

    # # Iterate through unique episode values in episodes_df
    # for episode_value in episodes_df['episode'].unique():

    #     # Set the size of the figure
    #     fig2, ax2 = plt.subplots(len(valid_csv_files),1,figsize=(4, len(valid_csv_files)), sharex=True)

    #     # Plot each valid CSV file
    #     for i,file_path in enumerate(valid_csv_files):
            
    #         df = pd.read_csv(file_path)
    #         x_label = 'Time (s)'
    #         y_label = os.path.splitext(os.path.basename(file_path))[0]
            

    #         # Adjust the values by subtracting the minimum value
    #         df.iloc[:, 0] -= min_value

    #         # Initialize an empty list to store statistics
    #         stats = []

    #         # Filter episodes_df for the current episode value
    #         episode_data = episodes_df[episodes_df['episode'] == episode_value]

    #         # Check if both 'start' and 'end' events exist for this episode
    #         has_start = (episode_data['event'] == 'start').any()
    #         has_end = (episode_data['event'] == 'end').any()

    #         if has_start and has_end:

    #             # Count the number of entries that start with 'action' in the 'event' column
    #             action_count = episode_data[episode_data['event'].str.startswith('action')].shape[0]

    #             # Append the steps stat only for the first csv, no need to append it every time
    #             if i == 0:
    #                 stats.append({'episode': episode_value, 'stat': 'steps', 'min': action_count, 'mean': action_count,  'sum': action_count,  'max': action_count})

    #             # Filter data based on the 'start' and 'stop' columns in episode_data
    #             # for _, episode_entry in episode_data.iterrows(): ### COMMENTED THIS BECAUSE I THINK IT IS NOT NEEDED
    #             start_time = episode_data[episode_data['event'] == 'start'].iloc[:, 0].values[0]
    #             stop_time = episode_data[episode_data['event'] == 'end'].iloc[:, 0].values[0]
            
    #             # print('episode',episode_value,'start',start_time,'end',stop_time)
    #             temp_df = df[(df.iloc[:, 0] >= start_time) & (df.iloc[:, 0] <= stop_time)]

    #             # Plot
    #             ax2[i].plot(temp_df.iloc[:, 0]-start_time,temp_df.iloc[:, 1])
                
    #             ax2[i].axvline(0, linestyle='--', color='red')
    #             ax2[i].text(0, (temp_df.iloc[:, 1].min()+temp_df.iloc[:, 1].max())/2, f"Episode {episode_value}", rotation=90, color='red')

    #             ax2[i].set_xlabel(x_label)
    #             ax2[i].set_ylabel(y_label)
                
                
    #             # Filter out -1 values
    #             filtered_values = temp_df.iloc[:, 1][temp_df.iloc[:, 1] != -1]

    #             # Append episode statistics to the list, excluding -1 from the calculations
    #             stats.append({
    #                 'episode': episode_value,
    #                 'stat': os.path.splitext(os.path.basename(file_path))[0],
    #                 'min': np.min(filtered_values) if not filtered_values.empty else np.nan,
    #                 'mean': np.mean(filtered_values) if not filtered_values.empty else np.nan,
    #                 'sum': np.sum(filtered_values) if not filtered_values.empty else np.nan,
    #                 'max': np.max(filtered_values) if not filtered_values.empty else np.nan
    #             })

    #             # Convert the list of dictionaries to a DataFrame
    #             stats_df = pd.DataFrame(stats)

    #             # Append the DataFrame to the output CSV file
    #             stats_df.to_csv(episodesstatsfile, mode='a', index=False, header=not os.path.exists(episodesstatsfile))

    #     fig2.tight_layout()
    #         # Ensure subplots are close to each other and adjust left and right margins
    #     fig2.subplots_adjust(hspace=0)
    #     fig2.savefig(os.path.join(episode_folder, f'episode{episode_value:03}.pdf'))
    #     plt.close()

        
    fig1.tight_layout()
        # Ensure subplots are close to each other and adjust left and right margins
    # fig1.subplots_adjust(hspace=0, left=0.07, right=0.93)
    fig1.savefig(os.path.join(folder, 'stats_global.pdf'))

        # Convert to Plotly figure
    fig = tls.mpl_to_plotly(plt.gcf())

    # Save the figure as an HTML file
    fig.write_html(os.path.join(folder, 'stats_global.html'))

    plt.close()

    print("Plots saved successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot valid CSV files in a folder.')
    parser.add_argument('folder', type=str, help='The folder containing CSV files.')
    # parser.add_argument('episodesstats', type=str, help='Output CSV file for episodes stats')
    # parser.add_argument('--print_global_events', action='store_true', help='Print episodes and events')
    # parser.add_argument('--print_episode_events', action='store_true', help='Print episodes and events')

    args = parser.parse_args()

    plot_files_in_folder(args.folder)
