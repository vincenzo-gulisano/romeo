#!/bin/bash

# Define base folder and input file
base_folder="/home/vincenzo/romeo/data/output"
input_file="/home/vincenzo/woost/data/input/input.txt"

# Define lists of values
wa=5
ws=600
duration=12000000
d=100000000
rate=25000
repetition=0

# Define id variable with concatenation of values
id="${wa}/${ws}/${duration}/${repetition}/${rate}"

# Create folder with id in base folder
exp_folder=${base_folder}/${id}/${d}
mkdir -p "${exp_folder}"

echo "Starting Kafka"
./scripts/start_kafka.sh ${exp_folder}

echo "Starting Python agent"
python_pid=$(./scripts/start_python_agent.sh ${exp_folder})
echo "The PID of the python agent is ${python_pid}"

echo "Starting SPE"

echo "Starting experiment for ${id} (compression)"
args="-s ${exp_folder} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t REALRATE -n ${rate} -d ${d}"

mvn clean compile package exec:java -Dexec.mainClass="com.vincenzogulisano.javapythoncommunicator.JPComm" -Dexec.args="${args}" > ${exp_folder}/spe.log 2>&1 &

sleep 5

# Use pgrep to find the PID of the Java process
JVM_PID=$(pgrep -f "com.vincenzogulisano.javapythoncommunicator.JPComm")

# Print the PID
echo "JVM PID: $JVM_PID"

args=($JVM_PID ${exp_folder}/)
python python/cpu_monitor.py $JVM_PID ${exp_folder}/ &
cpu_monitor_pid=$!

sleep $((duration / 1000))

echo "Duration time elapsed, killing..."

kill -9 ${JVM_PID}
kill -9 ${python_pid}
kill -9 ${cpu_monitor_pid}

./scripts/stop_kafka.sh
./scripts/stop_kafka.sh

pkill java
pkill python