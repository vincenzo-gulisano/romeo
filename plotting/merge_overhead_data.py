import argparse
import os
import pandas as pd


def process_experiment_data(folder_base, folder_agent, experiment_ids, output_csv):
    # Create an empty DataFrame to store the consolidated data
    consolidated_data = []

    for exp_id in experiment_ids:
    
        # Construct file paths
        cpu_file_a = os.path.join(folder_base, str(exp_id), "eps", "CPU-agg.average.000.csv")
        cpu_file_b = os.path.join(folder_agent, str(exp_id), "eps", "CPU-agg.average.000.csv")
        latency_file_a = os.path.join(folder_base, str(exp_id), "eps", "latency.average.000.csv")
        latency_file_b = os.path.join(folder_agent, str(exp_id), "eps", "latency.average.000.csv")

        # Process CPU files
        if os.path.exists(cpu_file_a):
            cpu_df_a = pd.read_csv(cpu_file_a)
            cpu_df_a["exp_id"] = exp_id
            cpu_df_a["stat"] = "CPU"
            cpu_df_a["type"] = "base"
            consolidated_data.append(cpu_df_a.rename(columns={"value": "value"}))

        if os.path.exists(cpu_file_b):
            cpu_df_b = pd.read_csv(cpu_file_b)
            cpu_df_b["exp_id"] = exp_id
            cpu_df_b["stat"] = "CPU"
            cpu_df_b["type"] = "agent"
            consolidated_data.append(cpu_df_b.rename(columns={"value": "value"}))

        # Process Latency files
        if os.path.exists(latency_file_a):
            latency_df_a = pd.read_csv(latency_file_a)
            latency_df_a["exp_id"] = exp_id
            latency_df_a["stat"] = "Latency"
            latency_df_a["type"] = "base"
            consolidated_data.append(latency_df_a.rename(columns={"value": "value"}))

        if os.path.exists(latency_file_b):
            latency_df_b = pd.read_csv(latency_file_b)
            latency_df_b["exp_id"] = exp_id
            latency_df_b["stat"] = "Latency"
            latency_df_b["type"] = "agent"
            consolidated_data.append(latency_df_b.rename(columns={"value": "value"}))

    # Combine all data into a single DataFrame
    consolidated_df = pd.concat(consolidated_data, ignore_index=True)
    consolidated_df = consolidated_df[["timestamp", "exp_id", "stat", "type", "value"]]

    # Save the consolidated data to the output CSV file
    consolidated_df.to_csv(output_csv, index=False)
    print(f"Consolidated data saved to {output_csv}")


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Consolidate data from CPU and Latency files across experiments.")
    parser.add_argument("folder_base", help="Path to folder containing the data collected without the Agent")
    parser.add_argument("folder_agent", help="Path to folder containing the data collected with the Agent")
    parser.add_argument("experiment_ids", nargs="+", help="List of experiment IDs")
    parser.add_argument("output_csv", help="Output CSV file path")

    args = parser.parse_args()

    # Process the files and consolidate the data
    process_experiment_data(args.folder_base, args.folder_agent, args.experiment_ids, args.output_csv)
