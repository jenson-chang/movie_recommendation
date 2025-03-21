from fastapi import FastAPI, HTTPException
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pickle

app = FastAPI(
    title="Movie Recommendation API",
    description="API for movie recommendations using collaborative filtering",
    version="1.0.0"
)

def load_model(model_path: str = "model.pkl") -> Optional[object]:
    """Load the prediction model from pickle file."""
    try:
        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Model file {model_path} not found")
        
        with open(model_file, "rb") as file:
            return pickle.load(file)
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None

# Initialize model
model = load_model()

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
    
    Raises:
        HTTPException: If user_id is invalid or model is not loaded
    """
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if "user_id" not in data:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    user_id = data["user_id"]
    
    # Filter predictions for the given user_id
    user_predictions = [(iid, est) for uid, iid, true_r, est, _ in model if uid == user_id]

    # If user_id is not found, return error
    if not user_predictions:
        raise HTTPException(
            status_code=404,
            detail=f"User ID {user_id} not found in predictions"
        )

    # Sort by estimated rating in descending order
    user_predictions.sort(key=lambda x: x[1], reverse=True)

    # Return top-N recommendations
    return {"recommendations": user_predictions[:4]}