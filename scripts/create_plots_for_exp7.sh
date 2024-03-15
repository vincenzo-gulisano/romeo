#!/bin/bash
base_exp_folder="./data/jingyu/exp7"
folders_to_explore=(rl2)
for folder_to_explore in "${folders_to_explore[@]}"; do

    exp_folder="${base_exp_folder}/${folder_to_explore}"

    echo "Processing folder ${exp_folder}"

    episodes=10

    rm ${exp_folder}/episodesstats.csv 
    rm ${exp_folder}/compressionandepisodesstats.csv

    echo "Creating extra stats"
    grep -Eo '[0-9]+,[0-9]+,action [0-9]+' ${exp_folder}/episodes.csv | sed -E 's/,action /,/' | cut -d, -f1,3 > ${exp_folder}/actions.csv
    awk '/^Got a new state\/reward pair: / {sub(/^Got a new state\/reward pair: /, ""); print int($1)} /^reward / {sub(/^reward /, ""); print $1}' ${exp_folder}/python_agent.log | paste -d, - -  > ${exp_folder}/rewards.csv
    awk -F',' 'BEGIN {OFS=","; sum=0} {sum += $2; print $1, sum}' ${exp_folder}/rewards.csv > ${exp_folder}/cumulativereward.csv
    awk -F',' 'NR > 1 { print $1 "," ($2 == -1 ? -1 : ($2 < 1000 ? 0 : 1)) }' ${exp_folder}/latency.average.csv > ${exp_folder}/latency.violations.csv

    echo "Creating plots"
    python plotting/plot_experiment_stats_exp7.py ${exp_folder}/ ${exp_folder}/episodesstats.csv 

    python plotting/append_episodesstatscsv_to_global_one.py ${exp_folder}/episodesstats.csv ${exp_folder}/compressionandepisodesstats.csv DQNAgent-exp7

    python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ rewards,sum,,
    python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ ratio.percent,mean,,
    python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ latency.violations,sum,,
    python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ steps,sum,,
    python plotting/plot_scatter.py ${exp_folder}/ ${exp_folder}/cum_reward_vs_mean_rate.pdf --stat_X=injectionrate.rate --stat_Y=rewards --aggregation_X=mean --aggregation_Y=sum
    python plotting/plot_scatter.py ${exp_folder}/ ${exp_folder}/ratio_vs_mean_rate.pdf --stat_X=injectionrate.rate --stat_Y=ratio.percent --aggregation_X=mean --aggregation_Y=mean
    python plotting/plot_scatter.py ${exp_folder}/ ${exp_folder}/violations_vs_mean_rate.pdf --stat_X=injectionrate.rate --stat_Y=latency.violations --aggregation_X=mean --aggregation_Y=sum

done