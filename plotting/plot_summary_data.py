import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.tools as tls

def plot_graphs(base_folder):
    # Read the baselines_data.csv file
    file_path = os.path.join(base_folder, 'baselines_data.csv')
    df = pd.read_csv(file_path)
    
    # Define marker styles for different baselines to ensure uniqueness
    markers = ['s', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'D', 'd', '|', '_']
    
    min_size=50
    max_size=200
    min_opacity=0.1
    max_opacity=0.8

    agent_plots = {
        'agent-1-100': [1,50,0.1,1,'red'],
        'agent-101-300': [1,50,0.1,1,'green']}
       
    # given_order = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'r', 'rl']  # The desired order for baselines
    given_order = ['agent-101-300']  # The desired order for baselines
    # given_order = ['0', '1', '2', '3', '6', '10', 'r']  # The desired order for baselines
    # given_order = ['0', '1', '2', '3', '6', '10', 'r', 'rl','rl2']  # The desired order for baselines

    # Create a set for faster membership tests
    unique_baselines_set = set(df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

    if len(unique_baselines) > len(markers):
        print("Warning: Not enough unique markers defined for the number of baselines.")
    
    # # Plot 1: eventtime vs cum_reward (this is split in 2!)
    # fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6), 
    #                            gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.05})

    # # Assume df, unique_baselines, and markers are defined earlier in your script

    # for i, baseline in enumerate(unique_baselines):
    #     subset = df[df['baseline'] == baseline].sort_values(by='eventtime')

    #     if baseline in agent_plots:
    #         # Determine sizes and opacities based on episode values
    #         num_points = len(subset['eventtime'])
    #         sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
    #         opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
    #         for j, (index, row) in enumerate(subset.iterrows()):
    #             ax1.scatter(row['eventtime'], row['cum_reward'], s=sizes[j],  edgecolors='none', color=agent_plots[baseline][4])
    #             ax2.scatter(row['eventtime'], row['cum_reward'], s=sizes[j],  edgecolors='none', color=agent_plots[baseline][4])
            
    #     else:
    #         # Plot on first subplot for values > split_bottom
    #         ax1.plot(subset['eventtime'], subset['cum_reward'], label=baseline, 
    #                 marker=markers[i % len(markers)], linewidth=0.5)
    #         # Plot on second subplot for values < split_upper
    #         ax2.plot(subset['eventtime'], subset['cum_reward'], label=baseline, marker=markers[i % len(markers)], 
    #                 linewidth=0.5)

    # split_bottom=40000
    # split_upper=40000
    # # Set limits for the Y-axis on both subplots to "cut out" values between split_bottom and split_upper
    # ax1.set_ylim(split_upper, max(df['cum_reward']) + 100)  # Adjust upper limit as needed
    # ax2.set_ylim(min(df['cum_reward']) - 100, split_bottom)  # Adjust lower limit as needed

    # # Hide the spines between ax and ax2
    # ax1.spines['bottom'].set_visible(False)
    # ax2.spines['top'].set_visible(False)
    # ax1.xaxis.tick_top()
    # ax1.tick_params(labeltop=False)  # Don't show tick labels at the top
    # ax2.xaxis.tick_bottom()

    # # Adding diagonal lines to indicate the break in Y axis
    # d = .01  # how big to make the diagonal lines in axes coordinates
    # kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
    # ax1.plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    # ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal

    # kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
    # ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    # ax2.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal

    # # Set labels and title
    # ax2.set_xlabel('Event Time')
    # ax2.set_ylabel('Cumulative Reward')
    # ax1.set_title('Event Time vs Cumulative Reward by Baseline')
    # ax1.legend(loc='upper right',ncol=2)

    # # Save the plot to the specified PDF file
    # plt.savefig(os.path.join(base_folder, 'eventtime_vs_cum_reward.pdf'))
    # plt.close()

    plt.figure(figsize=(10, 6))
    for i, baseline in enumerate(unique_baselines):
        subset = df[df['baseline'] == baseline] #.sort_values(by='eventtime')

        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                plt.plot(row['eventtime'], row['cum_reward'], ls='none', ms=sizes[j], marker='o', mfc='none', mec=agent_plots[baseline][4])
                # plt.scatter(row['eventtime'], row['cum_reward'], s=sizes[j],  edgecolors=agent_plots[baseline][4], facecolors='none')
            
        else:
            plt.plot(subset['eventtime'], subset['cum_reward'], label=baseline, marker=markers[i % len(markers)], linewidth=0.5)
    plt.xlabel('Event Time')
    plt.ylabel('Cumulative Reward')
    plt.legend()
    plt.title('Event Time vs Cumulative Reward by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_cum_reward.pdf'))

    # Convert to Plotly figure
    # fig1 = tls.mpl_to_plotly(plt.gcf())
    # Save the figure as an HTML file
    # fig1.write_html(os.path.join(base_folder, 'eventtime_vs_cum_reward.html'))

    plt.close()
    
    # Plot 2: eventtime vs mean_ratio
    plt.figure(figsize=(10, 6))
    for i, baseline in enumerate(unique_baselines):
        subset = df[df['baseline'] == baseline] #.sort_values(by='eventtime')

        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                plt.scatter(row['eventtime'], row['mean_ratio'], s=sizes[j],  edgecolors=agent_plots[baseline][4], color='none')
            
        else:
            plt.plot(subset['eventtime'], subset['mean_ratio'], label=baseline, marker=markers[i % len(markers)], linewidth=0.5)
    plt.xlabel('Event Time')
    plt.ylabel('Mean Ratio')
    plt.legend()
    plt.title('Event Time vs Mean Ratio by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_mean_ratio.pdf'))

    # Convert to Plotly figure
    # fig1 = tls.mpl_to_plotly(plt.gcf())
    # Save the figure as an HTML file
    # fig1.write_html(os.path.join(base_folder, 'eventtime_vs_mean_ratio.html'))

    plt.close()
    
    # # Plot 3: eventtime vs mean_violations
    # plt.figure(figsize=(10, 6))
    # for i, baseline in enumerate(unique_baselines):
    #     subset = df[df['baseline'] == baseline].sort_values(by='eventtime')

    #     if baseline in agent_plots:
    #         # Determine sizes and opacities based on episode values
    #         num_points = len(subset['eventtime'])
    #         sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
    #         opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points))
    #         for j, row in subset.iterrows():
    #             plt.scatter(row['eventtime'], row['mean_violations'], s=sizes[j],  edgecolors='none', color=agent_plots[baseline][4])
            
    #     else:
    #         plt.plot(subset['eventtime'], subset['mean_violations'], label=baseline, marker=markers[i % len(markers)], linewidth=0.5)
    # plt.xlabel('Event Time')
    # plt.ylabel('Mean Violations')
    # plt.legend()
    # plt.title('Event Time vs Mean Violations by Baseline')
    # plt.savefig(os.path.join(base_folder, 'eventtime_vs_mean_violations.pdf'))
    # plt.close()

    # Plot 3: eventtime vs mean_violations
    plt.figure(figsize=(10, 6))
    for i, baseline in enumerate(unique_baselines):
        subset = df[df['baseline'] == baseline] #.sort_values(by='eventtime')

        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                plt.scatter(row['eventtime'], row['sum_violations']/row['steps'], s=sizes[j],  edgecolors=agent_plots[baseline][4], color='none')
            
        else:
            plt.plot(subset['eventtime'], subset['sum_violations']/subset['steps'], label=baseline, marker=markers[i % len(markers)], linewidth=0.5)
    plt.xlabel('Event Time')
    plt.ylabel('Sum Violations')
    plt.legend()
    plt.title('Event Time vs Sum Violations by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_sum_violations.pdf'))

    # Convert to Plotly figure
    # fig1 = tls.mpl_to_plotly(plt.gcf())
    # Save the figure as an HTML file
    # fig1.write_html(os.path.join(base_folder, 'eventtime_vs_sum_violations.html'))

    plt.close()

    # Plot 3: eventtime vs mean_violations
    plt.figure(figsize=(10, 6))
    for i, baseline in enumerate(unique_baselines):
        subset = df[df['baseline'] == baseline] #.sort_values(by='eventtime')
        
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                plt.scatter(row['eventtime'], row['steps'], s=sizes[j],  edgecolors=agent_plots[baseline][4], color='none')
            
        else:
            plt.plot(subset['eventtime'], subset['steps'], label=baseline, marker=markers[i % len(markers)], linewidth=0.5)
    plt.xlabel('Event Time')
    plt.ylabel('Steps')
    plt.legend()
    plt.title('Event Time vs Steps by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_steps.pdf'))

    # Convert to Plotly figure
    # fig1 = tls.mpl_to_plotly(plt.gcf())
    # Save the figure as an HTML file
    # fig1.write_html(os.path.join(base_folder, 'eventtime_vs_steps.html'))

    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate plots from baselines_data.csv.')
    parser.add_argument('base_folder', type=str, help='Input folder containing baselines_data.csv.')
    
    args = parser.parse_args()
    
    plot_graphs(args.base_folder)
