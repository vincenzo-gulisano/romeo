import threading
import argparse
import time
from confluent_kafka import Producer, Consumer, KafkaError
import numpy as np 
import cv2 
# import matplotlib.pyplot as plt
# import PIL.Image as Image
# import gym
# import random

from gym import Env, spaces
import time

font = cv2.FONT_HERSHEY_COMPLEX_SMALL 

class SPEEnvironment(Env):
    def __init__(self, stepsPerEpisode):
        super(SPEEnvironment, self).__init__()

        # Define a 2-D observation space
        self.observation_space = spaces.Box(low = np.array([0,0,0]), 
                                            high = np.array([np.inf,1,1]),
                                            dtype = np.float32)
        
        # Define an action space ranging from 0 to 11
        # 0 means set compression to 0%
        # 1 means set compression to 10%
        # ...
        # 10 means set compression to 100%
        self.action_space = spaces.Discrete(11,)

        self.consumer = KafkaStatsConsumer()
        self.producer = KafkaActionsProducer(self.consumer)

        self.stepsPerEpisode = stepsPerEpisode
        self.remaingSteps = self.stepsPerEpisode

        self.prev_stat_time = time.time()

        # Start the consumer thread
        self.consumer.start_consumer()

    def reset(self):

        # Send the reset
        self.producer.produce("reset")

        self.remaingSteps = self.stepsPerEpisode
        print('self.remaingSteps set to',self.remaingSteps,'in reset')

        # Wait for the state and reward measurement
        self.prev_stat_time = time.time()
        state_measurement_available = False
        print('Waiting for new observation')
        while not state_measurement_available:
            time.sleep(1)
            with self.consumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by other threads
                if self.consumer.tracker.state is not None and self.consumer.tracker.last_time > self.prev_stat_time:
                    print('Got a new state/reward pair:',self.consumer.tracker.last_time,self.consumer.tracker.state,self.consumer.tracker.reward,flush=True)
                    state_measurement_available = True

        # Reset the reward
        self.ep_return  = self.consumer.tracker.reward

        # Return the observation
        return self.consumer.tracker.state.copy()
    
    def step(self,action):
    
        self.remaingSteps -= 1

        # Assert that it is a valid action 
        assert self.action_space.contains(action), "Invalid action"

        print('Transmitting action',action)
        self.producer.produce("changeD,"+str(action))

        # Wait for the state and reward measurement
        self.prev_stat_time = time.time()
        state_measurement_available = False
        print('Waiting for new observation')
        while not state_measurement_available:
            time.sleep(1)
            with self.consumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by other threads
                # print('self.consumer.tracker.state is not None',(self.consumer.tracker.state is not None),'self.consumer.tracker.last_time',self.consumer.tracker.last_time,'self.prev_stat_time',self.prev_stat_time)
                if self.consumer.tracker.state is not None and self.consumer.tracker.last_time > self.prev_stat_time:
                    print('Got a new state/reward pair:',self.consumer.tracker.last_time,self.consumer.tracker.state,self.consumer.tracker.reward,flush=True)
                    state_measurement_available = True
        
        # Increment the episodic return
        self.ep_return += 1

        # TODO There's something missing, the SPE itself could be done if it runs out of data. This is not being checked as of now...
        return self.consumer.tracker.state.copy(), self.consumer.tracker.reward, self.remaingSteps==0, []
    
    def close(self):
        super(SPEEnvironment, self).close()
        self.producer.produce("close")


class MeasurementTracker:
    def __init__(self):
        self.last_time = None
        self.state = None
        self.reward = None
        self.data_lock = threading.Lock()

    def process_input(self, input_str):

        print('Received:',input_str,'at time',time.time(),flush=True)

        # Split the string into parts using ","
        parts = input_str.split("/")

        with self.data_lock:

            # Extract timestamp as an integer
            self.last_time = time.time()
            # Convert the string to a list of doubles
            doubles_list = [float(x) for x in parts[0].split(',')]
            # Convert the list to a NumPy array of float32
            self.state =  np.array(doubles_list, dtype=np.float32)
            self.reward = int(parts[1])

class KafkaActionsProducer:
    def __init__(self, statsConsumer, bootstrap_servers='michelangelo.cse.chalmers.se:9092', actions_topic='dchanges'):
        self.bootstrap_servers = bootstrap_servers
        self.actions_topic = actions_topic
        self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})
        self.statsConsumer = statsConsumer

    def produce(self, action):
        self.producer.produce(self.actions_topic, key=str(time.time()), value=action)
        self.producer.flush()

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
    
    parser = argparse.ArgumentParser(description='Start an Agent that always chooses the same compression level')
    parser.add_argument('episodes', help='Number of episodes')
    parser.add_argument('steps', help='Number of steps')
    parser.add_argument('compression', help='Compression level')
    args = parser.parse_args()
    
    
    env = SPEEnvironment(args.steps)

    for i in range(args.episodes):
        print('starting episode',i+1)
        obs = env.reset()

        while True:
            
            action = args.compression
            obs, reward, done, info = env.step(action)
            
            if done == True:
                break

    print('closing')
    env.close()
