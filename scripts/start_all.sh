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

usecase=$1
policy=$2

# Set variables depending on the usecase
if [ "$usecase" = "LinearRoad" ]; then
    base_folder="./data/agentperformance_dqn/${policy}/linear"
    input_file="./data/input/input.txt"
    wa=5
    ws=600
    d=10
    starting_time_min=900
    starting_time_max=6000
    cpuThreshold=100
elif [ "$usecase" = "Synthetic" ]; then
    base_folder="./data/agentperformance_dqn/${policy}/synthetic"
    input_file="./data/input/synthetic.csv"
    wa=1
    ws=900
    d=10
    starting_time_min=1200
    starting_time_max=5800
    cpuThreshold=100
elif [ "$usecase" = "Synthetic5s" ]; then
    base_folder="./data/agentperformance_dqn/${policy}/synthetic5s"
    input_file="./data/input/synthetic.csv"
    wa=5
    ws=900
    d=10
    starting_time_min=1200
    starting_time_max=2100
    cpuThreshold=100
else
    echo "Invalid usecase."
    exit 1
fi

# Print the variables to verify
echo "usecaser: $usecase"
echo "policy: $policy"
echo "Base Folder: $base_folder"
echo "Input File: $input_file"
echo "WA: $wa"
echo "WS: $ws"
echo "D: $d"
echo "Starting Time Min: $starting_time_min"
echo "Starting Time Max: $starting_time_max"

duration=5000000000
episodes=15
steps=200
randomizeSeed=True

#bootstrapServer=129.16.20.158:9092
bootstrapServer='michelangelo.cse.chalmers.se:9092'

# Define id variable with concatenation of values
id="${wa}/${ws}/${duration}/${repetition}/${rate}"

# Create folder with id in base folder
exp_folder=${base_folder} #/${id}/${d}
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
#python_pid=$(./scripts/start_python_agent.sh ${exp_folder})
python_pid=$(./scripts/start_python_agent.sh ${episodes} ${steps} ${exp_folder} ${bootstrapServer} )
echo "The PID of the python agent is ${python_pid}"

echo "Starting SPE"

echo "Starting experiment for ${id} (compression)"
args="-s ${exp_folder} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t RL -d ${d} -stmin ${starting_time_min} -stmax ${starting_time_max} -usecase ${usecase} -pb ${policy} -rer ${randomizeSeed} -bs ${bootstrapServer} -ct ${cpuThreshold}"
echo "args=${args}"
mvn clean compile package exec:java -Dexec.mainClass="com.vincenzogulisano.javapythoncommunicator.JPComm" -Dexec.args="${args}" > ${exp_folder}/spe.log 2>&1 &

sleep 5

# Use pgrep to find the PID of the Java process
JVM_PID=$(pgrep -f "com.vincenzogulisano.javapythoncommunicator.JPComm")

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
kill -9 ${python_pid}
kill -9 ${cpu_monitor_pid}

./scripts/stop_kafka.sh
./scripts/stop_kafka.sh

pkill java
pkill python