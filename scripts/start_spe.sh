#!/bin/bash

# Define base folder and input file
base_folder="/home/vincenzo/romeo/data/output"
input_file="/home/vincenzo/woost/data/input/input.txt"

# Define lists of values
wa=60
ws=10800
duration=3600000
d=2000
rate=25000
repetition=0

# Define id variable with concatenation of values
id="${wa}/${ws}/${duration}/${repetition}/${rate}"

# Create folder with id in base folder
mkdir -p "${base_folder}/${id}/${d}"

echo "Starting experiment for ${id} (compression)"
args="-s ${base_folder}/${id}/${d} -i ${input_file} -l ${duration} -wa ${wa} -ws ${ws} -t FIXEDRATE -n ${rate} -d ${d}"

mvn clean compile exec:java -Dexec.mainClass="com.vincenzogulisano.javapythoncommunicator.JPComm" -Dexec.args="${args}"
