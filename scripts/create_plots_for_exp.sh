#!/bin/bash
base_exp_folder="./data/jingyu/exp4"
exp_folder="${base_exp_folder}/071-100"
episodes=30

# echo "Creating extra stats"
# grep -Eo '[0-9]+,[0-9]+,action [0-9]+' ${exp_folder}/episodes.csv | sed -E 's/,action /,/' | cut -d, -f1,3 > ${exp_folder}/actions.csv
# grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ]' '{print $6,$3}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/rewards.csv
# awk -F',' 'BEGIN {OFS=","; sum=0} {sum += $2; print $1, sum}' ${exp_folder}/rewards.csv > ${exp_folder}/cumulativereward.csv
# awk -F',' 'NR > 1 { print $1 "," ($2 < 1000 ? 0 : 1) }' ${exp_folder}/latency.average.csv > ${exp_folder}/latency.violations.csv
# grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ,]' '{print $9,$3}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/observedlatency.csv
# grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ,]' '{print $9,$4}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/observedcompression.csv
# grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ,]' '{print $9,$5}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/observedcpu.csv

# echo "Creating plots"
# episodes_as_list=$(seq -s, 0 $((episodes-1)))
# python plotting/plot_experiment_stats.py ${exp_folder}/ ${episodes_as_list} ${exp_folder}/episodesstats.csv

# python plotting/append_episodesstatscsv_to_global_one.py ${exp_folder}/episodesstats.csv ${base_exp_folder}/compressionandepisodesstats.csv DQNAgent-071-100

python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ rewards
python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ steps
python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ observedcompression
python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ latency.average