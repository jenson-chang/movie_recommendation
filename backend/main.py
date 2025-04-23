import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .recommend import get_recommendations, load_model_data

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
async def get_recommendations_endpoint(user_id: str, n: int = 10, initial_movies: list[str] = None):
    """
    Get movie recommendations for a user.
    For new users, uses their initial movie selections to generate recommendations.
    
    Args:
        user_id (str): The user ID to get recommendations for
        n (int): Number of recommendations to return (default: 10)
        initial_movies (list[str]): Optional list of movie IDs that the user has liked (for new users)
        
    Returns:
        dict: Dictionary containing recommendations
    """
    try:
        if cached_model_data is None:
            raise HTTPException(
                status_code=503,
                detail="Model data not loaded. Service is initializing."
            )
        
        # Get recommendations using cached data
        recommendations_df = get_recommendations(
            user_id, 
            model_data=cached_model_data, 
            n=n,
            initial_movies=initial_movies
        )
            
        # Format the response
        formatted_recommendations = {
            "user_id": user_id,
            "recommendations": [
                {"movie_id": str(movie_id)}
                for movie_id in recommendations_df['movie_id']
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
    """Health check endpoint."""
    if cached_model_data is None:
        return {"status": "initializing"}
    return {"status": "healthy"}