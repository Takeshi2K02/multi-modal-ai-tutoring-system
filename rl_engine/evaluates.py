# evaluate_plot.py
import time
import json
import os
import matplotlib.pyplot as plt
from stable_baselines3 import DQN
from stable_baselines3.common.vec_env import DummyVecEnv
from src.env.tutor_env import TutorEnv
from src.engine.rl_engine import RLEngine
from src.utils.logger import log_decision

LOG_FILE = "logs/rl_decisions.jsonl"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Wrap environment for SB3
env = DummyVecEnv([lambda: TutorEnv()])

# Load trained agent
agent = RLEngine("models/ppo_model.zip", env=env)

NUM_EPISODES = 5

# Clear previous log file
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

# ------------------------
# Run evaluation episodes
# ------------------------
for ep in range(1, NUM_EPISODES + 1):
    print(f"\n=== Episode {ep} ===")
    obs = env.reset()  # obs is a numpy array (batch dim included)
    done = False
    step_count = 0
    total_reward = 0

    while not done:
        step_count += 1

        # Agent decision
        packet = agent.decide(obs)

        # Step environment
        obs, reward, done, info = env.step([packet['action_id']])  # actions must be in a list/array

        # Log step
        packet.update({
            "step": step_count,
            "episode": ep,
            "reward": float(reward[0]),   # reward is array due to DummyVecEnv
            "obs": obs[0].tolist()        # store numeric obs array
        })
        log_decision(packet, LOG_FILE)

        # Print step info
        print(f"Step {step_count}: RL Decision: {packet}")

        total_reward += reward[0]
        time.sleep(0.05)

    print(f"Episode {ep} finished. Total Reward: {total_reward}")

# ------------------------
# Read log and visualize
# ------------------------
episodes = {}
with open(LOG_FILE, "r") as f:
    for line in f:
        entry = json.loads(line)
        ep_num = entry["episode"]
        episodes.setdefault(ep_num, []).append(entry)

for ep_num, steps in episodes.items():
    rewards = [s["reward"] for s in steps]
    obs_values = [s["obs"] for s in steps]
    steps_list = [s["step"] for s in steps]

    plt.figure(figsize=(10, 4))
    # Plot each observation feature
    for i in range(len(obs_values[0])):
        plt.plot(steps_list, [o[i] for o in obs_values], label=f"Obs {i}")
    plt.plot(steps_list, rewards, label="Reward", marker='s')
    plt.title(f"Episode {ep_num} Performance")
    plt.xlabel("Step")
    plt.ylabel("Value")
    plt.ylim(0, 1.1)
    plt.legend()
    plt.grid(True)
    plt.show()
