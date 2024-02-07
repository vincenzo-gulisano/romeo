import argparse
import pandas as pd
import matplotlib.pyplot as plt

def create_boxplot(input_csv, output_folder, stat, measure):
    # Read the input CSV file
    df = pd.read_csv(input_csv)

    # Filter the DataFrame based on the provided statistic
    filtered_df = df[df['stat'] == stat]

    # Get unique 'CCR-Compression' values and sort them in ascending order
    IDs = filtered_df['Agent-ID'].unique()
    positions = list(range(len(IDs)))  # Define positions for x ticks

    # print('IDs:',IDs)

    # Create boxplot for each unique CCR-Compression value
    plt.figure(figsize=(10, 6))
    for i, compression in enumerate(IDs):
        group_data = filtered_df[filtered_df['Agent-ID'] == compression]
        plt.boxplot(group_data[measure], positions=[i], widths=0.5, showmeans=True)

    plt.xlabel('Agent-ID')
    plt.ylabel(f'{measure} Values for {stat}')
    plt.title(f'Boxplot of {stat} for Different Agent-IDs')
    plt.xticks(positions, IDs, rotation=45)  # Set x ticks with IDs
    plt.xticks(rotation=45)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(f'{output_folder}/{stat}_{measure}_boxplot.pdf')
    plt.close()

if __name__ == "__main__":
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Create boxplot graphs from CSV data.')

    # Add arguments
    parser.add_argument('input_csv', type=str, help='Path to the input CSV file.')
    parser.add_argument('output_folder', type=str, help='Path to the output folder to save graphs.')
    parser.add_argument('statistic', type=str, help='Value of the statistic for which boxplot is to be created.')

    # Parse the arguments
    args = parser.parse_args()

    # Call the function to create boxplot
    create_boxplot(args.input_csv, args.output_folder, args.statistic,'mean')
    create_boxplot(args.input_csv, args.output_folder, args.statistic,'sum')
    create_boxplot(args.input_csv, args.output_folder, args.statistic,'max')
