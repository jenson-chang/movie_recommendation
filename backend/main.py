import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from recommend import get_hybrid_recommendations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the application."""
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, n: int = 5):
    """
    Get movie recommendations for a specific user from both content-based and collaborative filtering models.
    
    Args:
        user_id (str): The user ID to get recommendations for
        n (int): Number of recommendations to return from each model (default: 5)
        
    Returns:
        dict: Dictionary containing recommendations from both models
    """
    try:
        # Get recommendations from both models
        recommendations = get_hybrid_recommendations(user_id, n=n)
        
        if recommendations['content_based'].empty and recommendations['collaborative'].empty:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for user {user_id}"
            )
            
        # Format the response
        formatted_recommendations = {
            "user_id": user_id,
            "content_based": [
                {"movie_id": str(movie_id)}
                for movie_id in recommendations['content_based']['movie_id']
            ],
            "collaborative": [
                {"movie_id": str(movie_id)}
                for movie_id in recommendations['collaborative']['movie_id']
            ]
        }
        
        return formatted_recommendations
        
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting recommendations: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}