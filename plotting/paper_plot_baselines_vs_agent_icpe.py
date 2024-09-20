import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.tools as tls
from scipy import interpolate


def plot_graphs(
    base_folder,
    rate_file_path,
    agent_data,
    output_pdf,
    probs,
    probs_episod,
    usecase,
    id,
):
    # Read the baselines_data.csv file
    file_path = os.path.join(base_folder, "baselines_data.csv")
    df = pd.read_csv(file_path)

    plt.rcParams.update({"font.size": 7})  # Set global font size to 10

    # Define marker styles for different baselines to ensure uniqueness
    markers = ["s", "^", "v", "<", ">", "p", "*", "h", "H", "D", "d", "|", "_"]

    given_order = [
        "10",
        "9",
        "8",
        "7",
        "6",
        "5",
        "4",
        "3",
        "2",
        "1",
        "0",
        "r",
    ]
    # The desired order for baselines
    xtick_labels = [
        r"$D1.0$",
        r"$D0.9$",
        r"$D0.8$",
        r"$D0.7$",
        r"$D0.6$",
        r"$D0.5$",
        r"$D0.4$",
        r"$D0.3$",
        r"$D0.2$",
        r"$D0.1$",
        r"$D0.0$",
        r"$D^*$",
    ]
    # Create a set for faster membership tests
    unique_baselines_set = set(df["baseline"].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [
        baseline for baseline in given_order if baseline in unique_baselines_set
    ]

    if usecase == "linearroad":

        # This config are for LinearRoad
        boundaries = [0.5, 10.5, 11.5]
        boundary_text = ["safe", "unsafe"]
        boundary_text_align = ["left", "left"]
        latency_y_scale = "log"
        latency_y_lim = [0.03, 6]

    elif usecase == "synthetic":

        # This config are for Synthetic
        boundaries = [0.5, 4.5, 11.5, 11.5]
        boundary_text = ["safe", "", "unsafe"]
        boundary_text_align = ["left", "left", "right"]
        latency_y_scale = "log"
        latency_y_lim = [0.005, 50]

    initial_opacity = 0.3
    final_opacity = 0.9
    splits = 4  # Number of portions to divide the subset into
    max_line_width = 2.5  # Set your desired maximum line width
    smoothing_window_size = 5
    agent_color = "green"

    # Specify color and font size
    text_color = "green"  # Example color
    text_fontsize = 7  # Example font size

    if len(unique_baselines) > len(markers):
        print("Warning: Not enough unique markers defined for the number of baselines.")

    latencies_thresholds = [1.5]
    latencies_thresholds_ids = ["QoS threshold"]

    # Read the first and second columns from the CSV
    dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
    dfrate.columns = ["x", "y"]

    # Now, df['x'] and df['y'] are your x_data and y_data
    x_data = dfrate["x"]
    y_data = dfrate["y"]

    # Create a figure and a set of subplots, now with 4 rows
    text_width_pt = 506
    text_height_pt = 270
    points_per_inch = 72
    text_width_in = text_width_pt / points_per_inch
    text_height_in = text_height_pt / points_per_inch
    fig, axs = plt.subplots(
        5,
        2,
        figsize=(text_width_in, text_height_in),
        gridspec_kw={"hspace": 0, "wspace": 0, "height_ratios": [1, 0.5, 1, 1, 1]},
    )

    # Plot random data on the new top axes (axs[0])
    axs[0, 0].plot(
        x_data - dfrate["x"].min(), y_data / 1000, linestyle="-", color="blue"
    )
    axs[0, 0].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])
    axs[0, 0].set_ylabel(r"Input rate ($10^3$ t/s)", fontsize=text_fontsize)
    axs[0, 1].set_xlabel("Time (s)", fontsize=text_fontsize)

    # Adjust the indices for the other axes since we added a new one at the top
    # mean_ratio, divided by 100
    data_mean_ratio = [
        df[df["baseline"] == baseline]["q2_ratio"].dropna() / 100
        for baseline in unique_baselines
    ]
    parts = axs[2, 1].violinplot(
        data_mean_ratio, showmeans=False, showmedians=False, showextrema=False
    )
    for pc in parts["bodies"]:
        pc.set_facecolor("#D43F3A")
        pc.set_edgecolor("black")
        pc.set_alpha(1)
    axs[2, 0].set_ylabel("Ratio (%)", fontsize=text_fontsize)
    # Set specific tick positions
    axs[2, 1].set_ylim([-0.1, 1.1])
    axs[2, 0].set_xticks([])
    # Enable the grid
    axs[2, 0].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )
    axs[2, 1].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )

    # latency, divided by 1000
    data_latency = [
        df[df["baseline"] == baseline]["q2_latency"].dropna() / 1000
        for baseline in unique_baselines
    ]
    # axs[3,1].boxplot(data_latency, labels=unique_baselines)
    parts = axs[3, 1].violinplot(
        data_latency, showmeans=False, showmedians=False, showextrema=False
    )
    for pc in parts["bodies"]:
        pc.set_facecolor("#D43F3A")
        pc.set_edgecolor("black")
        pc.set_alpha(1)
    axs[3, 0].set_ylabel("Latency (s)", fontsize=text_fontsize)
    axs[3, 1].set_ylim(latency_y_lim)
    axs[3, 0].set_xticks([])
    axs[3, 1].set_yscale(latency_y_scale)
    for lat_idx, latency_threshold in enumerate(latencies_thresholds):
        axs[3, 1].axhline(
            y=latency_threshold, color="r", linestyle="--"
        )  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[3, 1].text(
            0.5,
            latency_threshold * 1.05,
            latencies_thresholds_ids[lat_idx],
            color="red",
            verticalalignment="bottom",
            horizontalalignment="left",
            fontsize=text_fontsize,
            transform=axs[3, 1].transData,
        )
        
    # cpu, divided by 100
    data_cpu = [
        df[df["baseline"] == baseline]["q2_cpu"].dropna() / 100
        for baseline in unique_baselines
    ]
    # axs[4,1].boxplot(data_cpu, labels=unique_baselines)
    parts = axs[4, 1].violinplot(
        data_cpu, showmeans=False, showmedians=False, showextrema=False
    )
    for pc in parts["bodies"]:
        pc.set_facecolor("#D43F3A")
        pc.set_edgecolor("black")
        pc.set_alpha(1)
    axs[4, 0].set_ylabel("CPU (%)", fontsize=text_fontsize)
    axs[4, 1].set_xlabel(
        "Baseline", fontsize=text_fontsize
    )  # Only the last subplot needs the x-axis label
    axs[4, 1].set_xticks(np.arange(1, len(unique_baselines) + 1))  # Set tick positions
    axs[4, 1].set_xticklabels(xtick_labels, fontsize=text_fontsize)
    axs[4, 1].set_ylim([-0.1, 1.1])
    # Enable the grid
    axs[4, 0].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )
    axs[4, 1].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )

    # Add vertical lines in all axes for each X value in boundaries (adjusting index for axs)
    for ax in axs[2:, 1]:
        for boundary in boundaries:
            ax.axvline(x=boundary, color="g", linestyle="--")

    # Add text on top of the second axes (previously first) in between consecutive pairs of boundaries
    for i, text in enumerate(boundary_text):
        # Calculate the position to place the text (middle between boundaries)
        x_pos = boundaries[i]
        # Place the text at the calculated position, with a slight offset upwards
        axs[2, 1].text(
            x_pos,
            1.01,
            text,
            transform=axs[2, 1].get_xaxis_transform(),
            ha=boundary_text_align[i],
            va="bottom",
            color=text_color,
            fontsize=text_fontsize,
        )

    # Disable y-axis labels and tick marks on the right-side axes
    for ax in axs[1:, 1]:  # Loop through second column axes
        ax.yaxis.set_tick_params(labelleft=False)  # Disable y-axis tick labels
        ax.set_ylabel("")  # Clear y-axis label
    axs[1, 0].set_visible(False)
    axs[1, 1].set_visible(False)

    # Now the part about the RL agent
    # Read the baselines_data.csv file
    baseline_file_path = os.path.join(agent_data)
    baseline_df = pd.read_csv(baseline_file_path)

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

    subset = baseline_df[baseline_df["baseline"] == id]

    opacities = np.geomspace(
        start=initial_opacity,
        stop=final_opacity,
        num=splits,
    )

    # Split the subset into `n` portions
    portions = np.array_split(subset, splits)

    for portion_num, portion in enumerate(portions, 1):
        if portion.empty:
            continue  # Skip if the portion is empty

        # Sort subset by 'eventtime_start'
        portion = portion.sort_values(by="eventtime_start")

        # Line width proportional to portion number, scaled between 1 and max_line_width
        line_width = 1 + (portion_num - 1) * (max_line_width - 1) / (splits - 1)

        # Extract x and y coordinates
        x_coords = portion["eventtime_start"] - dfrate["x"].min()
        y_coords_ratio = portion["q2_ratio"] / 100
        y_coords_latency = portion["q2_latency"] / 1000
        y_coords_cpu = portion["q2_cpu"] / 100

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

        # Plot the line for the current portion with line thickness proportional to portion number
        # axs[2, 0].plot(x_coords, y_coords_ratio, color=agent_plots[baseline][4],
        #             linewidth=line_width, alpha=opacities[portion_num-1])
        # Plot the smooth line
        axs[2, 0].plot(
            x_coords,
            smooth_points_ratio,
            color=agent_color,
            linewidth=line_width,
            alpha=opacities[portion_num - 1],
        )

        # Plot the line for the current portion with line thickness proportional to portion number
        # axs[3, 0].plot(x_coords, y_coords_latency, color=agent_plots[baseline][4],
        #             linewidth=line_width, alpha=opacities[portion_num-1])
        # Plot the smooth line
        axs[3, 0].plot(
            x_coords,
            smooth_points_latency,
            color=agent_color,
            linewidth=line_width,
            alpha=opacities[portion_num - 1],
        )
        
        # Plot the line for the current portion with line thickness proportional to portion number
        # axs[4, 0].plot(x_coords, y_coords_cpu, color=agent_plots[baseline][4],
        #             linewidth=line_width, alpha=opacities[portion_num-1])
        # Plot the smooth line
        axs[4, 0].plot(
            x_coords,
            smooth_points_cpu,
            color=agent_color,
            linewidth=line_width,
            alpha=opacities[portion_num - 1],
        )

        # Update min_et and max_et based on the current portion
        if min_et is None or x_coords.min() < min_et:
            min_et = x_coords.min()
        if max_et is None or x_coords.max() > max_et:
            max_et = x_coords.max()

    axs[2, 0].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])
    axs[2, 0].set_ylim([-0.1, 1.1])

    for lat_idx, latency_threshold in enumerate(latencies_thresholds):
        axs[3, 0].axhline(
            y=latency_threshold, color="r", linestyle="--"
        )  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[3, 0].text(
            0.5,
            latency_threshold * 1.05,
            latencies_thresholds_ids[lat_idx],
            color="red",
            verticalalignment="bottom",
            horizontalalignment="left",
            fontsize=text_fontsize,
            transform=axs[3, 1].transData,
        )
    axs[3, 0].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])
    axs[3, 0].set_ylim(latency_y_lim)
    axs[3, 0].set_yscale(latency_y_scale)

    axs[4, 0].set_xlim([0, dfrate["x"].max() - dfrate["x"].min()])
    axs[4, 0].set_xlabel(
        "Event Time (s)", fontsize=text_fontsize
    )  # Only the last subplot needs the x-axis label
    axs[4, 0].set_ylim([-0.1, 1.1])

    # adjust x lim of left plots
    axs[0, 0].set_xlim([min_et * 0.95, max_et * 1.05])
    axs[1, 0].set_xlim([min_et * 0.95, max_et * 1.05])
    axs[2, 0].set_xlim([min_et * 0.95, max_et * 1.05])
    axs[3, 0].set_xlim([min_et * 0.95, max_et * 1.05])
    axs[4, 0].set_xlim([min_et * 0.95, max_et * 1.05])

    # Now plotting probabilities
    # Load the data
    df_probs = pd.read_csv(probs)
    # Group the dataframe by episode
    grouped_probs = df_probs.groupby("Episode")

    # Ensure there is data for episode 100 before proceeding
    for episode, data in grouped_probs:
        if episode == probs_episod:

            # Sort the data by Action Time to ensure plots are in order
            data.sort_values("Action Time", inplace=True)

            # Adjust Action Time to start at 0
            data["Action Time"] -= data["Action Time"].iloc[0]

            # Plotting
            axs[0, 1].plot(data["Action Time"], data["Prob1"], label="Compress")
            axs[0, 1].plot(data["Action Time"], data["Prob2"], label="Stay")
            axs[0, 1].plot(data["Action Time"], data["Prob3"], label="Decompress")

            # Labeling
            axs[0, 1].set_xlabel("Wallclock Time (s)")
            axs[0, 1].set_ylabel("Prob.")
            # axs[0,1].set_ylim([0,1])
            # plt.title('Episode 100: Action Time vs Probabilities')
            axs[0, 1].legend(ncols=3, loc="lower right")
            # Get current x and y limits
            x_lim = axs[0, 1].get_xlim()
            y_lim = axs[0, 1].get_ylim()

            # Calculate the position for the text
            x_pos = (
                x_lim[0] + (x_lim[1] - x_lim[0]) / 2
            )  # Use the maximum x value for right alignment
            y_pos = y_lim[1] * 0.9  # Use the maximum y value for top alignment

            axs[0, 1].yaxis.tick_right()  # Move ticks to the right
            axs[0, 1].yaxis.set_label_position(
                "right"
            )  # Move the y-axis label to the right

            # Show the plot

    # Adjust layout
    fig.tight_layout()

    # Save the figure
    plt.savefig(output_pdf)
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
    parser.add_argument("probs", type=str, help="CSV with the probabilities")
    parser.add_argument(
        "probs_episod", type=int, help="Episode of which to plot probabilities"
    )
    parser.add_argument("usecase", type=str, help="usecase")
    parser.add_argument("id", type=str, help="id")

    args = parser.parse_args()

    plot_graphs(
        args.base_folder,
        args.rate_file_path,
        args.agent_data,
        args.output_pdf,
        args.probs,
        args.probs_episod,
        args.usecase,
        args.id,
    )
