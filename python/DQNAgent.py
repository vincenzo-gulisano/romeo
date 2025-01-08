import threading
import time
import argparse
from confluent_kafka import Producer, Consumer, KafkaError
import numpy as np 
import pandas as pd
import cv2 
import matplotlib.pyplot as plt
import PIL.Image as Image
import gym
from collections import deque
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
import csv

from scipy.stats import linregress


GAMMA = 0.99
lr = 0.01
# EPSILON = 0.1
buffer_size = 10000  # replay buffer size
batch_size = 128
#episodes = 50
target_update = 1000  # update target net every 1000 steps
#steps = 100
# EPSILON_START = 0.01
# EPSILON_END = 0.01
# EPSILON_DECAY = 500 # the higher value, the slower decay
TAU_START = 5
TAU_END = 1
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

        # Initialize weights 
        self.init_weights() 

    def forward(self, x):
        # flatten the input
        if x.dim() > 1:
            x = x.view(-1, self.input_size)
        x = F.relu(self.Linear1(x))
        x = F.relu(self.Linear2(x))
        x = self.Linear3(x)
        return x
    
    def init_weights(self): 
        # Initialize weights and biases for each layer 
        for m in self.modules(): 

            if isinstance(m, nn.Linear): 
                if m == self.Linear3:
                    init.constant_(m.weight, 0)
                    init.constant_(m.bias, 0)
                else:
                    init.uniform_(m.weight, -0.03, 0.03) 
                    m.bias.data.fill_(0.05)
    
    # def reinitialize_final_layer(self):
    #     init.uniform_(self.Linear3.weight, -0.03, 0.03)
    #     self.Linear3.bias.data.fill_(0.05)
    def reinitialized_weights(self):
        print("Reinitializing final layer weights...", flush=True)
        init.uniform_(self.Linear3.weight, -0.03, 0.03)
        self.Linear3.bias.data.fill_(0.03)


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

        # self.first_step = True # flag to track the first step
        self.reinitialized = False

        self.entropy_list = deque(maxlen=1000)  # To store last 1000 entropy values
        self.moving_average_entropy = None
        self.is_moving_average_ready = False  # Tracks if moving average is ready
        

    def reset_compression(self):
        self.current_compression = 100

    def put(self, s0, a0, r, t, s1):
        self.buffer.push(s0, a0, r, t, s1)

    # Assuming compute_entropy is already defined:
    def compute_entropy(self, prob1, prob2, prob3):
        # Compute entropy using the formula H = -sum(P * log(P))
        probs = np.array([prob1, prob2, prob3])
        # Avoid log(0) by only computing for non-zero probabilities
        entropy = -np.sum([p * np.log(p) for p in probs if p > 0])
        return entropy

    def select_action(self, state):
        # eps_threshold = random.random()
        #action = self.net(torch.Tensor(state))
        self.sample_count += 1

        # if self.first_step:detach
        #     self.first_step = False
        #     self.net.reinitialize_final_layer()
        if self.sample_count == batch_size + 1 and not self.reinitialized:
            self.net.reinitialized_weights()
            self.reinitialized = True

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

        probs = action_probabilities.detach().numpy()
        # Compute entropy for the action probabilities
        entropy = self.compute_entropy(probs[0], probs[1], probs[2])
        
        # Add the entropy to the list (deque keeps only the last 1000 elements)
        self.entropy_list.append(entropy)

        # Check if we have at least 1000 entropy values to compute the moving average
        if len(self.entropy_list) == 1000:
            self.moving_average_entropy = np.mean(self.entropy_list)
            self.is_moving_average_ready = True  # Moving average is ready
        else:
            self.is_moving_average_ready = False  # Not enough data yet

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
        
        return action, action_type, action_time, self.tau, probs, self.current_compression, entropy, self.moving_average_entropy, self.is_moving_average_ready

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
    def __init__(self, stepsPerEpisode, bootstrap_server):
        super(SPEEnvironment, self).__init__()

        self.valuesPerObservation = 7
        self.bootstrap_server = bootstrap_server
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

        self.action_space = spaces.Discrete(3,)
        self.consumer = KafkaStatsConsumer(self.valuesPerObservation,self.bootstrap_server)
        self.producer = KafkaActionsProducer(self.consumer,self.bootstrap_server)

        self.stepsPerEpisode = stepsPerEpisode
        self.remaingSteps = self.stepsPerEpisode

        self.prev_stat_time = time.time()

        # Start the consumer thread
        self.consumer.start_consumer()

        self.latency_last_events = -1
        self.latency_violations_per_episode = 1
        self.cpu_violations_per_episode = 1
        self.current_compression = 100  # define initial compression ratio
        self.bonus_latency_threshold = 1000
        self.latency_record = []
        self.steps_since_last_bonus = 0 # track the number of steps since last reward
        self.bonus_step_interval = 10
        self.bonus_ten_steps = 30
        self.bonus_all_steps = 0
        self.entropy_threshold = 0.6
        self.entropy_penalty = -5

        # self.state_labels = ["injectionrate", "throughput", "outrate", "latency", "compressionratio", "CPU-agg", "eventtime"]
        self.state_labels = ["injectionrate", "throughput", "outrate", "latency", "compressionratio", "CPU-agg"]
        
    def print_state(self, transformed_state, original_state):
        # get the maxmimum length of state labels for alignment
        max_label_length = max(len(label) for label in self.state_labels)
        max_value_length = max(max(len(f"{value:.2f}") for value in values) for values in original_state)
        column_width = max(max_label_length, max_value_length)
        for label, (slope,intercept), original_values in zip(self.state_labels, transformed_state, original_state):
            formatted_label = label.ljust(column_width)
            # formatted_values = ' '.join(f'{value:{column_width}.2f}' for value in values)
            transformed_values = f'{slope:>{column_width}.2f} {intercept:>{column_width}.2f}'
            original_values = ' '.join(f'{value:>{column_width}.2f}' for value in original_values)
            print(f"{formatted_label} {transformed_values} || {original_values}", flush=True)

    def linear_regression_transform(self, state_matrix):
        state_matrix = np.where(state_matrix == -1.00, np.nan, state_matrix)
        slopes = []
        intercepts = []

        # Time points for linear regression (assuming 0, 1, 2,... for the 7 time steps)
        time_points = np.arange(state_matrix.shape[1])

        for row in state_matrix:
            # Ignore NaN values
            mask = ~np.isnan(row)
            time_valid = time_points[mask]
            values_valid = row[mask]

            # If more than one valid point, perform linear regression
            if len(time_valid) > 1:
                slope, intercept, _, _, _ = linregress(time_valid, values_valid)
            else:
                slope, intercept = 0.0, values_valid[0] if len(values_valid) > 0 else 0.0
            
            slopes.append(slope)
            intercepts.append(intercept)

        # Return a transformed matrix with slopes and intercepts
        transformed_state = np.column_stack((slopes, intercepts))
        return transformed_state

    def reset(self,episode_number):

        #reset negative reward counter
        self.negative_reward_counter = 0
        # reset latency counter
        self.latency_counter = 0
        # reset the time tracker for latency events
        self.latency_last_events = -1  
        # reset initial compressionn ratio
        self.current_compression = 100
        self.latency_record = []
        self.steps_since_last_bonus = 0

        # Send the reset
        if episode_number>0:
            print('Calling reset', flush=True)
            self.producer.produce("reset")
        else:
            print('skipping reset on very first episode (already called by the SPE itself)', flush=True)
    
        self.remaingSteps = self.stepsPerEpisode
        print('self.remaingSteps set to',self.remaingSteps,'in reset', flush=True)

        # Wait for the state and reward measurement
        self.prev_stat_time = time.time()
        state_measurement_available = False
        print('Waiting for new observation', flush=True)
        while not state_measurement_available:
            time.sleep(0.1)
            with self.consumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by other threads
                # print('self.consumer.tracker.state is not None',(self.consumer.tracker.state is not None),'self.consumer.tracker.last_time',self.consumer.tracker.last_time,'self.prev_stat_time',self.prev_stat_time)
                if self.consumer.tracker.state is not None and self.consumer.tracker.last_time > self.prev_stat_time:
                    print('Got a new state/reward/extrainfo msg:',self.consumer.tracker.last_time, flush=True)
                    state = self.consumer.tracker.state.copy()
                    state_transformed = self.linear_regression_transform(state)
                    self.print_state(state_transformed, state)
                    print(f'reward {self.consumer.tracker.reward} || {self.consumer.tracker.original_reward}', flush=True)
                    state_measurement_available = True

        # Reset the reward
        self.ep_return  = self.consumer.tracker.reward
        # get the current event time
        self.current_event_time = state[6, :]
        # return states except eventtime
        return state_transformed[:-1]
    
    def scaled_compression_reward(self, ratio, bonus_step_interval_points_compression):
        """
        Scales a reward based on the compression level, where 0 compression gives maximum reward 
        and 100 compression gives zero reward.
        
        Parameters:
        - compression: int or float, where 0 indicates maximum compression and 100 indicates no compression.
        - bonus_step_interval_points_compression: int or float, the maximum reward given at 0 compression.

        Returns:
        - Scaled reward between 0 and bonus_step_interval_points_compression based on the compression level.
        """

        # Calculate reward, where 0 compression gives maximum reward, 100 compression gives zero
        reward = bonus_step_interval_points_compression * (1 - (ratio / 100))
        return reward
    
    def step(self, action, current_compression, entropy_ma, entropy_ready):
    
        self.remaingSteps -= 1
        done = False
        # self.bonus_given = False

        # Assert that it is a valid action 
        assert self.action_space.contains(action), "Invalid action"

        self.producer.produce("changeD," + str(int(current_compression/10)))

        # Wait for the state and reward measurement
        self.prev_stat_time = time.time()
        state_measurement_available = False
        # print('Waiting for new observation')
        while not state_measurement_available:
            time.sleep(0.1)
            with self.consumer.tracker.data_lock: # This is to ensure this thread does not read previous_values while they are being updated by other threads
                # print('self.consumer.tracker.state is not None',(self.consumer.tracker.state is not None),'self.consumer.tracker.last_time',self.consumer.tracker.last_time,'self.prev_stat_time',self.prev_stat_time)
                if self.consumer.tracker.state is not None and self.consumer.tracker.last_time > self.prev_stat_time:
                    # print('Got a new state/reward pair:',self.consumer.tracker.last_time,self.consumer.tracker.state,self.consumer.tracker.reward,flush=True)
                    print('Got a new state/reward/extrainfo msg:',self.consumer.tracker.last_time, flush=True)
                    state = self.consumer.tracker.state.copy()
                    state_transformed = self.linear_regression_transform(state)
                    self.print_state(state_transformed, state)
                    print(f'reward {self.consumer.tracker.reward} || {self.consumer.tracker.original_reward}', flush=True)
                    state_measurement_available = True
                    
        # We start at 0
        # self.consumer.tracker.reward = 0

        # give extra if completing predefined number of steps
        if self.steps_since_last_bonus == self.bonus_step_interval - 1:
            self.consumer.tracker.reward += self.bonus_ten_steps
            # But remove some if entropy is too loo
            if entropy_ready and entropy_ma < self.entropy_threshold:  # Penalize if entropy is low
                self.consumer.tracker.reward += self.entropy_penalty
            print(f"Extra reward bonus +{self.consumer.tracker.reward} for completing {self.bonus_step_interval} steps", flush=True)
        elif entropy_ready and entropy_ma < self.entropy_threshold:  # Penalize if entropy is low (single step)
            self.consumer.tracker.reward -= 1
            # print(f"-1 penalty for low entropy at {self.bonus_step_interval} steps", flush=True)
            print(f"-1 penalty for low entropy at this step", flush=True)

        self.steps_since_last_bonus += 1
        if self.steps_since_last_bonus == self.bonus_step_interval:
            self.steps_since_last_bonus = 0
        
        self.current_event_time = state[6, :]  # update eventtime

        # record latency of last second if it is not missing -1
        # current_event_time = self.current_event_time
        # current_latency = self.consumer.tracker.state[3]
        # for event_time, latency in zip(current_event_time, current_latency):
        #     if latency != -1:
        #         # check if the same event time has been recorded
        #         existing_entry = next((item for item in self.latency_record if item[0] == event_time), None)
        #         # if the record of this eventtime already exists, then update latency
        #         if existing_entry:
        #             index = self.latency_record.index(existing_entry)
        #             self.latency_record[index] = (event_time, latency)
        #         # if not, add new record
        #         else:
        #             self.latency_record.append((event_time, latency))

        # Check if episode should end
        if self.remaingSteps <= 0 or \
            self.consumer.tracker.numberOfLatencyExceedingEarlyTerminationThreshold >= self.latency_violations_per_episode or \
            self.consumer.tracker.numberOfCPUsExceedingEarlyTerminationThreshold >= self.cpu_violations_per_episode:
            done = True
            if self.consumer.tracker.numberOfLatencyExceedingEarlyTerminationThreshold >= self.latency_violations_per_episode:
                print("High latency observed", flush=True)
            if self.consumer.tracker.numberOfCPUsExceedingEarlyTerminationThreshold >= self.cpu_violations_per_episode:
                print("High cpu observed", flush=True)
            # if self.remaingSteps <= 0:
            #     self.consumer.tracker.reward += self.bonus_below_latency
            #     print(f"Extra reward bonus +{self.bonus_below_latency} because of reaching the end of this episode")
            # apply bonus if conditions are met at the end of an episode
            # valid_latencies = [latency for _, latency in self.latency_record[-10:]]  # extract only the latency values from the last 10 records
            # if len(valid_latencies) == self.bonus_step_interval and all(latency <= self.bonus_latency_threshold for latency in valid_latencies):
            #         self.consumer.tracker.reward += self.bonus_below_latency
            #         print(f"Extra reward bonus +{self.bonus_below_latency} because of low latency in the last {self.bonus_step_interval} observations")
        else:
            done = False

        # Increment the episodic return
        self.ep_return += 1
        return state_transformed[:-1], self.consumer.tracker.reward, done, []
    
    def close(self):
        super(SPEEnvironment, self).close()
        self.producer.produce("close")


