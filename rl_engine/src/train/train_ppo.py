from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from src.env.tutor_env import TutorEnv
import os
import random

# Student ID in JSON for randomization
STUDENTS = ["S1", "S2", "S3", "S4", "S5"]

print("--- Initializing RL Retraining: Project ID 25-26J-130 ---")

# =====================
# Create Environment
# =====================
env = TutorEnv()
env = Monitor(env)

original_reset = env.reset

def reset_with_random_student(_env):
    student_id = random.choice(STUDENTS)
    obs, info = original_reset(student_id=student_id)
    return obs, info

# Monkey-patch env.reset
env.reset = lambda **kwargs: reset_with_random_student(env)

# =====================
# Configure PPO
# =====================
# Switching to PPO for multi-dimensional stability (14-dim observation space)
model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    verbose=1,
)

# =====================
# Train Model
# =====================
print("Starting 100,000 timestep training phase...")
model.learn(total_timesteps=100000)

# =====================
# Save Model
# =====================
os.makedirs("models", exist_ok=True)
model.save("models/refined_pedagogical_policy")

print("\n✅ Training complete — system-centric policy saved as refined_pedagogical_policy.zip")
