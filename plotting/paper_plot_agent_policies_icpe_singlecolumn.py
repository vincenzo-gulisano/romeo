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

    fig, axs = plt.subplots(
        4,
        1,
        figsize=(text_width_in, text_height_in),
        gridspec_kw={"hspace": 0, "wspace": 0, "height_ratios": [0.2, 1, 1, 1]},
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
    
    initial_opacity = 0.3
    final_opacity = 0.9
    splits = 3  # Number of portions to divide the subset into
    max_line_width = 2.5  # Set your desired maximum line width
    smoothing_window_size = 2
    
    opacities = np.geomspace(
        start=initial_opacity,
        stop=final_opacity,
        num=splits,
    )

    latency_y_scale = "log"

    # This config are for LinearRoad
    # latency_y_lim = [0.03, 6]
    # # This config are for Synthetic
    # latency_y_lim = [0.005, 8]

    # Specify color and font size
    text_fontsize = 8  # Example font size

    latencies_thresholds = [1.5]
    latencies_thresholds_ids = ["QoS threshold"]

    # Read the first and second columns from the CSV
    dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
    dfrate.columns = ["x", "y"]

    # Adjust x_data to start at 0
    # dfrate['x'] = dfrate['x'] - dfrate['x'].min()

    # Now, df['x'] and df['y'] are your x_data and y_data
    x_data = dfrate["x"]
    y_data = dfrate["y"]

    axs[0].set_visible(False)
    
    axs[1].set_ylabel("n/c ratio", fontsize=text_fontsize)
    axs[1].set_xticks([])
    axs[1].grid(
        True, which="major", axis="y", linestyle="-", color="gray", linewidth=0.5
    )
    
    axs[2].set_ylabel("Latency (s)", fontsize=text_fontsize)
    axs[2].set_xticks([])
    
    axs[3].set_ylabel("CPU (%)", fontsize=text_fontsize)
    axs[3].grid(
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
                # axs[2].plot(x_coords, y_coords_ratio, color=agent_plots[baseline][4],
                #             linewidth=line_width, alpha=opacities[portion_num-1])
                # Plot the smooth line
                axs[1].plot(
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
                axs[2].plot(
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
                axs[3].plot(
                    x_coords,
                    smooth_points_cpu,
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
            
            # Determine sizes and opacities based on episode values
            # num_points = len(subset["eventtime_start"])
            # sizes = np.geomspace(
            #     start=agent_plots[baseline][0],
            #     stop=agent_plots[baseline][1],
            #     num=num_points,
            # )
            # opacities = np.geomspace(
            #     start=agent_plots[baseline][2],
            #     stop=agent_plots[baseline][3],
            #     num=num_points,
            # )
            # for j, (index, row) in enumerate(subset.iterrows()):
            #     if np.random.rand() <= agent_plots[baseline][5] or j == len(subset) - 1:
            #         # This version is to draw the circle
            #         x_points = [
            #             row["eventtime_start"] - dfrate["x"].min(),
            #             row["eventtime_end"] - dfrate["x"].min(),
            #         ]
            #         x_mid = (x_points[0] + x_points[1]) / 2
            #         y_points = [row["q2_ratio"] / 100, row["q2_ratio"] / 100]
            #         y_max = row["q1_ratio"] / 100
            #         y_mid = y_points[0]
            #         y_min = row["q3_ratio"] / 100
            #         # This version is to plot a line
            #         # axs[2].plot(x_points,y_points,linewidth=sizes[j], color=agent_plots[baseline][4], alpha=opacities[j])
            #         # This version is to plot a diamond
            #         # Coordinates
            #         x_coords = [
            #             x_points[0],
            #             x_mid,
            #             x_points[1],
            #             x_mid,
            #             x_points[0],
            #         ]  # Start and end at the same point to close the shape
            #         y_coords = [
            #             y_mid,
            #             y_min,
            #             y_mid,
            #             y_max,
            #             y_mid,
            #         ]  # Top, right-mid, bottom, left-mid, back to top
            #         # axs[2].plot(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Blue line with a linewidth of 2
            #         axs[1].fill(
            #             x_coords,
            #             y_coords,
            #             color=agent_plots[baseline][4],
            #             alpha=opacities[j],
            #         )  # Fill the rhombus with a blue color, semi-transparent
            #         if j == len(subset) - 1:
            #             axs[1].plot(
            #                 row["eventtime_start"] - dfrate["x"].min(),
            #                 row["q2_ratio"] / 100,
            #                 ls="none",
            #                 ms=1,
            #                 marker="o",
            #                 mfc=agent_plots[baseline][4],
            #                 alpha=opacities[j],
            #                 mec=agent_plots[baseline][4],
            #                 label=policies_labels[baseline],
            #             )
            #         if min_et is None or x_points[0] < min_et:
            #             min_et = x_points[0]
            #         if max_et is None or x_points[1] > max_et:
            #             max_et = x_points[1]
    axs[1].legend(
        loc="upper center",  # Position the legend at the top center
        bbox_to_anchor=(0.5, 1.45),  # Adjust the position above the axis
        ncol=4,  # Number of columns
        columnspacing=0.4,  # Adjust the space between columns
    )
    # axs[1].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[1].set_ylim(ncratio_ylim)
    
    axs[2].set_ylim(latency_ylim)

    # for i, baseline in enumerate(unique_baselines):
    #     subset = policies_df[policies_df["baseline"] == baseline]
    #     if baseline in agent_plots:
    #         # Determine sizes and opacities based on episode values
    #         num_points = len(subset["eventtime_start"])
    #         sizes = np.geomspace(
    #             start=agent_plots[baseline][0],
    #             stop=agent_plots[baseline][1],
    #             num=num_points,
    #         )
    #         opacities = np.geomspace(
    #             start=agent_plots[baseline][2],
    #             stop=agent_plots[baseline][3],
    #             num=num_points,
    #         )
    #         for j, (index, row) in enumerate(subset.iterrows()):
    #             if np.random.rand() <= agent_plots[baseline][5]:
    #                 x_points = [
    #                     row["eventtime_start"] - dfrate["x"].min(),
    #                     row["eventtime_end"] - dfrate["x"].min(),
    #                 ]
    #                 x_mid = (x_points[0] + x_points[1]) / 2
    #                 y_points = [row["q2_latency"] / 1000, row["q2_latency"] / 1000]
    #                 y_max = row["q3_latency"] / 1000
    #                 y_mid = y_points[0]
    #                 y_min = row["q1_latency"] / 1000
    #                 # This version is to plot a line
    #                 # axs[3].plot(x_points,y_points,linewidth=sizes[j], color=agent_plots[baseline][4], alpha=opacities[j])
    #                 # This version is to plot a diamond
    #                 # Coordinates
    #                 x_coords = [
    #                     x_points[0],
    #                     x_mid,
    #                     x_points[1],
    #                     x_mid,
    #                     x_points[0],
    #                 ]  # Start and end at the same point to close the shape
    #                 y_coords = [
    #                     y_mid,
    #                     y_min,
    #                     y_mid,
    #                     y_max,
    #                     y_mid,
    #                 ]  # Top, right-mid, bottom, left-mid, back to top
    #                 # axs[3].plot(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Blue line with a linewidth of 2
    #                 axs[2].fill(
    #                     x_coords,
    #                     y_coords,
    #                     color=agent_plots[baseline][4],
    #                     alpha=opacities[j],
    #                 )  # Fill the rhombus with a blue color, semi-transparent
    #                 # This version is to draw the circle
    #                 # axs[2].plot(row['eventtime_start']- dfrate['x'].min(), row['q2_latency']/1000, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)

    for lat_idx, latency_threshold in enumerate(latencies_thresholds):
        axs[2].axhline(
            y=latency_threshold, color="r", linestyle="--"
        )  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[2].text(
            2000,
            latency_threshold * 1.01,
            latencies_thresholds_ids[lat_idx],
            color="red",
            verticalalignment="bottom",
            horizontalalignment="left",
            fontsize=8,
            transform=axs[2].transData,
        )
    #     # axs[3].grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, color='gray')  # Enable y-axis grid
    # # axs[3].axhline(y=latencies_thresholds, color='r', linestyle='--')  # Horizontal line at max_latency
    # # axs[2].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    # axs[2].set_ylim(latency_y_lim)
    # axs[2].set_yscale(latency_y_scale)

    # for i, baseline in enumerate(unique_baselines):
    #     subset = policies_df[policies_df["baseline"] == baseline]
    #     if baseline in agent_plots:
    #         # Determine sizes and opacities based on episode values
    #         num_points = len(subset["eventtime_start"])
    #         sizes = np.geomspace(
    #             start=agent_plots[baseline][0],
    #             stop=agent_plots[baseline][1],
    #             num=num_points,
    #         )
    #         opacities = np.geomspace(
    #             start=agent_plots[baseline][2],
    #             stop=agent_plots[baseline][3],
    #             num=num_points,
    #         )
    #         for j, (index, row) in enumerate(subset.iterrows()):
    #             if np.random.rand() <= agent_plots[baseline][5]:
    #                 x_points = [
    #                     row["eventtime_start"] - dfrate["x"].min(),
    #                     row["eventtime_end"] - dfrate["x"].min(),
    #                 ]
    #                 x_mid = (x_points[0] + x_points[1]) / 2
    #                 y_points = [row["q2_cpu"] / 100, row["q2_cpu"] / 100]
    #                 y_max = row["q3_cpu"] / 100
    #                 y_mid = y_points[0]
    #                 y_min = row["q1_cpu"] / 100
    #                 # This version is to plot a line
    #                 # axs[4].plot(x_points,y_points,linewidth=sizes[j], color=agent_plots[baseline][4], alpha=opacities[j])
    #                 # This version is to plot a diamond
    #                 # Coordinates
    #                 x_coords = [
    #                     x_points[0],
    #                     x_mid,
    #                     x_points[1],
    #                     x_mid,
    #                     x_points[0],
    #                 ]  # Start and end at the same point to close the shape
    #                 y_coords = [
    #                     y_mid,
    #                     y_min,
    #                     y_mid,
    #                     y_max,
    #                     y_mid,
    #                 ]  # Top, right-mid, bottom, left-mid, back to top
    #                 # axs[4].plot(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Blue line with a linewidth of 2
    #                 axs[3].fill(
    #                     x_coords,
    #                     y_coords,
    #                     color=agent_plots[baseline][4],
    #                     alpha=opacities[j],
    #                 )  # Fill the rhombus with a blue color, semi-transparent
    #                 # This version is to draw the circle
    #                 # axs[3].plot(row['eventtime_start']- dfrate['x'].min(), row['q2_cpu']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    # # axs[3].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[3].set_xlabel(
        "Event Time (s)", fontsize=text_fontsize
    )  # Only the last subplot needs the x-axis label
    axs[3].set_ylim(cpu_ylim)

    # adjust x lim of left plots
    axs[0].set_xlim([min_et * 0.95, max_et * 1.05])
    axs[1].set_xlim([min_et * 0.95, max_et * 1.05])
    axs[2].set_xlim([min_et * 0.95, max_et * 1.05])
    axs[3].set_xlim([min_et * 0.95, max_et * 1.05])
    # axs[4].set_xlim([min_et*0.95,max_et*1.05])

    # # Now plotting probabilities
    # # Load the data
    # df_probs = pd.read_csv(probs)
    # # Group the dataframe by episode
    # grouped_probs = df_probs.groupby('Episode')

    # # Ensure there is data for episode 100 before proceeding
    # for episode, data in grouped_probs:
    #     if episode == probs_episod:

    #         # Sort the data by Action Time to ensure plots are in order
    #         data.sort_values('Action Time', inplace=True)

    #         # Adjust Action Time to start at 0
    #         data['Action Time'] -= data['Action Time'].iloc[0]

    #         # Plotting
    #         axs[0,1].plot(data['Action Time'], data['Prob1'], label='Compress')
    #         axs[0,1].plot(data['Action Time'], data['Prob2'], label='Stay')
    #         axs[0,1].plot(data['Action Time'], data['Prob3'], label='Decompress')

    #         # Labeling
    #         axs[0,1].set_xlabel('Wallclock Time (s)')
    #         axs[0,1].set_ylabel('Prob.')
    #         # axs[0,1].set_ylim([0,1])
    #         # plt.title('Episode 100: Action Time vs Probabilities')
    #         axs[0,1].legend(ncols=3,loc='lower right')
    #         # Get current x and y limits
    #         x_lim = axs[0,1].get_xlim()
    #         y_lim = axs[0,1].get_ylim()

    #         # Calculate the position for the text
    #         x_pos = x_lim[0]+(x_lim[1]-x_lim[0])/2  # Use the maximum x value for right alignment
    #         y_pos = y_lim[1]*0.9  # Use the maximum y value for top alignment

    #         # Place the text in the top right corner
    #         # print(x_lim[0])
    #         # print(y_lim[0])
    #         axs[0,1].text(0,y_lim[0]*1.01, 'Ep. '+str(episode), fontsize=10, color='black')

    #         axs[0,1].yaxis.tick_right()  # Move ticks to the right
    #         axs[0,1].yaxis.set_label_position('right')  # Move the y-axis label to the right

    #         # Show the plot

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