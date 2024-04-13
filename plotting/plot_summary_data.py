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
    
    
    # The values represent: initial size, fine size, initial opacity, final opacity, color, prob. of selection
    agent_plots = {
        'linearroad-RL': [1,30,0.1,1,'red',0.5]}
    # ,
        # 'agent-101-300': [1,30,0.1,1,'green',0.4]}
       
    given_order = ['linearroad-RL']  # The desired order for baselines
    
    # Create a set for faster membership tests
    unique_baselines_set = set(df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

    plt.figure(figsize=(10, 6))
    for i, baseline in enumerate(unique_baselines):
        subset = df[df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    plt.plot(row['eventtime'], row['cum_reward'], ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    plt.xlabel('Event Time')
    plt.ylabel('Cumulative Reward')
    # plt.legend()
    plt.title('Event Time vs Cumulative Reward by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_cum_reward.pdf'))

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
                if np.random.rand()<=agent_plots[baseline][5]:
                    plt.plot(row['eventtime'], row['mean_ratio'], ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    plt.xlabel('Event Time')
    plt.ylabel('Mean Ratio')
    # plt.legend()
    plt.title('Event Time vs Mean Ratio by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_mean_ratio.pdf'))
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
                if np.random.rand()<=agent_plots[baseline][5]:
                    plt.plot(row['eventtime'], row['latency'], ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    plt.xlabel('Event Time')
    plt.ylabel('Latency')
    # plt.legend()
    plt.title('Event Time vs Latency by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_latency.pdf'))
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
                if np.random.rand()<=agent_plots[baseline][5]:
                    plt.plot(row['eventtime'], row['cpu'], ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    plt.xlabel('Event Time')
    plt.ylabel('Steps')
    # plt.legend()
    plt.title('Event Time vs CPU by Baseline')
    plt.savefig(os.path.join(base_folder, 'eventtime_vs_cpu.pdf'))
    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate plots from baselines_data.csv.')
    parser.add_argument('base_folder', type=str, help='Input folder containing baselines_data.csv.')
    
    args = parser.parse_args()
    
    plot_graphs(args.base_folder)
