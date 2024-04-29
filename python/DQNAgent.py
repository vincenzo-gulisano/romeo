import threading
import time
import argparse
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
import torch.nn.init as init
import torch.optim as optim
from collections import namedtuple
import math
import os
import pickle


GAMMA = 0.9
lr = 0.01
# EPSILON = 0.1
buffer_size = 10000  # replay buffer size
batch_size = 128
#episodes = 50
target_update = 4  # the frequency for copying parameters from net to target_net
#steps = 100
# EPSILON_START = 0.01
# EPSILON_END = 0.01
# EPSILON_DECAY = 500 # the higher value, the slower decay
TAU_START = 10
TAU_END = 3
TAU_DECAY = 500


# define neural network
class Net(nn.Module):
    def __init__(self, input_shape, hidden_size, output_size):
        super(Net, self).__init__()
        # flatten the input
        self.flatten = nn.Flatten()
        self.input_size = input_shape[0] * input_shape[1] # calculate input size after flattening
        self.Linear1 = nn.Linear(self.input_size, hidden_size)
        self.Linear2 = nn.Linear(hidden_size, hidden_size)
        self.Linear3 = nn.Linear(hidden_size, output_size)

        # initialize weights using Xavier uniform distribution
        # init.xavier_uniform_(self.Linear1.weight)#, gain = nn.init.calculate_gain('relu'))
        # init.xavier_uniform_(self.Linear2.weight)#, gain = nn.init.calculate_gain('relu'))
        # init.xavier_uniform_(self.Linear3.weight)#, gain = nn.init.calculate_gain('relu'))

        # iniitialize weights using He initialization
        # init.kaiming_normal_(self.Linear1.weight, mode='fan_in', nonlinearity='relu')
        # init.kaiming_normal_(self.Linear2.weight, mode='fan_in', nonlinearity='relu')
        # init.kaiming_normal_(self.Linear3.weight, mode='fan_in', nonlinearity='relu')

        # # initialize biases within range [-0.1, 0.1]
        # init.uniform_(self.Linear1.bias, -0.1, 0.1)
        # init.uniform_(self.Linear2.bias, -0.1, 0.1)
        # init.uniform_(self.Linear3.bias, -0.1, 0.1)

        # self.Linear1.bias.data.fill_(0)
        # self.Linear2.bias.data.fill_(0)
        # self.Linear3.bias.data.fill_(0)

        # Initialize weights 
        self.init_weights() 

    def forward(self, x):
        # print('x: ', x)
        # flatten the input
        if x.dim() > 1:
            x = x.view(-1, self.input_size)
        x = F.relu(self.Linear1(x))
        x = F.relu(self.Linear2(x))
        x = self.Linear3(x)
        return x
    
    def init_weights(self): 
        # Define the lower and upper bounds of the uniform distribution 
        # lower_bound, upper_bound = -0.1, 0.1 

        # Initialize weights and biases for each layer 
        for m in self.modules(): 
            if isinstance(m, nn.Linear): 
                init.uniform_(m.weight, -0.03, 0.03) 
                m.bias.data.fill_(0.05)


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
    def __init__(self, input_shape, hidden_size, output_size):
        self.net = Net(input_shape, hidden_size, output_size)
        self.target_net = Net(input_shape, hidden_size, output_size)
        self.optim = optim.Adam(self.net.parameters(), lr=lr)

        self.target_net.load_state_dict(self.net.state_dict())
        self.buffer = ReplayMemory(buffer_size)
        self.loss_func = nn.MSELoss()
        self.steps_done = 0
        self.sample_count = 0
        self.reset_compression()

    def reset_compression(self):
        self.current_compression = 100

    def put(self, s0, a0, r, t, s1):
        self.buffer.push(s0, a0, r, t, s1)

    def select_action(self, state):
        # eps_threshold = random.random()
        #action = self.net(torch.Tensor(state))
        self.sample_count += 1

        # Boltzmann(softmax) exploration strategy
        self.tau = TAU_END + (TAU_START - TAU_END) * math.exp(-1 * self.sample_count / TAU_DECAY)
        # reshape state to 1D vector
        state = torch.Tensor(state).view(-1)
        q_values = self.net(state)
        # softmax function to convert q values into probablities that sum to one
        action_probabilities = F.softmax(q_values / self.tau, dim=-1)
        # sample from the 'action_probablities' distribution
        action = torch.multinomial(action_probabilities, 1).item()
        action_time = time.time()
        action_type = "softmax selection"

        # epsilon greedy decay
        # self.epsilon = EPSILON_END + (EPSILON_START - EPSILON_END) * math.exp(-1 * self.sample_count / EPSILON_DECAY)
        # # reshape state to 1D vector
        # state = torch.Tensor(state).view(-1)
        # action = self.net(state)
        # action_time = time.time()

        # if eps_threshold > self.epsilon:
        #     action = torch.argmax(action).numpy()
        #     action_type = "exploitation"
        # else:
        #     action = np.random.randint(0, action.shape[0])  # random sampling
        #     action_type = "exploration"
        
        # uodate compression ratio based on the action
        if action == 0:
            self.current_compression = max(0, self.current_compression - 10)
        elif action == 2:
            self.current_compression = min(100, self.current_compression + 10)
        
        return action, action_type, action_time, self.tau, action_probabilities.detach().numpy(), self.current_compression

    def update_parameters(self):
        if self.buffer.__len__() < batch_size:
            return
        samples = self.buffer.sample(batch_size)
        batch = Transition(*zip(*samples))
        # # convert tuple to numpy (column vector)
        # tmp = np.vstack(batch.action)
        # # convert to Tensor
        # # state_batch = torch.tensor(np.array(batch.state), dtype = torch.float32)
        # state_batch = torch.tensor(np.array(batch.state), dtype = torch.float32).view(batch_size, -1)

        # action_batch = torch.tensor(tmp.astype(int), dtype = torch.long)
        # reward_batch = torch.tensor(np.array(batch.reward), dtype = torch.float32)
        # done_batch = torch.tensor(np.array(batch.done), dtype = torch.float32)
        # # next_state_batch = torch.tensor(np.array(batch.next_state), dtype = torch.float32)
        # next_state_batch = torch.tensor(np.array(batch.next_state), dtype = torch.float32).view(batch.size, -1)

        # Ensure all elements in batch.state have the same shape and type
        state_list = [np.array(state).reshape(-1) for state in batch.state]
        next_state_list = [np.array(state).reshape(-1) for state in batch.next_state]

        # Convert lists to NumPy arrays
        state_array = np.vstack(state_list)
        next_state_array = np.vstack(next_state_list)
        action_array = np.vstack(batch.action)
        reward_array = np.array(batch.reward)
        done_array = np.array(batch.done)

        # Convert to PyTorch tensors
        state_batch = torch.tensor(state_array, dtype=torch.float32)
        next_state_batch = torch.tensor(next_state_array, dtype=torch.float32)
        action_batch = torch.tensor(action_array, dtype=torch.long)
        reward_batch = torch.tensor(reward_array, dtype=torch.float32)
        done_batch = torch.tensor(done_array, dtype=torch.float32)

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

    def get_q_values(self, state):
        with torch.no_grad():  # no gradient cal when evaluating
            state_tensor = torch.Tensor(state).view(-1)
            return self.net(state_tensor).numpy()


