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

    # Filter data for each exp_id
    filtered_base_dfs = []
    filtered_agent_dfs = []

    for exp_id in df["exp_id"].unique():
        
        # Get data for the current exp_id
        base_subset = df_base[df_base["exp_id"] == exp_id]
        agent_subset = df_agent[df_agent["exp_id"] == exp_id]

        # Combine base and agent data to find the filtering condition
        combined_subset = pd.concat([base_subset, agent_subset])

        # Find the first timestamp where latency > 1500 or CPU > 99
        condition = (
            ((combined_subset["stat"] == "Latency") & (combined_subset["value"] > 1500)) |
            ((combined_subset["stat"] == "CPU") & (combined_subset["value"] > 99))
        )
        
        if condition.any():
            cutoff_timestamp = combined_subset.loc[condition, "timestamp"].min()
            print(f"The cutoff timestamp for experiment {exp_id} is {cutoff_timestamp}")
            # Filter data up to the cutoff timestamp
            base_subset = base_subset[base_subset["timestamp"] <= cutoff_timestamp]
            agent_subset = agent_subset[agent_subset["timestamp"] <= cutoff_timestamp]
        else:
            print(f"No cutoff for experiment {exp_id}")

        # Skip the first and last 10% of the filtered data
        total_rows_base = len(base_subset)
        start_index_base = int(total_rows_base * 0.1)
        end_index_base = int(total_rows_base * 0.9)
        
        total_rows_agent = len(agent_subset)
        start_index_agent = int(total_rows_agent * 0.1)
        end_index_agent = int(total_rows_agent * 0.9)
        
        if total_rows_base >= 30 and total_rows_agent >=30:  # Ensure there are enough rows to trim
            base_subset = base_subset.iloc[start_index_base:end_index_base]
            agent_subset = agent_subset.iloc[start_index_agent:end_index_agent]

            # Add the filtered data to the list
            filtered_base_dfs.append(base_subset)
            filtered_agent_dfs.append(agent_subset)
        else:
            print(f"skipping experiment {exp_id} data because there are not enough data points, only {total_rows_base} for base and {total_rows_agent} for the agent")

    # Combine all filtered base and agent data
    df_base = pd.concat(filtered_base_dfs).reset_index(drop=True)
    df_agent = pd.concat(filtered_agent_dfs).reset_index(drop=True)

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
    result_df = filtered_df[["timestamp", "exp_id", "stat", "value_base", "value_diff", "percentage_diff"]]

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
