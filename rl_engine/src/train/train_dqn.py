from stable_baselines3 import DQN
from stable_baselines3.common.monitor import Monitor
from src.env.tutor_env import TutorEnv
import os
import random

# Student ID in JSON
STUDENTS = ["S1", "S2", "S3", "S4", "S5"]


# =====================
# Create Environment
# =====================
env = TutorEnv()
env = Monitor(env)  # tracks reward statistics

# -------------------------
# Custom reset wrapper
# Ensures: every episode → random student
# -------------------------

original_reset = env.reset

def reset_with_random_student(_env):
    student_id = random.choice(STUDENTS)

    obs, info = original_reset(student_id=student_id)
    return obs,info


# Monkey-patch env.reset to inject student id
env.reset = lambda **kwargs: reset_with_random_student(env)

# =====================
# Configure DQN
# =====================
model = DQN(
    "MlpPolicy",
    env,
    learning_rate=1e-3,
    buffer_size=50000,
    learning_starts=1000,
    batch_size=64,
    tau=1.0,
    gamma=0.99,
    train_freq=4,
    target_update_interval=1000,
    exploration_fraction=0.4,      # ← more exploration
    exploration_final_eps=0.1,     # ← don’t stop exploring too soon
    verbose=1,
)

# =====================
# Train Model
# =====================
model.learn(total_timesteps=50000)   # ← longer training

# =====================
# Save Model
# =====================
os.makedirs("models", exist_ok=True)
model.save("models/ppo_model")

print("✅ Training complete — model saved.")
