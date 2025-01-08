import argparse
import pandas as pd


def compute_differences(input_csv, output_csv):
    # Load the consolidated data
    df = pd.read_csv(input_csv)

    # Ensure the necessary columns are present
    required_columns = {"timestamp", "exp_id", "stat", "type", "value"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"Input CSV is missing one or more required columns: {required_columns}")

    # Separate the data by type
    df_base = df[df["type"] == "base"].copy()
    df_agent = df[df["type"] == "agent"].copy()

    # Merge the base and agent data on timestamp, exp_id, and stat
    merged_df = pd.merge(
        df_base, 
        df_agent, 
        on=["timestamp", "exp_id", "stat"], 
        suffixes=("_base", "_agent")
    )

    # Filter rows where both values are greater than 0
    filtered_df = merged_df[(merged_df["value_base"] > 0) & (merged_df["value_agent"] > 0)]
        
    # Create a copy of the filtered DataFrame to avoid the warning
    filtered_df = filtered_df.copy()

    # Compute the difference between the base and agent values
    filtered_df.loc[:, "value_diff"] = filtered_df["value_agent"] - filtered_df["value_base"]

    # Compute the percentage difference
    filtered_df.loc[:, "percentage_diff"] = (filtered_df["value_diff"] / filtered_df["value_base"]) * 100

    # Select the relevant columns for the output
    result_df = filtered_df[["timestamp", "exp_id", "stat", "value_diff", "percentage_diff"]]

    # Save the results to the output CSV
    result_df.to_csv(output_csv, index=False)
    print(f"Differences saved to {output_csv}")


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Compute differences between base and agent values for each exp_id.")
    parser.add_argument("input_csv", help="Path to the input consolidated CSV file")
    parser.add_argument("output_csv", help="Path to the output CSV file for differences")

    args = parser.parse_args()

    # Compute the differences and save to the output file
    compute_differences(args.input_csv, args.output_csv)