font = cv2.FONT_HERSHEY_COMPLEX_SMALL 

class SPEEnvironment(Env):
    def __init__(self, stepsPerEpisode):
        super(SPEEnvironment, self).__init__()

        self.valuesPerObservation = 7
        # metrics = 11
        # Define a 2-D observation space
        # states: injectionrate, throughput, outrate, latency, compression ratio, comp, dec, CPU-in, CPU-agg, CPU-out, event time
        # metrics = 7
        # states: injectionrate, throughput, outrate, latency, compression ratio, CPU-agg, event time
        # metrics = 6
        # states: injectionrate, throughput, outrate, latency, compression ratio, CPU-agg
        self.observation_space = spaces.Box(low = np.array(
                                                [np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                # np.full(self.valuesPerObservation, -1),
                                                # np.full(self.valuesPerObservation, -1),
                                                # np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                # np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1)
                                                ]), 
                                            high = np.array(
                                                [np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, 100),
                                                 # np.full(self.valuesPerObservation, np.inf),
                                                 # np.full(self.valuesPerObservation, np.inf),
                                                 # np.full(self.valuesPerObservation, 100),
                                                 np.full(self.valuesPerObservation, 100),
                                                 # np.full(self.valuesPerObservation, 100),
                                                 np.full(self.valuesPerObservation, np.inf)
                                                 ]),
                                            dtype = np.float32)
        # self.observation_space = spaces.Box(low = np.array([0,0,0,0]), 
        #                                     high = np.array([np.inf, np.inf, 100, 100]),
        #                                     dtype = np.float32)
        
        # Define an action space ranging from 0 to 11
        # 0 means set compression to 0%
        # 1 means set compression to 10%
        # ...
        # 10 means set compression to 100%
        # self.action_space = spaces.Discrete(11,)

        # 3 actions: reduce compression by 10, no change, increase compression by 10
        self.action_space = spaces.Discrete(3,)

        self.consumer = KafkaStatsConsumer(self.valuesPerObservation)
        self.producer = KafkaActionsProducer(self.consumer)

        self.stepsPerEpisode = stepsPerEpisode
        self.remaingSteps = self.stepsPerEpisode

        self.prev_stat_time = time.time()

        # Start the producer thread - NOT NEEDED IN PRINCIPLE
        # kafka_actions_producer.start_producer()

        # Start the consumer thread
        self.consumer.start_consumer()

        # track negative reward
        # self.negative_reward_counter = 0

        # track latency
        self.latency_threshold = 2500
        self.latency_counter = 0
        self.latency_last_events = -1
        # define thresholds for negative reward and latency violtions
        self.negative_reward_threshold = -150
        self.latency_violations_per_episode = 3
        # define initial compression ratio
        self.current_compression = 100

        # self.state_labels = ["injectionrate", "throughput", "outrate", "latency", "compressionratio", "CPU-agg", "eventtime"]
        self.state_labels = ["injectionrate", "throughput", "outrate", "latency", "compressionratio", "CPU-agg"]

    def print_state(self, state):
        # get the maxmimum length of state labels for alignment
        max_label_length = max(len(label) for label in self.state_labels)
        max_value_length = max(max(len(f"{value:.2f}") for value in values) for values in state)
        column_width = max(max_label_length, max_value_length)
        for label, values in zip(self.state_labels, state):
            formatted_label = label.ljust(column_width)
            formatted_values = ' '.join(f'{value:{column_width}.2f}' for value in values)
            print(f"{formatted_label} {formatted_values}")

    def reset(self):

        #reset negative reward counter
        #self.negative_reward_counter = 0

        # reset latency counter
        self.latency_counter = 0
        # reset the time tracker for latency events
        self.latency_last_events = -1  
        # reset initial compressionn ratio
        self.current_compression = 100

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
                    print('Got a new state/reward pair:',self.consumer.tracker.last_time)
                    self.print_state(self.consumer.tracker.state)
                    # for row in self.consumer.tracker.state:
                    #     print ([f'{num:.2f}' for num in row])
                    print('reward',self.consumer.tracker.reward,flush=True)
                    # print('Got a new state/reward pair:',self.consumer.tracker.last_time,self.consumer.tracker.state,self.consumer.tracker.reward,flush=True)
                    state_measurement_available = True

        # Reset the reward
        self.ep_return  = self.consumer.tracker.reward

        state = self.consumer.tracker.state.copy()
        # get the current event time
        self.current_event_time = state[6, :]
        # return states except eventtime
        return state[:-1]
        # # Return the observation
        # return self.consumer.tracker.state.copy()
    
    def step(self, action, current_compression):
    
        self.remaingSteps -= 1

        # Assert that it is a valid action 
        assert self.action_space.contains(action), "Invalid action"

        # select ccompression ratio based on the action
        # if action == 0:
        #     self.current_compression = max(0, self.current_compression - 10)
        # elif action == 2:
        #     self.current_compression = min(100, self.current_compression + 10)

        # print('Transmitting action',action)
        # self.producer.produce("changeD,"+str(action))
        self.producer.produce("changeD," + str(int(current_compression/10)))

        # Wait for the state and reward measurement
        self.prev_stat_time = time.time()
        state_measurement_available = False
        # print('Waiting for new observation')
        while not state_measurement_available:
            time.sleep(1)
            with self.consumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by other threads
                # print('self.consumer.tracker.state is not None',(self.consumer.tracker.state is not None),'self.consumer.tracker.last_time',self.consumer.tracker.last_time,'self.prev_stat_time',self.prev_stat_time)
                if self.consumer.tracker.state is not None and self.consumer.tracker.last_time > self.prev_stat_time:
                    # print('Got a new state/reward pair:',self.consumer.tracker.last_time,self.consumer.tracker.state,self.consumer.tracker.reward,flush=True)
                    print('Got a new state/reward pair:',self.consumer.tracker.last_time)
                    self.print_state(self.consumer.tracker.state)
                    # for row in self.consumer.tracker.state:
                    #     print ([f'{num:.2f}' for num in row])
                    print('reward',self.consumer.tracker.reward,flush=True)
                    state_measurement_available = True
        
        # # update negative reward counter
        # if self.consumer.tracker.reward < 0:
        #     self.negative_reward_counter += 1
        
        # # check if need to end this episode
        # if self.negative_reward_counter >= 3:
        #     done = True
        # else:
        #     done = False
        
        # update latency counter
        print(f"Checking high latency based on latency values")
        checkAlsoBasedReward = True
        state = self.consumer.tracker.state.copy()
        self.current_event_time = state[6, :]  # update eventtime
        # for event_time, latency in zip(self.consumer.tracker.state[10], self.consumer.tracker.state[3]):
        for event_time, latency in zip(self.current_event_time, self.consumer.tracker.state[3]):
            if event_time > self.latency_last_events:
                self.latency_last_events = event_time
                if latency > self.latency_threshold:
                    checkAlsoBasedReward = False
                    self.latency_counter += 1
                    print(f"High latency observed: {event_time, latency} ms at step {(self.stepsPerEpisode - self.remaingSteps) + 1}")
                    # print(f"High latency observed: {event_time, latency} ms at step {(self.stepsPerEpisode - self.remaingSteps)}")
            
        if checkAlsoBasedReward:
            print(f"Checking high latency based on actual reward")
            if self.consumer.tracker.reward < self.negative_reward_threshold:
                self.latency_counter += 1
                print(f"High latency observed because of reward at step {(self.stepsPerEpisode - self.remaingSteps) + 1}")
                # print(f"High latency observed because of reward at step {(self.stepsPerEpisode - self.remaingSteps)}")
        
        # check if latency is greater than 2.5s in three steps for every episode
        if self.latency_counter >= self.latency_violations_per_episode:
            done = True
        else:
            done = False
        
        # check if there has remaining steps
        if self.remaingSteps <= 0:
            done = True
        
        # Increment the episodic return
        self.ep_return += 1

        # TODO There's something missing, the SPE itself could be done if it runs out of data. This is not being checked as of now...
        # return self.consumer.tracker.state.copy(), self.consumer.tracker.reward, done, []
        return state[:-1], self.consumer.tracker.reward, done, []
    
    def close(self):
        super(SPEEnvironment, self).close()
        self.producer.produce("close")


