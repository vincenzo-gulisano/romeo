import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt

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

        # Create output folder for plots
        output_folder = os.path.dirname(output_csv)
        os.makedirs(output_folder, exist_ok=True)

        # Extract the file name without the extension
        output_id = os.path.splitext(os.path.basename(output_csv))[0]
        
        if 'cpu_df_a' in locals() and 'cpu_df_b' in locals():
            
            # Align data by timestamp
            aligned_cpu_df = pd.merge(
                cpu_df_a[["timestamp", "value"]],
                cpu_df_b[["timestamp", "value"]],
                on="timestamp",
                suffixes=("_base", "_agent")
            )
            
            plt.figure(figsize=(10, 6))
            plt.plot(cpu_df_a["timestamp"], cpu_df_a["value"], label="Base CPU", color='blue')
            plt.plot(cpu_df_b["timestamp"], cpu_df_b["value"], label="Agent CPU", color='orange')
            plt.plot(aligned_cpu_df["timestamp"], aligned_cpu_df["value_agent"] - aligned_cpu_df["value_base"], label="Difference (Agent - Base)", color='green')
            plt.xlabel("Timestamp")
            plt.ylabel("Value")
            plt.title(f"CPU Stats for Experiment {exp_id}")
            plt.legend()
            cpu_plot_path = os.path.join(output_folder, f"{output_id}.CPU_plot_exp_{exp_id}.pdf")
            plt.savefig(cpu_plot_path)
            plt.close()
            print(f"Saved CPU plot for experiment {exp_id} to {cpu_plot_path}")
                
        # Plot Latency data if both files exist
        if 'latency_df_a' in locals() and 'latency_df_b' in locals():
            
            # Align data by timestamp
            aligned_latency_df = pd.merge(
                latency_df_a[["timestamp", "value"]],
                latency_df_b[["timestamp", "value"]],
                on="timestamp",
                suffixes=("_base", "_agent")
            )
            
            plt.figure(figsize=(10, 6))
            plt.plot(latency_df_a["timestamp"], latency_df_a["value"], label="Base Latency", color='blue')
            plt.plot(latency_df_b["timestamp"], latency_df_b["value"], label="Agent Latency", color='orange')
            plt.plot(aligned_latency_df["timestamp"], aligned_latency_df["value_agent"] - aligned_latency_df["value_base"], label="Difference (Agent - Base)", color='green')
            plt.xlabel("Timestamp")
            plt.ylabel("Value")
            plt.title(f"Latency Stats for Experiment {exp_id}")
            plt.legend()
            latency_plot_path = os.path.join(output_folder, f"{output_id}.latency_plot_exp_{exp_id}.pdf")
            plt.savefig(latency_plot_path)
            plt.close()
            print(f"Saved Latency plot for experiment {exp_id} to {latency_plot_path}")
            
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
