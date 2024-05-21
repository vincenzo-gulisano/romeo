# Exp 0
1. 2 states: latency, two previous compression ratios
2. reward was very naïve, only -20 or +10

# Exp1
1. change target_update
target_update = 2  # copy frequency from net to target_net
2. reward function
if (latency > 1000) {
            return Long.toString((long) -(latency-1000));
        }
        return Long.toString((long) (100-ratios.get(1)));

3. (01-30-24 on slack by sup.) 
[Exp1] I also changed the Random generator I am using because I have the feeling everytime it peeks the same portions of data, not it should change.
4. (01-26-24 on slack by sup.) -- haven't tried yet
maybe the reward should be based also on how long the agent keeps the latency below the threshold, not just on whether it is under or above the threshold.

# Exp2
1. change target_update
target_update = 1
2. Define a 2-D observation space --> states: injection rate, latency, compression, CPU consumption
self.observation_space = spaces.Box(low = np.array([0,0,0,0]), 
                                    high = np.array([np.inf, np.inf, 100, 100]),
                                    dtype = np.float32)
3. Define an action space ranging from 0 to 11
0 means set compression to 0%
1 means set compression to 10%
...
10 means set compression to 100%
self.action_space = spaces.Discrete(11,)
4. reward function
public String getRewardAsString() {
    if (L > 1000) {
        return Long.toString((long) -(L - 1000) / 10);
    }
    return Long.toString((long) (100 - R));
}
5. (02-05-24 on slack by sup.) [Exp2] Changes:
(1)	while training based on the average latency in the last 20 seconds is probably not the best, having the latest statistic rather than an aggregation of the last X seconds is not a good idea either. This is because for the input rate, if the system is saturated, the latest rate could be small but that does not mean the injection is low, only that the system is saturated. So now I do average input rate / average latency / max latency in the last 10 seconds. So basically from 20 seconds to 10 seconds (so experiments should be also faster) and latency is max not average.
(2)	Based on Exp1. I also decided to add a measurement of the CPU. so that if the average input rate is low because the system is saturated, the CPU consumption will be high, and the agent will probably understand better.
(3)	I also changed the reward, now positive/negative are on the same order of magnitude.
## Exp2.2
1. training another 50 episodes based on Exp2
use 50 episodes' paras to train model, get a model for episode 51-100 episodes
2. (02-07-24 on slack by sup.) [Exp2.2] Changes:
basically now you must pass the number of episodes and steps as parameters and you can pass two additional parameters (optional) to specify whether the agent should learn or not and whether a pre-trained state should be loaded or not
## Exp2.3
1. training another 200 episodes based on Exp2.2
use 100 episodes' paras to train model, get a model for episode 101-300

# Exp3
1. early termination
if latency is greater than 1 second (1000 milliseconds) in three consecutive steps:
    early termination, and then go to next episode
2. training for 300 episodes --> every episode might has different steps, but the maximum steps for every episode is 50.
3. solve stuck in SPE
4. add more logs in spe
5. (02-19-24 on slack by sup.) [Exp3] 
what I like less is that it converges after 50 but it still oscillates a lot...

# Exp4
1. early termination
if latency is greater than 1 second (1000 milliseconds) in three consecutive steps:
    early termination, and then go to next episode
2. training for 100 episodes --> every episode has different steps, but the maximum steps for every episode is 150.
3. PLUS:
(1) there are two parameters in start_all.sh, 'starting_time_min' and 'starting_time_max', set to 900 and 9900. When a new episode starts, the first timestamp is chosen randomly in that interval. 
(2) [Linear query] Now, it takes more or less 10 seconds per action, which means 500 seconds per episode. Since the number of seconds in the input data is 11628, even if an episode starts at 9900, it is impossible to consume all the data. In fact, 11628-9900 = 1728, and 1728/10=172. I think we can increase the number of steps to 150 and, even in this case, if the agent manages to run for 150, it cannot exaust all the data.
4. solve stuck in SPE
5. add more logs in spe

# Exp5
1. 1 second for every step not 10 second
2. every step display the state in the last 7 seconds (the last column is the value for current step)
3. if the reward of any three stpes in this episode is negative, then terminate this episode, and go to next one.
4. use 'nan' to show the state with no value
5. reward funciton: 
    (1) positive (if (latency < 1000) & (compression < 100)): (100 - compression)^1.5
    (2) negative (if latency > 1000): - (int) ((latency - 1000)/10)
