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
base_folder="/home/vincenzo/romeo/data/jingyu/exp2.2/DQNAgent"
input_file="/home/vincenzo/woost/data/input/input.txt"

# Define lists of values
wa=5
ws=600
duration=10000000
d=601
rate=25000
repetition=0
starting_time_min=900
starting_time_max=9900
episodes=5
steps=100
agentstate="/home/vincenzo/romeo/data/jingyu/exp2.2/5/600/110000000/0/25000/601/dqn_model_episode_50.pth"
# compressions=(0 1 2 3 4 5 6 7 8 9 10)

# for compression in "${compressions[@]}"; do
#     echo "Compression: $compression"

# Define id variable with concatenation of values
id="${wa}/${ws}/DQNAgent"

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
python_pid=$(./scripts/start_DQNAgent.sh ${episodes} ${steps} ${agentstate} ${exp_folder})
echo "The PID of the python agent is ${python_pid}"

echo "Starting SPE"

echo "Starting experiment for ${id}"
args="-s ${exp_folder} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t RL -n ${rate} -d ${d} -stmin ${starting_time_min} -stmax ${starting_time_max}  -rer True"

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
    
echo "Creating extra stats"
grep -Eo '[0-9]+,[0-9]+,action [0-9]+' ${exp_folder}/episodes.csv | sed -E 's/,action /,/' | cut -d, -f1,3 > ${exp_folder}/actions.csv
grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ]' '{print $6,$3}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/rewards.csv
awk -F',' 'BEGIN {OFS=","; sum=0} {sum += $2; print $1, sum}' ${exp_folder}/rewards.csv > ${exp_folder}/cumulativereward.csv
awk -F',' 'NR > 1 { print $1 "," ($2 < 1000 ? 0 : 1) }' ${exp_folder}/latency.average.csv > ${exp_folder}/latency.violations.csv
grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ,]' '{print $9,$3}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/observedlatency.csv
grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ,]' '{print $9,$4}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/observedcompression.csv
grep -oE 'Received: -?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?,-?[0-9]+(\.[0-9]+)?/-?[0-9]+ at time [0-9]+(\.[0-9]+)?' ${exp_folder}/python_agent.log | awk -F'[/ ,]' '{print $9,$5}' | awk '{gsub(/\..*/, "", $1); print $1","$2}' > ${exp_folder}/observedcpu.csv

echo "Creating plots"
episodes_as_list=$(seq -s, 0 $((episodes-1)))
python plotting/plot_experiment_stats.py ${exp_folder}/ ${episodes_as_list} ${exp_folder}/episodesstats.csv

echo "Appending episodes stats to global csv"
python plotting/append_episodesstatscsv_to_global_one.py ${exp_folder}/episodesstats.csv ${base_folder}/compressionandepisodesstats.csv DQNAgent-E

# done

boxplot_stats=("rewards" "latency.average" "observedcompression" "latency.violations")

for boxplot_stat in "${boxplot_stats[@]}"; do
    python plotting/create_stat_episodes_boxplot_for_compressions.py ${base_folder}/compressionandepisodesstats.csv ${base_folder} ${boxplot_stat}
done