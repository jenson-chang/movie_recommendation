from fastapi import FastAPI, HTTPException
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pickle
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Movie Recommendation API",
    description="API for movie recommendations using collaborative filtering",
    version="1.0.0"
)

def load_model(model_path: str = "models/preprocessed_model.pkl") -> Optional[Dict[int, List[Tuple[int, float]]]]:
    """Load the preprocessed model from pickle file."""
    try:
        model_file = Path(model_path)
        logger.info(f"Attempting to load model from {model_file.absolute()}")
        if not model_file.exists():
            logger.error(f"Model file {model_path} not found")
            raise FileNotFoundError(f"Model file {model_path} not found")
        
        with open(model_file, "rb") as file:
            model = pickle.load(file)
            logger.info(f"Model loaded successfully. Contains predictions for {len(model)} users")
            return model
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None

# Initialize model
model = load_model()
if model is None:
    logger.error("Failed to load model during initialization")
else:
    logger.info("Model initialized successfully")

@app.get("/")
async def read_root() -> Dict[str, str]:
    """Root endpoint returning welcome message."""
    return {"message": "Welcome to the movie recommendation API!"}

@app.post("/predict/")
async def predict_movies(data: Dict[str, int]) -> Dict[str, List[Tuple[int, float]]]:
    """
    Get movie recommendations for a specific user.
    
    Args:
        data: Dictionary containing user_id
    
    Returns:
        Dictionary containing list of recommended movies with their scores
    """
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if "user_id" not in data:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    user_id = data["user_id"]
    logger.info(f"Getting predictions for user {user_id}")
    
    try:
        # Get predictions for the user (already sorted by rating)
        user_predictions = model.get(user_id, [])
        
        logger.info(f"Found {len(user_predictions)} predictions for user {user_id}")
        
        # If user_id is not found, return error
        if not user_predictions:
            raise HTTPException(
                status_code=404,
                detail=f"User ID {user_id} not found in predictions"
            )
        
        # Return top-N recommendations (already sorted)
        recommendations = user_predictions[:5]
        logger.info(f"Returning top {len(recommendations)} recommendations: {recommendations}")
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error making predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error making predictions: {str(e)}")