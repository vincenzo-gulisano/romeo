#!/bin/bash

# Create the episodelogs directory if it doesn't already exist
base_folder=$1
echo "Base folder: ${base_folder}"
mkdir -p ${base_folder}/episodelogs

# Loop from 1 to 100
for i in {0..200}
do
    echo "Looking for episode $i"	
    # Find the starting line number
    start_line=$(grep -n "starting episode ${i}$" ${base_folder}/python_agent.log | cut -d: -f1)
    echo "start line: $start_line"
    # Find the ending line number
    # Adjust "Episode 4 tot_t" to the correct pattern for finding the end of an episode.
    # It seems there might be a typo or a specific case for "Episode 4". 
    # If it's meant to be dynamic, replace 4 with $i
    end_line=$(grep -n "Episode  $i tot_t" ${base_folder}/python_agent.log | cut -d: -f1)
    echo "end line: $end_line"
    # Check if start_line and end_line are found
    if [[ -n $start_line && -n $end_line ]]; then
        # Use sed to extract text between the start and end lines, inclusive
        sed -n "${start_line},${end_line}p" ${base_folder}/python_agent.log > "${base_folder}/episodelogs/episode_${i}.txt"
    else
        echo "Episode $i not found."
    fi
done

