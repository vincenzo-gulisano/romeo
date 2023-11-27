kafka_folder=/home/vincenzo/kafka_2.13-3.6.0

rm -rf /tmp/kafka-logs/ /tmp/zookeeper/

echo "Starting zookeeper..."
${kafka_folder}/bin/zookeeper-server-start.sh ${kafka_folder}/config/zookeeper.properties &

sleep 10

echo "Starting kafka..."
${kafka_folder}/bin/kafka-server-start.sh ${kafka_folder}/config/server.properties &

sleep 10

echo "Registering topics actions and logs"
${kafka_folder}/bin/kafka-topics.sh --create --topic actions --bootstrap-server localhost:9092
${kafka_folder}/bin/kafka-topics.sh --create --topic stats --bootstrap-server localhost:9092

echo "All done, if you want to terminate kafka run stop_kafka.sh"