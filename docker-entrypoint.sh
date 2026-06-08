#!/bin/sh
set -e

exec uvicorn src.restaurant_recommender.app.api:app --host 0.0.0.0 --port 8000
