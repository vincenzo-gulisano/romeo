import csv
from collections import OrderedDict

# Path to the input CSV file
input_csv_path = '/home/vincenzo/romeo/data/input/synthetic.csv'
# Path to the output CSV file
output_csv_path = '/home/vincenzo/romeo/data/s_rate.csv'

# Initialize an ordered dictionary to store the count of each unique value in the second column
value_counts = OrderedDict()

# Read the input CSV file
with open(input_csv_path, mode='r', newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        # Extract the value from the second column
        value = row[0]
        # Update the count for the value in the ordered dictionary
        if value not in value_counts:
            value_counts[value] = 1
        else:
            value_counts[value] += 1

# Write the counts to the output CSV file
with open(output_csv_path, mode='w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    for value, count in value_counts.items():
        writer.writerow([value, count])

print("The count of each value in the second column has been written to", output_csv_path)