class MeasurementTracker:
    def __init__(self, valuesPerObservation):
        self.last_time = None
        self.state = None
        self.latest_compression = None
        self.original_reward = None
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
                
                # Find the latest compression value that is not -1
                # Extract the 6th row (index 5) from self.state
                compression_values = self.state[5]

                # Find the latest value in the row that is not -1
                self.latest_compression = None
                for value in reversed(compression_values):
                    if value != -1:
                        self.latest_compression = value
                        break

                
            except Exception as e:
                raise RuntimeError("An error occured parsing " + input_str) from e
            
            self.original_reward = int(parts[1])
            # if self.original_reward > 0:
            #     self.reward = 2
            # elif self.original_reward < 0:
            #     self.reward = -2
            # else:
            #     self.reward = 0
            self.reward = self.original_reward
            self.numberOfLatencyExceedingEarlyTerminationThreshold = int(parts[2])
            self.numberOfCPUsExceedingEarlyTerminationThreshold = int(parts[3])

class KafkaActionsProducer:
    def __init__(self, statsConsumer, bootstrap_servers, actions_topic='dchanges'):
        self.bootstrap_servers = bootstrap_servers
        self.actions_topic = actions_topic
        self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})
        self.statsConsumer = statsConsumer


    def produce(self, action):
        self.producer.produce(self.actions_topic, key=str(time.time()), value=action)
        self.producer.flush()

