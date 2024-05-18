import argparse
import pandas as pd
import matplotlib.pyplot as plt

def calculate_avg_ts_diff(file):
    df = pd.read_csv(file)

    df['ts'] = pd.to_numeric(df['ts'], errors='coerce')
    df.sort_values(by=['episode', 'ts'], inplace=True)

    print(df)

    # Filter rows where event is 'action'
    action_df = df[df['event'].str.startswith('action')]

    # Calculate time differences
    action_df['ts_diff'] = action_df.groupby('episode')['ts'].diff().dropna()

    # Average time difference per episode
    avg_ts_diff_per_episode = action_df.groupby('episode')['ts_diff'].mean().dropna()

    return avg_ts_diff_per_episode.values

def create_boxplot(data, labels, output_file):
    plt.figure(figsize=(10, 6))
    plt.boxplot(data, labels=labels)
    plt.title('Average TS Difference Between Consecutive "Action" Events')
    plt.ylabel('Average TS Difference')
    plt.xlabel('Input Files')
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

def main(args):
    input_files = args.input_files.split(',')
    avg_diffs = []
    labels = []

    for file in input_files:
        avg_diff = calculate_avg_ts_diff(file)
        avg_diffs.append(avg_diff)
        labels.append(file.split('/')[-1])  # Use file basename for label

    create_boxplot(avg_diffs, labels, args.output_pdf)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument('input_files', type=str, help='Comma-separated list of input CSV files')
    parser.add_argument('output_pdf', type=str, help='Name of output PDF file')

    args = parser.parse_args()
    main(args)
