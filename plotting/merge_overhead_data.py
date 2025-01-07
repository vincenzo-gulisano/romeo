import argparse
import os
import pandas as pd

def process_files(folder_a, folder_b, exps, output_file):
    # Create a DataFrame to store the consolidated data
    consolidated_df = pd.DataFrame()

    for i in range(exps):
        # Format the file index with leading zeros
        file_index = f"{i:03d}"

        # Define file paths
        cpu_file_a = os.path.join(folder_a, f"CPU-agg.average.{file_index}.csv")
        cpu_file_b = os.path.join(folder_b, f"CPU-agg.average.{file_index}.csv")
        latency_file_a = os.path.join(folder_a, f"latency.average.{file_index}.csv")
        latency_file_b = os.path.join(folder_b, f"latency.average.{file_index}.csv")

        # Load CPU files and merge
        cpu_df_a = pd.read_csv(cpu_file_a)
        cpu_df_b = pd.read_csv(cpu_file_b)
        cpu_combined = pd.concat([cpu_df_a, cpu_df_b]).drop_duplicates().sort_values(by="timestamp")

        # Load Latency files and merge
        latency_df_a = pd.read_csv(latency_file_a)
        latency_df_b = pd.read_csv(latency_file_b)
        latency_combined = pd.concat([latency_df_a, latency_df_b]).drop_duplicates().sort_values(by="timestamp")

        # Merge timestamps from CPU and Latency
        all_timestamps = pd.concat([cpu_combined["timestamp"], latency_combined["timestamp"]]).drop_duplicates().sort_values()
        if consolidated_df.empty:
            consolidated_df["timestamp"] = all_timestamps
        else:
            consolidated_df = consolidated_df.merge(pd.DataFrame({"timestamp": all_timestamps}), on="timestamp", how="outer")

        # Add CPU values
        cpu_combined.set_index("timestamp", inplace=True)
        consolidated_df[f"CPU_value_{file_index}_A"] = consolidated_df["timestamp"].map(cpu_combined["value"].to_dict())
        consolidated_df[f"CPU_value_{file_index}_B"] = consolidated_df["timestamp"].map(cpu_combined["value"].to_dict())

        # Add Latency values
        latency_combined.set_index("timestamp", inplace=True)
        consolidated_df[f"Latency_value_{file_index}_A"] = consolidated_df["timestamp"].map(latency_combined["value"].to_dict())
        consolidated_df[f"Latency_value_{file_index}_B"] = consolidated_df["timestamp"].map(latency_combined["value"].to_dict())

    # Save the consolidated DataFrame to the output CSV file
    consolidated_df.to_csv(output_file, index=False)
    print(f"Consolidated data saved to {output_file}")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Consolidate data from CPU and Latency files.")
    parser.add_argument("folder_a", help="Path to Folder A")
    parser.add_argument("folder_b", help="Path to Folder B")
    parser.add_argument("exps", type=int, help="Number of experiments")
    parser.add_argument("output_csv", help="Output CSV file path")

    args = parser.parse_args()

    # Process the files and consolidate the data
    process_files(args.folder_a, args.folder_b, args.exps, args.output_csv)
