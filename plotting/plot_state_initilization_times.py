import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Plot eventtime vs. end-start from a CSV file.')
    parser.add_argument('lineardata', type=str, help='Path to the CSV file for linear')
    parser.add_argument('syntheticdata', type=str, help='Path to the CSV file for synthetic')
    parser.add_argument('output', type=str, help='Path to save the plot (optional)')
    args = parser.parse_args()

    plt.rcParams.update({'font.size': 8})  # Set global font size to 10

    # Create a figure and a set of subplots, now with 4 rows
    text_width_pt = 506/2
    text_height_pt = 100
    points_per_inch = 72
    text_width_in = text_width_pt / points_per_inch
    text_height_in = text_height_pt / points_per_inch
    
    fig = plt.figure(figsize=(text_width_in, text_height_in))
    
    # Read CSV file
    data = pd.read_csv(args.lineardata, skipinitialspace=True)

    # Strip any unexpected spaces in column names
    data.columns = data.columns.str.strip()

    # Ensure the required columns are present
    if not all(column in data.columns for column in ['start', 'eventtime', 'end']):
        raise ValueError('CSV file must contain start, eventtime, and end columns.')
    # Calculate end - start
    data['duration'] = data['end'] - data['start']

    # # Print index of the minimum duration
    # min_duration_index = data['duration'].idxmin()
    # print(f'Index of minimum duration: {min_duration_index}')
    # print(f'minimum duration: {data['duration'].min()}')

    # Sort data by eventtime
    sorted_data = data.sort_values(by='eventtime')

    # Plot eventtime vs. end-start
    plt.plot(sorted_data['eventtime'], sorted_data['duration'], linestyle='-', color='b', label='Linear Road')

    # Read CSV file
    data = pd.read_csv(args.syntheticdata, skipinitialspace=True)

    # Strip any unexpected spaces in column names
    data.columns = data.columns.str.strip()

    # Ensure the required columns are present
    if not all(column in data.columns for column in ['start', 'eventtime', 'end']):
        raise ValueError('CSV file must contain start, eventtime, and end columns.')
    # Calculate end - start
    data['duration'] = data['end'] - data['start']
    
    # # Print index of the minimum duration
    # min_duration_index = data['duration'].idxmin()
    # print(f'Index of minimum duration: {min_duration_index}')
    # print(f'minimum duration: {data['duration'].min()}')

    # Sort data by eventtime
    sorted_data = data.sort_values(by='eventtime')

    # Plot eventtime vs. end-start
    plt.plot(sorted_data['eventtime'], sorted_data['duration'], linestyle=':', color='r', label='Synthetic')

    plt.xlabel('Start event time')
    plt.ylabel('Init. time (s)')
    # plt.title('Event Time vs. Duration')
    plt.grid(True)
    plt.legend()

    # Adjust layout
    fig.tight_layout()
    
    # Save or show the plot
    if args.output:
        plt.savefig(args.output)
        print(f'Plot saved to {args.output}')
    else:
        plt.show()

if __name__ == '__main__':
    main()