class MeasurementTracker:
    def __init__(self, valuesPerObservation):
        self.last_time = None
        self.state = None
        self.reward = None
        self.data_lock = threading.Lock()
        self.valuesPerObservation = valuesPerObservation


    def process_input(self, input_str):

        # print('Received:',input_str,'at time',time.time(),flush=True)

        # Split the string into parts using ","
        parts = input_str.split("/")

        with self.data_lock:

            # Extract timestamp as an integer
            self.last_time = time.time()
            # Split the string and create a list of floats, replacing -1 with np.nan
            # doubles_list = [np.nan if float(x) == -1.0 else float(x) for x in parts[0].split(',')]
            # Convert the string to a list of floats without replacing -1.0 with np.nan
            doubles_list = [float(x) for x in parts[0].split(',')]
            # Convert the list to a NumPy array of float32 and reshape it to 11x7
            # self.state = np.array(doubles_list, dtype=np.float32).reshape(11, self.valuesPerObservation)
            try:
                # select indices for specific 7 states
                indices = [
                    i for j in [
                        range(0 * self.valuesPerObservation, 5 * self.valuesPerObservation), # select indices for 'injectionrate, throughput, outrate, latency, compression ratio'
                        range(8 * self.valuesPerObservation, 9 * self.valuesPerObservation), # select indices for 'CPU-agg'
                        range(10 * self.valuesPerObservation, 11 * self.valuesPerObservation) # select indices for 'event time'
                    ] for i in j
                ]
                # select state_data corresponding to specific 7 states
                selected_state = [doubles_list[i] for i in indices]
                # self.state = np.array(doubles_list, dtype=np.float32).reshape(11, self.valuesPerObservation)
                # Convert the list to a NumPy array of float32 and reshape it to 7x7
                self.state = np.array(selected_state, dtype=np.float32).reshape(7, self.valuesPerObservation)
            except Exception as e:
                raise RuntimeError("An error occured parsing " + input_str) from e
            # state_matrix = np.array(doubles_list, dtype=np.float32).reshape(-1, self.valuesPerObservation)
            # self.state = state_matrix.T
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
    def __init__(self, valuesPerObservation, bootstrap_servers='michelangelo.cse.chalmers.se:9092', stats_topic='stats', group_id='0'):
        self.valuesPerObservation = valuesPerObservation
        self.tracker = MeasurementTracker(self.valuesPerObservation)
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
    parser.add_argument('-agentstate', help='State of the pre-trained agent', default=None)
    parser.add_argument('-learningactive', help='Wheter the agent should learn', default=True)
    args = parser.parse_args()
    
    print('Creating agent')
    print('episodes:',args.episodes)
    print('steps:',args.steps)
    print('agentstate:',args.agentstate)
    print('learningactive:',args.learningactive)
    

    env = SPEEnvironment(int(args.steps))
    # input_shape = (11, 7)
    input_shape = (6, 7)
    hidden_size = 128
    output_sie = env.action_space.n
    Agent = DQN(input_shape, hidden_size, output_sie)

    # load saved net's paras
    # model_file = 'image/Exp10.2/synthetic/1-200/Exp10-2_paras-1-200/exp10-2_dqn_model_episode_200.pth'
    # if os.path.exists(model_file):
    #     Agent.net.load_state_dict(torch.load(model_file))
    #     print("loaded net's paras...")

    # load replay buffer
    # replay_buffer = f'image/Exp10.2/synthetic/1-200/Exp10-2_replay_buffer-1-200/exp10-2_buffer_after_200_episodes.pkl'
    # with open (replay_buffer, 'rb') as f:
    #     Agent.buffer = pickle.load(f)
    # print('loaded replay buffer from last round...')
   
    if args.agentstate is not None:
        Agent.net.load_state_dict(torch.load(args.agentstate))
   
    incremental_average_reward = 0  # average reward of all episodes for incermental averaging

    # create folder to store paras (linear)
    # paras_folder_name = 'data/output/linear/5/600/5000000000/0/25000/601/Exp11-1_paras-1-100'
    # if not os.path.exists(paras_folder_name):
    #     os.makedirs(paras_folder_name)

    # create folder to store paras (synthetic)
    paras_folder_name = 'data/output/synthetic/1/900/5000000000/10/Exp13_paras-1-100'
    if not os.path.exists(paras_folder_name):
        os.makedirs(paras_folder_name)

    # create folder to store q value plots (linear)
    # q_value_folder_name = 'data/output/linear/5/600/5000000000/0/25000/601/Exp11-1_q_value_plot-1-100'
    # if not os.path.exists(q_value_folder_name):
    #     os.makedirs(q_value_folder_name)

    # create folder to store q value plots (synthetic)
    q_value_folder_name = 'data/output/synthetic/1/900/5000000000/10/Exp13_q_values_plot-1-100'
    if not os.path.exists(q_value_folder_name):
        os.makedirs(q_value_folder_name)
    
    # create folder to store replay buffer (linear)
    # replay_buffer_folder_name = 'data/output/linear/5/600/5000000000/0/25000/601/Exp11-1_replay_buffer-1-100'
    # if not os.path.exists(replay_buffer_folder_name):
    #     os.makedirs(replay_buffer_folder_name)
    
    # create folder to store replay buffer (synthetic)
    replay_buffer_folder_name = 'data/output/synthetic/1/900/5000000000/10/Exp13_replay_buffer-1-100'
    if not os.path.exists(replay_buffer_folder_name):
        os.makedirs(replay_buffer_folder_name)
    

    for i_episode in range(0, int(args.episodes)):
        print('starting episode',i_episode + 1)
        start_time = time.time() # start time of per episode
        s0 = env.reset()
        s0 = s0.reshape(-1)
        Agent.reset_compression()

        total_reward = 0  # total reward per episode
        # total_time = 0  # actual processing time per episode
        step_count = 0 # count the number of steps in every episode

        # plt.figure()
        steps = [] # store the steps for plotting
       # steps = [int (step) for step in steps] # guarantee the step is integer
        q_values_history = [[] for _ in range(env.action_space.n)]

        while True:
            # for epsilon greedy strategy
            # a0, action_type, action_time, epsilon, current_compression = Agent.select_action(s0)
            # for Boltzmann(softmax) exploration strategy
            a0, action_type, action_time, tau, action_probablities, current_compression = Agent.select_action(s0)
            q_values = Agent.net(torch.Tensor(s0)).detach().numpy().squeeze()
            # for epsilon greedy strategy
            # print(f"Episode {i_episode + 1}, Step {step_count + 1}, Action {a0}, Current Compression: {current_compression}, Action type: {action_type}, Epsilon: {epsilon:.6f}, Q values: {q_values}, Action time: {action_time}") 
            # for Boltzmann(softmax) exploration strategy
            print(f"Episode {i_episode + 1}, Step {step_count + 1}, Tau: {tau:.6f}, Q values: {q_values}, Action Probablities: {action_probablities}, Action {a0}, Current Compression: {current_compression}, Action time: {action_time}, Action type: {action_type}") 

            steps.append(step_count)

            for i, q_value in enumerate(q_values):
                q_values_history[i].append(q_value)

            # only keep the return value of s1, r, done, ignore the fourth return value
            step_result = env.step(a0, current_compression)
            s1, r, done = step_result[:3]

            # total_time += r  # cal. total time of current episode
            total_reward += r # cal total reward of current episode
            step_count += 1 # increment the step 

            if done:
                t = 1
            else:
                t = 0

            Agent.put(s0, a0, r, t, s1)  # put into replay buffer
            s0 = s1

            if args.learningactive:
                Agent.update_parameters()
            
            if done == True:
                end_time = time.time() # end time of per episode
                total_time = end_time - start_time
                print(f"Episode {i_episode + 1}, Step {step_count + 1}, This episode has finished.")
                # incremental average for all past episodes
                incremental_average_reward = incremental_average_reward +  (total_reward - incremental_average_reward) / (i_episode + 1)
                # standard average for this current episode
                standard_average_reward = total_reward / step_count if step_count else 0
                print(f"Episode {i_episode + 1}, Total Time: {total_time: .2f}, Total Reward: {total_reward}, Incremental Average Reward: {incremental_average_reward}, Standard Average Reward: {standard_average_reward}")
                break

        if i_episode % target_update == 0:
            Agent.target_net.load_state_dict(Agent.net.state_dict())

        plt.figure()
        colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'black', 'orange', 'purple', 'brown', 'pink']
        # markers = ['o', 'v', '^', '<', '>', 's', 'p', '*', 'h', 'H', 'D']
        for i, action_q_values in enumerate(q_values_history):
                if len(steps) == len(action_q_values):
                    action_q_values = [val[0] if isinstance(val, np.ndarray) and len(val) == 1 else val for val in action_q_values]
                    # plt.plot(steps, action_q_values, label = f'Action {i}', color = colors[i % len(colors)], marker = markers[i % len(markers)])
                    plt.plot(steps, action_q_values, label = f'Action {i}', color = colors[i % len(colors)])
                else:
                    print(f"Error: Mismatch in lengths for Action {i}")


        # saving q value plots
        plt.xlabel('Stpes')
        plt.ylabel('Q Values')
        plt.title(f'Q Values Over Episodes (Episode {i_episode + 1})')
        plt.legend()
        q_value_file_path = os.path.join(q_value_folder_name, f'exp13_q_values_plot_{i_episode + 1}.png')
        plt.savefig(q_value_file_path)
        plt.close()
            
        # saving paras and replay buffer per 10 episodes
        if (i_episode + 1) % 10 == 0: 
            # save model paras every 10 episodes
            paras_file_path = os.path.join(paras_folder_name, f'exp13_dqn_model_episode_{i_episode + 1}.pth')
            torch.save(Agent.net.state_dict(), paras_file_path)
            replay_buffer_file_path = os.path.join(replay_buffer_folder_name, f'exp13_buffer_after_{i_episode + 1}_episodes.pkl')
            with open (replay_buffer_file_path, 'wb') as f:
                pickle.dump(Agent.buffer, f)
            # print(f'Saved replay buffer after {i_episode + 1} episodes ...')
                 

    print('closing')
    env.close()