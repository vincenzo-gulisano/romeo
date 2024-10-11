#log_folder=$1
episodes=$1
steps=$2
log_folder=$3
bootstrap_server=$4


python ./python/DQNAgent.py ${episodes} ${steps} ${bootstrap_server} ${log_folder} > ${log_folder}/python_agent.log &

# Capture the process ID (PID) of the last background command
pid=$!

# Print the PID
echo $pid