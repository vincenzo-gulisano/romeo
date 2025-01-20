import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import numpy as np

def create_violin_plot(diff_file, output_pdf):
    # Read the diff file
    df = pd.read_csv(diff_file)

    # Filter data for CPU and Latency
    cpu_diffs = df[df['stat'] == 'CPU']['value_diff']
    latency_diffs = df[df['stat'] == 'Latency']['value_diff']

    # Calculate median and quartiles for CPU
    cpu_mean = np.mean(cpu_diffs)
    cpu_median = np.median(cpu_diffs)
    cpu_q1 = np.percentile(cpu_diffs, 25)
    cpu_q3 = np.percentile(cpu_diffs, 75)

    # Calculate median and quartiles for Latency
    latency_mean = np.mean(latency_diffs)
    latency_median = np.median(latency_diffs)
    latency_q1 = np.percentile(latency_diffs, 25)
    latency_q3 = np.percentile(latency_diffs, 75)

    # Print results
    print("CPU Differences:")
    print(f"Mean: {cpu_mean}")
    print(f"Median: {cpu_median}")
    print(f"25th Percentile (Q1): {cpu_q1}")
    print(f"75th Percentile (Q3): {cpu_q3}")

    print("\nLatency Differences:")
    print(f"Mean: {latency_mean}")
    print(f"Median: {latency_median}")
    print(f"25th Percentile (Q1): {latency_q1}")
    print(f"75th Percentile (Q3): {latency_q3}")

    # Create a DataFrame for the violin plot
    plot_data = pd.DataFrame({
        'Difference': pd.concat([cpu_diffs, latency_diffs]),
        'Stat': ['CPU'] * len(cpu_diffs) + ['Latency'] * len(latency_diffs)
    })

    # Create the plot
    plt.figure(figsize=(10, 6))
    sns.violinplot(x='Stat', y='Difference', data=plot_data, inner='quart', scale='width', palette='muted', showmeans=False, showmedians=False, showextrema=False)

    # Customize the plot
    plt.title('Difference Violin Plots for CPU and Latency', fontsize=14)
    plt.xlabel('Stat', fontsize=12)
    plt.ylabel('Difference', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    # Save the plot as a PDF
    plt.savefig(output_pdf, format='pdf')
    print(f"Violin plot saved to {output_pdf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create violin plots for CPU and Latency differences.")
    parser.add_argument('diff_file', help="Input CSV file containing the differences")
    parser.add_argument('output_pdf', help="Output PDF file to save the violin plots")

    args = parser.parse_args()

    create_violin_plot(args.diff_file, args.output_pdf)
