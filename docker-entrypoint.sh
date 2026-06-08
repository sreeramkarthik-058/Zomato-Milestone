#!/bin/sh
set -e

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

# Start uvicorn with the resolved port
exec uvicorn src.restaurant_recommender.app.api:app --host 0.0.0.0 --port "$PORT"
