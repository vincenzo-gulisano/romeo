import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_data(input_csv, output_folder):
    # Load the data
    df = pd.read_csv(input_csv)

    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Group the dataframe by episode
    grouped = df.groupby('Episode')
    
    # Iterate over each group (each episode)
    for episode, data in grouped:
        # Sort the data by Action Time to ensure plots are in order
        data.sort_values('Action Time', inplace=True)

        # Adjust Action Time to start at 0
        data['Action Time'] -= data['Action Time'].iloc[0]

        # Plotting
        plt.figure(figsize=(10, 6))
        plt.plot(data['Action Time'], data['Prob1'], label='Compress')
        plt.plot(data['Action Time'], data['Prob2'], label='Stay')
        plt.plot(data['Action Time'], data['Prob3'], label='Decompress')

        # Labeling
        plt.xlabel('Action Time (adjusted to start at 0)')
        plt.ylabel('Probabilities')
        plt.title(f'Episode {episode}: Action Time vs Probabilities')
        plt.legend()

        # Save the plot
        plot_file_path = os.path.join(output_folder, f'probs_{episode}.pdf')
        plt.savefig(plot_file_path)
        plt.close()

def main():
    # Setting up Argument Parsing
    parser = argparse.ArgumentParser(description="Plot probabilities against adjusted action time for each episode from a CSV file.")
    parser.add_argument("input_csv", type=str, help="Path to the input CSV file")
    parser.add_argument("output_folder", type=str, help="Path to the output folder where plots will be saved")
    
    # Parsing arguments
    args = parser.parse_args()

    # Process the data and generate plots
    plot_data(args.input_csv, args.output_folder)

if __name__ == "__main__":
    main()
