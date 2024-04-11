import argparse
import pandas as pd
import os

def process_subfolder(subfolder):
    csv_file = os.path.join(subfolder, 'compressionandepisodesstats.csv')
    if not os.path.exists(csv_file):
        return None
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Initialize a list to hold processed data
    data = []
    
    # Process each unique episode
    for episode in df['episode'].unique():
        episode_data = df[df['episode'] == episode]
        
        # Extract required stats for the episode
        mean_rate = episode_data[episode_data['stat'] == 'injectionrate.rate']['mean'].values[0]
        cum_reward = episode_data[episode_data['stat'] == 'rewards']['sum'].values[0]
        mean_ratio = episode_data[episode_data['stat'] == 'ratio.percent']['mean'].values[0]
        mean_violations = episode_data[episode_data['stat'] == 'latency.violations']['mean'].values[0]
        sum_violations = episode_data[episode_data['stat'] == 'latency.violations']['sum'].values[0]
        latency = episode_data[episode_data['stat'] == 'latency.average']['mean'].values[0]
        cpu = episode_data[episode_data['stat'] == 'CPU-agg.average']['mean'].values[0]
        steps = episode_data[episode_data['stat'] == 'steps']['sum'].values[0]
        eventtime = episode_data[episode_data['stat'] == 'eventtime.max']['min'].values[0]
        
        # Append to data list
        data.append({
            'baseline': os.path.basename(subfolder),
            'episode': episode,
            'mean_rate': mean_rate,
            'cum_reward': cum_reward,
            'mean_ratio': mean_ratio,
            'mean_violations': mean_violations,
            'sum_violations': sum_violations,
            'latency': latency,
            'cpu': cpu,
            'steps': steps,
            'eventtime': eventtime
        })
    
    return pd.DataFrame(data)

def aggregate_data(base_folder):
    baselines_data = pd.DataFrame(columns=['baseline', 'episode', 'mean_rate', 'cum_reward', 'mean_ratio', 'mean_violations','sum_violations','latency','cpu','steps','eventtime'])
    
    for subfolder in os.listdir(base_folder):
        subfolder_path = os.path.join(base_folder, subfolder)
        if os.path.isdir(subfolder_path):
            subfolder_data = process_subfolder(subfolder_path)
            if subfolder_data is not None:
                baselines_data = pd.concat([baselines_data, subfolder_data], ignore_index=True)
    
    return baselines_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Aggregate data from multiple subfolders into a single DataFrame.")
    parser.add_argument('base_folder', type=str, help='Base folder containing the subfolders.')
    
    args = parser.parse_args()
    
    baselines_data = aggregate_data(args.base_folder)
    
    # Save the DataFrame to a CSV file in the base folder
    output_path = os.path.join(args.base_folder, 'baselines_data.csv')
    baselines_data.to_csv(output_path, index=False)
    
    print(f"Data aggregated and saved to {output_path}")
