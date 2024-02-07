import argparse
import pandas as pd
import os

def append_column(input_csv, output_csv, column_value):
    # Read the input CSV file
    df = pd.read_csv(input_csv)

    # Add a new column with the specified value
    df['Agent-ID'] = column_value

    # Write the updated DataFrame to the output CSV file, appending to it
    df.to_csv(output_csv, mode='a', index=False, header=not os.path.exists(output_csv))

if __name__ == "__main__":
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Append a column to a CSV file.')

    # Add arguments
    parser.add_argument('input_csv', type=str, help='Path to the input CSV file.')
    parser.add_argument('output_csv', type=str, help='Path to the output CSV file.')
    parser.add_argument('column_value', type=str, help='Value to be added in the new column.')

    # Parse the arguments
    args = parser.parse_args()

    # Call the function to append the column
    append_column(args.input_csv, args.output_csv, args.column_value)