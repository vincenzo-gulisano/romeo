import threading
import time
import random
from confluent_kafka import Producer, Consumer, KafkaError


class KafkaActionsProducer:
    def __init__(self, bootstrap_servers='michelangelo.cse.chalmers.se:9092', actions_topic='actions'):
        self.bootstrap_servers = bootstrap_servers
        self.actions_topic = actions_topic
        self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})

    def produce_action(self):
        while True:
            # Produce a random action to the 'actions' topic
            action = random.choice(['actionA', 'actionB'])
            self.producer.produce(self.actions_topic, key=str(time.time()), value=action)
            self.producer.flush()
            time.sleep(1)

    def start_producer_thread(self):
        producer_thread = threading.Thread(target=self.produce_action)
        producer_thread.daemon = True
        producer_thread.start()

class KafkaStatsConsumer:
    def __init__(self, bootstrap_servers='michelangelo.cse.chalmers.se:9092', stats_topic='stats', group_id='0'):
        self.bootstrap_servers = bootstrap_servers
        self.stats_topic = stats_topic
        self.group_id = group_id
        self.consumer = Consumer({
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest',  # Start from the beginning when no offset is stored
            'enable.auto.commit': False  # Disable automatic offset commit
        })

    def consume_stats(self):
        self.consumer.subscribe([self.stats_topic])

        while True:
            msg = self.consumer.poll(timeout=1000)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            # Process the received message
            print(f"Received message from 'stats' topic: {msg.value().decode('utf-8')}")

    def start_consumer(self):
        consumer_thread = threading.Thread(target=self.consume_stats)
        consumer_thread.daemon = True
        consumer_thread.start()


if __name__ == "__main__":
    kafka_actions_producer = KafkaActionsProducer()
    kafka_stats_consumer = KafkaStatsConsumer()

    # Start the producer thread
    kafka_actions_producer.start_producer_thread()

    # Start the consumer thread
    kafka_stats_consumer.start_consumer()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
