#!/bin/bash
base_exp_folder="./data/exp14/WEAAW/synthetic"
folders_to_explore=("14.1")
plot_probabilities="True"
for folder_to_explore in "${folders_to_explore[@]}"; do

    exp_folder="${base_exp_folder}/${folder_to_explore}"

    echo "Processing folder ${exp_folder}"

    rm ${exp_folder}/episodesstats.csv 
    rm ${exp_folder}/compressionandepisodesstats.csv

    echo "Creating extra stats"
    grep -Eo '[0-9]+,[0-9]+,action [0-9]+' ${exp_folder}/episodes.csv | sed -E 's/,action /,/' | cut -d, -f1,3 > ${exp_folder}/actions.csv
    awk '/^Got a new state\/reward pair: / {sub(/^Got a new state\/reward pair: /, ""); print int($1)} /^reward / {sub(/^reward /, ""); print $1}' ${exp_folder}/python_agent.log | paste -d, - -  > ${exp_folder}/rewards.csv
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
        python plotting/plot_experiment_stats_exp.py ${exp_folder}/ ${exp_folder}/episodesstats.csv --makeplots
    else
        python plotting/plot_experiment_stats_exp.py ${exp_folder}/ ${exp_folder}/episodesstats.csv
    fi

    python plotting/append_episodesstatscsv_to_global_one.py ${exp_folder}/episodesstats.csv ${exp_folder}/compressionandepisodesstats.csv ${folder_to_explore}

    # python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ rewards,sum,,
    # python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ ratio.percent,mean,,
    # python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ latency.violations,sum,,
    # python plotting/create_stat_episodes_boxplot_for_compressions.py ${exp_folder}/compressionandepisodesstats.csv ${exp_folder}/ steps,sum,,
    # python plotting/plot_scatter.py ${exp_folder}/ ${exp_folder}/cum_reward_vs_event_time.pdf --stat_X=eventtime.max --stat_Y=rewards --aggregation_X=min --aggregation_Y=sum
    # python plotting/plot_scatter.py ${exp_folder}/ ${exp_folder}/ratio_vs_event_time.pdf --stat_X=eventtime.max --stat_Y=ratio.percent --aggregation_X=min --aggregation_Y=mean
    # python plotting/plot_scatter.py ${exp_folder}/ ${exp_folder}/violations_vs_event_time.pdf --stat_X=eventtime.max --stat_Y=latency.violations --aggregation_X=min --aggregation_Y=sum

done