## Exp5.1
1. Convert the string to a list of floats without replacing -1.0 with np.nan for running 100 episodes, each of which has maximum 150 steps
doubles_list = [float(x) for x in parts[0].split(',')]
## Exp5.2
1. Convert the string to a list of floats without replacing -1.0 with np.nan for running 500 episodes, each of which has maximum 150 steps
doubles_list = [float(x) for x in parts[0].split(',')]

# Exp6
1. Sup. changes a lot of things in SPE, but I cannot capture all the details...
2. 11 states for every 7 seconds:
(1) injection rate, throughput, outrate, latency, ratio, comp, dec, CPU-in, CPU-agg, CPU-out, event time
(2) the observation space (state): 11*7
3. try to distinguish/synchronize the clock time and event time
(how could I illustrate this? add clock time barrier and event time barrier?)
## Exp6.1
1. plot q values for every episode
2. just re-run 100 episodes to see if the exp6 has affected by other users also using the server.

# Exp7
1. terminates an episode if it sees a latency greater than 2.5 seconds three times
2. (03-07-24 on teams by sup.)
In this case, aggressive actions (i.e., D=0 or D=1, with D=1 not as aggressive as D=0) will only terminate the episode when the latency really explode. In most of the cases, the agent will be able to continue the episode, get negative rewards, and learn more about how to recover after a too drastic D is chosen. 
3. Expectations from this experiment before actually running it:
(1) The episodes will run for more steps.
(2) Steps per episodes graph will show a growing trend or still a fluctuating trend, but it should at least show fluctuations around a higher number of steps per episode than Exp6.
(3) If the episodes are getting longer, the reward is getting higher. Even if don't know if the cumulative reward per episode graph will be flutuating or showing some clear growing trend, the values should be higher.
(4) The Bloxplot for average compression should be at least as good as Exp6. And the new Boxplot we should re-print only for episodes that reach 150 steps, to understand if it is getting better when there are no ctastrophic actions.
(5) The plot of total latency violations per episode will also show higher values, but hopefully it will be stable over time (or maybe even slightly decreasing).
## Exp7.1
1. change action scetion to epsilon decay
epsilon_start = 0.1
epsilon_end = 0.01
epsilon_count = 500 # the higher value, the slower decay

self.epsilon = EPSILON_END + (EPSILON_START - EPSILON_END) * math.exp(-1 * self.sample_count / EPSILON_DECAY)

if random.random() > self.epsilon:
    choice = torch.argmax(action).numpy()
    action_type = "exploitation"
else:
    choice = np.random.randint(0, action.shape[0])  # random sampling
    action_type = "exploration"
## Exp7.2
1. use 'pickle' to store the content of buffer 

# Exp8
1. synthetic query was 'born'
2. run 100 episodes (max 150 steps per episode) for 'linear road' and 300 episode for 'synthetic' query

# Exp9
1. change the action to 3 values: 0 means reduced by 10, 1 means no change, and 2 is increased by 10
2. initial compression ratio for every episode is 100

# Exp10
1. changing states from 11 to 7:
(1) injection rate
(2) throughput
(3) out rate
(4) latency
(5) compression ratio
(6) CPU Agg
(7) event time
2. epsilon: 0.65 --> 0.01 (decay factor = 500), 
(1) linear: converge to 0.01 at episode 97 step 2 (6971 steps in total)
(2) synthetic: converge to 0.01 at episode 117 step 19 (7089  steps in total)
3. 80 steps for each episode
4. 200 episodes for both linear and synthetic
## Exp10.1
1. run 200 episodes for synthetic with epislon in [0.8, 0.3] and gamma in 0.7, just want to see what happens because the agent seems too conservative
## Exp10.2
1. change the reward function
the agent gets a reward when an action increases the compression, but then gets 0 as long as it "stays there"
(1) if taking the compression since the last report
(2) filter out '-1' values
(3) computes the difference between the last and the first (if there are at leat 2 values)
(4) if the difference is negative --> computes the reward
2. parameters setting
(1) epsilon in [0.9, 0.1] (decay factor = 500)
(2) gamma = 0.9
(3) target_update = 4 
    previous is 1, if so, that means, updating target network after every episode, which may lead to instability in the learning process, because the target network changes too frequently, it may not be enough to provide a stable learning goal for the evaluation network.
    target network is to provide a relatively stable target Q value to help the evaluation network (the main network) learn more stably. If the target network is updated too frequently, then the goal of evaluating learning will change frequently, which may lead to oscillation or instability in the learning.

