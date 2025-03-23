import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from recommend import get_hybrid_recommendations, get_user_top_rated_movies, load_model_data

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
    Get movie recommendations for a specific user from both content-based and collaborative filtering models,
    along with their top rated movies.
    
    Args:
        user_id (str): The user ID to get recommendations for
        n (int): Number of recommendations to return from each model (default: 5)
        
    Returns:
        dict: Dictionary containing recommendations from both models and top rated movies
    """
    try:
        # Load model data
        model_data = load_model_data()
        
        # Get recommendations from both models
        recommendations = get_hybrid_recommendations(user_id, n=n)
        
        # Get top rated movies
        top_rated = get_user_top_rated_movies(user_id, model_data, n=n)
        
        if recommendations['content_based'].empty and recommendations['collaborative'].empty and top_rated.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations or ratings found for user {user_id}"
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
            ],
            "top_rated": [
                {"movie_id": str(movie_id)}
                for movie_id in top_rated['movie_id']
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