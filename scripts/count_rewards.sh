#!/bin/bash

# Directory to search
search_dir=$1

# Array of reward values to check
rewards=(0 1 2 -5)

# Find all files named python_agent.log recursively in the specified directory
find "$search_dir" -type f -name 'python_agent.log' -print0 | while IFS= read -r -d $'\0' file; do
    echo "Processing file: $file"
    # Loop over each reward value
    for reward in "${rewards[@]}"; do
        # Count occurrences of "reward x"
        count=$(grep -io "reward $reward" "$file" | wc -l)
        echo "Count of 'reward $reward': $count"
    done
done
