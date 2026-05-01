# src/engine/rl_engine.py
import time
from stable_baselines3 import PPO
import numpy as np

class RLEngine:
    def __init__(self, model_path=None, env=None):
        if model_path:
            self.model = PPO.load(model_path, env=env)
        else:
            self.model = None

    def decide(self, observation):
        """
        observation is a numpy array from DummyVecEnv.
        Computes real softmax confidence from PPO policy distribution.
        """
        import torch
        import numpy as np

        action, _ = self.model.predict(observation, deterministic=False)

        # Derive real confidence from PPO policy's action distribution
        try:
            obs_tensor = torch.tensor(observation, dtype=torch.float32)
            if obs_tensor.ndim == 1:
                obs_tensor = obs_tensor.unsqueeze(0)
            
            with torch.no_grad():
                distribution = self.model.policy.get_distribution(obs_tensor)
                probs = distribution.distribution.probs  # shape: [1, n_actions]
                confidence = float(probs[0, int(action)].item())
        except Exception as e:
            print(f"[RL] Confidence extraction failed, defaulting to 0.5: {e}")
            confidence = 0.5

        return {
            "action_id": int(action),
            "confidence": round(confidence, 4),
            "timestamp": time.time()
        }
