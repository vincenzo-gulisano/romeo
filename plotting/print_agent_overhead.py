import argparse
import pandas as pd

def calculate_statistics(csv_file):
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    # Columns to compute statistics for
    columns = ["cpu_usage", "rss_memory_MB", "vms_memory_MB"]

    # Check if the required columns are present
    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        print(f"Missing required columns in the CSV file: {', '.join(missing_columns)}")
        return

    # Compute and print statistics
    for column in columns:
        mean_val = df[column].mean()
        median_val = df[column].median()
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)

        print(f"Statistics for {column}:")
        print(f"  Mean: {mean_val}")
        print(f"  Median: {median_val}")
        print(f"  First Quartile (Q1): {q1}")
        print(f"  Third Quartile (Q3): {q3}")
        print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute statistics from a CSV file.")
    parser.add_argument("csv_file", help="Path to the input CSV file.")
    args = parser.parse_args()

    calculate_statistics(args.csv_file)
