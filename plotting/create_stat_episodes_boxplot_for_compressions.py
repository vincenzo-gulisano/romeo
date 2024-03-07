import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def create_boxplot(input_csv, output_folder, statistic_name,aggregation,miny,maxy, continue_episodes_across_ids=False, plot_values_over_episodes=False):
    # Read the input CSV file
    df = pd.read_csv(input_csv)

    # Filter the DataFrame based on the provided statistic
    filtered_df = df[df['stat'] == statistic_name]

    # Get unique 'CCR-Compression' values and sort them in ascending order
    IDs = filtered_df['Agent-ID'].unique()
    positions = list(range(len(IDs)))  # Define positions for x ticks

    # Create boxplot for each unique CCR-Compression value
    plt.figure(figsize=(10, 6))
    for i, compression in enumerate(IDs):
        group_data = filtered_df[filtered_df['Agent-ID'] == compression]
        plt.boxplot(group_data[aggregation], positions=[i], widths=0.5, showmeans=True)

    plt.xlabel('Agent-ID')
    plt.ylabel(f'{aggregation} Values for {statistic_name}')
    plt.xticks(positions, IDs, rotation=45)  # Set x ticks with IDs
    plt.xticks(rotation=45)
    if miny is not None and maxy is not None:
        plt.ylim([miny,maxy])
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(f'{output_folder}/{statistic_name}_{aggregation}_boxplot.pdf')
    plt.close()

    if plot_values_over_episodes:
        # Create continuous plots for each id
        plt.figure(figsize=(10, 6))
        offset=0
        xs=[]
        ys=[]
        for i, compression in enumerate(IDs):
            group_data = filtered_df[filtered_df['Agent-ID'] == compression]
            plt.plot(group_data['episode']-group_data['episode'].iloc[0]+offset,group_data[aggregation],label=compression)
            if continue_episodes_across_ids:
                xs.extend([episode_value - group_data['episode'].iloc[0] + offset for episode_value in group_data['episode']])
                ys.extend([measure_value  for measure_value in group_data[aggregation]])
                offset=offset+group_data['episode'].iloc[-1]+1

        if continue_episodes_across_ids:
            
            #calculate equation for trendline
            z = np.polyfit(xs, ys, 1)
            p = np.poly1d(z)
            plt.plot(xs,p(xs))
            # z = np.polyfit(xs, ys, 5)
            # p = np.poly1d(z)
            # plt.plot(xs,p(xs))

            # If you want a moving average instead
            # window_size = 5  # Choose your window size for the moving average
            # moving_averages = np.convolve(ys, np.ones(window_size)/window_size, mode='same')
            # plt.plot(xs, moving_averages, color='red')

        plt.xlabel('Episode')
        plt.ylabel(f'{aggregation} Values for {statistic_name}')
        plt.legend()
        plt.grid(axis='y')
        plt.tight_layout()
        plt.savefig(f'{output_folder}/{statistic_name}_{aggregation}_episodes.pdf')
        plt.close()

if __name__ == "__main__":
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Create boxplot graphs from CSV data.')

    # Add arguments
    parser.add_argument('input_csv', type=str, help='Path to the input CSV file.')
    parser.add_argument('output_folder', type=str, help='Path to the output folder to save graphs.')
    parser.add_argument('statistic', type=str, help='Value of the statistic for which boxplot is to be created.')

    # Parse the arguments
    args = parser.parse_args()

    # Split the input string on "/"
    statistics = args.statistic.split("/")

    # Process each statistic
    for stat in statistics:
        components = stat.split(",")
        
        # Retrieve statistic_name and aggregation directly
        statistic_name = components[0]
        aggregation = components[1]
        
        # Convert miny and maxy to integers if they are not empty, else set to None
        miny = int(components[2]) if components[2] else None
        maxy = int(components[3]) if components[3] else None
    
        print('Processing statistic_name',statistic_name,'aggregation',aggregation,'miny',miny,'maxy',maxy)

        # Call the function to create boxplot
        create_boxplot(args.input_csv, args.output_folder, statistic_name,aggregation,miny,maxy,continue_episodes_across_ids=True,plot_values_over_episodes=True)
