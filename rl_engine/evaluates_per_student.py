import time
from src.env.tutor_env import TutorEnv
from stable_baselines3 import PPO

STUDENTS = ["S1", "S2", "S3", "S4", "S5"]

# -----------------------------
# Load personalized RL model
# -----------------------------
model = PPO.load("models/ppo_model")

# -----------------------------
# Evaluate each student separately
# -----------------------------
for student_id in STUDENTS:
    print("\n==============================")
    print(f" Evaluating student: {student_id}")
    print("==============================")

    env = TutorEnv()

    obs, _ = env.reset(student_id=student_id)

    total_reward = 0

    for step in range(30):   # run one session
        action, _ = model.predict(obs, deterministic=True)

        obs, reward, done, truncated, info = env.step(int(action))
        total_reward += reward

        print(
            f"Step {step+1:02d} | "
            f"Action = {int(action)} | "
            f"Attention={env.state['attention']:.2f} "
            f"Confusion={env.state['confusion']:.2f} "
            f"Boredom={env.state['boredom']:.2f} "
            f"Acc={env.state['recent_acc']:.2f} "
            f"Reward={reward:.3f}"
        )

        if done:
            break

    print(f"→ Total reward for {student_id}: {total_reward:.3f}")