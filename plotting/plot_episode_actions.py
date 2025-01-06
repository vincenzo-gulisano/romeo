import pandas as pd
import matplotlib.pyplot as plt
import argparse

def plot_actions_with_moving_average(input_csv, output_pdf):
    # Read the CSV file
    try:
        df = pd.read_csv(input_csv, header=None, names=['timestamp', 'action'])
    except Exception as e:
        print(f"Error reading {input_csv}: {e}")
        return

    # Ensure the necessary columns are present
    if not {'timestamp', 'action'}.issubset(df.columns):
        print("CSV does not contain the required columns: 'timestamp' and 'action'")
        return

    # Adjust timestamps to start from 0
    df['timestamp'] = df['timestamp'] - df['timestamp'].iloc[0]
    df['action'] = df['action']/10

    # Compute moving average with a window of 2
    df['action_moving_avg'] = df['action'].rolling(window=20).mean()

    plt.rcParams.update({"font.size": 7})  # Set global font size to 10

    text_width_pt = 506 / 2
    text_height_pt = 270 * 0.35
    points_per_inch = 72
    text_width_in = text_width_pt / points_per_inch
    text_height_in = text_height_pt / points_per_inch
    
    # Plot the action values and the moving average
    plt.figure(figsize=(text_width_in, text_height_in))
    plt.plot(df['timestamp'], df['action'], label="Action", color="blue", linestyle="-",alpha=0.5, linewidth=1)
    plt.plot(df['timestamp'], df['action_moving_avg'], label="Moving Average (window=2)", color="orange", linestyle="--", linewidth=2)

    # Customize the plot
    plt.xlabel("Wallclock Time (s)")
    plt.ylabel(r"$X$ value")
    # plt.title("Action Over Time with Moving Average")
    # plt.legend()
    plt.tight_layout()

    # Save the plot to a PDF file
    plt.savefig(output_pdf)
    plt.close()
    print(f"Plot saved as {output_pdf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Actions and Moving Average from CSV")
    parser.add_argument("input_csv", help="Path to the input CSV file")
    parser.add_argument("output_pdf", help="Path to the output PDF file")
    args = parser.parse_args()

    plot_actions_with_moving_average(args.input_csv, args.output_pdf)
