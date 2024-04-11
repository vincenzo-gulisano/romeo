import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.tools as tls

def set_share_axes(axs, target=None, sharex=False, sharey=False):
    if target is None:
        target = axs.flat[0]
    # Manage share using grouper objects
    for ax in axs.flat:
        if sharex:
            target._shared_axes['x'].join(target, ax)
        if sharey:
            target._shared_axes['y'].join(target, ax)
    # Turn off x tick labels and offset text for all but the bottom row
    if sharex and axs.ndim > 1:
        for ax in axs[:-1,:].flat:
            ax.xaxis.set_tick_params(which='both', labelbottom=False, labeltop=False)
            ax.xaxis.offsetText.set_visible(False)
    # Turn off y tick labels and offset text for all but the left most column
    if sharey and axs.ndim > 1:
        for ax in axs[:,1:].flat:
            ax.yaxis.set_tick_params(which='both', labelleft=False, labelright=False)
            ax.yaxis.offsetText.set_visible(False)

def plot_graphs(base_folder):
    # Read the baselines_data.csv file
    file_path = os.path.join(base_folder, 'baselines_data.csv')
    df = pd.read_csv(file_path)
    
    # Define marker styles for different baselines to ensure uniqueness
    markers = ['s', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'D', 'd', '|', '_']
    
    given_order = ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1', '0', 'r']  # The desired order for baselines
    xtick_labels = ['D1.0', 'D0.9', 'D0.8', 'D0.7', 'D0.6', 'D0.5', 'D0.4', 'D0.3', 'D0.2', 'D0.1', 'D0.0', r'D^*']
    # Create a set for faster membership tests
    unique_baselines_set = set(df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

    boundaries = [0.5,7.5,10.5,11.5]
    boundary_text = ['safe','worth','unsafe']
    # Specify color and font size
    text_color = 'green'  # Example color
    text_fontsize = 8  # Example font size
    
    if len(unique_baselines) > len(markers):
        print("Warning: Not enough unique markers defined for the number of baselines.")
    
    max_latency=1

    # Generate some random data for the new top axes
    x_data = np.arange(len(unique_baselines))
    y_data = np.random.rand(len(unique_baselines))

    # Create a figure and a set of subplots, now with 4 rows
    fig, axs = plt.subplots(5, 1, figsize=(5, 6),gridspec_kw={'hspace': 0,'height_ratios': [1, 0.5, 1, 1, 1]})

    # Plot random data on the new top axes (axs[0])
    axs[0].plot(x_data, y_data, linestyle='-', color='blue')
    axs[0].set_ylabel(r'Input rate (10^3 t/s)')
    axs[0].set_xlabel('Time (s)')

    # Adjust the indices for the other axes since we added a new one at the top
    # mean_ratio, divided by 100
    data_mean_ratio = [df[df['baseline'] == baseline]['mean_ratio'].dropna() / 100 for baseline in unique_baselines]
    axs[2].boxplot(data_mean_ratio, labels=unique_baselines)
    axs[2].set_ylabel('Compression (%)')
    axs[2].set_yticks([0, 1])

    # latency, divided by 1000
    data_latency = [df[df['baseline'] == baseline]['latency'].dropna() / 1000 for baseline in unique_baselines]
    axs[3].boxplot(data_latency, labels=unique_baselines)
    axs[3].set_ylabel('Latency (s)')
    axs[3].axhline(y=max_latency, color='r', linestyle='--')  # Horizontal line at max_latency
    # Add text for threshold latency
    axs[3].text(0.5, max_latency*1.05, 'Threshold latency', color='red', verticalalignment='bottom', horizontalalignment='left', fontsize=8, transform=axs[3].transData)

    # cpu, divided by 100
    data_cpu = [df[df['baseline'] == baseline]['cpu'].dropna() / 100 for baseline in unique_baselines]
    axs[4].boxplot(data_cpu, labels=unique_baselines)
    axs[4].set_ylabel('CPU (%)')
    axs[4].set_yticks([0, 1])
    axs[4].set_xlabel('Baseline')  # Only the last subplot needs the x-axis label

    # Add vertical lines in all axes for each X value in boundaries (adjusting index for axs)
    for ax in axs[2:]:
        for boundary in boundaries:
            ax.axvline(x=boundary, color='g', linestyle='--')

    # Add text on top of the second axes (previously first) in between consecutive pairs of boundaries
    for i, text in enumerate(boundary_text):
        # Calculate the position to place the text (middle between boundaries)
        x_pos = (boundaries[i] + boundaries[i + 1]) / 2
        # Place the text at the calculated position, with a slight offset upwards
        axs[2].text(x_pos, 1.01, text, transform=axs[2].get_xaxis_transform(), ha='center', va='bottom', color=text_color, fontsize=text_fontsize)

    # set_share_axes(axs[1:], sharex=True)
    axs[1].set_visible(False)
    
    # Adjust layout
    fig.tight_layout()
    
    # Save the figure
    plt.savefig(os.path.join(base_folder, 'baselines.pdf'))
    plt.close()

    # # Create a figure and a set of subplots
    # fig, axs = plt.subplots(3, 1, figsize=(5, 5), sharex=True, gridspec_kw={'hspace': 0})

    # # mean_ratio, divided by 100
    # data_mean_ratio = [df[df['baseline'] == baseline]['mean_ratio'].dropna() / 100 for baseline in unique_baselines]
    # axs[0].boxplot(data_mean_ratio, labels=unique_baselines)
    # axs[0].set_ylabel('Compression (%)')
    # axs[0].set_yticks([0, 1])

    # # latency, divided by 1000
    # data_latency = [df[df['baseline'] == baseline]['latency'].dropna() / 1000 for baseline in unique_baselines]
    # axs[1].boxplot(data_latency, labels=unique_baselines)
    # axs[1].set_ylabel('Latency (s)')
    # axs[1].axhline(y=max_latency, color='r', linestyle='--')  # Horizontal line at max_latency
    # # Add text
    # axs[1].text(0.5, max_latency*1.05, 'Threshold latency', color='red', verticalalignment='bottom', horizontalalignment='left', fontsize=8, transform=axs[1].transData)

    # # cpu, divided by 100
    # data_cpu = [df[df['baseline'] == baseline]['cpu'].dropna() / 100 for baseline in unique_baselines]
    # axs[2].boxplot(data_cpu, labels=unique_baselines)
    # axs[2].set_ylabel('CPU (%)')
    # axs[2].set_yticks([0, 1])
    # axs[2].set_xlabel('Baseline')  # Only the last subplot needs the x-axis label
    # # axs[2].set_xticklabels(xtick_labels)

    # for ax in axs:
    #     for boundary in boundaries:
    #         ax.axvline(x=boundary, color='g', linestyle='--')
                
    # # Add text on top of the first axes in between consecutive pairs of boundaries
    # for i, text in enumerate(boundary_text):
    #     # Calculate the position to place the text (middle between boundaries)
    #     x_pos = (boundaries[i] + boundaries[i + 1]) / 2
    #     # Place the text at the calculated position, with a slight offset upwards (y=1.05, in axes fraction coordinates)
    #     axs[0].text(x_pos, 1.01, text, transform=axs[0].get_xaxis_transform(), ha='center', va='bottom', color=text_color, fontsize=text_fontsize)

    # # Adjust layout to remove vertical space between axes
    # fig.tight_layout(pad=0.4, h_pad=0.0, w_pad=0.0)

    # # Save the figure
    # plt.savefig(os.path.join(base_folder, 'baselines.pdf'))
    # plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate plots from baselines_data.csv.')
    parser.add_argument('base_folder', type=str, help='Input folder containing baselines_data.csv.')
    
    args = parser.parse_args()
    
    plot_graphs(args.base_folder)
