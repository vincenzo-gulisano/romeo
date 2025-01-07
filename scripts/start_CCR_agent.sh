episodes=$1
steps=$2
compression=$3
state_measurement_check_period=$4
log_folder=$5

python ./python/CCRAgent.py ${episodes} ${steps} ${compression} ${state_measurement_check_period} > ${log_folder}/python_agent.log &

# Capture the process ID (PID) of the last background command
pid=$!

# Print the PID
echo $pid