#!/bin/bash

# Assign the first parameter to base_exp_folder
base_exp_folder=$1

# Assign the second parameter to plot_probabilities
plot_probabilities=$2

# Shift the parameters so that $@ now contains only the remaining parameters (extra arguments)
shift 2

# Assign all remaining parameters to the folders_to_explore array
folders_to_explore=("$@")

# Debug output (optional, you can remove this)
echo "Base experiment folder: $base_exp_folder"
echo "Plot probabilities: $plot_probabilities"
echo "Folders to explore: ${folders_to_explore[@]}"

reward_pattern="New" # OLD FOR BASELINES
for folder_to_explore in "${folders_to_explore[@]}"; do

    exp_folder="${base_exp_folder}/${folder_to_explore}"

    echo "Processing folder ${exp_folder}"

    rm ${exp_folder}/episodesstats.csv 
    rm ${exp_folder}/compressionandepisodesstats.csv

    echo "Creating extra stats"
    grep -Eo '[0-9]+,[0-9]+,action [0-9]+' ${exp_folder}/episodes.csv | sed -E 's/,action /,/' | cut -d, -f1,3 > ${exp_folder}/actions.csv
    if [ "$reward_pattern" = "Old" ]; then
        awk '/^Got a new state\/reward pair: / {sub(/^Got a new state\/reward pair: /, ""); print int($1)} /^reward / {sub(/^reward /, ""); print $1}' ${exp_folder}/python_agent.log | paste -d, - -  > ${exp_folder}/rewards.csv
    else
        awk '/^Got a new state\/reward\/extrainfo msg: / {sub(/^Got a new state\/reward\/extrainfo msg: /, ""); print int($1)} /^reward / {sub(/^reward /, ""); print $1}' ${exp_folder}/python_agent.log | paste -d, - -  > ${exp_folder}/rewards.csv
    fi
    awk -F',' 'BEGIN {OFS=","; sum=0} {sum += $2; print $1, sum}' ${exp_folder}/rewards.csv > ${exp_folder}/cumulativereward.csv
    awk -F',' 'NR > 1 { print $1 "," ($2 == -1 ? -1 : ($2 < 1000 ? 0 : 1)) }' ${exp_folder}/latency.average.csv > ${exp_folder}/latency.violations.csv

    echo "Trying to extract the action probabilities based on soft max"
    python plotting/create_action_probabilities_csv_from_python_log.py ${exp_folder}/python_agent.log ${exp_folder}/actionsprobs.csv
    # If statement based on the boolean variable
    if [ "$plot_probabilities" = "True" ]; then
        python plotting/plot_action_probabilities.py ${exp_folder}/actionsprobs.csv ${exp_folder}/eps
    else
        echo "Not plotting probabilities since plot_probabilities is $plot_probabilities instead of True"
    fi

    echo "Creating plots and stats"
    if [ "$plot_probabilities" = "True" ]; then
        python plotting/plot_experiment_stats_exp.py ${exp_folder}/ ${exp_folder}/episodesstats.csv --makeplots --dumpdata
    else
        python plotting/plot_experiment_stats_exp.py ${exp_folder}/ ${exp_folder}/episodesstats.csv
    fi

    python plotting/append_episodesstatscsv_to_global_one.py ${exp_folder}/episodesstats.csv ${exp_folder}/compressionandepisodesstats.csv ${folder_to_explore}

done
