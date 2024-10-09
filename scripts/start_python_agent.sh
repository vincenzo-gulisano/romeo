#log_folder=$1
episodes=$1
steps=$2
log_folder=$3


python ./python/DQNAgent.py ${episodes} ${steps} --exp_folder ${log_folder}> ${log_folder}/python_agent.log &

# Capture the process ID (PID) of the last background command
pid=$!

# Print the PID
echo $pid