class KafkaStatsConsumer:
    def __init__(self, valuesPerObservation, bootstrap_servers, stats_topic='stats', group_id='0'):
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
                    print(msg.error(), flush=True)
                    break

            # Process the received message
            stat = msg.value().decode('utf-8')
            print(f"Received message from 'stats' topic: {stat}", flush=True)
            self.tracker.process_input(stat)

    def start_consumer(self):
        consumer_thread = threading.Thread(target=self.consume_stats)
        consumer_thread.daemon = True
        consumer_thread.start()



def create_folder_and_path(base_folder, sub_folder, file_name=None):
    folder_path = os.path.join(base_folder, sub_folder)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)    
    # If a file name is provided, join it to the folder path
    if file_name:
        return os.path.join(folder_path, file_name)
    else:
        return folder_path

def write_to_csv(file_path, mode, data, data_type):
    with open(file_path, mode=mode, newline='') as file:
        writer = csv.writer(file, quoting = csv.QUOTE_MINIMAL)
        if data_type == 'step_tot_reward':
            writer.writerow([data[0], data[1], data[2]]) # episode, step, total reward
        if data_type == 'rewards':
            writer.writerow([data[0], data[1]]) # action_time, reward
        if data_type == 'probs':
            writer.writerow([data[0], data[1], data[2], data[3], 
                             data[4], data[5], data[6], data[7], 
                             data[8]]) # episode, step, prob 0, prob 1, prob 2, entropy, entropy_ma, entropy_ready, reward

