import pickle
from pathlib import Path
import logging
import re
from collections import defaultdict
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_prediction(pred_str):
    """Parse a prediction string into its components."""
    try:
        user_match = re.search(r'user: (\d+)', str(pred_str))
        item_match = re.search(r'item: (\d+)', str(pred_str))
        est_match = re.search(r'est = ([\d.]+)', str(pred_str))
        
        if user_match and item_match and est_match:
            user_id = int(user_match.group(1))
            item_id = int(float(item_match.group(1)))
            est = float(est_match.group(1))
            return user_id, item_id, est
        return None
    except Exception as e:
        logger.error(f"Error parsing prediction: {e}")
        return None

def preprocess_model():
    """Convert the model predictions into a more efficient format."""
    try:
        # Load the original model from zip file
        model_path = Path("models/model.zip")
        logger.info(f"Loading model from {model_path.absolute()}")
        
        with zipfile.ZipFile(model_path, 'r') as zip_ref:
            with zip_ref.open('model.pkl') as pkl_file:
                model = pickle.load(pkl_file)
        
        logger.info(f"Loaded original model with {len(model)} predictions")
        
        # Create a dictionary to store predictions by user
        user_predictions = defaultdict(list)
        
        # Process each prediction
        for pred in model:
            parsed = parse_prediction(pred)
            if parsed:
                user_id, movie_id, rating = parsed
                user_predictions[user_id].append((movie_id, rating))
        
        logger.info(f"Processed predictions for {len(user_predictions)} users")
        
        # Sort predictions for each user by rating
        for user_id in user_predictions:
            user_predictions[user_id].sort(key=lambda x: x[1], reverse=True)
        
        logger.info("Sorted all user predictions")
        
        # Convert defaultdict to regular dict for serialization
        preprocessed_model = dict(user_predictions)
        
        # Save the preprocessed model directly as pickle file
        output_path = Path("models/preprocessed_model.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(preprocessed_model, f)
        
        logger.info(f"Saved preprocessed model to {output_path.absolute()}")
        
    except Exception as e:
        logger.error(f"Error preprocessing model: {e}")
        raise

if __name__ == "__main__":
    preprocess_model() 