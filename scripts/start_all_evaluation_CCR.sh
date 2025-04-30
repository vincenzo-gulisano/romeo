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

##################################################################

# # This is for Linear Road - Agent performance

# bootstrapServer=129.16.20.20:9092 # THIS IS MICHELANGELO
# cpuThreshold=100
# base_folder="./data/agentperformance/linearroad"
# input_file="./data/input/input.txt"
# wa=5
# ws=600
# starting_time_min=900
# starting_time_max=9900
# usecase="LinearRoad"
# duration=100000000
# randomSeeds=(1)
# policy="ELOB"
# episodes=15
# compressions=(10 9 8 7 6 5 4 3 2 1 0)

# declare -A steps_map
# declare -A period_map

# # Agent contacting every 0.5 seconds, 40 times
# steps_map["0"]=200
# period_map["0"]=0.5
# steps_map["1"]=200
# period_map["1"]=0.5
# steps_map["2"]=200
# period_map["2"]=0.5
# steps_map["3"]=200
# period_map["3"]=0.5
# steps_map["4"]=200
# period_map["4"]=0.5
# steps_map["5"]=200
# period_map["5"]=0.5
# steps_map["6"]=200
# period_map["6"]=0.5
# steps_map["7"]=200
# period_map["7"]=0.5
# steps_map["8"]=200
# period_map["8"]=0.5
# steps_map["9"]=200
# period_map["9"]=0.5
# steps_map["10"]=200
# period_map["10"]=0.5

# randomizeSeed=True

##################################################################

# This is for Linear Road - Scalability

bootstrapServer=129.16.20.20:9092 # THIS IS MICHELANGELO
cpuThreshold=100
base_folder="./data/scalability/linearroad"
input_file="./data/input/input.txt"
wa=5
ws=600
starting_time_min=8500
starting_time_max=9900
usecase="LinearRoad"
duration=100000000
randomSeeds=(1 2 3 4 5)
policy="WELAW"
episodes=1
compressions=(3)

declare -A steps_map
declare -A period_map

# Comment the one you are not going to use

# # Agent contacting every 0.5 seconds, 80 times <- this is agent ON
steps_map["3"]=80
period_map["3"]=0.5

# Agent contacting every 80 seconds, 2 times <- this is agent OFF
# steps_map["3"]=2
# period_map["3"]=80

randomizeSeed=False

##################################################################

for randomSeed in "${randomSeeds[@]}"; do
for compression in "${compressions[@]}"; do
    
    # Default values
    steps=${steps_map[$compression]:-2} # Default to 2 if not mapped
    state_measurement_check_period=${period_map[$compression]:-120.0} # Default to 120.0 if not mapped
    
    echo "For compression $compression:"
    echo "  steps: $steps"
    echo "  state_measurement_check_period: $state_measurement_check_period"

    # Define id variable with concatenation of values
    id="${compression}/${steps}/${state_measurement_check_period}/${randomSeed}"

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
    python_pid=$(./scripts/start_CCR_agent.sh ${episodes} ${steps} ${compression} ${state_measurement_check_period} ${exp_folder})
    echo "The PID of the python agent is ${python_pid}"

    echo "Starting SPE"

    echo "Starting experiment for ${id} (compression)"
    args="-s ${exp_folder} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t RL -d 10 -stmin ${starting_time_min} -stmax ${starting_time_max} -usecase ${usecase} -pb ${policy} -rer ${randomizeSeed} -randomSeed ${randomSeed} -bs ${bootstrapServer} -ct ${cpuThreshold}"
    echo "args=${args}"
    
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
done
