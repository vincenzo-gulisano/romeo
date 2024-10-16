
# # # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False WELAW/synthetic
# # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False WELAW/linear
# # # # python plotting/create_summary_data.py data/exp16.12/WELAW

# # # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False LOB/synthetic
# # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False LOB/linear
# # # # python plotting/create_summary_data.py data/exp16.12/LOB

# # # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False ELOB/synthetic
# # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False ELOB/linear
# # # # python plotting/create_summary_data.py data/exp16.12/ELOB

# # # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False WELOB/synthetic
# # # # ./scripts/create_plots_for_exp.sh data/exp16.12 False WELOB/linear
# # # # python plotting/create_summary_data.py data/exp16.12/WELOB

# # # python plotting/actions_rewards.py data/exp16.12 

# # # python plotting/actions_times.py data/exp16.12

# # python plotting/plot_cumulative_reward.py data/exp16.12/ 1001 3100


# sed -i '' 's/linear/welob_linear/g' data/exp16.12/WELOB/baselines_data.csv
# sed -i '' 's/linear/elob_linear/g' data/exp16.12/ELOB/baselines_data.csv
# sed -i '' 's/linear/lob_linear/g' data/exp16.12/LOB/baselines_data.csv
# sed -i '' 's/linear/welaw_linear/g' data/exp16.12/WELAW/baselines_data.csv

# find data/exp16.12/ -type f -name "baselines_data.csv" -exec cat {} + > data/exp16.12/merged.csv

python plotting/paper_plot_baselines_vs_multiple_agents_icpe_single_column.py data/10/linearroad-CCR/5/600 data/10/linearroad-CCR/5/600/lr_rate.csv data/exp16.12/merged.csv data/exp16.12/lr_baseline_vs_multiple_agents.pdf linearroad welaw_linear welob_linear,elob_linear,lob_linear,welaw_linear WEL-OB,EL-OB,L-OB,WEL-AW

