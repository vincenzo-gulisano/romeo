import threading
import time
from confluent_kafka import Producer, Consumer, KafkaError
import numpy as np 
import cv2 
import matplotlib.pyplot as plt
import PIL.Image as Image
import gym
import random

from gym import Env, spaces
import time

font = cv2.FONT_HERSHEY_COMPLEX_SMALL 

class SPEEnvironment(Env):
    def __init__(self, stepsPerEpisode):
        super(SPEEnvironment, self).__init__()

        # Define a 2-D observation space
        self.observation_space = spaces.Box(low = [0,0,0], 
                                            high = [np.inf,1,1],
                                            dtype = np.float16)
        
        # Define an action space ranging from 0 to 11
        # 0 means set compression to 0%
        # 1 means set compression to 10%
        # ...
        # 10 means set compression to 100%
        self.action_space = spaces.Discrete(4,)

        self.kafka_stats_consumer = KafkaStatsConsumer()
        self.kafka_actions_producer = KafkaActionsProducer(kafka_stats_consumer)

        self.stepsPerEpisode = stepsPerEpisode
        self.remaingSteps = self.stepsPerEpisode

        self.prev_stat_time = time.time()

        # Start the producer thread - NOT NEEDED IN PRINCIPLE
        # kafka_actions_producer.start_producer()

        # Start the consumer thread
        kafka_stats_consumer.start_consumer()

    def reset(self):

        # Send the reset
        self.producer.produce(self.actions_topic, key=str(time.time()), value="reset")
        self.producer.flush()

        self.remaingSteps = self.stepsPerEpisode

        # Wait for the state and reward measurement
        self.prev_stat_time = time.time()
        state_measurement_available = False
        while not state_measurement_available:
            time.sleep(1)
            with self.kafka_stats_consumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by other threads
                if self.kafka_stats_consumer.tracker.state is not None and self.kafka_stats_consumer.tracker.last_time > self.prev_stat_time:
                    print('Got a new state/reward pair:',self.kafka_stats_consumer.tracker.last_time,self.kafka_stats_consumer.tracker.state,self.kafka_stats_consumer.tracker.reward,flush=True)
                    state_measurement_available = True

        # Reset the reward
        self.ep_return  = self.kafka_stats_consumer.tracker.reward

        # Return the observation
        return self.kafka_stats_consumer.tracker.state.copy()
    
    def step(self,action):
    
        self.remaingSteps -= 1

        # Assert that it is a valid action 
        assert self.action_space.contains(action), "Invalid action"

        self.producer.produce(self.actions_topic, key=str(time.time()), value="changeD,"+str(action))
        self.producer.flush()

        # Wait for the state and reward measurement
        self.prev_stat_time = time.time()
        state_measurement_available = False
        while not state_measurement_available:
            time.sleep(1)
            with self.kafka_stats_consumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by other threads
                if self.kafka_stats_consumer.tracker.state is not None and self.kafka_stats_consumer.tracker.last_time > self.prev_stat_time:
                    print('Got a new state/reward pair:',self.kafka_stats_consumer.tracker.last_time,self.kafka_stats_consumer.tracker.state,self.kafka_stats_consumer.tracker.reward,flush=True)
                    state_measurement_available = True
        
        # Increment the episodic return
        self.ep_return += 1

        # TODO There's something missing, the SPE itself could be done if it runs out of data. This is not being checked as of now...
        return self.kafka_stats_consumer.tracker.state.copy(), self.kafka_stats_consumer.tracker.reward, self.remaingSteps==0, []
    
class MeasurementTracker:
    def __init__(self):
        self.last_time = None
        self.state = None
        self.reward = None
        self.data_lock = threading.Lock()

    def process_input(self, input_str):

        print('Received:',input_str)

        # Split the string into parts using ","
        parts = input_str.split("/")

        with self.data_lock:

            # Extract timestamp as an integer
            self.last_time = time.time()
            self.state = parts[0]
            self.reward = int(parts[1])

class KafkaActionsProducer:
    def __init__(self, statsConsumer, bootstrap_servers='michelangelo.cse.chalmers.se:9092', actions_topic='dchanges'):
        self.bootstrap_servers = bootstrap_servers
        self.actions_topic = actions_topic
        self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})
        self.statsConsumer = statsConsumer
        # self.prev_stat_time = None
        # self.max_D = 600
        # self.action_D = 600
        # self.actionsPerEpisode = 15;

    # def produce_action(self):
    #     actionsBeforeReset=self.actionsPerEpisode
    #     while True:
    #         # Produce a random action to the 'actions' topic
    #         time.sleep(1)
    #         with self.statsConsumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by the other thread
    #             if actionsBeforeReset==0:
    #                 actionsBeforeReset=self.actionsPerEpisode
    #                 print('Sending reset command',flush=True)
    #                 self.action_D = self.max_D
    #                 self.prev_stat_time = time.time()
    #                 self.producer.produce(self.actions_topic, key=str(time.time()), value="reset")
    #                 self.producer.flush()
    #             elif self.statsConsumer.tracker.state is not None and (self.prev_stat_time is None or self.statsConsumer.tracker.last_time > self.prev_stat_time):
    #                 print('Got a new state/reward pair:',self.statsConsumer.tracker.last_time,self.statsConsumer.tracker.state,self.statsConsumer.tracker.reward,flush=True)
    #                 if self.statsConsumer.tracker.reward < 0 and self.action_D < self.max_D:
    #                     self.action_D = min (self.action_D+50,self.max_D)
    #                     self.producer.produce(self.actions_topic, key=str(time.time()), value="changeD,"+str(self.action_D))
    #                     self.producer.flush()
    #                     print('D updated to ',self.action_D)
    #                     actionsBeforeReset-=1
    #                 if self.statsConsumer.tracker.reward == 10 and self.action_D > 0:
    #                     self.action_D = max (self.action_D-40,0)
    #                     self.producer.produce(self.actions_topic, key=str(time.time()), value="changeD,"+str(self.action_D))
    #                     self.producer.flush()
    #                     print('D updated to ',self.action_D)
    #                     actionsBeforeReset-=1
    #                 if self.statsConsumer.tracker.reward == 0 and self.action_D > 0:
    #                     self.action_D = max (self.action_D-20,0)
    #                     self.producer.produce(self.actions_topic, key=str(time.time()), value="changeD,"+str(self.action_D))
    #                     self.producer.flush()
    #                     print('D updated to ',self.action_D)
    #                     actionsBeforeReset-=1
    #                     # self.measurements.pop(0)
    #                 self.prev_stat_time = self.statsConsumer.tracker.last_time

    # def start_producer(self):
    #     producer_thread = threading.Thread(target=self.produce_action)
    #     producer_thread.daemon = True
    #     producer_thread.start()

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
    # kafka_stats_consumer = KafkaStatsConsumer()
    # kafka_actions_producer = KafkaActionsProducer(kafka_stats_consumer)

    # # Start the producer thread
    # kafka_actions_producer.start_producer()

    # # Start the consumer thread
    # kafka_stats_consumer.start_consumer()

    # # Keep the main thread alive
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     pass
    steps_per_episode = 15
    env = SPEEnvironment(steps_per_episode)
    obs = env.reset()

    while True:
        # Take a random action
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        
        # Render the game
        # env.render()
        
        if done == True:
            break

    env.close()
