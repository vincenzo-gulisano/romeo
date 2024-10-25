
# ./scripts/create_plots_for_exp.sh data/exp16.16 False WELAW/synthetic
# ./scripts/create_plots_for_exp.sh data/exp16.16 False WELAW/linear
# python plotting/create_summary_data.py data/exp16.16/WELAW

# # ./scripts/create_plots_for_exp.sh data/exp16.16 False LOB/synthetic
# ./scripts/create_plots_for_exp.sh data/exp16.16 False LOB/linear
# python plotting/create_summary_data.py data/exp16.16/LOB

# # ./scripts/create_plots_for_exp.sh data/exp16.16 False ELOB/synthetic
# ./scripts/create_plots_for_exp.sh data/exp16.16 False ELOB/linear
# python plotting/create_summary_data.py data/exp16.16/ELOB

# # ./scripts/create_plots_for_exp.sh data/exp16.16 False WELOB/synthetic
# ./scripts/create_plots_for_exp.sh data/exp16.16 False WELOB/linear
# python plotting/create_summary_data.py data/exp16.16/WELOB

# # # python plotting/actions_rewards.py data/exp16.16 

# # # python plotting/actions_times.py data/exp16.16

# # # python plotting/plot_cumulative_reward.py data/exp16.16/ 1001 3100


# sed -i '' 's/linear/welob_linear/g' data/exp16.16/WELOB/baselines_data.csv
# sed -i '' 's/linear/elob_linear/g' data/exp16.16/ELOB/baselines_data.csv
# sed -i '' 's/linear/lob_linear/g' data/exp16.16/LOB/baselines_data.csv
# sed -i '' 's/linear/welaw_linear/g' data/exp16.16/WELAW/baselines_data.csv

# # # sed -i '' 's/synthetic/welob_synthetic/g' data/exp16.16/WELOB/baselines_data.csv
# # # sed -i '' 's/synthetic/elob_synthetic/g' data/exp16.16/ELOB/baselines_data.csv
# # # sed -i '' 's/synthetic/lob_synthetic/g' data/exp16.16/LOB/baselines_data.csv
# # # sed -i '' 's/synthetic/welaw_synthetic/g' data/exp16.16/WELAW/baselines_data.csv

# find data/exp16.16/ -type f -name "baselines_data.csv" -exec cat {} + > data/exp16.16/merged.csv

# # find $1 -type f -name "python_agent.log" -exec bash -c '
# #   for file; do
# #     echo "Processing $file"
# #     cpu_count=$(grep -c "High cpu observed" "$file")
# #     latency_count=$(grep -c "High latency observed" "$file")
# #     echo "High CPU observed: $cpu_count"
# #     echo "High Latency observed: $latency_count"
# #   done
# # ' bash {} +

# # python plotting/plot_probs_evolution.py data/exp16.16

# # # python plotting/paper_plot_baselines_vs_multiple_agents_icpe_single_column.py data/10/linearroad-CCR/5/600 data/10/linearroad-CCR/5/600/lr_rate.csv data/exp16.16/merged.csv data/exp16.16/lr_baseline_vs_multiple_agents.pdf linearroad welaw_linear welob_linear,elob_linear,lob_linear,welaw_linear WEL-OB,EL-OB,L-OB,WEL-AW

# python plotting/paper_plot_baselines_vs_multiple_agents_icpe_single_column.py data/10/synthetic-CCR/1/900 data/10/synthetic-CCR/1/900/s_rate.csv data/exp16.16/merged.csv data/exp16.16/s_baseline_vs_multiple_agents.pdf synthetic welaw_synthetic welob_synthetic,elob_synthetic,lob_synthetic,welaw_synthetic WEL-OB,EL-OB,L-OB,WEL-AW

# ./scripts/extract_taus.sh data/exp16.16

#  python plotting/plot_taus.py data/exp16.16 

#  python plotting/compute_cumulative_steps_per_episode.py data/exp16.16/


# python plotting/plot_probs_evolution.py data/exp16.16
python plotting/plot_cumulative_reward.py data/exp16.16/ 1001 3100