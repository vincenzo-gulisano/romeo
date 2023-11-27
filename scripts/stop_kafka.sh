echo "killing kafka processes"
kill -9 $1
kill -9 $2
rm -rf /tmp/kafka-logs/ /tmp/zookeeper/