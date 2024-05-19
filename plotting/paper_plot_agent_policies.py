import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.tools as tls

def plot_graphs(rate_file_path,agent_data,output_pdf):
   
    # This config are for LinearRoad
    latency_y_scale = 'log'
    
    # Specify font size
    text_fontsize = 8  # Example font size
    
    # if len(unique_baselines) > len(markers):
    #     print("Warning: Not enough unique markers defined for the number of baselines.")
    
    max_latency=1

    # Read the first and second columns from the CSV
    dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
    dfrate.columns = ['x', 'y']

    # Now, df['x'] and df['y'] are your x_data and y_data
    x_data = dfrate['x']
    y_data = dfrate['y']

    plt.rcParams.update({'font.size': 8})  # Set global font size to 10

    # Create a figure and a set of subplots, now with 4 rows
    fig, axs = plt.subplots(5, 1, figsize=(5, 6), gridspec_kw={'hspace': 0, 'height_ratios': [1, 0.5, 1, 1, 1]})

    # Plot random data on the new top axes (axs[0])
    axs[0].plot(x_data - dfrate['x'].min(), y_data, linestyle='-', color='blue')
    axs[0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[0].set_ylabel(r'Input rate ($10^3$ t/s)', fontsize=text_fontsize)
    axs[0].set_xlabel('Event Time (s)', fontsize=text_fontsize)

    axs[2].set_ylabel('Compression (%)', fontsize=text_fontsize)
    axs[2].set_xticks([])
    axs[2].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    
    axs[3].set_ylabel('Latency (s)', fontsize=text_fontsize)
    axs[3].set_xticks([])
    
    axs[4].set_ylabel('CPU (%)', fontsize=text_fontsize)
    axs[4].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    
    axs[1].set_visible(False)
    
    # Now the part about the RL agent
    # Read the baselines_data.csv file
    baseline_file_path = os.path.join(agent_data)
    baseline_df = pd.read_csv(baseline_file_path)

    # Convert the 'baseline' column to text (object) type
    baseline_df['baseline'] = baseline_df['baseline'].astype(str)

    # The values represent: initial size, fine size, initial opacity, final opacity, color, prob. of selection
    agent_plots = {
        'weaob_linear': [1,1,1,1,'red',1],
        'eaob_linear': [1,1,1,1,'orange',1],
        'aob_linear': [1,1,1,1,'blue',1],
        'weaaw_linear': [1,1,1,1,'green',1],
        'weaob_synthetic': [1,1,1,1,'red',1],
        'eaob_synthetic': [1,1,1,1,'orange',1],
        'aob_synthetic': [1,1,1,1,'blue',1],
        'weaaw_synthetic': [1,1,1,1,'green',1],
        '13.1': [1,5,0.1,0.8,'red',1],
        '13.2': [1,5,0.1,0.8,'green',1],
        '12.1': [1,5,0.1,0.8,'red',1],
        '12.2': [5,10,0.1,0.8,'green',1]}
       
    given_order = ['weaob_linear','eaob_linear','weaaw_linear']  # The desired order for baselines
    given_order = ['weaob_synthetic','eaob_synthetic','weaaw_synthetic']  # The desired order for baselines
    
    # Create a set for faster membership tests
    unique_baselines_set = set(baseline_df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

    for i, baseline in enumerate(unique_baselines):
        subset = baseline_df[baseline_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime_start'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    axs[2].plot(row['eventtime_start']- dfrate['x'].min(), row['mean_ratio']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    axs[2].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[2].set_ylim([-0.1,1.1])
    
    for i, baseline in enumerate(unique_baselines):
        subset = baseline_df[baseline_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime_start'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    axs[3].plot(row['eventtime_start']- dfrate['x'].min(), row['latency_mean']/1000, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    axs[3].axhline(y=max_latency, color='r', linestyle='--')  # Horizontal line at max_latency
    axs[3].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[3].set_ylim([0.008,8])
    axs[3].set_yscale(latency_y_scale)

    for i, baseline in enumerate(unique_baselines):
        subset = baseline_df[baseline_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime_start'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    axs[4].plot(row['eventtime_start']- dfrate['x'].min(), row['cpu_mean']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    axs[4].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[4].set_xlabel('Event Time (s)', fontsize=text_fontsize)  # Only the last subplot needs the x-axis label
    axs[4].set_ylim([-0.1,1.1])
    
    # Adjust layout
    fig.tight_layout()
    
    # Save the figure
    plt.savefig(output_pdf)
    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate plots from baselines_data.csv.')
    parser.add_argument('rate_file_path', type=str, help='Input file containing per second input rate of the input data.')
    parser.add_argument('agent_data', type=str, help='Input file containing the RL agent stats.')
    parser.add_argument('output_pdf', type=str, help='Output PDF file.')

    args = parser.parse_args()
    
    plot_graphs(args.rate_file_path,args.agent_data,args.output_pdf)
