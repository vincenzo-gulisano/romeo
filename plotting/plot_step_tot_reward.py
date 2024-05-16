import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.colors as mcolors
import argparse
# from matplotlib.colors import Normalize

def plot_figure(base_folder):
    data1 = pd.read_csv(os.path.join(base_folder, 'step_tot_reward_13.csv')) # red
    data2 = pd.read_csv(os.path.join(base_folder, 'step_tot_reward_14.csv')) #green
    plt.figure(figsize=(10, 6))

    # create a color map, and start with a darker red
    cmap1 = plt.get_cmap('Reds')
    new_color1 = cmap1(np.linspace(0.3, 1.0, 256))
    new_cmap1 = mcolors.LinearSegmentedColormap.from_list('trunc({n},{a:.2f},{b:.2f})'.format(n=cmap1, a=0.3, b=1.0), new_color1)

    # calculate dynamic sizes and alpha values
    num_episodes1 = len(data1['episode'].unique())
    sizes1 = np.geomspace(start = 10, stop = 400, num = num_episodes1) 
    opacities1 = np.geomspace (start = 0.1, stop = 1, num = num_episodes1)

    # mapp wach episode to a size and opacity
    size_map1 = {episode: size for episode, size in zip(sorted(data1['episode'].unique()), sizes1)}
    alpha_map1 = {episode: alpha for episode, alpha in zip(sorted(data1['episode'].unique()), opacities1)}

    # plot scatter plot with dynamic sizes and alpha values
    for episode in sorted(data1['episode'].unique()):
        subset = data1[data1['episode'] == episode]
        plt.scatter(subset['step'], subset['total_reward'], c=[new_cmap1(episode) for _ in subset['episode']],
                    s=size_map1[episode], alpha=alpha_map1[episode], edgecolors='none', label=f'episode {episode}')

    
    cmap2 = plt.get_cmap('Greens')
    new_color2 = cmap2(np.linspace(0.3, 1.0, 256))  # take color from 30% of cmap
    new_cmap2 = mcolors.LinearSegmentedColormap.from_list('trunc({n},{a:.2f},{b:.2f})'.format(n=cmap2, a=0.3, b=1.0), new_color2)

    # calculate dynamic sizes and alpha values
    num_episodes2 = len(data2['episode'].unique())
    sizes2 = np.geomspace(start = 10, stop = 400, num = num_episodes2) 
    opacities2 = np.geomspace (start = 0.1, stop = 1, num = num_episodes2)

    # mapp wach episode to a size and opacity
    size_map2 = {episode: size for episode, size in zip(sorted(data2['episode'].unique()), sizes2)}
    alpha_map2 = {episode: alpha for episode, alpha in zip(sorted(data2['episode'].unique()), opacities2)}

    # plot scatter plot with dynamic sizes and alpha values
    for episode in sorted(data2['episode'].unique()):
        subset = data2[data2['episode'] == episode]
        plt.scatter(subset['step'], subset['total_reward'], c=[new_cmap2(episode) for _ in subset['episode']],
                    s=size_map2[episode], alpha=alpha_map2[episode], edgecolors='none', label=f'episode {episode}')
        

                # Annotate each episode
        # episode_center = subset[['step', 'total_reward']].mean()
        # plt.annotate(f'{episode}', (episode_center['step'], episode_center['total_reward']), fontsize=9)


    plt.xlabel('Steps')
    plt.ylabel('Total Reward')
    plt.title('Total Reward by Steps per Episode')

    plt.grid(True, axis = 'y')
    # for i, row in data.iterrows():
    #     plt.annotate(f'({row["step"]}, {row["total_reward"]})', (row["step"], row["total_reward"]))

    plt.savefig(os.path.join(base_folder, 'total_rewards_by_steps.pdf'), format='pdf')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot total rewards by steps per episode from a CSV file")
    parser.add_argument('base_folder', type=str, help='Path to the base folder')
    args = parser.parse_args()

    plot_figure(args.base_folder)