from src.env.tutor_env import TutorEnv
from src.engine.rl_engine import RLEngine
from src.utils.logger import log_decision
import time
import os
from datetime import datetime

BASE_DIR_RL = os.path.dirname(os.path.abspath(__file__))
env = TutorEnv()
engine = RLEngine(os.path.join(BASE_DIR_RL, "models/dqn_model"))

# print(">>> RL Engine Live Stream Active [Looping every 5s]...")

while True:
    student_id = "alex_123"  # Target student for live monitoring
    env.sync_with_db(student_id)
    obs, _ = env.reset(student_id=student_id)
    packet = engine.decide(obs)

    # print(f"[{datetime.now().strftime('%H:%M:%S')}] RL Decision: {packet['action_id']} for {student_id}")
    log_decision(packet)

    # Broadcast to Agentic AI Core (Live Telemetry Hub)
    try:
        import requests
        requests.post("http://localhost:8000/api/telemetry/rl", json={
            "user_id": student_id,
            "action_id": packet["action_id"],
            "confidence": packet["confidence"],
            "reasoning": f"Live DQN inference loop. Sync active."
        }, timeout=0.5)
    except Exception as e:
        # print(f"Telemetry Broadcast Error: {e}")
        pass
    
    time.sleep(3) # Faster loop for responsiveness

