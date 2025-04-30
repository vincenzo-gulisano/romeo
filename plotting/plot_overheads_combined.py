import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def create_violin_plots(bo_co_lr, bo_co_s, output_pdf):
    # Load data from the input CSV files
    data_sources = {
        "bo_co_lr": bo_co_lr,
        "bo_co_s": bo_co_s,
    }
    
    dataframes = {}
    for label, filepath in data_sources.items():
        df = pd.read_csv(filepath)
        df['source'] = label  # Add a source column for grouping
        df['abs_value_diff'] = df['value_diff'] #.abs()  # Add a column with the absolute value of value_diff
        dataframes[label] = df
    
    # Combine all data into a single DataFrame
    combined_df = pd.concat(dataframes.values(), ignore_index=True)

    # Filter data for CPU and Latency
    cpu_data = combined_df[combined_df['stat'] == 'CPU']
    
    # Aggregate CPU data by 'exp_id' to compute the mean per experiment
    cpu_data_means = cpu_data.groupby(['source', 'exp_id'])['value_base'].mean().reset_index()
    cpu_data_diff_means = cpu_data.groupby(['source', 'exp_id'])['abs_value_diff'].mean().reset_index()

    latency_data = combined_df[combined_df['stat'] == 'Latency']

    # Aggregate CPU data by 'exp_id' to compute the mean per experiment
    latency_data_means = latency_data.groupby(['source', 'exp_id'])['value_base'].mean().reset_index()
    latency_data_diff_means = latency_data.groupby(['source', 'exp_id'])['abs_value_diff'].mean().reset_index()

    # Scale the value_diff column
    cpu_data['value_base'] /= 100
    latency_data['value_base'] /= 1000
    cpu_data['value_diff'] /= 100
    latency_data['value_diff'] /= 1000
    cpu_data['abs_value_diff'] /= 100
    latency_data['abs_value_diff'] /= 1000
    cpu_data_means['value_base'] /= 100
    cpu_data_diff_means['abs_value_diff'] /= 100
    latency_data_means['value_base'] /= 1000
    latency_data_diff_means['abs_value_diff'] /= 1000

    text_width_pt = 506 / 2
    text_height_pt = 270 * 0.35 * 2
    points_per_inch = 72
    text_width_in = text_width_pt / points_per_inch
    text_height_in = text_height_pt / points_per_inch
    
    plt.rcParams.update({"font.size": 7})  # Set global font size to 10

    # Create the plots
    fig, axes = plt.subplots(2, 2, figsize=(text_width_in, text_height_in))

    # Left: Violin plot for CPU
    sns.violinplot(
        data=cpu_data_means,
        x='source',
        y='value_base',
        ax=axes[0,0],
        cut=0,  # Limit violin plot strictly to min and max of data
        palette='muted',
        scale='width',
        inner=None, showmeans=False, showmedians=False, showextrema=False,
        linewidth=0.5,  # Set the outer line width
    )
    axes[0,0].set_ylabel('Base CPU Cons.')
    axes[0,0].set_xlabel('')  # Remove Y-axis label
    axes[0,0].set_xticks(range(len(cpu_data['source'].unique())))  # Set custom X-ticks
    axes[0,0].set_xticklabels(
            ['', '']
        )

    # Add mean as horizontal lines
    cpu_means = cpu_data_means.groupby('source')['value_base'].mean().reset_index()

    for i, source in enumerate(cpu_means['source']):
        mean_value = cpu_means.loc[cpu_means['source'] == source, 'value_base'].values[0]
        axes[0, 0].hlines(
            mean_value, i - 0.25, i + 0.25,  # Line spans slightly within the width of each violin
            color='black', linestyle='-', linewidth=1.5, label=f"Mean ({source})" if i == 0 else ""
        )

    # Right: Violin plot for Latency
    sns.violinplot(
        data=latency_data_means,
        x='source',
        y='value_base',
        ax=axes[0,1],
        palette='muted',
        cut=0,  # Limit violin plot strictly to min and max of data
        scale='width', 
        inner=None, showmeans=False, showmedians=False, showextrema=False,
        linewidth=0.5,  # Set the outer line width
    )
    axes[0,1].set_ylabel('Base Latency (s)')
    axes[0,1].set_xlabel('')  # Remove Y-axis label
    axes[0,1].set_xticks(range(len(latency_data['source'].unique())))  # Set custom X-ticks
    axes[0,1].set_xticklabels(
        ['', '']
    )

    # Add mean as horizontal lines
    latency_means = latency_data_means.groupby('source')['value_base'].mean().reset_index()

    for i, source in enumerate(latency_means['source']):
        mean_value = latency_means.loc[latency_means['source'] == source, 'value_base'].values[0]
        axes[0, 1].hlines(
            mean_value, i - 0.25, i + 0.25,  # Line spans slightly within the width of each violin
            color='black', linestyle='-', linewidth=1.5, label=f"Mean ({source})" if i == 0 else ""
        )
        
    # Left: Violin plot for CPU
    sns.violinplot(
        data=cpu_data_diff_means,
        x='source',
        y='abs_value_diff',
        ax=axes[1,0],
        cut=0,  # Limit violin plot strictly to min and max of data
        palette='muted',
        scale='width',
        inner=None, showmeans=False, showmedians=False, showextrema=False,
        linewidth=0.5,  # Set the outer line width
    )
    axes[1,0].set_ylabel('CPU Cons. Diff.')
    axes[1,0].set_xlabel('')  # Remove Y-axis label
    axes[1,0].set_xticks(range(len(cpu_data['source'].unique())))  # Set custom X-ticks
    axes[1,0].set_xticklabels(
        ['LR', 'S']
    )

    # Add mean as horizontal lines
    cpu_diff_means = cpu_data_diff_means.groupby('source')['abs_value_diff'].mean().reset_index()

    for i, source in enumerate(cpu_diff_means['source']):
        mean_value = cpu_diff_means.loc[cpu_diff_means['source'] == source, 'abs_value_diff'].values[0]
        axes[1, 0].hlines(
            mean_value, i - 0.25, i + 0.25,  # Line spans slightly within the width of each violin
            color='black', linestyle='-', linewidth=1.5, label=f"Mean ({source})" if i == 0 else ""
        )
        
    # Right: Violin plot for Latency
    sns.violinplot(
        data=latency_data_diff_means,
        x='source',
        y='abs_value_diff',
        ax=axes[1,1],
        palette='muted',
        cut=0,  # Limit violin plot strictly to min and max of data
        scale='width', 
        inner=None, showmeans=False, showmedians=False, showextrema=False,
        linewidth=0.5,  # Set the outer line width
    )
    axes[1,1].set_ylabel('Latency Diff. (s)')
    axes[1,1].set_xlabel('')  # Remove Y-axis label
    axes[1,1].set_xticks(range(len(latency_data['source'].unique())))  # Set custom X-ticks
    axes[1,1].set_xticklabels(
        ['LR', 'S']
    )

    # Add mean as horizontal lines
    latency_diff_means = latency_data_diff_means.groupby('source')['abs_value_diff'].mean().reset_index()

    for i, source in enumerate(latency_diff_means['source']):
        mean_value = latency_diff_means.loc[latency_diff_means['source'] == source, 'abs_value_diff'].values[0]
        axes[1, 1].hlines(
            mean_value, i - 0.25, i + 0.25,  # Line spans slightly within the width of each violin
            color='black', linestyle='-', linewidth=1.5, label=f"Mean ({source})" if i == 0 else ""
        )
        
    
    # Compute and print quantiles and mean for CPU data grouped by 'source'
    print("CPU Data (value_base) Statistics by Source:")
    cpu_stats = cpu_data_means.groupby('source')['value_base'].agg(
        mean='mean',
        q01=lambda x: x.quantile(0.01),
        q25=lambda x: x.quantile(0.25),
        q50=lambda x: x.quantile(0.5),
        q75=lambda x: x.quantile(0.75),
        q99=lambda x: x.quantile(0.99)
    )
    print(cpu_stats)
    
    # Compute and print quantiles and mean for CPU data grouped by 'source'
    print("CPU Data (abs_value_diff) Statistics by Source:")
    cpu_stats = cpu_data_diff_means.groupby('source')['abs_value_diff'].agg(
        mean='mean',
        q01=lambda x: x.quantile(0.01),
        q25=lambda x: x.quantile(0.25),
        q50=lambda x: x.quantile(0.5),
        q75=lambda x: x.quantile(0.75),
        q99=lambda x: x.quantile(0.99)
    )
    print(cpu_stats)

    # Compute and print quantiles and mean for Latency data grouped by 'source'
    print("\nLatency Data (value_base) Statistics by Source:")
    latency_stats = latency_data_means.groupby('source')['value_base'].agg(
        mean='mean',
        q01=lambda x: x.quantile(0.01),
        q25=lambda x: x.quantile(0.25),
        q50=lambda x: x.quantile(0.5),
        q75=lambda x: x.quantile(0.75),
        q99=lambda x: x.quantile(0.99)
    )
    print(latency_stats)
    
    # Compute and print quantiles and mean for Latency data grouped by 'source'
    print("\nLatency Data (abs_value_diff) Statistics by Source:")
    latency_stats = latency_data_diff_means.groupby('source')['abs_value_diff'].agg(
        mean='mean',
        q01=lambda x: x.quantile(0.01),
        q25=lambda x: x.quantile(0.25),
        q50=lambda x: x.quantile(0.5),
        q75=lambda x: x.quantile(0.75),
        q99=lambda x: x.quantile(0.99)
    )
    print(latency_stats)

    # Save the plot to the output PDF
    plt.tight_layout()
    plt.savefig(output_pdf)
    plt.close()
    print(f"Plots saved to {output_pdf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create violin plots from experiment data")
    parser.add_argument("bo_co_lr", help="Input file for bo_co_lr")
    parser.add_argument("bo_co_s", help="Input file for bo_co_s")
    parser.add_argument("output_pdf", help="Output PDF file for the plots")
    args = parser.parse_args()

    create_violin_plots(args.bo_co_lr, args.bo_co_s, args.output_pdf)
