import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from recommend import get_hybrid_recommendations, get_user_top_rated_movies, load_model_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO level to hide debug messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration of the root logger
)
logger = logging.getLogger(__name__)

# Add a stream handler to ensure logs go to stdout/stderr
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)  # Set handler level to INFO to hide debug messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Global variable to store cached model data
cached_model_data = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the application."""
    global cached_model_data
    logger.info("Starting up...")
    try:
        logger.info("Loading model data during startup...")
        cached_model_data = load_model_data()
        logger.info("Successfully loaded and cached model data")
    except Exception as e:
        logger.error(f"Failed to load model data during startup: {e}")
        raise
    yield
    logger.info("Shutting down...")
    # Clear the cached data
    cached_model_data = None

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
async def get_recommendations(user_id: str, n: int = 10, content_weight: float = 0.5):
    """
    Get hybrid movie recommendations for a specific user, combining content-based and collaborative filtering models,
    along with their top rated movies.
    
    Args:
        user_id (str): The user ID to get recommendations for
        n (int): Number of recommendations to return (default: 10)
        content_weight (float): Weight for content-based recommendations (0 to 1, default: 0.5)
                              - 1.0: Only content-based
                              - 0.0: Only collaborative
                              - 0.5: Equal mix
        
    Returns:
        dict: Dictionary containing hybrid recommendations and top rated movies
    """
    try:
        if cached_model_data is None:
            raise HTTPException(
                status_code=503,
                detail="Model data not loaded. Service is initializing."
            )
        
        # Get hybrid recommendations using cached data
        recommendations = get_hybrid_recommendations(
            user_id, 
            model_data=cached_model_data, 
            n=n,
            content_weight=content_weight
        )
        
        # Get top rated movies
        top_rated = get_user_top_rated_movies(user_id, cached_model_data, n=n)
        
        if recommendations.empty and top_rated.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations or ratings found for user {user_id}"
            )
            
        # Format the response
        formatted_recommendations = {
            "user_id": user_id,
            "recommendations": [
                {"movie_id": str(movie_id)}
                for movie_id in recommendations['movie_id']
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

@app.get("/")
async def root():
    """Root endpoint for ALB health checks."""
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if cached_model_data is None:
        return {"status": "initializing"}
    return {"status": "healthy"}