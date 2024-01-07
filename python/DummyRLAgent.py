import threading
import time
import random
from confluent_kafka import Producer, Consumer, KafkaError
import sys
from collections import defaultdict
from datetime import datetime, timedelta

class MeasurementTracker:
    def __init__(self):
        self.last_time = None
        self.previous_values = {}   
        self.data_lock = threading.Lock()

        # self.reset()
        # self.period = 20
        # self.nanvalue = -1

    # def reset(self):
    #     # self.measurements = defaultdict(list)
    #     # self.last_time = None
    #     self.previous_values = {}

    # def should_value_be_registered(self,timestamp,id,value):
    #     if id=='outrate' and value==0:
    #         return False
    #     if id=='latency' and value==-1:
    #         return False
    #     return True

    def process_input(self, input_str):

        print('Received:',input_str)

        # Split the string into parts using ","
        parts = input_str.split(",")

        # Extract timestamp as an integer
        timestamp = int(parts[0])

        with self.data_lock:

            # Iterate over id, value pairs
            for i in range(1, len(parts), 2):
                # Assuming id and value are strings
                id = parts[i]
                value = float(parts[i + 1])

                self.previous_values[id] = {
                            'previous_value': value,
                            'timestamp': timestamp
                        }
                
                print('registered',timestamp,id,value)
                
            self.last_time = timestamp


        print('previous_values',self.previous_values)
                
        # # current_time = datetime.utcfromtimestamp(timestamp)
        # # print('current_time:',timestamp)

        # # Check if it's time to empty and calculate averages
        # if self.last_time is None or timestamp - self.last_time > self.period:
        #     self.aggregate_and_clean(timestamp)

        # if self.should_value_be_registered(timestamp,id,float(value)):
        #     # print('storing in measurements')
        #     self.measurements[id].append((timestamp, float(value)))

    # def aggregate_and_clean(self, current_time):

    #     # print('aggregate_and_clean!')
    #     for id, values in self.measurements.items():
    #         # print(id,values)
    #         if values:
    #             average_value = sum([v[1] for v in values]) / len(values)
    #             self.previous_values[id] = {
    #                 'previous_value': average_value,
    #                 'timestamp': values[-1][0],
    #                 'current_timestamp': current_time
    #             }
    #             print(current_time,id,average_value,[round(v[1], 2) for v in values])
    #         else:
    #             self.previous_values[id] = {
    #                 'previous_value': None,
    #                 'timestamp': None,
    #                 'current_timestamp': current_time
    #             }
    #             print(current_time,id,'-',[round(v[1], 2) for v in values])

    #     for id, values in list(self.measurements.items()):
    #         self.measurements[id] = [(t, v) for t, v in values if current_time - t <= self.period]
    #     self.last_time = current_time

class KafkaActionsProducer:
    def __init__(self, statsConsumer, bootstrap_servers='michelangelo.cse.chalmers.se:9092', actions_topic='dchanges'):
        self.bootstrap_servers = bootstrap_servers
        self.actions_topic = actions_topic
        self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})
        self.statsConsumer = statsConsumer
        self.prev_stat_time = None
        self.max_D = 600
        self.action_D = 600
        self.measurements = []
        self.actionsPerEpisode = 15;

    def compute_reward(self):
        print('self.measurements[0][latency][previous_value]',self.measurements[0]['latency']['previous_value'], flush=True)
        print('self.measurements[1][latency][previous_value]',self.measurements[1]['latency']['previous_value'], flush=True)
        print('self.measurements[0][ratio][previous_value]',self.measurements[0]['ratio']['previous_value'], flush=True)
        print('self.measurements[1][ratio][previous_value]',self.measurements[1]['ratio']['previous_value'], flush=True)
        print('Latency',self.measurements[1]['latency']['previous_value'],'delta comp:',(self.measurements[1]['ratio']['previous_value']-self.measurements[0]['ratio']['previous_value']), flush=True)
        if (self.measurements[1]['latency']['previous_value']>1000):
            return -100
        if (self.measurements[1]['ratio']['previous_value']<self.measurements[0]['ratio']['previous_value']):
            return 10
        return 1

    def produce_action(self):
        actionsBeforeReset=self.actionsPerEpisode
        while True:
            # Produce a random action to the 'actions' topic
            time.sleep(1)
            with self.statsConsumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by the other thread
                if actionsBeforeReset==0:
                    actionsBeforeReset=self.actionsPerEpisode
                    print('Sending reset command')
                    self.action_D = self.max_D
                    self.prev_stat_time = None
                    self.measurements = []
                    self.producer.produce(self.actions_topic, key=str(time.time()), value="reset")
                    self.producer.flush()
                    # self.statsConsumer.tracker.reset()
                elif len(self.statsConsumer.tracker.previous_values)>0 and (self.prev_stat_time is None or self.statsConsumer.tracker.last_time > self.prev_stat_time):
                    print('Got a new measurement from the environment for time',self.statsConsumer.tracker.last_time)
                    self.measurements.append(self.statsConsumer.tracker.previous_values.copy())
                    # print(self.measurements)
                    if len(self.measurements) == 2:
                        reward = self.compute_reward()
                        print('computed reward:',reward)
                        if reward < 0 and self.action_D < self.max_D:
                            self.action_D = min (self.action_D+50,self.max_D)
                            self.producer.produce(self.actions_topic, key=str(time.time()), value="changeD,"+str(self.action_D))
                            self.producer.flush()
                            print('D updated to ',self.action_D)
                            actionsBeforeReset-=1
                        if reward == 10 and self.action_D > 0:
                            self.action_D = max (self.action_D-40,0)
                            self.producer.produce(self.actions_topic, key=str(time.time()), value="changeD,"+str(self.action_D))
                            self.producer.flush()
                            print('D updated to ',self.action_D)
                            actionsBeforeReset-=1
                        if reward == 1 and self.action_D > 0:
                            self.action_D = max (self.action_D-20,0)
                            self.producer.produce(self.actions_topic, key=str(time.time()), value="changeD,"+str(self.action_D))
                            self.producer.flush()
                            print('D updated to ',self.action_D)
                            actionsBeforeReset-=1
                        self.measurements.pop(0)
                    self.prev_stat_time = self.statsConsumer.tracker.last_time

    def start_producer_thread(self):
        producer_thread = threading.Thread(target=self.produce_action)
        producer_thread.daemon = True
        producer_thread.start()

class KafkaStatsConsumer:
    def __init__(self, bootstrap_servers='michelangelo.cse.chalmers.se:9092', stats_topic='stats', group_id='0'):
        self.tracker = MeasurementTracker()
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
            stat = msg.value().decode('utf-8')
            # print(f"Received message from 'stats' topic: {stat}")
            self.tracker.process_input(stat)

    def start_consumer(self):
        consumer_thread = threading.Thread(target=self.consume_stats)
        consumer_thread.daemon = True
        consumer_thread.start()


if __name__ == "__main__":
    kafka_stats_consumer = KafkaStatsConsumer()
    kafka_actions_producer = KafkaActionsProducer(kafka_stats_consumer)

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
