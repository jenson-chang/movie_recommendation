import numpy as np
import pandas as pd
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

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
    """
    logger.info("Starting to load model data")
    project_root = get_project_root()
    models_dir = os.path.join(project_root, 'models')
    logger.debug(f"Loading models from directory: {models_dir}")
    
    model_data = {}
    
    # Load collaborative predictions
    try:
        collab_path = os.path.join(models_dir, 'collab_predictions.parquet')
        logger.info(f"Attempting to load collaborative predictions from {collab_path}")
        collab_predictions_df = pd.read_parquet(collab_path)
        logger.info(f"Successfully loaded collaborative predictions with shape: {collab_predictions_df.shape}")
        model_data['collab_predictions_df'] = collab_predictions_df
        logger.info("Collaborative predictions loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load collaborative predictions from {collab_path}: {str(e)}")
        raise

    # Load content predictions
    try:
        content_path = os.path.join(models_dir, 'content_predictions.parquet')
        logger.info(f"Attempting to load content predictions from {content_path}")
        content_predictions_df = pd.read_parquet(content_path)
        logger.info(f"Successfully loaded content predictions with shape: {content_predictions_df.shape}")
        model_data['content_predictions_df'] = content_predictions_df
        logger.info("Content predictions loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load content predictions from {content_path}: {str(e)}")
        raise

    # Load current ratings
    try:
        ratings_path = os.path.join(models_dir, 'current_ratings.parquet')
        logger.info(f"Attempting to load current ratings from {ratings_path}")
        current_ratings_df = pd.read_parquet(ratings_path)
        logger.info(f"Successfully loaded current ratings with shape: {current_ratings_df.shape}")
        model_data['current_ratings_df'] = current_ratings_df
        logger.info("Current ratings loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load current ratings from {ratings_path}: {str(e)}")
        raise
    
    # Convert IDs to strings
    try:
        logger.info("Starting ID conversion to strings")
        for df_name in ['collab_predictions_df', 'content_predictions_df', 'current_ratings_df']:
            logger.info(f"Converting IDs to strings for {df_name}")
            df = model_data[df_name]
            df['movie_id'] = df['movie_id'].astype(str)
            df['user_id'] = df['user_id'].astype(str)
        logger.info("Successfully converted all IDs to strings")
    except Exception as e:
        logger.error(f"Failed to convert IDs to strings: {str(e)}")
        raise
    
    logger.info("All model data successfully loaded and processed")
    return model_data

def get_user_content_recommendations(user_id, model_data, n=10):
    """Get content-based recommendations for a user"""
    logger.info(f"Getting content-based recommendations for user {user_id}")
    # Get predictions for the user
    user_predictions = model_data['content_predictions_df'][
        model_data['content_predictions_df']['user_id'] == str(user_id)
    ]
    
    if user_predictions.empty:
        logger.info(f"No content-based predictions found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    logger.debug(f"Found {len(user_predictions)} predictions for user {user_id}")
    
    # Sort by predicted rating and get top n recommendations
    top_predictions = user_predictions.nlargest(n, 'rating')
    logger.debug(f"Top {n} content-based recommendations for user {user_id}: {top_predictions['movie_id'].tolist()}")
    
    return top_predictions[['movie_id']]

def get_user_collab_recommendations(user_id, model_data, n=5):
    """Get collaborative filtering recommendations for a user"""
    logger.info(f"Getting collaborative filtering recommendations for user {user_id}")
    # Get predictions for the user
    user_predictions = model_data['collab_predictions_df'][
        model_data['collab_predictions_df']['user_id'] == str(user_id)
    ]
    
    if user_predictions.empty:
        logger.info(f"No collaborative filtering predictions found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    logger.debug(f"Found {len(user_predictions)} predictions for user {user_id}")
    
    # Sort by predicted rating and get top n recommendations
    top_predictions = user_predictions.nlargest(n, 'rating')
    logger.debug(f"Top {n} collaborative recommendations for user {user_id}: {top_predictions['movie_id'].tolist()}")
    
    return top_predictions[['movie_id']]

def get_user_top_rated_movies(user_id, model_data, n=5):
    """
    Get the top n highest rated movies for a given user from their current ratings.
    """
    logger.info(f"Getting top {n} rated movies for user {user_id}")
    # Get ratings for the user
    user_ratings = model_data['current_ratings_df'][
        model_data['current_ratings_df']['user_id'] == str(user_id)
    ]
    
    if user_ratings.empty:
        logger.info(f"No ratings found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    logger.debug(f"Found {len(user_ratings)} ratings for user {user_id}")
    
    # Sort by rating and get top n movies
    top_rated = user_ratings.nlargest(n, 'rating')
    logger.debug(f"Top {n} rated movies for user {user_id}: {top_rated['movie_id'].tolist()}")
    
    return top_rated[['movie_id']]

def get_hybrid_recommendations(user_id, n=5):
    """
    Get top recommendations from both content-based and collaborative filtering models.
    Returns top 5 recommendations from each model separately.
    """
    logger.info(f"Starting hybrid recommendations for user {user_id}")
    try:
        # Load model data
        model_data = load_model_data()
        
        # Get recommendations from both models
        content_recs = get_user_content_recommendations(user_id, model_data, n=n)
        collab_recs = get_user_collab_recommendations(user_id, model_data, n=n)
        
        logger.debug(f"Content-based recommendations count: {len(content_recs)}")
        logger.debug(f"Collaborative recommendations count: {len(collab_recs)}")
        
        return {
            'content_based': content_recs,
            'collaborative': collab_recs
        }
    except Exception as e:
        logger.error(f"Error in hybrid recommendations for user {user_id}: {str(e)}")
        raise