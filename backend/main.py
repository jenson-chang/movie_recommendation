import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables to store model data
predictions = None
user_id_to_indices = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model data on startup and cleanup on shutdown."""
    global predictions, user_id_to_indices
    
    model_path = 'models/model.npz'
    if not os.path.exists(model_path):
        logger.error(f"Model file not found at {model_path}")
        raise RuntimeError(f"Model file not found at {model_path}")
        
    try:
        logger.info(f"Loading model from: {model_path}")
        loaded_data = np.load(model_path, allow_pickle=True)
        predictions = loaded_data['predictions']
        user_id_to_indices = loaded_data['user_id_to_indices'].item()
        logger.info("Successfully loaded model data")
    except Exception as e:
        logger.error(f"Error loading model data: {e}")
        raise RuntimeError(f"Failed to load model data: {str(e)}")
    
    yield
    
    # Cleanup (if needed) happens after the yield
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

def get_user_predictions(user_id, top_n=10):
    """
    Get top N predictions for a specific user.
    
    Args:
        user_id (str): The user ID to get predictions for
        top_n (int): Number of top predictions to return
        
    Returns:
        list: List of tuples (movie_id, estimated_rating) sorted by rating
    """
    try:
        # Get predictions for user (O(1) lookup)
        if user_id not in user_id_to_indices:
            logger.warning(f"No predictions found for user {user_id}")
            return []
            
        indices = user_id_to_indices[user_id]
        user_predictions = predictions[indices]
        
        # Sort by estimated rating and get top N
        sorted_predictions = np.sort(user_predictions, order='estimated_rating')[::-1][:top_n]
        
        # Convert to list of tuples (movie_id, estimated_rating)
        return [(pred['movie_id'], pred['estimated_rating']) for pred in sorted_predictions]
        
    except Exception as e:
        logger.error(f"Error getting predictions for user {user_id}: {e}")
        raise

@app.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, top_n: int = 5):
    """
    Get movie recommendations for a specific user.
    
    Args:
        user_id (str): The user ID to get recommendations for
        top_n (int): Number of recommendations to return (default: 5)
        
    Returns:
        dict: Dictionary containing recommendations
    """
    try:
        # Get predictions using the new function
        predictions = get_user_predictions(user_id, top_n)
        
        if not predictions:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for user {user_id}"
            )
            
        # Format the response
        recommendations = [
            {
                "movie_id": movie_id,
                "estimated_rating": float(rating)
            }
            for movie_id, rating in predictions
        ]
        
        return {
            "user_id": user_id,
            "recommendations": recommendations
        }
        
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