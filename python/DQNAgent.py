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

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from collections import namedtuple
import math


GAMMA = 0.99
lr = 0.1
EPSION = 0.1
buffer_size = 10000  # replay buffer size
batch_size = 128
num_episode = 50
target_update = 1  # copy frequency from net to target_net
steps_per_episode = 100


# Define neural network
class Net(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(Net, self).__init__()
        self.Linear1 = nn.Linear(input_size, hidden_size)
        self.Linear2 = nn.Linear(hidden_size, hidden_size)
        self.Linear3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # print('x: ', x)
        x = F.relu(self.Linear1(x))
        x = F.relu(self.Linear2(x))
        x = self.Linear3(x)
        return x


# nametuple container
Transition = namedtuple('Transition',
                        ('state', 'action', 'reward', 'done', 'next_state'))


class ReplayMemory(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):  # sampling
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


class DQN(object):
    def __init__(self, input_size, hidden_size, output_size):
        self.net = Net(input_size, hidden_size, output_size)
        self.target_net = Net(input_size, hidden_size, output_size)
        self.optim = optim.Adam(self.net.parameters(), lr=lr)

        self.target_net.load_state_dict(self.net.state_dict())
        self.buffer = ReplayMemory(buffer_size)
        self.loss_func = nn.MSELoss()
        self.steps_done = 0

    def put(self, s0, a0, r, t, s1):
        self.buffer.push(s0, a0, r, t, s1)

    def select_action(self, state):
        eps_threshold = random.random()
        action = self.net(torch.Tensor(state))
        if eps_threshold > EPSION:
            choice = torch.argmax(action).numpy()
        else:
            choice = np.random.randint(0, action.shape[0])  # random sampling
        return choice

    def update_parameters(self):
        if self.buffer.__len__() < batch_size:
            return
        samples = self.buffer.sample(batch_size)
        batch = Transition(*zip(*samples))
        # convert tuple to numpy
        tmp = np.vstack(batch.action)
        # convert to Tensor
        state_batch = torch.tensor(np.array(batch.state), dtype = torch.float32)
        action_batch = torch.tensor(tmp.astype(int), dtype = torch.long)
        reward_batch = torch.tensor(np.array(batch.reward), dtype = torch.float32)
        done_batch = torch.tensor(np.array(batch.done), dtype = torch.float32)
        next_state_batch = torch.tensor(np.array(batch.next_state), dtype = torch.float32)

        q_next = torch.max(self.target_net(next_state_batch).detach(), dim=1)[0]
        q_eval = self.net(state_batch).gather(1, action_batch)

        # Ensure shapes of reward_batch and q_next match
        reward_batch = reward_batch.unsqueeze(1)
        q_next = q_next.unsqueeze(1)

        # Compute target Q values
        q_tar = reward_batch + (1 - done_batch.unsqueeze(1)) * GAMMA * q_next

        # unsqueeze(1): ensure that the shapes of (1-done_batch) and q_next match reward_batch
        # q_tar = reward_batch.unsqueeze(1) + (1-done_batch) * GAMMA * q_next
        loss = self.loss_func(q_eval, q_tar)
        # print(loss)
        self.optim.zero_grad()
        loss.backward()
        self.optim.step()


font = cv2.FONT_HERSHEY_COMPLEX_SMALL 

class SPEEnvironment(Env):
    def __init__(self, stepsPerEpisode):
        super(SPEEnvironment, self).__init__()

        # Define a 2-D observation space
        # states: injection rate, latency, compression, CPU consumption
        self.observation_space = spaces.Box(low = np.array([0,0,0,0]), 
                                            high = np.array([np.inf, np.inf, 100, 100]),
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

        # Start the producer thread - NOT NEEDED IN PRINCIPLE
        # kafka_actions_producer.start_producer()

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
                # print('self.consumer.tracker.state is not None',(self.consumer.tracker.state is not None),'self.consumer.tracker.last_time',self.consumer.tracker.last_time,'self.prev_stat_time',self.prev_stat_time)
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
        # self.prev_stat_time = None
        # self.max_D = 600
        # self.action_D = 600
        # self.actionsPerEpisode = 15;

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
    #episodes = 20
    #steps_per_episode = 20
    env = SPEEnvironment(steps_per_episode)
    Agent = DQN(env.observation_space.shape[0], 256, env.action_space.n)
    average_reward = 0  # average reward of all episodes

    for i_episode in range(num_episode):
        print('starting episode',i_episode + 1)
        s0 = env.reset()
        tot_reward = 0  # total reward per episode
        tot_time = 0  # actual processing time per episode

        while True:
            # Take a random action
            # action = env.action_space.sample()
            # obs, reward, done, info = env.step(action)
            a0 = Agent.select_action(s0)
            #s1, r, done, _ = env.step(a0)

            # only keep the return value of s1, r, done, ignore the fourth return value
            step_result = env.step(a0)
            s1, r, done = step_result[:3]

            tot_time += r  # cal. total time of current episode
            # reward cal. method
            # x, x_dot, theta, theta_dot = s1
            # r1 = (env.x_threshold - abs(x)) / env.x_threshold - 0.8
            # r2 = (env.theta_threshold_radians - abs(theta)) / env.theta_threshold_radians - 0.5
            # r = r1 + r2
            tot_reward += r  # cal total reward of current episode
            if done:
                t = 1
            else:
                t = 0
            Agent.put(s0, a0, r, t, s1)  # put into replay buffer
            s0 = s1
            Agent.update_parameters()
            
            # Render the game
            # env.render()
            
            if done == True:
                average_reward = average_reward + 1 / (i_episode + 1) * (
                        tot_reward - average_reward)
                if ((i_episode + 1) % 2 == 0):
                    print('Episode ', i_episode + 1, 'tot_time: ', tot_time,
                      ' tot_reward: ', tot_reward, ' average_reward: ',
                      average_reward)
                break

    if i_episode % target_update == 0:
            Agent.target_net.load_state_dict(Agent.net.state_dict())
            

    if (i_episode + 1) % 10 == 0:  # saving paras per 10 episodes
        torch.save(Agent.net.state_dict(), 'data/output/5/600/110000000/0/25000/601/dqn_model.pth')
        # this might the correct one to save model paras every 10 episodes
        # filename = 'data/output/5/600/110000000/0/25000/601/dqn_model_episode_{}.pth'.format(i_episode + 1)
        # torch.save(Agent.net.state_dict(), filename)


    print('closing')
    env.close()