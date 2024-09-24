import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import plotly.tools as tls

def plot_graphs(rate_file_path,agent_data,output_pdf):
    # Read the baselines_data.csv file
    # file_path = os.path.join(base_folder, 'baselines_data.csv')
    # df = pd.read_csv(file_path)
    

    plt.rcParams.update({'font.size': 8})  # Set global font size to 10

    # Read the RL policies file
    policies_file_path = os.path.join(agent_data)
    policies_df = pd.read_csv(policies_file_path)

    # Convert the 'baseline' column to text (object) type
    policies_df['baseline'] = policies_df['baseline'].astype(str)

    # The values represent: initial size, fine size, initial opacity, final opacity, color, prob. of selection
    agent_plots = {
        'weaob_linear': [1,10,0.1,1,'red',0.25],
        'eaob_linear': [1,10,0.1,1,'orange',.25],
        'aob_linear': [1,10,0.1,1,'blue',.25],
        'weaaw_linear': [1,10,0.1,1,'green',.125], # 0.125 for first experiments wince we have 200 episodes
        'weaob_synthetic': [1,10,0.1,1,'red',.25],
        'eaob_synthetic': [1,10,0.1,1,'orange',.25],
        'aob_synthetic': [1,10,0.1,1,'blue',.25],
        'weaaw_synthetic': [1,10,0.1,1,'green',.125], # 0.125 for first experiments wince we have 200 episodes
        '13.1': [1,5,0.1,0.8,'red',1],
        '13.2': [1,5,0.1,0.8,'green',1],
        '12.1': [1,5,0.1,0.8,'red',1],
        '12.2': [5,10,0.1,0.8,'green',1]}
       
    policies_order = ['weaob_linear','eaob_linear','aob_linear','weaaw_linear']  # The desired order for baselines
    # policies_order = ['weaob_synthetic','eaob_synthetic','aob_synthetic','weaaw_synthetic']  # The desired order for baselines
    
    policies_labels = {
        'weaob_linear' : 'WEL-OB',
        'eaob_linear' : 'EL-OB',
        'aob_linear' : 'L-OB',
        'weaaw_linear' : 'WEL-AW',
        'weaob_synthetic' : 'WEL-OB',
        'eaob_synthetic' : 'EL-OB',
        'aob_synthetic' : 'L-OB',
        'weaaw_synthetic' : 'WEL-AW',
    }

    # This config are for LinearRoad
    boundaries = [0.5,3.5,6.5,9.5,12.5]
    boundary_text = ['WEL-OB','EL-OB','L-OB','WEL-AW']
    latency_y_scale = 'log'
    latency_y_lim = [0.03,6]
    # # This config are for Synthetic
    # latency_y_lim = [0.005,8]
    

    # Specify color and font size
    text_color = 'green'  # Example color
    text_fontsize = 8  # Example font size
    
    latencies_thresholds=[1.5]
    latencies_thresholds_ids=['QoS threshold']

    # Define marker styles for different baselines to ensure uniqueness
    # markers = ['s', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'D', 'd', '|', '_']
    

    # given_order = ['10', '9', '8', '7', '6', '5', '4', '3', '2', '1', '0', 'r']  # The desired order for baselines
    xtick_labels = [r'$q1$',r'$q2$',r'$q3$',r'$q1$',r'$q2$',r'$q3$',r'$q1$',r'$q2$',r'$q3$', r'$q1$',r'$q2$',r'$q3$']
    # Create a set for faster membership tests
    # unique_baselines_set = set(df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    # unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

    
    # if len(unique_baselines) > len(markers):
    #     print("Warning: Not enough unique markers defined for the number of baselines.")
    
    # latencies_thresholds=[0.75,1.5]
    # latencies_thresholds_ids=['soft','hard']

    # Read the first and second columns from the CSV
    dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
    dfrate.columns = ['x', 'y']

    # Adjust x_data to start at 0
    # dfrate['x'] = dfrate['x'] - dfrate['x'].min()

    # Now, df['x'] and df['y'] are your x_data and y_data
    x_data = dfrate['x']
    y_data = dfrate['y']

    # Create a figure and a set of subplots, now with 4 rows
    text_width_pt = 506
    text_height_pt = 180
    points_per_inch = 72
    text_width_in = text_width_pt / points_per_inch
    text_height_in = text_height_pt / points_per_inch
    
    fig, axs = plt.subplots(4, 2, figsize=(text_width_in, text_height_in), gridspec_kw={'hspace': 0, 'wspace': 0, 'height_ratios': [0.2, 1, 1, 1],'width_ratios': [1, 0.5]})

    # Plot random data on the new top axes (axs[0])
    # axs[0,0].plot(x_data - dfrate['x'].min(), y_data, linestyle='-', color='blue')
    # axs[0,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    # axs[0,0].set_ylabel(r'Input rate ($10^3$ t/s)', fontsize=text_fontsize)
    # axs[0,1].set_xlabel('Time (s)', fontsize=text_fontsize)

    # Adjust the indices for the other axes since we added a new one at the top
    # mean_ratio, divided by 100

    data_ratio = []
    for i, policy in enumerate(policies_order):
        subset = policies_df[policies_df['baseline'] == policy] 
        if policy in agent_plots:
            data_ratio.append(subset['q1_ratio'].dropna() / 100)
            data_ratio.append(subset['q2_ratio'].dropna() / 100)
            data_ratio.append(subset['q3_ratio'].dropna() / 100)
    axs[1,1].boxplot(data_ratio, showfliers=True, flierprops={'marker':'.', 'markersize':3})
    axs[1,0].set_ylabel('n/c ratio', fontsize=text_fontsize)
    # Set specific tick positions
    axs[1,1].set_ylim([-0.1,1.1])
    axs[1,0].set_xticks([])
    axs[1,1].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    axs[1,1].set_yticklabels(['0', '', '', '', '', '1'])
    # Enable the grid
    axs[1,0].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    axs[1,1].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)

    # latency, divided by 1000
    data_latency = []
    for i, policy in enumerate(policies_order):
        subset = policies_df[policies_df['baseline'] == policy] 
        if policy in agent_plots:
            data_latency.append(subset['q1_latency'].dropna() / 1000)
            data_latency.append(subset['q2_latency'].dropna() / 1000)
            data_latency.append(subset['q3_latency'].dropna() / 1000)
    axs[2,1].boxplot(data_latency, showfliers=True, flierprops={'marker':'.', 'markersize':3})
    axs[2,0].set_ylabel('latency (s)', fontsize=text_fontsize)
    axs[2,1].set_ylim(latency_y_lim)
    axs[2,0].set_xticks([])
    axs[2,1].set_yscale(latency_y_scale)
    for lat_idx,latency_threshold in enumerate(latencies_thresholds): 
        axs[2,1].axhline(y=latency_threshold, color='r', linestyle='--')  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[2,1].text(0.5, latency_threshold*1.01, latencies_thresholds_ids[lat_idx], color='red', verticalalignment='bottom', horizontalalignment='left', fontsize=8, transform=axs[2,1].transData)
        # axs[3].grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, color='gray')  # Enable y-axis grid

    # cpu, divided by 100
    data_cpu = []
    for i, policy in enumerate(policies_order):
        subset = policies_df[policies_df['baseline'] == policy] 
        if policy in agent_plots:
            data_cpu.append(subset['q1_cpu'].dropna() / 100)
            data_cpu.append(subset['q2_cpu'].dropna() / 100)
            data_cpu.append(subset['q3_cpu'].dropna() / 100)
    axs[3,1].boxplot(data_cpu, showfliers=True, flierprops={'marker':'.', 'markersize':3})
    axs[3,0].set_ylabel('CPU', fontsize=text_fontsize)
    axs[3,1].set_xlabel('Baseline', fontsize=text_fontsize)  # Only the last subplot needs the x-axis label
    axs[3,1].set_xticklabels(xtick_labels, fontsize=text_fontsize)
    axs[3,1].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
    axs[3,1].set_yticklabels(['0', '', '', '', '', '1'])
    axs[3,1].set_ylim([-0.1,1.1])
    # Enable the grid
    axs[3,0].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    axs[3,1].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    
    # Add vertical lines in all axes for each X value in boundaries (adjusting index for axs)
    for ax in axs[1:,1]:
        for boundary in boundaries:
            ax.axvline(x=boundary, color='g', linestyle='--')

    # Add text on top of the second axes (previously first) in between consecutive pairs of boundaries
    for i, text in enumerate(boundary_text):
        # Calculate the position to place the text (middle between boundaries)
        x_pos = (boundaries[i] + boundaries[i + 1]) / 2
        # Place the text at the calculated position, with a slight offset upwards
        axs[1,1].text(x_pos, 1.01, text, transform=axs[1,1].get_xaxis_transform(), ha='center', va='bottom', color=text_color, fontsize=text_fontsize)

    # Disable y-axis labels and tick marks on the right-side axes
    for ax in axs[0:, 1]:  # Loop through second column axes
        ax.yaxis.set_tick_params(labelleft=False)  # Disable y-axis tick labels
        ax.set_ylabel('')  # Clear y-axis label
    axs[0,0].set_visible(False)
    axs[0,1].set_visible(False)
    
    # Create a set for faster membership tests
    unique_baselines_set = set(policies_df['baseline'].unique())

    # Use list comprehension to filter given_order by items present in df['baseline'].unique()
    unique_baselines = [baseline for baseline in policies_order if baseline in unique_baselines_set]

    # The following variables are used to find the min and max event times in the plot
    min_et = None
    max_et = None

    for i, baseline in enumerate(unique_baselines):
        subset = policies_df[policies_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime_start'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5] or j == len(subset)-1:
                    # This version is to draw the circle
                    x_points = [row['eventtime_start']- dfrate['x'].min(),row['eventtime_end']- dfrate['x'].min()]
                    x_mid=(x_points[0]+x_points[1])/2
                    y_points = [row['q2_ratio']/100,row['q2_ratio']/100]
                    y_max = row['q1_ratio']/100
                    y_mid = y_points[0]
                    y_min = row['q3_ratio']/100
                    # This version is to plot a line
                    # axs[2,0].plot(x_points,y_points,linewidth=sizes[j], color=agent_plots[baseline][4], alpha=opacities[j])
                    # This version is to plot a diamond
                    # Coordinates
                    x_coords = [x_points[0], x_mid, x_points[1], x_mid, x_points[0]]  # Start and end at the same point to close the shape
                    y_coords = [y_mid, y_min, y_mid, y_max, y_mid]  # Top, right-mid, bottom, left-mid, back to top
                    # axs[2,0].plot(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Blue line with a linewidth of 2
                    axs[1,0].fill(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Fill the rhombus with a blue color, semi-transparent
                    if j == len(subset)-1:
                        axs[1,0].plot(row['eventtime_start']- dfrate['x'].min(), row['q2_ratio']/100, ls='none', ms=1, marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],label=policies_labels[baseline])
                    if min_et is None or x_points[0]<min_et:
                        min_et = x_points[0]
                    if max_et is None or x_points[1]>max_et:
                        max_et = x_points[1]
    axs[1, 0].legend(
        loc='upper center',  # Position the legend at the top center
        bbox_to_anchor=(0.5, 1.45),  # Adjust the position above the axis
        ncol=4,  # Number of columns
        columnspacing=0.4  # Adjust the space between columns
    )
    # axs[1,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[1,0].set_ylim([-0.1,1.1])

    for i, baseline in enumerate(unique_baselines):
        subset = policies_df[policies_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime_start'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    x_points = [row['eventtime_start']- dfrate['x'].min(),row['eventtime_end']- dfrate['x'].min()]
                    x_mid=(x_points[0]+x_points[1])/2
                    y_points = [row['q2_latency']/1000,row['q2_latency']/1000]
                    y_max = row['q3_latency']/1000
                    y_mid = y_points[0]
                    y_min = row['q1_latency']/1000
                    # This version is to plot a line
                    # axs[3,0].plot(x_points,y_points,linewidth=sizes[j], color=agent_plots[baseline][4], alpha=opacities[j])
                    # This version is to plot a diamond
                    # Coordinates
                    x_coords = [x_points[0], x_mid, x_points[1], x_mid, x_points[0]]  # Start and end at the same point to close the shape
                    y_coords = [y_mid, y_min, y_mid, y_max, y_mid]  # Top, right-mid, bottom, left-mid, back to top
                    # axs[3,0].plot(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Blue line with a linewidth of 2
                    axs[2,0].fill(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Fill the rhombus with a blue color, semi-transparent
                    # This version is to draw the circle
                    # axs[2,0].plot(row['eventtime_start']- dfrate['x'].min(), row['q2_latency']/1000, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)

    for lat_idx,latency_threshold in enumerate(latencies_thresholds): 
        axs[2,0].axhline(y=latency_threshold, color='r', linestyle='--')  # Horizontal line at max_latency
        # Add text for threshold latency
        axs[2,0].text(0.5, latency_threshold*1.01, latencies_thresholds_ids[lat_idx], color='red', verticalalignment='bottom', horizontalalignment='left', fontsize=8, transform=axs[2,1].transData)
        # axs[3].grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, color='gray')  # Enable y-axis grid
    # axs[3,0].axhline(y=latencies_thresholds, color='r', linestyle='--')  # Horizontal line at max_latency
    # axs[2,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[2,0].set_ylim(latency_y_lim)
    axs[2,0].set_yscale(latency_y_scale)

    for i, baseline in enumerate(unique_baselines):
        subset = policies_df[policies_df['baseline'] == baseline] 
        if baseline in agent_plots:
            # Determine sizes and opacities based on episode values
            num_points = len(subset['eventtime_start'])
            sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
            opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
            for j, (index, row) in enumerate(subset.iterrows()):
                if np.random.rand()<=agent_plots[baseline][5]:
                    x_points = [row['eventtime_start']- dfrate['x'].min(),row['eventtime_end']- dfrate['x'].min()]
                    x_mid=(x_points[0]+x_points[1])/2
                    y_points = [row['q2_cpu']/100,row['q2_cpu']/100]
                    y_max = row['q3_cpu']/100
                    y_mid = y_points[0]
                    y_min = row['q1_cpu']/100
                    # This version is to plot a line
                    # axs[4,0].plot(x_points,y_points,linewidth=sizes[j], color=agent_plots[baseline][4], alpha=opacities[j])
                    # This version is to plot a diamond
                    # Coordinates
                    x_coords = [x_points[0], x_mid, x_points[1], x_mid, x_points[0]]  # Start and end at the same point to close the shape
                    y_coords = [y_mid, y_min, y_mid, y_max, y_mid]  # Top, right-mid, bottom, left-mid, back to top
                    # axs[4,0].plot(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Blue line with a linewidth of 2
                    axs[3,0].fill(x_coords, y_coords, color=agent_plots[baseline][4], alpha=opacities[j])  # Fill the rhombus with a blue color, semi-transparent
                    # This version is to draw the circle
                    # axs[3,0].plot(row['eventtime_start']- dfrate['x'].min(), row['q2_cpu']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
    # axs[3,0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
    axs[3,0].set_xlabel('Event Time (s)', fontsize=text_fontsize)  # Only the last subplot needs the x-axis label
    axs[3,0].set_ylim([-0.1,1.1])
    
    # adjust x lim of left plots
    axs[0,0].set_xlim([min_et*0.95,max_et*1.05])
    axs[1,0].set_xlim([min_et*0.95,max_et*1.05])
    axs[2,0].set_xlim([min_et*0.95,max_et*1.05])
    axs[3,0].set_xlim([min_et*0.95,max_et*1.05])
    # axs[4,0].set_xlim([min_et*0.95,max_et*1.05])

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate plots from baselines_data.csv.')
    # parser.add_argument('base_folder', type=str, help='Input folder containing baselines_data.csv.')
    parser.add_argument('rate_file_path', type=str, help='Input file containing per second input rate of the input data.')
    parser.add_argument('agent_data', type=str, help='Input file containing the RL agent stats.')
    parser.add_argument('output_pdf', type=str, help='Output PDF file.')
    # parser.add_argument('probs', type=str, help='CSV with the probabilities')
    # parser.add_argument('probs_episod', type=int, help='Episode of which to plot probabilities')

    args = parser.parse_args()
    
    plot_graphs(args.rate_file_path,args.agent_data,args.output_pdf)

# import argparse
# import pandas as pd
# import matplotlib.pyplot as plt
# import os
# import numpy as np
# import plotly.tools as tls

# def plot_graphs(rate_file_path,agent_data,output_pdf):
   
#     # This config are for LinearRoad
#     latency_y_scale = 'log'
    
#     # Specify font size
#     text_fontsize = 8  # Example font size
    
#     # if len(unique_baselines) > len(markers):
#     #     print("Warning: Not enough unique markers defined for the number of baselines.")
    
#     max_latency=1

#     # Read the first and second columns from the CSV
#     dfrate = pd.read_csv(rate_file_path, usecols=[0, 1], header=None)
#     dfrate.columns = ['x', 'y']

#     # Now, df['x'] and df['y'] are your x_data and y_data
#     x_data = dfrate['x']
#     y_data = dfrate['y']

#     plt.rcParams.update({'font.size': 8})  # Set global font size to 10

#     # Create a figure and a set of subplots, now with 4 rows
#     fig, axs = plt.subplots(5, 1, figsize=(5, 6), gridspec_kw={'hspace': 0, 'height_ratios': [1, 0.5, 1, 1, 1]})

#     # Plot random data on the new top axes (axs[0])
#     axs[0].plot(x_data - dfrate['x'].min(), y_data, linestyle='-', color='blue')
#     axs[0].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
#     axs[0].set_ylabel(r'Input rate ($10^3$ t/s)', fontsize=text_fontsize)
#     axs[0].set_xlabel('Event Time (s)', fontsize=text_fontsize)

#     axs[2].set_ylabel('Compression (%)', fontsize=text_fontsize)
#     axs[2].set_xticks([])
#     axs[2].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    
#     axs[3].set_ylabel('Latency (s)', fontsize=text_fontsize)
#     axs[3].set_xticks([])
    
#     axs[4].set_ylabel('CPU (%)', fontsize=text_fontsize)
#     axs[4].grid(True, which='major', axis='y', linestyle='-', color='gray', linewidth=0.5)
    
#     axs[1].set_visible(False)
    
#     # Now the part about the RL agent
#     # Read the baselines_data.csv file
#     baseline_file_path = os.path.join(agent_data)
#     baseline_df = pd.read_csv(baseline_file_path)

#     # Convert the 'baseline' column to text (object) type
#     baseline_df['baseline'] = baseline_df['baseline'].astype(str)

#     # The values represent: initial size, fine size, initial opacity, final opacity, color, prob. of selection
#     agent_plots = {
#         'weaob_linear': [1,1,1,1,'red',1],
#         'eaob_linear': [1,1,1,1,'orange',1],
#         'aob_linear': [1,1,1,1,'blue',1],
#         'weaaw_linear': [1,1,1,1,'green',1],
#         'weaob_synthetic': [1,1,1,1,'red',1],
#         'eaob_synthetic': [1,1,1,1,'orange',1],
#         'aob_synthetic': [1,1,1,1,'blue',1],
#         'weaaw_synthetic': [1,1,1,1,'green',1],
#         '13.1': [1,5,0.1,0.8,'red',1],
#         '13.2': [1,5,0.1,0.8,'green',1],
#         '12.1': [1,5,0.1,0.8,'red',1],
#         '12.2': [5,10,0.1,0.8,'green',1]}
       
#     given_order = ['weaob_linear','eaob_linear','aob_linear','weaaw_linear']  # The desired order for baselines
#     # given_order = ['weaob_synthetic','eaob_synthetic','aob_synthetic','weaaw_synthetic']  # The desired order for baselines
    
#     # Create a set for faster membership tests
#     unique_baselines_set = set(baseline_df['baseline'].unique())

#     # Use list comprehension to filter given_order by items present in df['baseline'].unique()
#     unique_baselines = [baseline for baseline in given_order if baseline in unique_baselines_set]

#     for i, baseline in enumerate(unique_baselines):
#         subset = baseline_df[baseline_df['baseline'] == baseline] 
#         if baseline in agent_plots:
#             # Determine sizes and opacities based on episode values
#             num_points = len(subset['eventtime_start'])
#             sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
#             opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
#             for j, (index, row) in enumerate(subset.iterrows()):
#                 if np.random.rand()<=agent_plots[baseline][5]:
#                     axs[2].plot(row['eventtime_start']- dfrate['x'].min(), row['mean_ratio']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
#     axs[2].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
#     axs[2].set_ylim([-0.1,1.1])
    
#     for i, baseline in enumerate(unique_baselines):
#         subset = baseline_df[baseline_df['baseline'] == baseline] 
#         if baseline in agent_plots:
#             # Determine sizes and opacities based on episode values
#             num_points = len(subset['eventtime_start'])
#             sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
#             opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
#             for j, (index, row) in enumerate(subset.iterrows()):
#                 if np.random.rand()<=agent_plots[baseline][5]:
#                     axs[3].plot(row['eventtime_start']- dfrate['x'].min(), row['latency_mean']/1000, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
#     axs[3].axhline(y=max_latency, color='r', linestyle='--')  # Horizontal line at max_latency
#     axs[3].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
#     axs[3].set_ylim([0.008,8])
#     axs[3].set_yscale(latency_y_scale)

#     for i, baseline in enumerate(unique_baselines):
#         subset = baseline_df[baseline_df['baseline'] == baseline] 
#         if baseline in agent_plots:
#             # Determine sizes and opacities based on episode values
#             num_points = len(subset['eventtime_start'])
#             sizes = np.geomspace(start=agent_plots[baseline][0], stop=agent_plots[baseline][1], num=num_points)
#             opacities = np.geomspace(start=agent_plots[baseline][2], stop=agent_plots[baseline][3], num=num_points)
#             for j, (index, row) in enumerate(subset.iterrows()):
#                 if np.random.rand()<=agent_plots[baseline][5]:
#                     axs[4].plot(row['eventtime_start']- dfrate['x'].min(), row['cpu_mean']/100, ls='none', ms=sizes[j], marker='o', mfc=agent_plots[baseline][4], alpha=opacities[j],mec=agent_plots[baseline][4],)
#     axs[4].set_xlim([0,dfrate['x'].max()-dfrate['x'].min()])
#     axs[4].set_xlabel('Event Time (s)', fontsize=text_fontsize)  # Only the last subplot needs the x-axis label
#     axs[4].set_ylim([-0.1,1.1])
    
#     # Adjust layout
#     fig.tight_layout()
    
#     # Save the figure
#     plt.savefig(output_pdf)
#     plt.close()

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description='Generate plots from baselines_data.csv.')
#     parser.add_argument('rate_file_path', type=str, help='Input file containing per second input rate of the input data.')
#     parser.add_argument('agent_data', type=str, help='Input file containing the RL agent stats.')
#     parser.add_argument('output_pdf', type=str, help='Output PDF file.')

#     args = parser.parse_args()
    
#     plot_graphs(args.rate_file_path,args.agent_data,args.output_pdf)
