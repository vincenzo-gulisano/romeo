import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def plot_files_in_folder(folder,episodes,print_global_events,print_episode_events):


    print('Gathering valid CSV files')
    # Get all CSV files with 2 columns and only numerical values
    csv_files = [file for file in os.listdir(folder) if file.endswith('.csv')]
    valid_csv_files = []

    for file in csv_files:
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
    episodes_path = os.path.join(folder, 'episodes.csv')
    episodes_df = pd.read_csv(episodes_path)

    print('Computing the minimum value of the first column among all files...')
    min_value = min(pd.read_csv(file).iloc[:, 0].min() for file in valid_csv_files)
    min_value = min(min_value,episodes_df.iloc[:, 0].min())
    print('...',min_value)

    episodes_df['ts'] -= min_value

    # Plot each valid CSV file
    for file_path in valid_csv_files:
        df = pd.read_csv(file_path)
        x_label = 'Time (s)'
        y_label = os.path.splitext(os.path.basename(file_path))[0]
        
        # Adjust the values by subtracting the minimum value
        df.iloc[:, 0] -= min_value

        # Plotting

        # Set the size of the figure
        fig, ax = plt.subplots(figsize=(40, 15))

        ax.plot(df.iloc[:, 0], df.iloc[:, 1], label=y_label)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        # plt.yscale('log')
        
        # Add vertical lines for each ts in episodes.csv
        if print_global_events:
            for index, row in episodes_df.iterrows():
                ax.axvline(row['ts'], linestyle='--', color='red')
                ax.text(row['ts'], df.iloc[:, 1].max(), f"{row['episode']}: {row['event']}", rotation=90, color='red')

        # ax.legend()
        ax.set_title(f'Plot for {os.path.basename(file_path)}')

        plt.savefig(f"{os.path.splitext(file_path)[0]}.pdf")
        plt.close()

    # Iterate through unique episode values in episodes_df
    for episode_value in episodes_df['episode'].unique():

        if (episode_value in episodes):

            print('Creating detailed graphs for episode',episode_value)
            
            # Create a subfolder for each unique episode value
            episode_folder = os.path.join(folder, str(episode_value))
            os.makedirs(episode_folder, exist_ok=True)

            # Filter episodes_df for the current episode value
            episode_data = episodes_df[episodes_df['episode'] == episode_value]

            csv_files_to_process = ['injectionrate.rate.csv','throughput.count.csv','actions.csv','CPU-agg.average.csv','latency.average.csv','ratio.percent.csv','observedlatency.csv','observedcompression.csv','rewards.csv','cumulativereward.csv']

            # Set the size of the figure
            fig, axs = plt.subplots(len(csv_files_to_process), 1, figsize=(10, 3 * len(csv_files_to_process)))

            # Plot each valid CSV file for the current episode value
            for i, basename in enumerate(csv_files_to_process):

                file_path = next((f for f in valid_csv_files if os.path.basename(f) == basename), None)
    
                df = pd.read_csv(file_path)
                x_label = 'Time (s)'
                y_label = os.path.splitext(os.path.basename(file_path))[0]
                
                # Adjust the values by subtracting the minimum value
                df.iloc[:, 0] -= min_value

                axs[i].set_xlabel(x_label)
                axs[i].set_ylabel(y_label)
                
                # Filter data based on the 'start' and 'stop' columns in episode_data
                for _, episode_entry in episode_data.iterrows():
                    start_time = episode_data[episode_data['event'] == 'start'].iloc[:, 0].values[0]
                    stop_time = episode_data[episode_data['event'] == 'end'].iloc[:, 0].values[0]
                    
                    # print('episode',episode_value,'start',start_time,'end',stop_time)
                    temp_df = df[(df.iloc[:, 0] >= start_time) & (df.iloc[:, 0] <= stop_time)]
                    # moving_avg = temp_df.iloc[:, 1].rolling(window=10).mean()
                    # print('data',temp_df)
                    # Plot only the data between 'start' and 'stop'
                    axs[i].plot(temp_df.iloc[:, 0],
                            temp_df.iloc[:, 1],
                            label=f"{y_label} - Episode {episode_value}", linewidth=0.5)
                    # axs[i].plot(temp_df.iloc[:, 0], moving_avg, label=f"{y_label} - Episode {episode_value} (Moving Avg)", linewidth=1)

                # Add vertical lines for each ts in episodes.csv
                if print_episode_events:
                    for _, row in episode_data.iterrows():
                        axs[i].axvline(row['ts'], linestyle='--', color='red')
                        axs[i].text(row['ts'], temp_df.iloc[:, 1].max(), f"{row['episode']}: {row['event']}", rotation=90, color='red')

                # ax.legend()
                # axs[i].set_title(f'Plot for {os.path.basename(file_path)} - Episode {episode_value}')

            # plt.savefig(os.path.join(episode_folder, f"episode_{episode_value}.pdf"))
            plt.savefig(os.path.join(episode_folder, f"episode_{episode_value}.png"))
            plt.close()
            
    print("Plots saved successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot valid CSV files in a folder.')
    parser.add_argument('folder', type=str, help='The folder containing CSV files.')
    parser.add_argument('episodes', type=str, help='Episodes for which detailed stats should be created')
    parser.add_argument('--print_global_events', action='store_true', help='Print episodes and events')
    parser.add_argument('--print_episode_events', action='store_true', help='Print episodes and events')

    args = parser.parse_args()

        # Split the string into a list of strings
    episodes_string = args.episodes.split(',')

    # Convert each string value to an integer
    episodes = [int(value) for value in episodes_string]

    plot_files_in_folder(args.folder,episodes,args.print_global_events,args.print_episode_events)
