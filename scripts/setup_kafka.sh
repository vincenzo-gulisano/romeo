kafka_folder=/home/vincenzo/kafka_2.13-3.6.0

echo "Starting zookeeper and keeping track of the id"
${kafka_folder}/bin/zookeeper-server-start.sh ${kafka_folder}/config/zookeeper.properties & 
zookeper_pid=$!

sleep 5

echo "Starting kafka and keeping track of the id"
${kafka_folder}/bin/kafka-server-start.sh ${kafka_folder}/config/server.properties & 
kafka_pid=$!

sleep 5

echo "Registering topics actions and logs"
${kafka_folder}/bin/kafka-topics.sh --create --topic actions --bootstrap-server localhost:9092
${kafka_folder}/bin/kafka-topics.sh --create --topic logs --bootstrap-server localhost:9092

echo "All done, if you want to terminate kafka run stop_kafka.sh ${zookeper_pid} ${kafka_pid}"