def plot_q_values(steps, q_values_history, episode_num, q_value_file_path):
    plt.figure()
    colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'black', 'orange', 'purple', 'brown', 'pink']
    for i, action_q_values in enumerate(q_values_history):
        if len(steps) == len(action_q_values):
            action_q_values = [val[0] if isinstance(val, np.ndarray) and len(val) == 1 else val for val in action_q_values]
            plt.plot(steps, action_q_values, label=f'Action {i}', color=colors[i % len(colors)])
        else:
            print(f"Error: Mismatch in lengths for Action {i}")
    plt.xlabel('Steps')
    plt.ylabel('Q Values')
    plt.title(f'Q Values Over Episodes (Episode {episode_num})')
    plt.legend()
    plt.savefig(q_value_file_path)
    plt.close()

def save_model_and_buffer(agent, episode_num, model_file_path, buffer_file_path):
    torch.save(agent.net.state_dict(), model_file_path)
    with open(buffer_file_path, 'wb') as f:
        pickle.dump(agent.buffer, f)

def load_model_and_buffer(agent, model_file, buffer_file):
    if os.path.exists(model_file):
        agent.net.load_state_dict(torch.load(model_file))
        print(f'Loaded model parameters from {model_file}')
    if os.path.exists(buffer_file):
        with open(buffer_file, 'rb') as f:
            agent.buffer = pickle.load(f)
        print(f'Loaded replay buffer from {buffer_file}')


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Start an Agent that always chooses the same compression level')
    parser.add_argument('episodes', help='Number of episodes')
    parser.add_argument('steps', help='Number of steps')
    parser.add_argument('bootstrapServer', help='bootstrapServer', default=True)
    parser.add_argument('baseFolder', help='baseFolder', default=True)
    parser.add_argument('-agentstate', help='State of the pre-trained agent', default=None)
    parser.add_argument('-learningactive', help='Wheter the agent should learn', default=True)
    # parser.add_argument('--exp_folder', help='The experiment folder to store results', required=True)
    args = parser.parse_args()
    
    print('Creating agent', flush=True)
    print('episodes:',args.episodes, flush=True)
    print('steps:',args.steps, flush=True)
    print('bootstrapServer:',args.bootstrapServer, flush=True)
    print('baseFolder:',args.baseFolder, flush=True)
    print('agentstate:',args.agentstate, flush=True)
    print('learningactive:',args.learningactive, flush=True)
    

    env = SPEEnvironment(int(args.steps),args.bootstrapServer)
    # input_shape = (11, 7)
    input_shape = (6, 2)
    hidden_size = 128
    output_size = env.action_space.n
    Agent = DQN(input_shape, hidden_size, output_size)

    #load model's paras and replay buffer
    # model_file = 'image/exp16-5/WELAW/synthetic5s/1-60/model_paras/dqn_model_episode_50.pth'
    # buffer_file = 'image/exp16-5/WELAW/synthetic5s/1-60/replay_buffer/replay_buffer_episode_50.pkl'
    # load_model_and_buffer(Agent, model_file, buffer_file)

    #exp_folder = args.baseFolder #  args.exp_folder
    paras_folder = create_folder_and_path(args.baseFolder, 'model_paras')
    q_value_folder = create_folder_and_path(args.baseFolder, 'q_values_plot')
    replay_buffer_folder = create_folder_and_path(args.baseFolder, 'replay_buffer')
    step_tot_reward_path = create_folder_and_path(args.baseFolder, '', 'step_tot_reward.csv')
    action_time_reward_path = create_folder_and_path(args.baseFolder, '', 'rewards.csv')
    probs_path = create_folder_and_path(args.baseFolder, '', 'probs.csv')

    if args.agentstate is not None:
        Agent.net.load_state_dict(torch.load(args.agentstate))
   
    incremental_average_reward = 0  # average reward of all episodes for incermental averaging
    cumulative_steps = 0 # track steps across episodes


    for i_episode in range(0, int(args.episodes)):
        print('starting episode',i_episode + 1, flush=True)
        start_time = time.time() # start time of per episode
        s0 = env.reset(i_episode)
        s0 = s0.reshape(-1)
        Agent.reset_compression()

        total_reward = 0  # total reward per episode
        # total_time = 0  # actual processing time per episode
        step_count = 0 # count the number of steps in every episode

        steps = [] # store the steps for plotting
        q_values_history = [[] for _ in range(env.action_space.n)]

        while True:
            # for epsilon greedy strategy
            # a0, action_type, action_time, epsilon, current_compression = Agent.select_action(s0)
            # for Boltzmann(softmax) exploration strategy
            a0, action_type, action_time, tau, action_probablities, current_compression, entropy, moving_average_entropy, is_moving_average_ready = Agent.select_action(s0)
            q_values = Agent.net(torch.Tensor(s0)).detach().numpy().squeeze()
            # for epsilon greedy strategy
            # print(f"Episode {i_episode + 1}, Step {step_count + 1}, Action {a0}, Current Compression: {current_compression}, Action type: {action_type}, Epsilon: {epsilon:.6f}, Q values: {q_values}, Action time: {action_time}") 
            # for Boltzmann(softmax) exploration strategy
            print(f"Episode {i_episode + 1}, Step {step_count + 1}, Tau: {tau:.6f}, Q values: {q_values}, Action Probablities: {action_probablities}, Action {a0}, Entropy: {entropy}, Entropy MA: {moving_average_entropy}, Entropy MA ready: {is_moving_average_ready}, Current Compression: {current_compression}, Action time: {action_time}, Action type: {action_type}", flush=True)

            steps.append(step_count)
            for i, q_value in enumerate(q_values):
                q_values_history[i].append(q_value)

            # only keep the return value of s1, r, done, ignore the fourth return value
            step_result = env.step(a0, current_compression, moving_average_entropy, is_moving_average_ready)
            s1, r, done = step_result[:3]
            total_reward += r # cal total reward of current episode
            print(f"After {step_count + 1} steps, total reward so far in this episode: {total_reward}", flush=True)
            
            write_to_csv(action_time_reward_path, mode = 'a', data = [int(action_time), r], data_type = 'rewards')
            # episode, step, prob 0, prob 1, prob 2, entropy, entropy_ma, entropy_ready, reward
            write_to_csv(probs_path, mode = 'a', data = [i_episode + 1, step_count + 1, 
                                                         action_probablities[0], action_probablities[1], 
                                                         action_probablities[2], entropy, 
                                                         moving_average_entropy, is_moving_average_ready, r], data_type = 'probs')
            
            if done == True:
                end_time = time.time() # end time of per episode
                total_time = end_time - start_time
                print(f"Episode {i_episode + 1}, Step {step_count + 1}, This episode has finished.", flush=True)
                # incremental average for all past episodes
                incremental_average_reward = incremental_average_reward +  (total_reward - incremental_average_reward) / (i_episode + 1)
                # standard average for this current episode
                standard_average_reward = total_reward / step_count if step_count else 0
                print(f"Episode {i_episode + 1}, Total Time: {total_time: .2f}, Total Reward: {total_reward}, Incremental Average Reward: {incremental_average_reward}, Standard Average Reward: {standard_average_reward}", flush=True)
                # write results to 'step_tot_reward.csv'
                write_to_csv(step_tot_reward_path, mode = 'a', data = [i_episode + 1, step_count + 1, total_reward], data_type = 'step_tot_reward')
                break

            step_count += 1 # increment the step for each episode
            cumulative_steps += 1 # increment the step across the episode

            t = 1 if done else 0
            Agent.put(s0, a0, r, t, s1)  # put into replay buffer
            s0 = s1

            if args.learningactive:
                Agent.update_parameters()
            
            if (cumulative_steps + 1) % target_update == 0:
                Agent.target_net.load_state_dict(Agent.net.state_dict())
                print(f"Target network updated after {cumulative_steps + 1} steps.", flush=True)

        q_value_file_path = os.path.join(q_value_folder, f'q_value_plot_{i_episode + 1}.png')
        plot_q_values(steps, q_values_history, i_episode + 1, q_value_file_path)
        model_file_path = os.path.join(paras_folder, f'dqn_model_episode_{i_episode + 1}.pth')
        buffer_file_path = os.path.join(replay_buffer_folder, f'replay_buffer_episode_{i_episode + 1}.pkl')
        if (i_episode + 1) % 10 == 0:
            save_model_and_buffer(Agent, i_episode + 1, model_file_path, buffer_file_path)
                 
    print('closing', flush=True)
    env.close()
