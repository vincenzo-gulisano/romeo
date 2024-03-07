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
import torch.optim as optim
from collections import namedtuple
import math
import os


GAMMA = 0.99
lr = 0.1
EPSION = 0.1
buffer_size = 10000  # replay buffer size
batch_size = 128
#episodes = 50
target_update = 1  # copy frequency from net to target_net
#steps = 100


# define neural network
class Net(nn.Module):
    def __init__(self, input_shape, hidden_size, output_size):
        super(Net, self).__init__()
        # flatten the input
        self.flatten = nn.Flatten()
        self.input_size = input_shape[0] * input_shape[1] # cal input size after flattening
        self.Linear1 = nn.Linear(self.input_size, hidden_size)
        self.Linear2 = nn.Linear(hidden_size, hidden_size)
        self.Linear3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # print('x: ', x)
        # flatten the input
        if x.dim() > 1:
            x = x.view(-1, self.input_size)
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
    def __init__(self, input_shape, hidden_size, output_size):
        self.net = Net(input_shape, hidden_size, output_size)
        self.target_net = Net(input_shape, hidden_size, output_size)
        self.optim = optim.Adam(self.net.parameters(), lr=lr)

        self.target_net.load_state_dict(self.net.state_dict())
        self.buffer = ReplayMemory(buffer_size)
        self.loss_func = nn.MSELoss()
        self.steps_done = 0

    def put(self, s0, a0, r, t, s1):
        self.buffer.push(s0, a0, r, t, s1)

    def select_action(self, state):
        eps_threshold = random.random()
        #action = self.net(torch.Tensor(state))
        # reshape state to 1D vector
        state = torch.Tensor(state).view(-1)
        action = self.net(state)
        action_time = time.time()
        if eps_threshold > EPSION:
            choice = torch.argmax(action).numpy()
            action_type = "exploitation"
        else:
            choice = np.random.randint(0, action.shape[0])  # random sampling
            action_type = "exploration"
        return choice, action_type, action_time

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
        # states: injectionrate, throughput, outrate, latency, ratio, comp, dec, CPU-in, CPU-agg, CPU-out, event time
        self.observation_space = spaces.Box(low = np.array(
                                                [np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1),
                                                np.full(self.valuesPerObservation, -1)]), 
                                            high = np.array(
                                                [np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, 100),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, np.inf),
                                                 np.full(self.valuesPerObservation, 100),
                                                 np.full(self.valuesPerObservation, 100),
                                                 np.full(self.valuesPerObservation, 100),
                                                 np.full(self.valuesPerObservation, np.inf)]),
                                            dtype = np.float32)
        # self.observation_space = spaces.Box(low = np.array([0,0,0,0]), 
        #                                     high = np.array([np.inf, np.inf, 100, 100]),
        #                                     dtype = np.float32)
        
        # Define an action space ranging from 0 to 11
        # 0 means set compression to 0%
        # 1 means set compression to 10%
        # ...
        # 10 means set compression to 100%
        self.action_space = spaces.Discrete(11,)

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
        self.negative_reward_counter = 0

    def reset(self):

        #reset negative reward counter
        self.negative_reward_counter = 0

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
                    for row in self.consumer.tracker.state:
                        print ([f'{num:.2f}' for num in row])
                    print('reward',self.consumer.tracker.reward,flush=True)
                    # print('Got a new state/reward pair:',self.consumer.tracker.last_time,self.consumer.tracker.state,self.consumer.tracker.reward,flush=True)
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
                    # print('Got a new state/reward pair:',self.consumer.tracker.last_time,self.consumer.tracker.state,self.consumer.tracker.reward,flush=True)
                    print('Got a new state/reward pair:',self.consumer.tracker.last_time)
                    for row in self.consumer.tracker.state:
                        print ([f'{num:.2f}' for num in row])
                    print('reward',self.consumer.tracker.reward,flush=True)
                    state_measurement_available = True
        
        # update negative reward counter
        if self.consumer.tracker.reward < 0:
            self.negative_reward_counter += 1
        
        # check if need to end this episode
        if self.negative_reward_counter >= 3:
            done = True
        else:
            done = False
        
        # check if there has remainig steps
        if self.remaingSteps <= 0:
            done = True
        
        # Increment the episodic return
        self.ep_return += 1

        # TODO There's something missing, the SPE itself could be done if it runs out of data. This is not being checked as of now...
        return self.consumer.tracker.state.copy(), self.consumer.tracker.reward, done, []
    
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

        print('Received:',input_str,'at time',time.time(),flush=True)

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
            self.state = np.array(doubles_list, dtype=np.float32).reshape(11, self.valuesPerObservation)
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
    input_shape = (11, 7)
    Agent = DQN(input_shape, 256, env.action_space.n)

    # load saved net's paras after 50 episodes
    # model_file = 'image/Exp3/Exp3_paras/dqn_model_episode_260.pth'
    # if os.path.exists(model_file):
    #     Agent.net.load_state_dict(torch.load(model_file))
    #     print("loaded net's paras...")
   
    if args.agentstate is not None:
        Agent.net.load_state_dict(torch.load(args.agentstate))
   
    average_reward = 0  # average reward of all episodes

    # create folder to store paras
    paras_folder_name = 'data/output/5/600/5000000000/0/25000/601/Exp6_paras (1-100)'
    if not os.path.exists(paras_folder_name):
        os.makedirs(paras_folder_name) 

    # create folder to store q value plots
    q_value_folder_name = 'data/output/5/600/5000000000/0/25000/601/Exp6_q_value_plots (1-100)'
    if not os.path.exists(q_value_folder_name):
        os.makedirs(q_value_folder_name)

    for i_episode in range(0, int(args.episodes)):
        print('starting episode',i_episode + 1)
        s0 = env.reset()
        s0 = s0.reshape(-1)
        tot_reward = 0  # total reward per episode
        tot_time = 0  # actual processing time per episode
        step_count = 0 # count the number of steps in every episode

        # plt.figure()
        steps = [] # store the steps for plotting
       # steps = [int (step) for step in steps] # guarantee the step is integer
        q_values_history = [[] for _ in range(env.action_space.n)]

        while True:
            a0, action_type, action_time = Agent.select_action(s0)
            #s1, r, done, _ = env.step(a0)
            q_values = Agent.net(torch.Tensor(s0)).detach().numpy().squeeze()
            print(f"Step {step_count + 1}, Action {a0}, Action type: {action_type}, Q values: {q_values}, Action time: {action_time}") 

            steps.append(step_count)

            for i, q_value in enumerate(q_values):
                q_values_history[i].append(q_value)

            # only keep the return value of s1, r, done, ignore the fourth return value
            step_result = env.step(a0)
            s1, r, done = step_result[:3]

            tot_time += r  # cal. total time of current episode
            # reward cal. method
            # x, x_dot, theta, theta_dot = s1
            # r1 = (env.x_threshold - abs(x)) / env.x_threshold - 0.8
            # r2 = (env.theta_threshold_radians - abs(theta)) / env.theta_threshold_radians - 0.5
            # r = r1 + r2
            tot_reward += r # cal total reward of current episode
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

                average_reward = average_reward + 1 / (i_episode + 1) * (tot_reward - average_reward)
                print('Episode ', i_episode + 1, 'tot_time: ', tot_time, ' tot_reward: ', tot_reward, ' average_reward: ', average_reward)
                break

        if i_episode % target_update == 0:
            Agent.target_net.load_state_dict(Agent.net.state_dict())

        plt.figure()
        for i, action_q_values in enumerate(q_values_history):
                if len(steps) == len(action_q_values):
                    action_q_values = [val[0] if isinstance(val, np.ndarray) and len(val) == 1 else val for val in action_q_values]
                    plt.plot(steps, action_q_values, label = f'Action {i}')
                else:
                    print(f"Error: Mismatch in lengths for Action {i}")


        # saving q value plots
        plt.xlabel('Stpes')
        plt.ylabel('Q Values')
        plt.title(f'Q Values Over Episodes (Episode {i_episode + 1})')
        plt.legend()
        q_value_file_path = os.path.join(q_value_folder_name, f'exp6_q_values_plot_{i_episode + 1}.png')
        plt.savefig(q_value_file_path)
        plt.close()
            

        # saving paras per 10 episodes
        if (i_episode + 1) % 10 == 0: 
            # save model paras every 10 episodes
            paras_file_path = os.path.join(paras_folder_name, f'exp6_dqn_model_episode_{i_episode + 1}.pth')
            torch.save(Agent.net.state_dict(), paras_file_path)        

    print('closing')
    env.close()