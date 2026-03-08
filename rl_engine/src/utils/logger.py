# src/utils/logger.py
import json
import os

def log_decision(packet, path="logs/rl_decisions.jsonl"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(packet) + "\n")
