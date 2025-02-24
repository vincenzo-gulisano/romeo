# romeo
ReinfOrceMent lEarning cOmpressor

# Linear Road Experiments (Fig. 7)

- To begin with, run the baselines for different X values (notice I changed from WELAW to WELOB only for compression 0 and always starting with compression 10 when loading the state... this is now hardcoded and might be better to have as a parameter since I am not sure whether it affects the scalability experiments)
- `./scripts/start_all_evaluation_CCR.sh`
- `./scripts/create_plots_for_exp.sh data/agentperformance/linearroad True 0/40/0.5/1 1/40/0.5/1 2/40/0.5/1 3/40/0.5/1 4/40/0.5/1 5/40/0.5/1 6/40/0.5/1 7/40/0.5/1 8/40/0.5/1 9/40/0.5/1 10/40/0.5/1`
- `python plotting/create_summary_data.py data/agentperformance/linearroad`

The final plot
`python plotting/paper_plot_baselines_vs_multiple_agents_icpe_single_column.py data/agentperformance/linearroad data/lr_rate.csv data/exp16.20/merged.csv data/exp16.20/lr_baseline_vs_multiple_agents.pdf data/exp16.20/lr_baseline_vs_multiple_agents.png linearroad welaw_linear welob_linear,elob_linear,lob_linear,welaw_linear WEL-OB,EL-OB,L-OB,WEL-AW`

- Probably need to change the naming of the folders, for now did it manually
- Looked at previous data (the previous baselines and it seems the format was the same, so going on for now)

# Scalability Experiments

- These are started using the start_all_evaluation_CCR.sh script.
  - The experiment config needs to be added in the beginning. The script contains a sample setup to compare no agent vs. agent for a given compression for Linear Road
- To then create the plots, you can use the following scripts (these are using the folders given in the sample `start_all_evaluation_CCR.sh` script)
  - `./scripts/create_plots_for_exp.sh data/scalability/linearroad/3/80/0.5 True 1 2 3 4 5`
  - `./scripts/create_plots_for_exp.sh data/scalability/linearroad/3/2/80 True 1 2 3 4 5`
  - `python plotting/merge_overhead_data.py data/scalability/linearroad/3/2/80 data/scalability/linearroad/3/80/0.5 1 2 3 4 5 data/scalability/linearroad/merged.csv`
  - `python plotting/compute_overheads_from_merged_data.py data/scalability/linearroad/merged.csv data/scalability/linearroad/diffs.csv`
  - `python plotting/plot_overheads.py data/scalability/linearroad/diffs.csv data/scalability/linearroad/plot.pdf`
- To create the same plot you find in the paper, you can then use (notice in the paper the experiments are for both linear road and synthetic. In the command below just reusing twice the linear road data for simplicity)
  - `python plotting/plot_overheads_combined.py data/scalability/linearroad/diffs.csv data/scalability/linearroad/diffs.csv data/scalability/plotcombined.pdf`
  