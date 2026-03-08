#!/bin/bash
# Clear port 8000 if it's already in use
lsof -t -i:8000 | xargs kill -9 2>/dev/null || true

# Activate the virtual environment and start the server
source venv/bin/activate
uvicorn server:app --reload --port 8000
