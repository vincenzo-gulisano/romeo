import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import plotly.tools as tls

def plot_files_in_folder(folder,episodesstatsfile,makeplots,dumpdata,print_global_events,print_episode_events):

    # Font size used in the per-episode plots
    fs = 6

    print('Make episode plots?',makeplots)
    print('Dump data?',dumpdata)

    valid_csv_files = []

    csv_files_to_process = ['injectionrate.rate.csv','throughput.count.csv','actions.csv','CPU-agg.average.csv','latency.average.csv','ratio.percent.csv','rewards.csv','cumulativereward.csv','latency.violations.csv','eventtime.max.csv']

    for file in csv_files_to_process:
        file_path = os.path.join(folder, file)
        print(file_path)
        try:
            df = pd.read_csv(file_path, dtype={0: 'int64', 1: 'float64'}, header=None)
            # Check if the CSV file has exactly 2 columns and contains numerical values
            if len(df.columns) == 2 and df.applymap(lambda x: isinstance(x, (int, float))).all().all():
                # print(file_path,'is a valid file path')
                valid_csv_files.append(file_path)
            else:
                print(file_path,'is not a valid file path')
                print('len(df.columns) == 2',len(df.columns) == 2)

                # Check if all entries are int or float
                is_valid_data = df.applymap(lambda x: isinstance(x, (int, float)))

                print('All values are int or float:', is_valid_data.all(axis=None))

                # Find rows that contain invalid (non-int, non-float) data
                invalid_entries = df[~is_valid_data]

                if not invalid_entries.empty:
                    # Print rows and details of invalid entries
                    for index, row in invalid_entries.iterrows():
                        for col in row.index:
                            value = row[col]
                            if not isinstance(value, (int, float)):
                                print(f"Row {index}, Column '{col}' has invalid type: {type(value).__name__}, value: {value}")
                else:
                    print('No invalid entries found.')
        except pd.errors.EmptyDataError:
            pass  # Handle empty CSV files

    if not valid_csv_files:
        print("No valid CSV files found in the folder.")
        return

    # Read episodes.csv
    episodes_path = os.path.join(folder, 'episodes.csv')
    episodes_df = pd.read_csv(episodes_path)

    highest_episode = episodes_df['episode'].max()

    print('Computing the minimum value of the first column among all files...')
    min_value = min(pd.read_csv(file).iloc[:, 0].min() for file in valid_csv_files)
    print('min values from each file: ',[pd.read_csv(file).iloc[:, 0].min() for file in valid_csv_files])
    min_value = min(min_value,episodes_df.iloc[:, 0].min())
    print('...',min_value)

    episodes_df['ts'] -= min_value

    # Set the size of the figure
    fig1, ax1 = plt.subplots(len(valid_csv_files),1,figsize=(highest_episode, len(valid_csv_files)*2), sharex=True)

    # Plot each valid CSV file
    for i,file_path in enumerate(valid_csv_files):
        df = pd.read_csv(file_path)
        x_label = 'Time (s)'
        y_label = os.path.splitext(os.path.basename(file_path))[0]
        
        # Adjust the values by subtracting the minimum value
        df.iloc[:, 0] -= min_value

        # Plotting for fig 1
        ax1[i].plot(df.iloc[:, 0], df.iloc[:, 1], label=y_label)
        ax1[i].set_xlabel(x_label)
        ax1[i].set_ylabel(y_label)
        # plt.yscale('log')
        
        # Add vertical lines for each ts in episodes.csv
        if print_global_events:
            for index, row in episodes_df.iterrows():
                if row['event']=='start' or row['event']=='end':
                    ax1[i].axvline(row['ts'], linestyle='--', color='red')
                    ax1[i].text(row['ts'], (df.iloc[:, 1].min()+df.iloc[:, 1].max())/2, f"{row['episode']}: {row['event']}", rotation=90, color='red')

        if i==0:
            ax1[i].set_title(f'Plot for {os.path.basename(file_path)}')

    # Create a subfolder for each unique episode value
    episode_folder = os.path.join(folder, 'eps')
    os.makedirs(episode_folder, exist_ok=True)

    # Define the consistent column order
    column_order = ['episode', 'stat', 'q1', 'q2', 'q3', 'sum', 'mean']


    # Iterate through unique episode values in episodes_df
    for episode_value in episodes_df['episode'].unique():

        # Set the size of the figure
        if makeplots:
            fig2, ax2 = plt.subplots(len(valid_csv_files),1,figsize=(4, len(valid_csv_files)), sharex=True)
        somethingPlotted = False

        # Plot each valid CSV file
        for i,file_path in enumerate(valid_csv_files):
            
            df = pd.read_csv(file_path)
            x_label = 'Time (s)'
            y_label = os.path.splitext(os.path.basename(file_path))[0]
            

            # Adjust the values by subtracting the minimum value
            df.iloc[:, 0] -= min_value

            # Initialize an empty list to store statistics
            stats = []

            # Filter episodes_df for the current episode value
            episode_data = episodes_df[episodes_df['episode'] == episode_value]

            # Check if both 'start' and 'end' events exist for this episode
            has_start = (episode_data['event'] == 'start').any()
            has_end = (episode_data['event'] == 'end').any()

            if has_start and has_end:

                somethingPlotted = True

                # Count the number of entries that start with 'action' in the 'event' column
                action_count = episode_data[episode_data['event'].str.startswith('action')].shape[0]

                # Filter data based on the 'start' and 'stop' columns in episode_data
                # for _, episode_entry in episode_data.iterrows(): ### COMMENTED THIS BECAUSE I THINK IT IS NOT NEEDED
                start_time = episode_data[episode_data['event'] == 'start'].iloc[:, 0].values[0] + 5
                stop_time = episode_data[episode_data['event'] == 'end'].iloc[:, 0].values[0]
            
                # Append the steps and duration stat only for the first csv, no need to append it every time
                if i == 0:
                    stats.append({'episode': episode_value, 'stat': 'steps', 'q1': action_count, 'q2': action_count,  'sum': action_count,  'q3': action_count,  'mean': action_count})
                    stats.append({'episode': episode_value, 'stat': 'duration', 'q1': stop_time-start_time, 'q2': stop_time-start_time,  'sum': stop_time-start_time,  'q3': stop_time-start_time, 'mean': stop_time-start_time})

                # print('episode',episode_value,'start',start_time,'end',stop_time)
                temp_df = df[(df.iloc[:, 0] >= start_time) & (df.iloc[:, 0] <= stop_time)]
                filtered_df = temp_df[temp_df.iloc[:, 1] != -1]

                # Dump data
                if dumpdata and (y_label == 'CPU-agg.average' or y_label == 'latency.average'):
                    # Create a DataFrame for saving to CSV
                    csv_data = pd.DataFrame({'timestamp': filtered_df.iloc[:, 0]-start_time, 'value': filtered_df.iloc[:, 1]})
                    output_csv_path = os.path.join(episode_folder, f'{y_label}.{episode_value:03}.csv')  # Customize the naming if needed
                    csv_data.to_csv(output_csv_path, index=False)
                    print(f"Saved plot data to {output_csv_path}")
                    
                # Plot
                if makeplots:
                    ax2[i].plot(filtered_df.iloc[:, 0]-start_time,filtered_df.iloc[:, 1])
                    y_label = y_label + f' {len(temp_df)}'
                    ax2[i].set_xlabel(x_label, fontsize=fs)
                    ax2[i].set_ylabel(y_label, fontsize=fs)
                    ax2[i].tick_params(axis='both', labelsize=fs)   
                
                
                # Filter out -1 values
                filtered_values = temp_df.iloc[:, 1][temp_df.iloc[:, 1] != -1]

                # Append episode statistics to the list, excluding -1 from the calculations
                # notice min and max are first and third quartile, respectively!
                stats.append({
                    'episode': episode_value,
                    'stat': os.path.splitext(os.path.basename(file_path))[0],
                    'q1': filtered_values.quantile(0.25) if not filtered_values.empty else np.nan,
                    'q2': filtered_values.quantile(0.5) if not filtered_values.empty else np.nan,
                    'sum': np.sum(filtered_values) if not filtered_values.empty else np.nan,
                    'q3': filtered_values.quantile(0.75) if not filtered_values.empty else np.nan,
                    'mean': filtered_values.mean() if not filtered_values.empty else np.nan
                })

                # Convert the list of dictionaries to a DataFrame
                stats_df = pd.DataFrame(stats)

                # Append the DataFrame to the output CSV file
                stats_df.to_csv(episodesstatsfile, mode='a', index=False, header=not os.path.exists(episodesstatsfile), columns=column_order)


        if makeplots and somethingPlotted:
            fig2.tight_layout()
            # Ensure subplots are close to each other and adjust left and right margins
            fig2.subplots_adjust(hspace=0)
            fig2.savefig(os.path.join(episode_folder, f'episode{episode_value:03}.pdf'))
            plt.close()

        
    fig1.tight_layout()
        # Ensure subplots are close to each other and adjust left and right margins
    fig1.subplots_adjust(hspace=0, left=0.07, right=0.93)
    fig1.savefig(os.path.join(folder, 'stats_global.pdf'))

    # Convert to Plotly figure
    fig1 = tls.mpl_to_plotly(plt.gcf())

    # Save the figure as an HTML file
    fig1.write_html(os.path.join(folder, 'stats_global.html'))

    plt.close()

    print("Plots saved successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot valid CSV files in a folder.')
    parser.add_argument('folder', type=str, help='The folder containing CSV files.')
    parser.add_argument('episodesstats', type=str, help='Output CSV file for episodes stats')
    parser.add_argument('--makeplots', action='store_true', help='Whether or not to create plots')
    parser.add_argument('--print_global_events', action='store_true', help='Print episodes and events')
    parser.add_argument('--print_episode_events', action='store_true', help='Print episodes and events')
    parser.add_argument('--dumpdata', action='store_true', help='Whether or not to dump data')

    args = parser.parse_args()
    if args.makeplots:
        print("Making plots because makeplots is True")
    else:
        print("Not making plots because makeplots is False")
    if args.dumpdata:
        print("Dumping CPU and latency data")
    else:
        print("Not dumping CPU and latency data")
    plot_files_in_folder(args.folder,args.episodesstats,args.makeplots,args.dumpdata,args.print_global_events,args.print_episode_events)
