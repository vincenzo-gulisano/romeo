import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.ticker as ticker
import sys


# Define a function to handle edge cases
def rolling_mean_custom(series, window):
    return [np.mean(series[max(0, i - window // 2): i + window // 2 + 1]) for i in range(len(series))]


def plot_graphs(
    base_folder,
    rate_file_path,
    agent_data,
    output_pdf,
    output_png,
    # probs,
    # probs_episod,
    usecase,
    barplots_ids,
    barplots_ids_labels,
):

    # Now the part about the RL agent
    # Read the baselines_data.csv file
    baseline_file_path = os.path.join(agent_data)
    baseline_df = pd.read_csv(baseline_file_path)

    # Read the baselines_data.csv file
    file_path = os.path.join(base_folder, "baselines_data.csv")
    df = pd.read_csv(file_path)

    plt.rcParams.update({"font.size": 7})  # Set global font size to 10

    # Create a figure and a set of subplots
    text_width_pt = 506 / 2
    text_height_pt = 270 * 1.8
    points_per_inch = 72
    text_width_in = text_width_pt / points_per_inch
    text_height_in = text_height_pt / points_per_inch
    fig, axs = plt.subplots(
        10,
        1,
        figsize=(text_width_in, text_height_in),
        gridspec_kw={
            "hspace": 0,
            "wspace": 0,
            "height_ratios": [1, 0, 1, 1, 1, 1, 0.5, 1, 1, 1],
        },
    )

    axs[1].set_visible(False)
    axs[6].set_visible(False)

    given_order = [
        10,
        9,
        8,
        7,
        6,
        5,
        4,
        3,
        2,
        1,
        0,
        # "r",
    ]
    # The desired order for baselines
    xtick_labels = [
        r"$1.0$",
        r"$0.9$",
        r"$0.8$",
        r"$0.7$",
        r"$0.6$",
        r"$0.5$",
        r"$0.4$",
        r"$0.3$",
        r"$0.2$",
        r"$0.1$",
        r"$0.0$",
    ]
    xtick_labels.extend(barplots_ids_labels)
    # Create a set for faster membership tests
    unique_baselines_set = set(df["baseline"].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [
        baseline for baseline in given_order if baseline in unique_baselines_set
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Blue, Orange, Green, Red

    if usecase == "linearroad":

        # This config are for LinearRoad
        boundaries = [0.5, 10.5]  # , 11.5]
        boundary_text = ["safe"]  # , "unsafe"]
        boundary_text_align = ["left", "left"]
        latency_y_scale = "log"
        latency_y_lim_baselines = [0.03, 6]
        latency_y_lim_agent = [0.1, 4]
        latency_y_ticks_agent = [0.2, 0.5, 2]
        latency_y_ticks_baseline = [0.1, 1.5, 5]
        ratio_y_lim = [-0.1, 1.1]
        cpu_y_lim = [0.0, 1.1]
        smoothing_window_size = 10

    elif usecase == "synthetic":

        # This config are for Synthetic
        boundaries = [0.5, 4.5]  # , 11.5, 11.5]
        boundary_text = ["safe"]  # , "", "unsafe"]
        boundary_text_align = ["left", "left", "right"]
        latency_y_scale = "log"
        latency_y_lim_baselines = [0.005, 100]
        latency_y_lim_agent = [0.5, 2]
        latency_y_ticks_agent = [0.6, 1, 2]
        latency_y_ticks_baseline = [0.1, 1.5, 10]
        ratio_y_lim = [0.5, 0.8]
        cpu_y_lim = [0.3, 0.9]
        smoothing_window_size = 10

    initial_opacity = 0.3
    final_opacity = 0.9
    splits = 2  # Number of portions to divide the subset into
    max_line_width = 1  # Set your desired maximum line width
    agent_color = "green"

    # Specify color and font size
    text_color = "green"  # Example color
    text_fontsize = 7  # Example font size

    latencies_thresholds = [1.5]
    latencies_thresholds_ids = [r"  $\ell$ threshold"]

    # Read the first and second columns from the CSV
    dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
    dfrate.columns = ["x", "y"]

    # Now, df['x'] and df['y'] are your x_data and y_data
    x_data = dfrate["x"]
    y_data = dfrate["y"]

    # Plot input rate on the new top axes (axs[0])
    axs[0].plot(x_data - dfrate["x"].min(), y_data / 1000, linestyle="-", color="blue")
    axs[0].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])
    axs[0].set_ylabel(r"Input rate ($10^3$ t/s)", fontsize=text_fontsize)
    axs[0].set_xticks([])

    # Adjust the indices for the other axes since we added a new one at the top
    # mean_ratio, divided by 100
    data_mean_ratio = [
        df[df["baseline"] == baseline]["q2_ratio"].dropna() / 100
        for baseline in unique_baselines
    ]
        
    # Store the length of the first dataset (from df) for color differentiation
    df_length = len(data_mean_ratio)

    for barplot_id in barplots_ids:
        data_mean_ratio.append(
            baseline_df[baseline_df["baseline"] == barplot_id]["mean_ratio"].dropna()
            / 100
        )
    parts = axs[7].violinplot(
        data_mean_ratio, showmeans=False, showmedians=False, showextrema=False
    )
    for i, pc in enumerate(parts["bodies"]):
        if i < df_length:
            # Data from df
            pc.set_facecolor("#D43F3A")  # Color for df data
        else:
            # Data from baseline_df
            pc.set_facecolor("#008000")  # Different color for baseline_df data
        pc.set_edgecolor("black")
        pc.set_alpha(1)
    axs[7].set_ylabel("n/c ratio", fontsize=text_fontsize)
    # Set specific tick positions
    axs[7].set_ylim([-0.1, 1.1])
    # Enable the grid
    axs[7].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )

    # latency, divided by 1000
    data_latency = [
        df[df["baseline"] == baseline]["q3_latency"].dropna() / 1000
        for baseline in unique_baselines
    ]
    
    for barplot_id in barplots_ids:
        data_latency.append(
            baseline_df[baseline_df["baseline"] == barplot_id]["mean_latency"].dropna()
            / 1000
        )
    parts = axs[8].violinplot(
        data_latency, showmeans=False, showmedians=False, showextrema=False
    )
    for i, pc in enumerate(parts["bodies"]):
        if i < df_length:
            # Data from df
            pc.set_facecolor("#D43F3A")  # Color for df data
        else:
            # Data from baseline_df
            pc.set_facecolor("#008000")  # Different color for baseline_df data
        pc.set_edgecolor("black")
        pc.set_alpha(1)
    axs[8].set_ylim(latency_y_lim_baselines)
    axs[8].set_ylabel("Latency (s)", fontsize=text_fontsize)
    axs[8].set_yscale(latency_y_scale)
    axs[8].set_yticks(latency_y_ticks_baseline)
    # Format the y-tick labels to show numbers with up to one decimal place
    axs[8].yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f"{x:.1f}" if x % 1 else f"{int(x)}")
    )
    for lat_idx, latency_threshold in enumerate(latencies_thresholds):
        axs[8].axhline(
            y=latency_threshold, color="r", linestyle="--"
        )  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[8].text(
            0.7,
            latency_threshold * 1.05,
            latencies_thresholds_ids[lat_idx],
            color="red",
            verticalalignment="bottom",
            horizontalalignment="left",
            fontsize=text_fontsize,
            transform=axs[8].transData,
        )

    # cpu, divided by 100
    data_cpu = [
        df[df["baseline"] == baseline]["q2_cpu"].dropna() / 100
        for baseline in unique_baselines
    ]
    
    # axs[4,1].boxplot(data_cpu, labels=unique_baselines)
    for barplot_id in barplots_ids:
        data_cpu.append(
            baseline_df[baseline_df["baseline"] == barplot_id]["mean_cpu"].dropna() / 100
        )
    parts = axs[9].violinplot(
        data_cpu, showmeans=False, showmedians=False, showextrema=False
    )
    for i, pc in enumerate(parts["bodies"]):
        if i < df_length:
            # Data from df
            pc.set_facecolor("#D43F3A")  # Color for df data
        else:
            # Data from baseline_df
            pc.set_facecolor("#008000")  # Different color for baseline_df data
        pc.set_edgecolor("black")
        pc.set_alpha(1)
    axs[9].set_ylabel("CPU cons.", fontsize=text_fontsize)
    axs[9].set_xlabel(
        # r"Baseline ($D$ value, or $R$ for random)", fontsize=text_fontsize
        r"Baseline ($X$ value), or Agent policy",
        fontsize=text_fontsize,
    )  # Only the last subplot needs the x-axis label
    axs[9].set_xticks(np.arange(1, len(xtick_labels) + 1))  # Set tick positions
    # print(len(unique_baselines) + 1)
    axs[9].set_xticklabels(xtick_labels, fontsize=text_fontsize, rotation=45)
    axs[9].set_ylim([-0.1, 1.1])
    # Enable the grid
    axs[9].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )

    # Add vertical lines in all axes for each X value in boundaries (adjusting index for axs)
    for ax in axs[7:]:
        for boundary in boundaries:
            ax.axvline(x=boundary, color="g", linestyle="--")

    # Add text on top of the second axes (previously first) in between consecutive pairs of boundaries
    for i, text in enumerate(boundary_text):
        # Calculate the position to place the text (middle between boundaries)
        x_pos = boundaries[i]
        # Place the text at the calculated position, with a slight offset upwards
        axs[7].text(
            x_pos,
            1.01,
            text,
            transform=axs[7].get_xaxis_transform(),
            ha=boundary_text_align[i],
            va="bottom",
            color=text_color,
            fontsize=text_fontsize,
        )

    # Convert the 'baseline' column to text (object) type
    baseline_df["baseline"] = baseline_df["baseline"].astype(str)

    # Create a set for faster membership tests
    unique_baselines_set = set(baseline_df["baseline"].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [
        baseline for baseline in given_order if baseline in unique_baselines_set
    ]

    # The following variables are used to find the min and max event times in the plot
    min_et = None
    max_et = None

    for agent_num, agent_id in enumerate(barplots_ids, 0):
        subset = baseline_df[baseline_df["baseline"] == agent_id]

        opacities = np.geomspace(
            start=initial_opacity,
            stop=final_opacity,
            num=splits,
        )

        # Split the subset into `n` portions
        portions = np.array_split(subset, splits)

        for portion_num, portion in enumerate(portions, 1):
            if portion.empty or portion_num != splits:
                continue  # Skip if the portion is empty

            # Sort subset by 'eventtime_start'
            portion = portion.sort_values(by="eventtime_start")

            # Line width proportional to portion number, scaled between 1 and max_line_width
            if splits>1:
                line_width = 1 + (portion_num - 1) * (max_line_width - 1) / (splits - 1)
            else:
                line_width = max_line_width
                
            # Extract x and y coordinates
            x_coords = portion["eventtime_start"] - dfrate["x"].min()
            y_coords_ratio = portion["mean_ratio"] / 100
            y_coords_latency = portion["mean_latency"] / 1000
            y_coords_cpu = portion["mean_cpu"] / 100
            y_coords_duration = portion["duration"]

            # smooth the line
            smooth_points_ratio = rolling_mean_custom(y_coords_ratio, smoothing_window_size)
            # smooth_points_ratio = (
            #     pd.Series(y_coords_ratio)
            #     .rolling(window=smoothing_window_size, center=True)
            #     .mean()
            # )
            smooth_points_latency = rolling_mean_custom(y_coords_latency, smoothing_window_size)
            # smooth_points_latency = (
            #     pd.Series(y_coords_latency)
            #     .rolling(window=smoothing_window_size, center=True)
            #     .mean()
            # )
            smooth_points_cpu = rolling_mean_custom(y_coords_cpu, smoothing_window_size)
            # smooth_points_cpu = (
            #     pd.Series(y_coords_cpu)
            #     .rolling(window=smoothing_window_size, center=True)
            #     .mean()
            # )
            smooth_points_duration = rolling_mean_custom(y_coords_duration, smoothing_window_size)
            # smooth_points_duration = (
            #     pd.Series(y_coords_duration)
            #     .rolling(window=smoothing_window_size, center=True)
            #     .mean()
            # )

            # Plot the line for the current portion with line thickness proportional to portion number
            # axs[2].plot(x_coords, y_coords_ratio, color=agent_plots[baseline][4],
            #             linewidth=line_width, alpha=opacities[portion_num-1])
            # Plot the smooth line
            axs[2].plot(
                x_coords,
                smooth_points_ratio,
                color=colors[agent_num],
                linewidth=line_width,
                alpha=opacities[portion_num - 1]
            )
            

            # Plot the line for the current portion with line thickness proportional to portion number
            # axs[3].plot(x_coords, y_coords_latency, color=agent_plots[baseline][4],
            #             linewidth=line_width, alpha=opacities[portion_num-1])
            # Plot the smooth line
            axs[3].plot(
                x_coords,
                smooth_points_latency,
                color=colors[agent_num],
                linewidth=line_width,
                alpha=opacities[portion_num - 1],
            )

            # Plot the line for the current portion with line thickness proportional to portion number
            # axs[4].plot(x_coords, y_coords_cpu, color=agent_plots[baseline][4],
            #             linewidth=line_width, alpha=opacities[portion_num-1])
            # Plot the smooth line
            axs[4].plot(
                x_coords,
                smooth_points_cpu,
                color=colors[agent_num],
                linewidth=line_width,
                alpha=opacities[portion_num - 1],
                label=barplots_ids_labels[agent_num],
            )

            axs[5].plot(
                x_coords,
                smooth_points_duration,
                color=colors[agent_num],
                linewidth=line_width,
                alpha=opacities[portion_num - 1],
            )


            # Update min_et and max_et based on the current portion
            if min_et is None or x_coords.min() > min_et:
                min_et = x_coords.min()
            if max_et is None or x_coords.max() < max_et:
                max_et = x_coords.max()

    axs[4].legend(ncol=4, handletextpad=0.5, columnspacing=0.5)
    axs[2].set_ylabel("n/c ratio", fontsize=text_fontsize)
    axs[2].set_ylim(ratio_y_lim)
    axs[2].set_xticks([])
    axs[2].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )
    axs[2].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])

    for lat_idx, latency_threshold in enumerate(latencies_thresholds):
        axs[3].axhline(
            y=latency_threshold, color="r", linestyle="--"
        )  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[3].text(
            min_et,
            latency_threshold * 1.05,
            latencies_thresholds_ids[lat_idx],
            color="red",
            verticalalignment="bottom",
            horizontalalignment="left",
            fontsize=text_fontsize,
            transform=axs[3].transData,
        )
    axs[3].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])
    axs[3].set_ylim(latency_y_lim_agent)
    axs[3].set_yscale(latency_y_scale)
    axs[3].set_ylabel("Latency (s)", fontsize=text_fontsize)
    axs[3].set_xticks([])
    # Specify custom y-ticks
    axs[3].set_yticks(latency_y_ticks_agent)
    # Format the y-tick labels to show numbers with up to one decimal place
    axs[3].yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f"{x:.1f}" if x % 1 else f"{int(x)}")
    )

    axs[4].set_ylabel("CPU cons.", fontsize=text_fontsize)
    axs[4].set_ylim(cpu_y_lim)
    axs[4].set_xticks([])
    axs[4].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )
    axs[4].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])

    axs[5].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])
    axs[5].set_xlabel(
        "Event Time (s)", fontsize=text_fontsize
    )  # Only the last subplot needs the x-axis label
    # axs[4].set_ylim(cpu_y_lim)
    axs[5].set_ylabel("Duration (s)", fontsize=text_fontsize)
    axs[5].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )
    
    print('min_et',min_et,'max_et',max_et)

    # adjust x lim of left plots
    axs[0].set_xlim([min_et, max_et])
    axs[1].set_xlim([min_et, max_et])
    axs[2].set_xlim([min_et, max_et])
    axs[3].set_xlim([min_et, max_et])
    axs[4].set_xlim([min_et, max_et])
    axs[5].set_xlim([min_et, max_et])

    # Adjust layout
    fig.tight_layout()

    # Save the figure
    plt.savefig(output_pdf)
    plt.savefig(output_png)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate plots from baselines_data.csv."
    )
    parser.add_argument(
        "base_folder", type=str, help="Input folder containing baselines_data.csv."
    )
    parser.add_argument(
        "rate_file_path",
        type=str,
        help="Input file containing per second input rate of the input data.",
    )
    parser.add_argument(
        "agent_data", type=str, help="Input file containing the RL agent stats."
    )
    parser.add_argument("output_pdf", type=str, help="Output PDF file.")
    parser.add_argument("output_png", type=str, help="Output png file.")
    parser.add_argument("usecase", type=str, help="usecase")
    # parser.add_argument("id", type=str, help="id")

    parser.add_argument("barplots_ids", type=str, help="id")
    parser.add_argument("barplots_ids_labels", type=str, help="id")

    args = parser.parse_args()

    barplots_ids = args.barplots_ids.split(",")
    barplots_ids_labels = args.barplots_ids_labels.split(",")

    plot_graphs(
        args.base_folder,
        args.rate_file_path,
        args.agent_data,
        args.output_pdf,
        args.output_png,
        # args.probs,
        # args.probs_episod,
        args.usecase,
        barplots_ids,
        barplots_ids_labels,
    )
