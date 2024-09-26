import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.tools as tls


def plot_graphs(rate_file_path, agent_data, output_pdf, usecase):
    
    plt.rcParams.update({"font.size": 8})  # Set global font size to 10

    # Create a figure and a set of subplots, now with 4 rows
    text_width_pt = 506 / 2 * 2
    text_height_pt = 180 * 2
    points_per_inch = 72
    text_width_in = text_width_pt / points_per_inch
    text_height_in = text_height_pt / points_per_inch

    initial_opacity = 0.3
    final_opacity = 0.9
    splits = 3  # Number of portions to divide the subset into
    min_line_width = 2  # Set your desired maximum line width
    max_line_width = 2  # Set your desired maximum line width
    smoothing_window_size = 5
    
    fig, axs = plt.subplots(
        7,
        splits,
        figsize=(text_width_in, text_height_in),
        gridspec_kw={"hspace": 0, "wspace": 0, "height_ratios": [0.2, 1, 1, 1, 1, 1, 1]},
    )

    # Read the RL policies file
    policies_file_path = os.path.join(agent_data)
    policies_df = pd.read_csv(policies_file_path)

    # Convert the 'baseline' column to text (object) type
    policies_df["baseline"] = policies_df["baseline"].astype(str)

    # The values represent: initial size, fine size, initial opacity, final opacity, color, prob. of selection
    agent_plots = {
        "welob_linear": [1, 10, 0.1, 1, "red", 0.25],
        "elob_linear": [1, 10, 0.1, 1, "orange", 0.25],
        "lob_linear": [1, 10, 0.1, 1, "blue", 0.25],
        "welaw_linear": [
            1,
            10,
            0.1,
            1,
            "green",
            0.125,
        ],  # 0.125 for first experiments wince we have 200 episodes
        "welob_synthetic": [1, 10, 0.1, 1, "red", 0.25],
        "elob_synthetic": [1, 10, 0.1, 1, "orange", 0.25],
        "lob_synthetic": [1, 10, 0.1, 1, "blue", 0.25],
        "welaw_synthetic": [
            1,
            10,
            0.1,
            1,
            "green",
            0.125,
        ],  # 0.125 for first experiments wince we have 200 episodes
        "13.1": [1, 5, 0.1, 0.8, "red", 1],
        "13.2": [1, 5, 0.1, 0.8, "green", 1],
        "12.1": [1, 5, 0.1, 0.8, "red", 1],
        "12.2": [5, 10, 0.1, 0.8, "green", 1],
    }

    if usecase == 'linearroad':
        policies_order = [
            "welob_linear",
            "elob_linear",
            "lob_linear",
            "welaw_linear",
        ]  # The desired order for baselines
        cpu_ylim = [0,0.1]
        latency_ylim = [0,2]
        ncratio_ylim = [-0.1,1.1]
        steps_ylim = [0,55]
        reward_ylim = [0,150]
        violations_ylim = [0,55]
    elif usecase == 'synthetic':
        policies_order = [
            "welob_synthetic",
            "elob_synthetic",
            "lob_synthetic",
            "welaw_synthetic",
        ]  # The desired order for baselines
        cpu_ylim = [0,1]
        latency_ylim = [0,2]
        ncratio_ylim = [0.5,1.0]
        steps_ylim = [0,55]
        reward_ylim = [0,150]
        violations_ylim = [0,55]
    elif usecase == 'synthetic5s':
        policies_order = [
            "welob_synthetic",
            "elob_synthetic",
            "lob_synthetic",
            "welaw_synthetic",
        ]  # The desired order for baselines
        cpu_ylim = [-0.1,1.1]
        latency_ylim = [0,2]
        ncratio_ylim = [-0.1,1.1]
        steps_ylim = [0,55]
        reward_ylim = [0,150]
        violations_ylim = [0,55]

    policies_labels = {
        "welob_linear": "WEL-OB",
        "elob_linear": "EL-OB",
        "lob_linear": "L-OB",
        "welaw_linear": "WEL-AW",
        "welob_synthetic": "WEL-OB",
        "elob_synthetic": "EL-OB",
        "lob_synthetic": "L-OB",
        "welaw_synthetic": "WEL-AW",
    }
    
    opacities = np.geomspace(
        start=initial_opacity,
        stop=final_opacity,
        num=splits,
    )

    # Specify color and font size
    text_fontsize = 8  # Example font size

    latencies_thresholds = [1.5]
    latencies_thresholds_ids = ["QoS threshold"]

    # Read the first and second columns from the CSV
    dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
    dfrate.columns = ["x", "y"]

    for ax in axs[0, 0:]:
        ax.set_visible(False)
    
    axs[1,0].set_ylabel("n/c ratio", fontsize=text_fontsize)
    for ax in axs[1, 0:]:
        ax.set_xticks([])
        ax.grid(
            True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
        )
    
    axs[2,0].set_ylabel("Latency (s)", fontsize=text_fontsize)
    for ax in axs[2, 0:]:
        ax.set_xticks([])

    axs[3,0].set_ylabel("CPU (%)", fontsize=text_fontsize)
    for ax in axs[3, 0:]:
        ax.set_xticks([])
        ax.grid(
            True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
        )
    
    # Create a set for faster membership tests
    unique_baselines_set = set(policies_df["baseline"].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [
        baseline for baseline in policies_order if baseline in unique_baselines_set
    ]

    # The following variables are used to find the min and max event times in the plot
    min_et = None
    max_et = None

    for i, baseline in enumerate(unique_baselines):
        subset = policies_df[policies_df["baseline"] == baseline]
            
        if baseline in agent_plots:
                     
            # Split the subset into `n` portions
            portions = np.array_split(subset, splits)

            for portion_num, portion in enumerate(portions, 1):
                if portion.empty: # or portion_num!=splits:
                    continue  # Skip if the portion is empty

                # Sort subset by 'eventtime_start'
                portion = portion.sort_values(by="eventtime_start")

                # Line width proportional to portion number, scaled between 1 and max_line_width
                line_width = min_line_width + (portion_num - 1) * (max_line_width - 1) / (splits - 1)

                # Extract x and y coordinates
                x_coords = portion["eventtime_start"] - dfrate["x"].min()
                y_coords_ratio = portion["q2_ratio"] / 100
                y_coords_latency = portion["q2_latency"] / 1000
                y_coords_cpu = portion["q2_cpu"] / 100
                y_coords_steps = portion["steps"]
                y_coords_reward = portion["cum_reward"]
                y_coords_violations = portion["sum_violations"]

                # smooth the line
                smooth_points_ratio = (
                    pd.Series(y_coords_ratio)
                    .rolling(window=smoothing_window_size, center=True)
                    .mean()
                )
                smooth_points_latency = (
                    pd.Series(y_coords_latency)
                    .rolling(window=smoothing_window_size, center=True)
                    .mean()
                )
                smooth_points_cpu = (
                    pd.Series(y_coords_cpu)
                    .rolling(window=smoothing_window_size, center=True)
                    .mean()
                )
                smooth_points_steps = (
                    pd.Series(y_coords_steps)
                    .rolling(window=smoothing_window_size, center=True)
                    .mean()
                )
                smooth_points_reward = (
                    pd.Series(y_coords_reward)
                    .rolling(window=smoothing_window_size, center=True)
                    .mean()
                )
                smooth_points_violations = (
                    pd.Series(y_coords_violations)
                    .rolling(window=smoothing_window_size, center=True)
                    .mean()
                )

                # Plot the line for the current portion with line thickness proportional to portion number
                # axs[2].plot(x_coords, y_coords_ratio, color=agent_plots[baseline][4],
                #             linewidth=line_width, alpha=opacities[portion_num-1])
                # Plot the smooth line
                axs[1,portion_num-1].plot(
                    x_coords,
                    smooth_points_ratio,
                    color=agent_plots[baseline][4],
                    label=policies_labels[baseline],
                    linewidth=line_width,
                    alpha=opacities[portion_num - 1],
                )

                # Plot the line for the current portion with line thickness proportional to portion number
                # axs[3].plot(x_coords, y_coords_latency, color=agent_plots[baseline][4],
                #             linewidth=line_width, alpha=opacities[portion_num-1])
                # Plot the smooth line
                axs[2,portion_num-1].plot(
                    x_coords,
                    smooth_points_latency,
                    color=agent_plots[baseline][4],
                    label=policies_labels[baseline],
                    linewidth=line_width,
                    alpha=opacities[portion_num - 1],
                )

                # Plot the line for the current portion with line thickness proportional to portion number
                # axs[4].plot(x_coords, y_coords_cpu, color=agent_plots[baseline][4],
                #             linewidth=line_width, alpha=opacities[portion_num-1])
                # Plot the smooth line
                axs[3,portion_num-1].plot(
                    x_coords,
                    smooth_points_cpu,
                    color=agent_plots[baseline][4],
                    label=policies_labels[baseline],
                    linewidth=line_width,
                    alpha=opacities[portion_num - 1],
                )

                axs[4,portion_num-1].plot(
                    x_coords,
                    smooth_points_steps,
                    color=agent_plots[baseline][4],
                    label=policies_labels[baseline],
                    linewidth=line_width,
                    alpha=opacities[portion_num - 1],
                )
                
                axs[5,portion_num-1].plot(
                    x_coords,
                    smooth_points_reward,
                    color=agent_plots[baseline][4],
                    label=policies_labels[baseline],
                    linewidth=line_width,
                    alpha=opacities[portion_num - 1],
                )
                
                axs[6,portion_num-1].plot(
                    x_coords,
                    smooth_points_violations,
                    color=agent_plots[baseline][4],
                    label=policies_labels[baseline],
                    linewidth=line_width,
                    alpha=opacities[portion_num - 1],
                )
                
                # Update min_et and max_et based on the current portion
                if min_et is None or x_coords.min() < min_et:
                    min_et = x_coords.min()
                if max_et is None or x_coords.max() > max_et:
                    max_et = x_coords.max()
            
    
    for ax in axs[1, (splits-2):(splits-1)]:
        ax.legend(
            loc="upper center",  # Position the legend at the top center
            bbox_to_anchor=(0.5, 1.25),  # Adjust the position above the axis
            ncol=4,  # Number of columns
            columnspacing=0.2,  # Adjust the space between columns
        )
        # axs[1].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    for ax in axs[1, 0:]:
        ax.set_ylim(ncratio_ylim)
    for ax in axs[1, 1:]:
        ax.set_yticklabels([])

    for ax in axs[2, 0:]:
        ax.set_ylim(latency_ylim)
    for ax in axs[2, 1:]:
        ax.set_yticklabels([])

    for lat_idx, latency_threshold in enumerate(latencies_thresholds):
        for ax in axs[2, 0:]:
            ax.axhline(
                y=latency_threshold, color="r", linestyle="--"
            )  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[2,0].text(
            2000,
            latency_threshold * 1.01,
            latencies_thresholds_ids[lat_idx],
            color="red",
            verticalalignment="bottom",
            horizontalalignment="left",
            fontsize=8,
            transform=axs[2,0].transData,
        )
    
    for ax in axs[3, 0:]:
        ax.set_ylim(cpu_ylim)
    for ax in axs[3, 1:]:
        ax.set_yticklabels([])

    
    axs[4,0].set_ylabel("steps", fontsize=text_fontsize)
    for ax in axs[4, 0:]:
        ax.set_ylim(steps_ylim)
        ax.set_xticks([])
    for ax in axs[4, 1:]:
        ax.set_yticklabels([])

    axs[5,0].set_ylabel("Acts. Reward", fontsize=text_fontsize)
    for ax in axs[5, 0:]:
        ax.set_xticks([])
        ax.set_ylim(reward_ylim)
    for ax in axs[5, 1:]:
        ax.set_yticklabels([])

    axs[6,0].set_ylabel("Violations", fontsize=text_fontsize)
    for ax in axs[6, 0:]:
        ax.set_xlabel(
            "Event Time (s)", fontsize=text_fontsize
        )  # Only the last subplot needs the x-axis label
        ax.set_ylim(violations_ylim)
    for ax in axs[6, 1:]:
        ax.set_yticklabels([])

    # adjust x lim of left plots
    
    for ax in axs[0, 0:]:
        ax.set_xlim([min_et * 0.95, max_et * 1.05])
    for ax in axs[1, 0:]:
        ax.set_xlim([min_et * 0.95, max_et * 1.05])
    for ax in axs[2, 0:]:
        ax.set_xlim([min_et * 0.95, max_et * 1.05])
    for ax in axs[3, 0:]:
        ax.set_xlim([min_et * 0.95, max_et * 1.05])
    for ax in axs[4, 0:]:
        ax.set_xlim([min_et * 0.95, max_et * 1.05])
    for ax in axs[5, 0:]:
        ax.set_xlim([min_et * 0.95, max_et * 1.05])
    for ax in axs[6, 0:]:
        ax.set_xlim([min_et * 0.95, max_et * 1.05])
    
    # Adjust layout
    fig.tight_layout()

    # Save the figure
    plt.savefig(output_pdf)
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate plots from baselines_data.csv."
    )
    # parser.add_argument('base_folder', type=str, help='Input folder containing baselines_data.csv.')
    parser.add_argument(
        "rate_file_path",
        type=str,
        help="Input file containing per second input rate of the input data.",
    )
    parser.add_argument(
        "agent_data", type=str, help="Input file containing the RL agent stats."
    )
    parser.add_argument("output_pdf", type=str, help="Output PDF file.")
    parser.add_argument("usecase", type=str, help="usecase")

    args = parser.parse_args()

    plot_graphs(args.rate_file_path, args.agent_data, args.output_pdf, args.usecase)