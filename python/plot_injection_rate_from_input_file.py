import argparse
import pandas as pd
import matplotlib.pyplot as plt

def plot_csv(input_csv, output_pdf):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_csv, header=None, names=['type', 'ts','vid', 'speed','xway', 'lane','dir', 'seg','pos'])

    # Count occurrences of each unique value in the 'ts' column
    ts_counts = df['ts'].value_counts().sort_index()

    # Check if the values in the 'ts' column are sorted
    sorted_check = df['ts'].is_monotonic_increasing

    print('sorted_check:',sorted_check)

    # Plot the counts

    # Plot 'ts' values on the X-axis and counts on the Y-axis as a line
    plt.plot(ts_counts.index, ts_counts.values)
    plt.xlabel('ts')
    plt.ylabel('rate')
    # plt.title('Count of Unique Values in CSV')
    plt.grid(True)

    # Save the plot as a PDF
    plt.savefig(output_pdf, format='pdf')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Create a bar plot of unique values count in a CSV file.')
    parser.add_argument('input_csv', help='Path to the input CSV file (without header)')
    parser.add_argument('output_pdf', help='Path to the output PDF file')
    args = parser.parse_args()

    # Plot the CSV and save the result as a PDF
    plot_csv(args.input_csv, args.output_pdf)

if __name__ == "__main__":
    main()
