import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

def find_min_timestamp(folder,csv_files):
    min_timestamp = float('inf')

    for csv_file in csv_files:
        df = pd.read_csv(os.path.join(folder,csv_file), header=None, names=['ts', 'value'])
        min_timestamp = min(min_timestamp, df['ts'].min())

    return min_timestamp

def plot_csv(folder,csv_file, output_folder, min_timestamp):
    df = pd.read_csv(os.path.join(folder,csv_file), header=None, names=['ts', 'value'])
    df['ts'] -= min_timestamp

    # Filter out rows with NaN values in the 'value' column
    df = df.dropna(subset=['value'])

    plt.plot(df['ts'], df['value'])
    plt.xlabel('Timestamp (adjusted)')
    plt.ylabel('Value')
    plt.title(f'CSV Plot: {os.path.basename(csv_file)}')
    plt.grid(True)

    output_path = os.path.join(output_folder, os.path.basename(csv_file).replace('.csv', '_plot.pdf'))
    plt.savefig(output_path, format='pdf')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Create PDF plots from CSV files.')
    parser.add_argument('folder', help='Path to the folder containing CSV files')
    parser.add_argument('csv_files', nargs='+', help='List of CSV files to process')
    args = parser.parse_args()

    # Check if the folder exists
    if not os.path.exists(args.folder):
        print(f"Error: Folder '{args.folder}' does not exist.")
        return

    # Find the minimum timestamp among all files
    min_timestamp = find_min_timestamp(args.folder,args.csv_files)

    # Create PDF plots
    for csv_file in args.csv_files:
        plot_csv(args.folder, csv_file, args.folder, min_timestamp)

if __name__ == "__main__":
    main()