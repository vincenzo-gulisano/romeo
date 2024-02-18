import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def create_scatter_plot(input_csv, output_folder,stat1,stat2):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_csv)

    # Filter rows where stat is "injection.rate", Create a new DataFrame with selected columns, Rename the 'mean' column to 'meaninjection'
    injection_df = df[df['stat'] == stat1]
    new_df_inj = injection_df[['mean','episode', 'Agent-ID']]
    new_df_inj.rename(columns={'mean': 'mean'+stat1}, inplace=True)
    new_df_inj.reset_index(drop=True, inplace=True)

    # the same for reward
    rewards_df = df[df['stat'] == stat2]
    new_df_rew = rewards_df[['mean','episode', 'Agent-ID']]
    new_df_rew.rename(columns={'mean': 'mean'+stat2}, inplace=True)
    new_df_rew.reset_index(drop=True, inplace=True)

    combined_df = pd.merge(new_df_inj, new_df_rew, on=['Agent-ID','episode'], how='outer')
    # print(combined_df)
    # combined_df['hues'] = pd.cut(combined_df["CCR-Compression"], bins=combined_df["CCR-Compression"].nunique(), labels=[f'{i}' for i in range(0, combined_df["CCR-Compression"].nunique())])

    # Create the scatter plot
    markers = ['o', 's', 'D', '^', 'v', 'p', 'P', '*', 'X', 'd', 'H']
    sns.scatterplot(data=combined_df, x='mean'+stat1, y='mean'+stat2, style  ='Agent-ID',markers=markers)
    # plt.ylim(-10000, 10000)
    # Set labels and title
    plt.xlabel('Mean for stat=injection.rate')
    plt.ylabel('Sum for stat=rewards')
    # plt.title('Scatter Plot of Mean for Different Stats')

    # Move the legend outside the plot
    # plt.legend(title='',loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=6)
    # Adjust the bottom margin to accommodate the legend
    # plt.subplots_adjust(bottom=0.2)


    # Save the plot to a PDF file
    plt.savefig(f'{output_folder}/scatter_{stat1}_{stat2}.png')
    plt.close()

if __name__ == "__main__":
    # Set up argparse
    parser = argparse.ArgumentParser(description='Create scatter plot from CSV data')
    parser.add_argument('input_csv', type=str, help='Input CSV filename')
    parser.add_argument('output_folder', type=str, help='Output PDF filename')

    # Parse the arguments
    args = parser.parse_args()

    # Create the scatter plot
    create_scatter_plot(args.input_csv, args.output_folder, 'injectionrate.rate','rewards')
    create_scatter_plot(args.input_csv, args.output_folder, 'injectionrate.rate','observedcompression')
