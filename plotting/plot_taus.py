import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse

def plot_tau_values(folder):
    # Walk through the directory
    for root, _, files in os.walk(folder):
        for file in files:
            if file == "taus.csv":
                file_path = os.path.join(root, file)
                print(f"Found: {file_path}")

                # Read the Tau values from the CSV file
                try:
                    data = pd.read_csv(file_path, header=None, names=["Tau"])
                    
                    # Create a plot for the current taus.csv file
                    plt.figure(figsize=(10, 6))
                    plt.plot(data["Tau"], label='Tau Values', color='blue', alpha=0.7)
                    
                    plt.xlabel("Index")
                    plt.ylabel("Tau Values")
                    plt.title(f"Plot of Tau Values from {file_path}")
                    plt.legend()
                    plt.grid()

                    # Save the plot as a PNG file in the same directory as the CSV
                    output_file_path = os.path.splitext(file_path)[0] + "_plot.png"
                    plt.savefig(output_file_path)
                    plt.close()
                    print(f"Plot saved as {output_file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

# Main function to handle argument parsing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot Tau values from taus.csv files.")
    parser.add_argument("folder", help="Folder to search for taus.csv files")
    args = parser.parse_args()

    plot_tau_values(args.folder)
