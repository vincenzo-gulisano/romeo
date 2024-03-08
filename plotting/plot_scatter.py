import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_data(input_folder, output_pdf, stat_X, stat_Y, aggregation_X, aggregation_Y, min_size=50, max_size=50, min_opacity=1.0, max_opacity=1.0):
    # Construct the file path and read the CSV
    file_path = f'{input_folder}/compressionandepisodesstats.csv'
    df = pd.read_csv(file_path)
    
    # Filter for specified stats
    X_df = df[df['stat'] == stat_X]
    Y_df = df[df['stat'] == stat_Y]
    
    # Rename 'stat' column to 'statX' in X_df and to 'statY' in Y_df
    X_df = X_df.rename(columns={aggregation_X: 'statX'})
    Y_df = Y_df.rename(columns={aggregation_Y: 'statY'})

    # Merge dataframes on 'episode'
    merged_df = pd.merge(X_df[['episode', 'statX']], Y_df[['episode', 'statY']], on='episode', suffixes=('_x', '_y'))
    
    # Sort by 'episode' to determine size and opacity dynamically
    merged_df.sort_values('episode', inplace=True)
    
    # print(merged_df)

    # Determine sizes and opacities based on episode values
    num_points = len(merged_df)
    sizes = np.geomspace(start=min_size, stop=max_size, num=num_points)
    opacities = np.geomspace(start=min_opacity, stop=max_opacity, num=num_points)
    
    # Plotting
    plt.figure(figsize=(10, 6))
    for i, row in merged_df.iterrows():
        # print(row)
        plt.scatter(row['statX'], row['statY'], s=sizes[i], alpha=opacities[i], color='b', edgecolors='none')
    
    plt.xlabel(stat_X+' '+aggregation_X)
    plt.ylabel(stat_Y+' '+aggregation_Y)
    # plt.title('Injection Rate vs. Cumulative Reward by Episode')
    plt.grid(True)
    
    # Save the plot to the specified PDF file
    plt.savefig(output_pdf)
    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot data from compressionandepisodesstats.csv.')
    parser.add_argument('input_folder', type=str, help='Input folder containing the CSV file.')
    parser.add_argument('output_pdf', type=str, help='Output PDF file for the plot.')
    parser.add_argument('--stat_X', type=str, default='injectionrate.rate', help='Stat name for injection rate.')
    parser.add_argument('--stat_Y', type=str, default='rewards', help='Stat name for rewards.')
    parser.add_argument('--aggregation_X', type=str, default='mean', help='Column name for mean values.')
    parser.add_argument('--aggregation_Y', type=str, default='sum', help='Column name for sum values.')
    
    args = parser.parse_args()
    
    plot_data(args.input_folder, args.output_pdf, args.stat_X, args.stat_Y, args.aggregation_X, args.aggregation_Y)
