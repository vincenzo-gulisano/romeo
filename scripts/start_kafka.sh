log_folder=$1
echo "Log folder for kafka related logs: ${log_folder}"

kafka_folder=~/kafka_2.13-3.6.0

rm -rf /tmp/kafka-logs
rm -rf /tmp/zookeeper

echo "Starting zookeeper..."
${kafka_folder}/bin/zookeeper-server-start.sh ${kafka_folder}/config/zookeeper.properties  > ${log_folder}/zookeper_start.log 2>&1 &

sleep 5

echo "Starting kafka..."
${kafka_folder}/bin/kafka-server-start.sh ${kafka_folder}/config/server.properties > ${log_folder}/kafka_start.log 2>&1 &

sleep 5

echo "Registering topic dchanges"
${kafka_folder}/bin/kafka-topics.sh --create --topic dchanges --bootstrap-server localhost:9092 > ${log_folder}/topic_creation.log 2>&1
echo "Registering topic logs"
${kafka_folder}/bin/kafka-topics.sh --create --topic stats --bootstrap-server localhost:9092 >> ${log_folder}/topic_creation.log 2>&1

echo "All done, if you want to terminate kafka run stop_kafka.sh"