# romeo
ReinfOrceMent lEarning cOmpressor



# Scalability Experiments

- These are started using the start_all_evaluation_CCR.sh script.
  - The experiment config needs to be added in the beginning. The script contains a sample setup to compare no agent vs. agent for a given compression for Linear Road
- To then create the plots, you can use the following scripts (these are using the folders given in the sample `start_all_evaluation_CCR.sh` script)
  - `./scripts/create_plots_for_exp.sh data/scalability/linearroad/3/80/0.5 True 1 2 3 4 5`
  - `./scripts/create_plots_for_exp.sh data/scalability/linearroad/3/2/80 True 1 2 3 4 5`
  - `python plotting/merge_overhead_data.py data/scalability/linearroad/3/2/80 data/scalability/linearroad/5/80/0.5 1 2 3 4 5 data/scalability/linearroad/merged.csv`
  - `python plotting/compute_overheads_from_merged_data.py data/scalability/linearroad/merged.csv data/scalability/linearroad/diffs.csv`
  - `python plotting/plot_overheads.py data/scalability/linearroad/diffs.csv data/scalability/linearroad/plot.pdf`
- To create the same plot you find in the paper, you can then use
  