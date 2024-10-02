import numpy as np
import pandas as pd
from scipy.stats import linregress

# Create the matrix (each row is a statistic, each column is a time point)
data = {
    'injectionrate': [926.00, 900.00, 939.00, 923.00, 904.00, 927.00, -1.00],
    'throughput': [926.00, 900.00, 939.00, 923.00, 904.00, 927.00, -1.00],
    'outrate': [-1.00, -1.00, 31949.00, -1.00, -1.00, -1.00, -1.00],
    'latency': [-1.00, -1.00, 52.00, -1.00, -1.00, -1.00, -1.00],
    'compressionratio': [100.00, 100.00, 100.00, 100.00, 100.00, 100.00, -1.00],
    'CPU-agg': [5.00, 1.00, 1.00, 5.00, 0.00, 0.00, -1.00]
}

df = pd.DataFrame(data)

# Replace -1.0 with NaN
df.replace(-1.0, np.nan, inplace=True)

# Time points (0, 1, 2, ...)
time_points = np.arange(len(df))

# Initialize lists to store slopes and intercepts
slopes = []
intercepts = []

# Loop over each row (statistic)
for row in df.T.values:  # Transpose to loop by row
    # Get the non-NaN indices and values
    mask = ~np.isnan(row)
    time_valid = time_points[mask]
    values_valid = row[mask]
    
    # If we have more than 1 valid point, perform linear regression
    if len(time_valid) > 1:
        slope, intercept, _, _, _ = linregress(time_valid, values_valid)
    else:
        slope, intercept = 0.0, values_valid[0]
    
    # Append the result to the lists
    slopes.append(slope)
    intercepts.append(intercept)

# Create a DataFrame to display results
results_df = pd.DataFrame({
    'Statistic': df.columns,
    'Slope': slopes,
    'Intercept': intercepts
})

# Display the slopes and intercepts
print(results_df)
