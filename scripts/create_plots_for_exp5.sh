#!/bin/bash
base_exp_folder="./data/jingyu/exp5.1"
exp_folder="${base_exp_folder}/101-600"
episodes=100

# rm ${exp_folder}/episodesstats.csv 
# rm ${base_exp_folder}/compressionandepisodesstats.csv

echo "Creating extra stats"
grep -Eo '[0-9]+,[0-9]+,action [0-9]+' ${exp_folder}/episodes.csv | sed -E 's/,action /,/' | cut -d, -f1,3 > ${exp_folder}/actions.csv
awk '/^Got a new state\/reward pair: / {sub(/^Got a new state\/reward pair: /, ""); print int($1)} /^reward / {sub(/^reward /, ""); print $1}' ${exp_folder}/python_agent.log | paste -d, - -  > ${exp_folder}/rewards.csv
awk -F',' 'BEGIN {OFS=","; sum=0} {sum += $2; print $1, sum}' ${exp_folder}/rewards.csv > ${exp_folder}/cumulativereward.csv
awk -F',' 'NR > 1 { print $1 "," ($2 < 1000 ? 0 : 1) }' ${exp_folder}/latency.average.csv > ${exp_folder}/latency.violations.csv

echo "Creating plots"
python plotting/plot_experiment_stats_exp5.py --print_global_events ${exp_folder}/ ${exp_folder}/episodesstats.csv 

python plotting/append_episodesstatscsv_to_global_one.py ${exp_folder}/episodesstats.csv ${base_exp_folder}/compressionandepisodesstats.csv DQNAgent-101-600

python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ rewards
python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ ratio.percent
python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ latency.average
python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_exp_folder}/compressionandepisodesstats.csv ${base_exp_folder}/ steps