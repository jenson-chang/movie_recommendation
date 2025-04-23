import numpy as np
import pandas as pd
import os
import logging
import time
import pickle
import tensorflow as tf
from typing import Optional
import pyarrow.parquet as pq
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"{func.__name__} took {duration:.2f} seconds to execute")
        return result
    return wrapper

def get_project_root():
    """Get the project root directory."""
    # In Docker, the app directory is mounted at /app
    if os.path.exists('/app'):
        logger.debug("Running in Docker container, using /app as root")
        return '/app'
    # For local development, use relative path
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logger.debug(f"Running locally, using {root} as root")
    return root

def load_model_data():
    """
    Load all necessary data for recommendations.
    Returns a dictionary of successfully loaded data.
    """
    logger.info("Starting to load model data")
    project_root = get_project_root()
    models_dir = os.path.join(project_root, 'models')
    logger.debug(f"Loading models from directory: {models_dir}")
    
    model_data = {}
    
    # Load NCF model
    try:
        model_path = os.path.join(models_dir, 'ncf_model.h5')
        logger.info(f"Attempting to load NCF model from {model_path}")
        model = tf.keras.models.load_model(model_path)
        model_data['ncf_model'] = model
        logger.info("NCF model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load NCF model from {model_path}: {str(e)}")
        raise RuntimeError("Failed to load NCF model")

    # Load NCF dataset mappings
    try:
        mappings_path = os.path.join(models_dir, 'ncf_dataset.pkl')
        logger.info(f"Attempting to load NCF dataset mappings from {mappings_path}")
        with open(mappings_path, 'rb') as f:
            mappings = pickle.load(f)
        model_data['ncf_mappings'] = mappings
        logger.info("NCF dataset mappings loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load NCF dataset mappings from {mappings_path}: {str(e)}")
        raise RuntimeError("Failed to load NCF dataset mappings")
    
    if not model_data:
        logger.error("No model data was successfully loaded")
        raise RuntimeError("Failed to load any model data")
    
    logger.info("Successfully loaded NCF model and mappings")
    return model_data

@timing_decorator
def get_user_recommendations(user_id, model_data, n=10, initial_movies=None):
    """
    Get NCF-based recommendations for a user.
    For new users, uses their initial movie selections to generate recommendations.
    
    Args:
        user_id: The user ID to get recommendations for
        model_data: Dictionary containing the loaded model and mappings
        n: Number of recommendations to return
        initial_movies: List of movie IDs that the user has selected (for new users)
    """
    logger.info(f"Getting NCF recommendations for user {user_id}")
    
    model = model_data['ncf_model']
    mappings = model_data['ncf_mappings']
    
    # Get all item IDs
    item_ids = list(mappings['item_mapping'].keys())
    
    # Check if user is new
    user_id_str = str(user_id)
    if user_id_str not in mappings['user_mapping']:
        if initial_movies is None or len(initial_movies) == 0:
            logger.error(f"New user {user_id} has no initial movie selections")
            return pd.DataFrame(columns=['movie_id'])
            
        logger.info(f"New user {user_id} detected, using initial movie selections")
        
        # Get embeddings for the initial movies
        initial_movie_indices = [mappings['item_mapping'][movie_id] for movie_id in initial_movies]
        initial_movie_embeddings = model.get_layer('item_embedding').get_weights()[0][initial_movie_indices]
        
        # Use the average of initial movie embeddings as the user embedding
        user_embedding = np.mean(initial_movie_embeddings, axis=0)
    else:
        user_idx = mappings['user_mapping'][user_id_str]
        user_embedding = model.get_layer('user_embedding').get_weights()[0][user_idx]
    
    # Get item embeddings
    item_indices = [mappings['item_mapping'][item_id] for item_id in item_ids]
    item_embeddings = model.get_layer('item_embedding').get_weights()[0][item_indices]
    
    # Make predictions
    predictions = model.predict([
        np.array([user_embedding] * len(item_ids)),
        item_embeddings
    ]).flatten()
    
    # Create DataFrame with predictions
    predictions_df = pd.DataFrame({
        'movie_id': item_ids,
        'prediction': predictions
    })
    
    # Remove movies the user has already rated or selected
    if 'current_ratings_df' in model_data:
        user_ratings = model_data['current_ratings_df'].loc[user_id_str] if user_id_str in model_data['current_ratings_df'].index else pd.DataFrame()
        if not user_ratings.empty:
            rated_movies = user_ratings['movie_id'].tolist()
            predictions_df = predictions_df[~predictions_df['movie_id'].isin(rated_movies)]
    
    # Remove initial movie selections from recommendations
    if initial_movies:
        predictions_df = predictions_df[~predictions_df['movie_id'].isin(initial_movies)]
    
    # Get top n predictions
    top_predictions = predictions_df.nlargest(n, 'prediction')[['movie_id']]
    logger.debug(f"Top {n} NCF recommendations for user {user_id}: {top_predictions['movie_id'].tolist()}")
    
    return top_predictions

@timing_decorator
def get_recommendations(user_id, model_data=None, n=10, initial_movies=None):
    """
    Get recommendations using the NCF model.
    Returns top n recommendations.
    
    Args:
        user_id: The user ID to get recommendations for
        model_data: Optional pre-loaded model data. If None, will load data.
        n: Number of recommendations to return
        initial_movies: List of movie IDs that the user has selected (for new users)
    """
    try:
        # Load model data only if not provided (outside timing)
        if model_data is None:
            logger.info("No cached model data provided, loading fresh data...")
            model_data = load_model_data()
        else:
            logger.info("Using cached model data for recommendations")
        
        # Get NCF recommendations
        recommendations = get_user_recommendations(user_id, model_data, n, initial_movies)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {str(e)}")
        return pd.DataFrame(columns=['movie_id'])