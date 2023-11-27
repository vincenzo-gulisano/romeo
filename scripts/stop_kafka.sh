echo "killing kafka processes"
pkill -9 kafka_zookper
pkill -9 kafka_server
rm -rf /tmp/kafka-logs/ /tmp/zookeeper/