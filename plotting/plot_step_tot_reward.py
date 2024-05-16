import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.colors as mcolors
import argparse
# from matplotlib.colors import Normalize

def plot_figure(base_folder):
    data = pd.read_csv(os.path.join(base_folder, 'step_tot_reward.csv'))
    plt.figure(figsize=(10, 6))

    # create a color map, and start with a darker red
    cmap = plt.get_cmap('Reds')
    new_colors = cmap(np.linspace(0.3, 1.0, 256))  # take color from 30% of cmap
    new_cmap = mcolors.LinearSegmentedColormap.from_list('trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=0.3, b=1.0), new_colors)

    # calculate dynamic sizes and alpha values
    num_episodes = len(data['episode'].unique())
    sizes = np.geomspace(start = 10, stop = 400, num = num_episodes) 
    opacities = np.geomspace (start = 0.1, stop = 1, num = num_episodes)

    # mapp wach episode to a size and opacity
    size_map = {episode: size for episode, size in zip(sorted(data['episode'].unique()), sizes)}
    alpha_map = {episode: alpha for episode, alpha in zip(sorted(data['episode'].unique()), opacities)}

    # plot scatter plot with dynamic sizes and alpha values
    for episode in sorted(data['episode'].unique()):
        subset = data[data['episode'] == episode]
        plt.scatter(subset['step'], subset['total_reward'], c=[new_cmap(episode) for _ in subset['episode']],
                    s=size_map[episode], alpha=alpha_map[episode], edgecolors='none', label=f'episode {episode}')
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