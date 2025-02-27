import argparse
import pandas as pd
import os

def process_subfolder(subfolder,id):
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
        q2_rate = episode_data[episode_data['stat'] == 'injectionrate.rate']['q2'].values[0]
        cum_reward = episode_data[episode_data['stat'] == 'rewards']['sum'].values[0]
        q1_ratio = episode_data[episode_data['stat'] == 'ratio.percent']['q1'].values[0]
        q2_ratio = episode_data[episode_data['stat'] == 'ratio.percent']['q2'].values[0]
        q3_ratio = episode_data[episode_data['stat'] == 'ratio.percent']['q3'].values[0]
        mean_ratio = episode_data[episode_data['stat'] == 'ratio.percent']['mean'].values[0]
        q2_violations = episode_data[episode_data['stat'] == 'latency.violations']['q2'].values[0]
        sum_violations = episode_data[episode_data['stat'] == 'latency.violations']['sum'].values[0]
        q1_latency = episode_data[episode_data['stat'] == 'latency.average']['q1'].values[0]
        q2_latency = episode_data[episode_data['stat'] == 'latency.average']['q2'].values[0]
        q3_latency = episode_data[episode_data['stat'] == 'latency.average']['q3'].values[0]
        mean_latency = episode_data[episode_data['stat'] == 'latency.average']['mean'].values[0]
        q1_cpu = episode_data[episode_data['stat'] == 'CPU-agg.average']['q1'].values[0]
        q2_cpu = episode_data[episode_data['stat'] == 'CPU-agg.average']['q2'].values[0]
        q3_cpu = episode_data[episode_data['stat'] == 'CPU-agg.average']['q3'].values[0]
        mean_cpu = episode_data[episode_data['stat'] == 'CPU-agg.average']['mean'].values[0]
        steps = episode_data[episode_data['stat'] == 'steps']['sum'].values[0]
        duration = episode_data[episode_data['stat'] == 'duration']['sum'].values[0]
        eventtime_start = episode_data[episode_data['stat'] == 'eventtime.max']['q1'].values[0]
        eventtime_end = episode_data[episode_data['stat'] == 'eventtime.max']['q3'].values[0]
        
        # Append to data list
        data.append({
            'baseline': id,
            'episode': episode,
            'q2_rate': q2_rate,
            'cum_reward': cum_reward,
            'q1_ratio': q1_ratio,
            'q2_ratio': q2_ratio,
            'q3_ratio': q3_ratio,
            'mean_ratio': mean_ratio,
            'q2_violations': q2_violations,
            'sum_violations': sum_violations,
            'q1_latency': q1_latency,
            'q2_latency': q2_latency,
            'q3_latency': q3_latency,
            'mean_latency': mean_latency,
            'q1_cpu': q1_cpu,
            'q2_cpu': q2_cpu,
            'q3_cpu': q3_cpu,
            'mean_cpu': mean_cpu,
            'steps': steps,
            'duration': duration,
            'eventtime_start': eventtime_start,
            'eventtime_end': eventtime_end
        })
    
    return pd.DataFrame(data)

def aggregate_data(folders):
    baselines_data = pd.DataFrame(columns=['baseline', 'episode', 'q2_rate', 'cum_reward', 'q1_ratio', 'q2_ratio', 'q3_ratio', 'mean_ratio', 
                                           'q2_violations','sum_violations','q1_latency','q2_latency','q3_latency','mean_latency','q1_cpu','q2_cpu','q3_cpu','mean_cpu',
                                           'steps','duration','eventtime_start','eventtime_end'])
    
    for folder_id in folders:
        base_folder, id_ = folder_id.split(':')
        subfolder_data = process_subfolder(base_folder, id_)
        if subfolder_data is not None:
            baselines_data = pd.concat([baselines_data, subfolder_data], ignore_index=True)
    
    return baselines_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Aggregate data from folders into a single DataFrame.")
    parser.add_argument('folders', type=str, nargs='+', help='List of base_folder and id pairs (e.g., base1:id1 base2:id2 ...).')
    parser.add_argument('output_path', type=str, help='Path to save the aggregated CSV.')

    
    args = parser.parse_args()
    
    baselines_data = aggregate_data(args.folders)
    
    # Save the DataFrame to a CSV file in the base folder
    baselines_data.to_csv(args.output_path, index=False)
    
    print(f"Data aggregated and saved to {args.output_path}")
