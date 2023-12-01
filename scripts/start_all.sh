#!/bin/bash

# Define base folder and input file
base_folder="/home/vincenzo/romeo/data/output"
input_file="/home/vincenzo/woost/data/input/input.txt"

# Define lists of values
wa=60
ws=600
duration=1200000
d=2000
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
args="-s ${exp_folder} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t FIXEDRATE -n ${rate} -d ${d}"

mvn clean compile package exec:java -Dexec.mainClass="com.vincenzogulisano.javapythoncommunicator.JPComm" -Dexec.args="${args}" > ${exp_folder}/spe.log 2>&1

echo "SPE done, killing the rest..."

kill -9 ${python_pid}

./scripts/stop_kafka.sh
./scripts/stop_kafka.sh