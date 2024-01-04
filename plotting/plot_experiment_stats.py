import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def plot_files_in_folder(folder):


    print('Gathering valid CSV files')
    # Get all CSV files with 2 columns and only numerical values
    csv_files = [file for file in os.listdir(folder) if file.endswith('.csv')]
    valid_csv_files = []

    for file in csv_files:
        file_path = os.path.join(folder, file)
        try:
            df = pd.read_csv(file_path)
            # Check if the CSV file has exactly 2 columns and contains numerical values
            if len(df.columns) == 2 and all(df.applymap(lambda x: isinstance(x, (int, float))).all(axis=1)):
                print(file_path,'is a valid file path')
                valid_csv_files.append(file_path)
            else:
                print(file_path,'is not a valid file path')
        except pd.errors.EmptyDataError:
            pass  # Handle empty CSV files

    if not valid_csv_files:
        print("No valid CSV files found in the folder.")
        return

    # Read episodes.csv
    episodes_path = os.path.join(folder, 'episodes.csv')
    episodes_df = pd.read_csv(episodes_path)

    print('Computing the minimum value of the first column among all files...')
    min_value = min(pd.read_csv(file).iloc[:, 0].min() for file in valid_csv_files)
    min_value = min(min_value,episodes_df.iloc[:, 0].min())
    print('...',min_value)

    episodes_df['ts'] -= min_value

    # Plot each valid CSV file
    for file_path in valid_csv_files:
        df = pd.read_csv(file_path)
        x_label = 'Time (s)'
        y_label = os.path.splitext(os.path.basename(file_path))[0]
        
        # Adjust the values by subtracting the minimum value
        df.iloc[:, 0] -= min_value

        # Plotting
        plt.plot(df.iloc[:, 0], df.iloc[:, 1], label=y_label)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.yscale('log')
        
        # # Add vertical lines for each ts in episodes.csv
        # for index, row in episodes_df.iterrows():
        #     plt.axvline(row['ts'], linestyle='--', color='red')
        #     plt.text(row['ts'], df.iloc[:, 1].max(), f"{row['episode']}: {row['event']}", rotation=90, color='red')

        plt.legend()
        plt.title(f'Plot for {os.path.basename(file_path)}')
        plt.savefig(f"{os.path.splitext(file_path)[0]}.pdf")
        plt.clf()

    print("Plots saved successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot valid CSV files in a folder.')
    parser.add_argument('folder', type=str, help='The folder containing CSV files.')

    args = parser.parse_args()
    plot_files_in_folder(args.folder)
