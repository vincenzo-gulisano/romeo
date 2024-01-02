log_folder=$1

python ./python/DummyRLAgent.py > ${log_folder}/python_agent.log &

# Capture the process ID (PID) of the last background command
pid=$!

# Print the PID
echo $pid