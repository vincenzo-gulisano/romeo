import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.tools as tls

def plot_graphs(base_folder,rate_file_path,agent_data,output_pdf,probs,probs_episod):
    # Read the baselines_data.csv file
    file_path = os.path.join(base_folder, 'baselines_data.csv')
    df = pd.read_csv(file_path)
    
    # Define marker styles for different baselines to ensure uniqueness
    markers = ['s', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'D', 'd', '|', '_']
    
    given_order = ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1', '0', 'r']  # The desired order for baselines
    xtick_labels = [r'$D1.0$',r'$D0.9$',r'$D0.8$',r'$D0.7$',r'$D0.6$',r'$D0.5$',r'$D0.4$',r'$D0.3$',r'$D0.2$', r'$D0.1$', r'$D0.0$', r'$D^*$']
    # Create a set for faster membership tests
    unique_baselines_set = set(df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

    # This config are for LinearRoad
    boundaries = [0.5,7.5,10.5,11.5]
    boundary_text = ['safe','worth','unsafe']
    latency_y_scale = 'log'
    # This config are for Synthetic
    boundaries = [0.5,4.5,7.5,11.5]
    boundary_text = ['safe','worth','unsafe']
    latency_y_scale = 'log'
    
    
    # Specify color and font size
    text_color = 'green'  # Example color
    text_fontsize = 8  # Example font size
    
    if len(unique_baselines) > len(markers):
        print("Warning: Not enough unique markers defined for the number of baselines.")
    
    max_latency=1

    # Read the first and second columns from the CSV
    dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
    dfrate.columns = ['x', 'y']

    # Adjust x_data to start at 0
    # dfrate['x'] = dfrate['x'] - dfrate['x'].min()

    # Now, df['x'] and df['y'] are your x_data and y_data
    x_data = dfrate['x']
    y_data = dfrate['y']

    plt.rcParams.update({'font.size': 8})  # Set global font size to 10

    # Create a figure and a set of subplots, now with 4 rows
    fig, axs = plt.subplots(5, 2, figsize=(10, 6), gridspec_kw={'hspace': 0, 'height_ratios': [1, 0.5, 1, 1, 1]})

    # Plot random data on the new top axes (axs[0])
    axs[0,0].plot(x_data - dfrate['x'].min(), y_data, linestyle='-', color='blue')
    axs[0,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[0,0].set_ylabel(r'Input rate ($10^3$ t/s)', fontsize=text_fontsize)
    axs[0,1].set_xlabel('Time (s)', fontsize=text_fontsize)

    # Adjust the indices for the other axes since we added a new one at the top
    # mean_ratio, divided by 100
    data_mean_ratio = [df[df['baseline'] == baseline]['mean_ratio'].dropna() / 100 for baseline in unique_baselines]
    axs[2,1].boxplot(data_mean_ratio, labels=unique_baselines)
    axs[2,0].set_ylabel('Compression (%)', fontsize=text_fontsize)
    # Set specific tick positions
    axs[2,1].set_ylim([-0.1,1.1])
    axs[2,0].set_xticks([])
    axs[2,1].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    axs[2,1].set_yticklabels(['0', '', '', '', '', '1'])
    # Enable the grid
    axs[2,0].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    axs[2,1].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)

    # latency, divided by 1000
    data_latency = [df[df['baseline'] == baseline]['latency'].dropna() / 1000 for baseline in unique_baselines]
    axs[3,1].boxplot(data_latency, labels=unique_baselines)
    axs[3,0].set_ylabel('Latency (s)', fontsize=text_fontsize)
    axs[3,1].set_ylim([0.008,8])
    axs[3,0].set_xticks([])
    axs[3,1].set_yscale(latency_y_scale)
    axs[3,1].axhline(y=max_latency, color='r', linestyle='--')  # Horizontal line at max_latency
    # Add text for threshold latency
    axs[3,1].text(0.5, max_latency*1.05, 'Threshold latency', color='red', verticalalignment='bottom', horizontalalignment='left', fontsize=8, transform=axs[3,1].transData)
    # axs[3].grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, color='gray')  # Enable y-axis grid

    # cpu, divided by 100
    data_cpu = [df[df['baseline'] == baseline]['cpu'].dropna() / 100 for baseline in unique_baselines]
    axs[4,1].boxplot(data_cpu, labels=unique_baselines)
    axs[4,0].set_ylabel('CPU (%)', fontsize=text_fontsize)
    axs[4,1].set_xlabel('Baseline', fontsize=text_fontsize)  # Only the last subplot needs the x-axis label
    axs[4,1].set_xticklabels(xtick_labels, fontsize=text_fontsize)
    axs[4,1].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    axs[4,1].set_yticklabels(['0', '', '', '', '', '1'])
    axs[4,1].set_ylim([-0.1,1.1])
    # Enable the grid
    axs[4,0].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    axs[4,1].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    
    # Add vertical lines in all axes for each X value in boundaries (adjusting index for axs)
    for ax in axs[2:,1]:
        for boundary in boundaries:
            ax.axvline(x=boundary, color='g', linestyle='--')

    # Add text on top of the second axes (previously first) in between consecutive pairs of boundaries
    for i, text in enumerate(boundary_text):
        # Calculate the position to place the text (middle between boundaries)
        x_pos = (boundaries[i] + boundaries[i + 1]) / 2
        # Place the text at the calculated position, with a slight offset upwards
        axs[2,1].text(x_pos, 1.01, text, transform=axs[2,1].get_xaxis_transform(), ha='center', va='bottom', color=text_color, fontsize=text_fontsize)

    # Disable y-axis labels and tick marks on the right-side axes
    for ax in axs[1:, 1]:  # Loop through second column axes
        ax.yaxis.set_tick_params(labelleft=False)  # Disable y-axis tick labels
        ax.set_ylabel('')  # Clear y-axis label
    axs[1,0].set_visible(False)
    axs[1,1].set_visible(False)
    
    # Now the part about the RL agent
    # Read the baselines_data.csv file
    baseline_file_path = os.path.join(agent_data)
    baseline_df = pd.read_csv(baseline_file_path)

    # Convert the 'baseline' column to text (object) type
    baseline_df['baseline'] = baseline_df['baseline'].astype(str)

    # The values represent: initial size, fine size, initial opacity, final opacity, color, prob. of selection
    agent_plots = {
        'weaaw_linear': [0.5,10,0.4,0.8,'red',1],
        'weaaw_synthetic': [0.5,10,0.4,0.8,'red',1],
        '13.1': [1,5,0.1,0.8,'red',1],
        '13.2': [1,5,0.1,0.8,'green',1],
        '12.1': [1,5,0.1,0.8,'red',1],
        '12.2': [5,10,0.1,0.8,'green',1]}
       
    given_order = ['weaaw_linear']  # The desired order for baselines
    given_order = ['weaaw_synthetic']  # The desired order for baselines
    
    # Create a set for faster membership tests
    unique_baselines_set = set(baseline_df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

    for i, baseline in enumerate(unique_baselines):
        subset = baseline_df[baseline_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    axs[2,0].plot(row['eventtime']- dfrate['x'].min(), row['mean_ratio']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    axs[2,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[2,0].set_ylim([-0.1,1.1])
    
    for i, baseline in enumerate(unique_baselines):
        subset = baseline_df[baseline_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    axs[3,0].plot(row['eventtime']- dfrate['x'].min(), row['latency']/1000, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    axs[3,0].axhline(y=max_latency, color='r', linestyle='--')  # Horizontal line at max_latency
    axs[3,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[3,0].set_ylim([0.008,8])
    axs[3,0].set_yscale(latency_y_scale)

    for i, baseline in enumerate(unique_baselines):
        subset = baseline_df[baseline_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    axs[4,0].plot(row['eventtime']- dfrate['x'].min(), row['cpu']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    axs[4,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[4,0].set_xlabel('Event Time (s)', fontsize=text_fontsize)  # Only the last subplot needs the x-axis label
    axs[4,0].set_ylim([-0.1,1.1])
    
    # Now plotting probabilities
    # Load the data
    df_probs = pd.read_csv(probs)
    # Group the dataframe by episode
    grouped_probs = df_probs.groupby('Episode')

    # Ensure there is data for episode 100 before proceeding
    for episode, data in grouped_probs:
        if episode == probs_episod:
            
            # Sort the data by Action Time to ensure plots are in order
            data.sort_values('Action Time', inplace=True)

            # Adjust Action Time to start at 0
            data['Action Time'] -= data['Action Time'].iloc[0]

            # Plotting
            axs[0,1].plot(data['Action Time'], data['Prob1'], label='Compress')
            axs[0,1].plot(data['Action Time'], data['Prob2'], label='Stay')
            axs[0,1].plot(data['Action Time'], data['Prob3'], label='Decompress')

            # Labeling
            axs[0,1].set_xlabel('Wallclock Time (s)')
            axs[0,1].set_ylabel('Prob.')
            axs[0,1].set_ylim([0,1])
            # plt.title('Episode 100: Action Time vs Probabilities')
            axs[0,1].legend()

            axs[0,1].yaxis.tick_right()  # Move ticks to the right
            axs[0,1].yaxis.set_label_position('right')  # Move the y-axis label to the right

            # Show the plot

    # Adjust layout
    fig.tight_layout()
    
    # Save the figure
    plt.savefig(output_pdf)
    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate plots from baselines_data.csv.')
    parser.add_argument('base_folder', type=str, help='Input folder containing baselines_data.csv.')
    parser.add_argument('rate_file_path', type=str, help='Input file containing per second input rate of the input data.')
    parser.add_argument('agent_data', type=str, help='Input file containing the RL agent stats.')
    parser.add_argument('output_pdf', type=str, help='Output PDF file.')
    parser.add_argument('probs', type=str, help='CSV with the probabilities')
    parser.add_argument('probs_episod', type=int, help='Episode of which to plot probabilities')

    args = parser.parse_args()
    
    plot_graphs(args.base_folder,args.rate_file_path,args.agent_data,args.output_pdf,args.probs,args.probs_episod)
