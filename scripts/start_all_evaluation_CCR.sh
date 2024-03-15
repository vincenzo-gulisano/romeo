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

# This is for Linear Road
base_folder="/home/vincenzo/romeo/data/output/CCR-exp7"
input_file="/home/vincenzo/woost/data/input/input.txt"
wa=5
ws=600
d=601
starting_time_min=900
starting_time_max=9900
usecase="LinearRoad"

# This is for the synthetic query
base_folder="/home/vincenzo/romeo/data/output/synthetic-CCR"
input_file="/home/vincenzo/romeo/data/input/synthetic.csv"
wa=1
ws=900
d=901
starting_time_min=1200
starting_time_max=6800
usecase="Synthetic"

# Define lists of values
duration=100000000
episodes=10
steps=150
compressions=(0 1 2 3 4 5 6 7 8 9 10 -1)

for compression in "${compressions[@]}"; do
    echo "Compression: $compression"

    # Define id variable with concatenation of values
    id="${wa}/${ws}/${compression}"

    # Create folder with id in base folder
    exp_folder=${base_folder}/${id}
    mkdir -p "${exp_folder}"

    echo "Cleaning stats folder"
    rm -rf ${exp_folder}/*.csv
    rm -rf ${exp_folder}/*.log
    rm -rf ${exp_folder}/*.pdf

    echo "Killing any past JVM instance that should have been killed before"
    # Get PIDs using pgrep
    PIDS=$(pgrep -f "com.vincenzogulisano.javapythoncommunicator.JPComm")

    # Check if PIDS is not empty
    if [ -n "$PIDS" ]; then
        # Iterate over each PID and send kill command
        for PID in $PIDS; do
            kill "$PID"
            echo "JVM with PID $PID killed."
        done
    fi

    echo "killing previous python processes and stopping Kafka"
    pkill -9 python
    ./scripts/stop_kafka.sh

    sleep 3

    echo "Starting Kafka"
    ./scripts/start_kafka.sh ${exp_folder}

    echo "Starting Python agent"
    python_pid=$(./scripts/start_CCR_agent.sh ${episodes} ${steps} ${compression} ${exp_folder})
    echo "The PID of the python agent is ${python_pid}"

    echo "Starting SPE"

    echo "Starting experiment for ${id} (compression)"
    args="-s ${exp_folder} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t RL -d ${d} -stmin ${starting_time_min} -stmax ${starting_time_max} -usecase ${usecase}"

    mvn clean compile package exec:java -Dexec.mainClass="com.vincenzogulisano.javapythoncommunicator.JPComm" -Dexec.args="${args}" > ${exp_folder}/spe.log 2>&1 &

    sleep 5

    # Use pgrep to find the PID of the Java process
    JVM_PID=$(pgrep -f "com.vincenzogulisano.javapythoncommunicator.JPComm")

    # Print the PID
    echo "JVM PID: $JVM_PID"

    # Example: Sleep until 60 seconds from now or until process with PID 123 is alive
    duration_seconds=$((duration / 1000))
    target_time=$(( $(get_current_time) + duration_seconds ))

    echo "Sleeping until $target_time or until process with PID $JVM_PID is not alive."
    sleep_until_time_or_pid "$target_time" "$JVM_PID"

    kill -9 ${JVM_PID}
    kill -9 ${python_pid}
    kill -9 ${cpu_monitor_pid}

    ./scripts/stop_kafka.sh
    ./scripts/stop_kafka.sh

done