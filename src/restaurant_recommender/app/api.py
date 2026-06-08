"""FastAPI REST API server for Epicurean Pulse / Chef AI recommendations."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from restaurant_recommender.orchestrator import RecommendationOrchestrator
from restaurant_recommender.models import UserPreferences, RecommendationResponse

app = FastAPI(
    title="Chef AI / Epicurean Pulse API",
    description="Backend API for recommending restaurants.",
    version="1.0.0"
)

# Enable CORS for React frontend (defaulting to localhost:5173, but open to any local host)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the orchestrator once
orchestrator = RecommendationOrchestrator()

@app.post("/api/recommend", response_model=RecommendationResponse)
def get_recommendations(preferences: UserPreferences):
    """
    Get recommended restaurants based on user preferences.
    """
    try:
        # Pre-load/run if needed (already handled inside recommend())
        response = orchestrator.recommend(preferences)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health_check():
    """Simple status check."""
    return {"status": "healthy", "service": "Chef AI"}
