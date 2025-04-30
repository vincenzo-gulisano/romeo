kafka_folder=~/kafka_2.13-3.6.0
echo "killing kafka processes"
${kafka_folder}/bin/zookeeper-server-stop.sh
${kafka_folder}/bin/kafka-server-stop.sh

rm -rf /tmp/kafka-logs
rm -rf /tmp/zookeeper