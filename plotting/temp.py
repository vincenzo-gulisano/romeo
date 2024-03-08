import pandas as pd
import matplotlib.pyplot as plt

# Replace 'yourfile.csv' with the path to your CSV file
file_path = '/home/vincenzo/romeo/data/jingyu/exp6/03/temp3.csv'

# Read the CSV file. Assuming there's no header, and data is separated by commas
df = pd.read_csv(file_path, header=None)
# Plotting
fig, axes = plt.subplots(nrows=11, ncols=1, figsize=(10, 20))  # Adjust figsize as needed

for i, column in enumerate(df.columns):
    axes[i].plot(df.index, df[column], label=column)
    axes[i].legend()
    axes[i].set_title(column)
    axes[i].set_xlabel('Index')
    axes[i].set_ylabel('Values')

plt.tight_layout()
plt.savefig('columns_plot.pdf')  # Save the plot to a PDF
plt.show()