#!/bin/bash


# Function to get the current time in seconds
get_current_time() {
    echo $(date +%s)
}

# Function to sleep until a certain time or until a PID is alive
sleep_until_time_or_pid() {
    local target_time=$1
    local pid_to_check=$2

    while true; do
        current_time=$(get_current_time)
        time_left=$((target_time - current_time))

        # Check if the specified PID is alive
        if ! kill -0 "$pid_to_check" 2>/dev/null; then
            echo "Process with PID $pid_to_check is not alive."
            break
        fi

        # Check if the time has elapsed
        if [ "$time_left" -le 0 ]; then
            echo "Time has elapsed."
            break
        fi

        # Sleep for a short interval (adjust as needed)
        sleep 1
    done
}

# Define base folder and input file
base_folder="/home/vincenzo/romeo/data/mainquery/output"
input_file="/home/vincenzo/woost/data/input/input.txt"

# Define lists of values
wa=1
ws=300
duration=3600000
d=601 # Not used, in principle
rate=20000 # Not used, in principle
repetition=0 # Not used, in principle
starting_time_min=900 # Not used, in principle
starting_time_max=9900 # Not used, in principle
duration=300000 #3600000
ratetype=FIXEDRATE #REALRATE
lfa=true #false

# Define id variable with concatenation of values
id="${wa}/${ws}/${duration}/${repetition}/${ratetype}/${rate}"

# Create folder with id in base folder
exp_folder=${base_folder}/${id}/${d}
mkdir -p "${exp_folder}"

echo "Cleaning stats folder"
rm -rf ${exp_folder}/*.csv
rm -rf ${exp_folder}/*.log
rm -rf ${exp_folder}/*.pdf

echo "Killing any past JVM instance that should have been killed before"
# Get PIDs using pgrep
PIDS=$(pgrep -f "com.vincenzogulisano.usecases.linearroad.QueryCountConsecutiveStops")

# Check if PIDS is not empty
if [ -n "$PIDS" ]; then
    # Iterate over each PID and send kill command
    for PID in $PIDS; do
        kill "$PID"
        echo "JVM with PID $PID killed."
    done
fi

# echo "killing previous python processes and stopping Kafka"
# pkill -9 python
# ./scripts/stop_kafka.sh

# sleep 3

# echo "Starting Kafka"
# ./scripts/start_kafka.sh ${exp_folder}

# echo "Starting Python agent"
# python_pid=$(./scripts/start_python_agent.sh ${exp_folder})
# echo "The PID of the python agent is ${python_pid}"

echo "Starting SPE"

echo "Starting experiment for ${id} (compression)"
nanosleep=$((1000000000 / rate))
echo "For rate ${rate} the nano sleep is ${nanosleep}"
args="-s ${exp_folder} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t ${ratetype} -n ${nanosleep} -d ${d} -stmin ${starting_time_min} -stmax ${starting_time_max} -lfa ${lfa}"

mvn clean compile package exec:java -Dexec.mainClass="com.vincenzogulisano.usecases.linearroad.QueryCountConsecutiveStops" -Dexec.args="${args}" > ${exp_folder}/spe.log 2>&1 &

# sleep 5

# Use pgrep to find the PID of the Java process
JVM_PID=$(pgrep -f "com.vincenzogulisano.usecases.linearroad.QueryCountConsecutiveStops")

# Print the PID
echo "JVM PID: $JVM_PID"

# args=($JVM_PID ${exp_folder}/)
# python python/cpu_monitor.py $JVM_PID ${exp_folder}/ &
# cpu_monitor_pid=$!


# Example: Sleep until 60 seconds from now or until process with PID 123 is alive
duration_seconds=$((duration / 1000))
target_time=$(( $(get_current_time) + duration_seconds ))

echo "Sleeping until $target_time or until process with PID $JVM_PID is not alive."
sleep_until_time_or_pid "$target_time" "$JVM_PID"

kill -9 ${JVM_PID}
# kill -9 ${python_pid}
# kill -9 ${cpu_monitor_pid}

# ./scripts/stop_kafka.sh
# ./scripts/stop_kafka.sh

# pkill java
# pkill python