# Exp11
1. replace epsilon greedy with softmax exploration
TAU_START = 10
TAU_END = 1
TAU_DECAY = 500
## Exp11.1(Exp12)
1. initial weights for NN using xavier initialization --> all logs are in /home/jingyu/romeo/image/Exp11.1/synthetic/xvaier
<!-- initialize weights using Xavier uniform distribution -->
init.xavier_uniform_(self.Linear1.weight)#, gain = nn.init.calculate_gain('relu'))
init.xavier_uniform_(self.Linear2.weight)#, gain = nn.init.calculate_gain('relu'))
init.xavier_uniform_(self.Linear3.weight)#, gain = nn.init.calculate_gain('relu'))
<!-- initialize biases within range [-0.1, 0.1] -->
init.uniform_(self.Linear1.bias, -0.1, 0.1)
init.uniform_(self.Linear2.bias, -0.1, 0.1)
init.uniform_(self.Linear3.bias, -0.1, 0.1)
2. initial weights for NN using He initialization --> all log are in /home/jingyu/romeo/image/Exp11.1/synthetic/he_initialization
<!-- iniitialize weights using He initialization -->
init.kaiming_normal_(self.Linear1.weight, mode='fan_in', nonlinearity='relu')
init.kaiming_normal_(self.Linear2.weight, mode='fan_in', nonlinearity='relu')
init.kaiming_normal_(self.Linear3.weight, mode='fan_in', nonlinearity='relu')
 <!-- initialize biases within range [-0.1, 0.1] -->
init.uniform_(self.Linear1.bias, -0.1, 0.1)
init.uniform_(self.Linear2.bias, -0.1, 0.1)
init.uniform_(self.Linear3.bias, -0.1, 0.1)
3. initial weights for NN using scaled uniform initialization --> all logs are in /home/jingyu/romeo/image/Exp11.1/synthetic/scaled
def init_weights(self): 
    <!-- Initialize weights and biases for each layer  -->
    for m in self.modules(): 
        if isinstance(m, nn.Linear): 
            init.uniform_(m.weight, -0.07, 0.07) 
            m.bias.data.fill_(0.05)
4. change reward funciton
private long computeRewardBasedOnActionLatencyAndCompression() {

        long prevD = varDValues.get(0);
        long lastD = varDValues.get(1);
        boolean latencyAboveThreshold = latencyAboveThresholdInReportedStates.get(0);
        boolean compressionGreaterThanZero = compressionsGreaterThanZeroInReportedStates.get(0);
        boolean compressionsEqualToOne = compressionsEqualToOneInReportedStates.get(0);

        if (latencyAboveThreshold) {
            if (prevD > lastD) {
                logger.debug("Latency exceeded and compression increased --> bad");
                return -1;
            } else if (prevD == lastD) {
                if (compressionsEqualToOne) {
                    logger.debug("Latency exceeded and compression unchanged (but already at 1) --> good");
                    return +1;
                } else {
                    logger.debug("Latency exceeded and compression unchanged (but smaller than 1) --> bad");
                    return -1;
                }
            } else {
                logger.debug("Latency exceeded and compression decreased --> good");
                return +1;
            }
        } else {
            if (prevD > lastD) {
                logger.debug("Below max latency and compression increased --> good");
                return +1;
            } else if (prevD == lastD) {
                if (compressionGreaterThanZero) {
                    logger.debug(
                            "Below max latency and compression unchanged (but greater than zero) --> bad");
                    return -1;
                } else {
                    logger.debug(
                            "Below max latency and compression unchanged (but equal to zero) --> good");
                    return +1;
                }
            } else {
                logger.debug("Below max latency and compression decreased --> bad");
                return -1;
            }
        }

    }
5. change the number of hidden neuron of NN
hidden_size = 128 (256 -> 128)
6. change learning rate
lr = 0.01 (0.1 -> 0.01)
7. format the state output
def print_state(self, state):
    <!-- get the maxmimum length of state labels for alignment -->
    max_label_length = max(len(label) for label in self.state_labels)
    max_value_length = max(max(len(f"{value:.2f}") for value in values) for values in state)
    column_width = max(max_label_length, max_value_length)
    for label, values in zip(self.state_labels, state):
        formatted_label = label.ljust(column_width)
        formatted_values = ' '.join(f'{value:{column_width}.2f}' for value in values)
        print(f"{formatted_label}: {formatted_values}")
