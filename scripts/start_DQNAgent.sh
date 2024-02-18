episodes=$1
steps=$2
agentstate=$3
log_folder=$4

python ./python/DQNAgent.py ${episodes} ${steps} -learningactive False -agentstate ${agentstate} > ${log_folder}/python_agent.log &

# Capture the process ID (PID) of the last background command
pid=$!

# Print the PID
echo $pid 