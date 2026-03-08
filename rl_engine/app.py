import streamlit as st
import json
import time

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Adaptive RL Tutor – Prototype",
    layout="centered"
)

st.title("Adaptive Learning Decision Engine")
st.subheader("PP1 Prototype – Reinforcement Learning Component")

st.markdown("---")

# -----------------------------
# Load latest RL decision
# -----------------------------
LOG_PATH = "logs/rl_decisions.jsonl"

def load_latest_decision():
    try:
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            if not lines:
                return None
            return json.loads(lines[-1])
    except FileNotFoundError:
        return None

packet = load_latest_decision()

# -----------------------------
# Simulated learner state
# -----------------------------
st.header("Learner State (Input to RL Engine)")

if packet:
    obs = packet["obs"]

    st.write(f"**Attention Level:** {obs[0]:.2f}")
    st.write(f"**Confusion Level:** {obs[2]:.2f}")
    st.write(f"**Boredom Level:** {obs[3]:.2f}")
    st.write(f"**Recent Accuracy:** {obs[5]:.2f}")
    st.write(f"**Time on Task:** {obs[6]*60:.1f} seconds")

    st.caption("Learner data is currently simulated for prototype purposes.")
else:
    st.warning("No RL decisions found yet.")

st.markdown("---")

# -----------------------------
# RL Engine Output
# -----------------------------
st.header("RL Engine Decision Output")

ACTION_MAP = {
    0: "Hint",
    1: "Worked Example",
    2: "Interactive Quiz",
    3: "Challenge Question",
    4: "Encouragement",
    5: "Learning Modality Shift"
}

if packet:
    action_id = packet["action_id"]
    st.success(f"**Selected Teaching Strategy:** {ACTION_MAP[action_id]}")
    st.write(f"**Action ID:** {action_id}")
    st.write(f"**Confidence Score:** {packet['confidence']:.2f}")
    st.write(f"**Internal Reward:** {packet['reward']:.3f}")
else:
    st.info("Run the RL evaluation to generate decisions.")

st.markdown("---")