8. modify the reward (incremental/standard average reward) and total processing time at the end of each episode
if done == True:
    end_time = time.time() # end time of per episode
    total_time = end_time - start_time
    print(f"Episode {i_episode + 1}, Step {step_count + 1}, This episode has finished.")
    <!-- incremental average for all past episodes -->
    incremental_average_reward = incremental_average_reward +  (total_reward - incremental_average_reward) / (i_episode + 1)
    <!-- standard average for this current episode -->
    standard_average_reward = total_reward / step_count if step_count else 0
    print(f"Episode {i_episode + 1}, Total Time: {total_time: .2f}, Total Reward: {total_reward}, Incremental Average Reward: {incremental_average_reward}, Standard Average Reward: {standard_average_reward}")
    break
9. change d to 10 in start.all.sh for synthetic and linear
base_folder="/home/jingyu/romeo/data/output/synthetic"
input_file="/home/vincenzo/romeo/data/input/synthetic.csv"
wa=1
ws=900
d=10
starting_time_min=1200
starting_time_max=6500
usecase="Synthetic"
10. tau within [10, 1]
## Exp11.2(Exp12)
1. running 20 episodes with tau fixed at 3 for linear and synthetic

# Exp13
1. change reward funciton
if (latency was smaller than threshold AND (compression ratio decreased OR compression ratio is 0 OR action was 0 OR (action was 1 and D was 0))) {
  +1
} else if (latency was equal to or greater than latency AND (compression ratio increased OR compression ratio is 1 OR action was 2 OR (action was 1 and D was 10))) {
  +1
} else {
  -1
}
2. tau within [10, 3] for decay factor = 500
3. initial weihgts for each leyer in NN by scaled uniform distribution within [-0.03, 0.03]
4. 6 states (injectionrate, throughput, outrate, latency, compression ratio, CPU-agg) for DQN to learn/train
## Exp13.1
1. change discount factor (gamma) to 0.99 (0.9 --> 0.99)
2. run 100 episodes on four policies for linear and synthetic
(1) policy="WEAOB" -- Wallclock, Event time, Aggregate OBlivios
(2) policy="EAOB" -- Event time, Aggregate OBlivios
(3) policy="AOB" -- Aggregate OBlivios
(4) policy="WEAAW" -- Wallclock, Event time, Aggregate AWare
## Exp13.2
1. 50 steps for each episode
2. gamma = 0.999
3. policy is "WEAAW"
4. no more early termination
5. reward bonus +10 if the last report of latency in last consecutive 10 steps is less than 1 second. 
## Exp13.3
1. 20 episodes for only synthetic with tau fixed at 1
(1) want to see what happens with the probabilities
(2) it's not purely random, because some actions have higher probabilities than others, but it's almost random
(3) would like to understand if this is because tau is too large

# Exp14
1. change discount factor to 0.99 (0.999 to 0.99)
2. change target frequency to 20 (4 to 20)
3. reward
3.1 +1: latency is below 1.5 seconds (hard threshold)
3.2 +2: latency is below 0.75 seconds (soft threshold)
3.3 +5: finishing every 10 steps
3.4 +10: latency of last 10 eventtime with non-missing value is below 1 second
4. early termination
latency for any 3 steps in each episode is higher than 2.5 seconds --> terminate this episode, then go to next one
5. run 200 episodes 50 steps for each episode
6. change tau within [5,1] ([10,3] to [5,1])
# Exp14.1
1. change reward function
(1) +2: latency before and after action are both below soft and compression increased
(2) +1: latency before and after action are both below soft and compression did not increase
(3) +2: latency before and after action are both not high and compression increased
(4) +1: latency before and after action are both not high and compression did not increase
(5) +2: latency before is high and after action is not
(6) -5: if not above
# Exp14.2
1. fixed missing high latencies problem for two queries
2. run 100 episodes for WEAOB, EAOB and AOB
3. run 200 episodes for WEEAW
# Exp14.3
1. run all policies again but this time for synthetic only and changing the WA to 20 secs -- basically for linear road OB policies mean more conservative behavior (because most of the rewards are 0, which means the agent tries to reach the end as safe as possible), in that case in theory the behavior of the different policies should be different too, like in linear road I think
2. starting_time_max=5800 (from 6500 to 5800)