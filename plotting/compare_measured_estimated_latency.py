import argparse
import pandas as pd
import matplotlib.pyplot as plt

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Plot and compare two CSV files.')
    parser.add_argument('input_file1', type=str, help='Path to the first CSV file')
    parser.add_argument('input_file2', type=str, help='Path to the second CSV file')
    parser.add_argument('output_pdf', type=str, help='Path to the output PDF file')
    args = parser.parse_args()

    # Read CSV files
    df1 = pd.read_csv(args.input_file1, header=None, names=['ts', 'value'])
    df2 = pd.read_csv(args.input_file2, header=None, names=['ts', 'value'])

    # Subtract the minimum ts from each file
    min_ts1 = df1['ts'].min()
    min_ts2 = df2['ts'].min()
    df1['ts'] -= min_ts1
    df2['ts'] -= min_ts2

    # Compute the max ts for both
    max_ts = min(df1['ts'].max(), df2['ts'].max())
    start_ts = 0

    # Create a figure with two subplots
    fig, ax1 = plt.subplots()

    # Plot ts vs value for both on the left y axes
    ax1.plot(df1['ts'].iloc[start_ts:max_ts], df1['value'].iloc[start_ts:max_ts], label='Measured', color='blue')
    ax1.plot(df2['ts'].iloc[start_ts:max_ts], df2['value'].iloc[start_ts:max_ts], label='Estimated', color='green')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Value', color='black')
    ax1.tick_params('y', colors='black')
    ax1.legend(loc='upper left')

    # Create a second y-axis for percentage difference
    ax2 = ax1.twinx()
    # percentage_difference = ((df1['value'].iloc[start_ts:max_ts] - df2['value'].iloc[start_ts:max_ts]) / df2['value'].iloc[start_ts:max_ts])
    percentage_difference = ((df1['value'].iloc[start_ts:max_ts] - df2['value'].iloc[start_ts:max_ts]))
    ax2.plot(df1['ts'].iloc[start_ts:max_ts], percentage_difference, label='Percentage Difference', linestyle='--', color='red')
    ax2.set_ylabel('Error', color='red')
    ax2.tick_params('y', colors='red')
    ax2.legend(loc='upper right')

    # Adjust layout and save the figure to the output PDF file
    fig.tight_layout()
    plt.savefig(args.output_pdf)
    plt.show()

if __name__ == "__main__":
    main()
