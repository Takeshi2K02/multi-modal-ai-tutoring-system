# src/engine/rl_engine.py
import time
from stable_baselines3 import DQN
import numpy as np

class RLEngine:
    def __init__(self, model_path=None, env=None):
        if model_path:
            self.model = DQN.load(model_path, env=env)
        else:
            self.model = None

    def decide(self, observation):
        """
        observation is a numpy array from DummyVecEnv
        """
        action, _ = self.model.predict(observation, deterministic=False)
        return {"action_id": int(action), 
        "confidence": 1.0, 
        "timestamp": time.time()}
