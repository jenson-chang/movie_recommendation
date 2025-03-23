import numpy as np
import pandas as pd
import os

def get_project_root():
    """Get the project root directory."""
    # In Docker, the app directory is mounted at /app
    if os.path.exists('/app'):
        return '/app'
    # For local development, use relative path
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_model_data():
    """
    Load all necessary data for recommendations.
    """
    project_root = get_project_root()
    models_dir = os.path.join(project_root, 'models')
    
    collab_predictions_df = pd.read_parquet(os.path.join(models_dir, 'collab_predictions.parquet'))
    content_predictions_df = pd.read_parquet(os.path.join(models_dir, 'content_predictions.parquet'))
    
    # Convert IDs to strings
    collab_predictions_df['movie_id'] = collab_predictions_df['movie_id'].astype(str)
    collab_predictions_df['user_id'] = collab_predictions_df['user_id'].astype(str)
    content_predictions_df['movie_id'] = content_predictions_df['movie_id'].astype(str)
    content_predictions_df['user_id'] = content_predictions_df['user_id'].astype(str)
    
    return {
        'collab_predictions_df': collab_predictions_df,
        'content_predictions_df': content_predictions_df
    }

def get_user_content_recommendations(user_id, model_data, n=10):
    """Get content-based recommendations for a user"""
    # Get predictions for the user
    user_predictions = model_data['content_predictions_df'][
        model_data['content_predictions_df']['user_id'] == str(user_id)
    ]
    
    if user_predictions.empty:
        print("No content-based predictions found for user")
        return pd.DataFrame(columns=['movie_id'])
    
    # Sort by predicted rating and get top n recommendations
    top_predictions = user_predictions.nlargest(n, 'rating')
    
    return top_predictions[['movie_id']]

def get_user_collab_recommendations(user_id, model_data, n=5):
    """Get collaborative filtering recommendations for a user"""
    # Get predictions for the user
    user_predictions = model_data['collab_predictions_df'][
        model_data['collab_predictions_df']['user_id'] == str(user_id)
    ]
    
    if user_predictions.empty:
        print("No collaborative filtering predictions found for user")
        return pd.DataFrame(columns=['movie_id'])
    
    # Sort by predicted rating and get top n recommendations
    top_predictions = user_predictions.nlargest(n, 'rating')
    
    return top_predictions[['movie_id']]

def get_hybrid_recommendations(user_id, n=5):
    """
    Get top recommendations from both content-based and collaborative filtering models.
    Returns top 5 recommendations from each model separately.
    """
    # Load model data
    model_data = load_model_data()
    
    # Get recommendations from both models
    content_recs = get_user_content_recommendations(user_id, model_data, n=n)
    collab_recs = get_user_collab_recommendations(user_id, model_data, n=n)
    
    return {
        'content_based': content_recs,
        'collaborative': collab_recs
    }