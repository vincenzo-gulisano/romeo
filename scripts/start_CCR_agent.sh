episodes=$1
steps=$2
compression=$3
log_folder=$4

python ./python/CCRAgent.py ${episodes} ${steps} ${compression} > ${log_folder}/python_agent.log &

# Capture the process ID (PID) of the last background command
pid=$!

# Print the PID
echo $pid