import numpy as np
import pandas as pd

def load_model_data():
    """
    Load all necessary data for recommendations.
    """
    movies_df = pd.read_parquet('../backend/models/movies.parquet')
    ratings_df = pd.read_parquet('../backend/models/ratings.parquet')
    predictions_df = pd.read_parquet('../backend/models/predictions.parquet')
    
    # Convert IDs to strings
    movies_df['movie_id'] = movies_df['movie_id'].astype(str)
    ratings_df['movie_id'] = ratings_df['movie_id'].astype(str)
    ratings_df['user_id'] = ratings_df['user_id'].astype(str)
    predictions_df['movie_id'] = predictions_df['movie_id'].astype(str)
    predictions_df['user_id'] = predictions_df['user_id'].astype(str)
    
    return {
        'movies_df': movies_df,
        'ratings_df': ratings_df,
        'predictions_df': predictions_df,
        'cosine_sim': np.load('../backend/models/cosine_sim.npy')
    }

def get_user_content_recommendations(user_id, model_data, n=10):
    """Get content-based recommendations for a user"""
    # Convert user_id to string for consistent comparison
    user_id = str(user_id)
    
    # Get user ratings
    user_ratings = model_data['ratings_df'][model_data['ratings_df']['user_id'] == user_id]
    
    if len(user_ratings) == 0:
        print("No ratings found for user")
        return pd.DataFrame(columns=['movie_id', 'genres'])  # Return empty DataFrame with correct columns
    
    # Get user's favorite movies (rated >= 4)
    user_favorites = user_ratings[user_ratings['rating'] >= 4]['movie_id'].tolist()
    
    if not user_favorites:
        print("No favorite movies found")
        return pd.DataFrame(columns=['movie_id', 'genres'])
    
    # Initialize movie scores
    movie_scores = np.zeros(len(model_data['movies_df']))
    
    # Calculate scores based on favorites
    for fav_movie_id in user_favorites:
        fav_idx = model_data['movies_df'][model_data['movies_df']['movie_id'] == fav_movie_id].index
        if len(fav_idx) > 0:
            movie_scores += model_data['cosine_sim'][fav_idx[0]]
    
    # Zero out already rated movies
    rated_indices = model_data['movies_df'][model_data['movies_df']['movie_id'].isin(user_ratings['movie_id'])].index
    movie_scores[rated_indices] = 0
    
    # Get top N recommendations
    top_indices = movie_scores.argsort()[-n:][::-1]
    recommendations = model_data['movies_df'].iloc[top_indices][['movie_id', 'genres']]
    
    return recommendations

def get_user_collab_recommendations(user_id, model_data, n=5):
    """Get collaborative filtering recommendations for a user"""
    # Get predictions for the user
    user_predictions = model_data['predictions_df'][
        model_data['predictions_df']['user_id'] == str(user_id)
    ]
    
    if user_predictions.empty:
        return pd.DataFrame()
    
    # Sort by estimated rating and get top n
    top_predictions = user_predictions.nlargest(n, 'estimated_rating')
    
    # Get movie details
    recommendations = model_data['movies_df'][
        model_data['movies_df']['movie_id'].isin(top_predictions['movie_id'])
    ][['movie_id', 'genres']]
    
    return recommendations

def combine_recommendations(content_recs, collab_recs, model_data, content_weight=0.4, n=10):
    """
    Combine recommendations from content-based and collaborative filtering.
    
    Args:
        content_recs: Content-based recommendations DataFrame
        collab_recs: Collaborative filtering recommendations DataFrame
        model_data: Dictionary containing all model data including movies_df
        content_weight: Weight for content-based recommendations (default: 0.4)
        n: Number of final recommendations to return (default: 10)
    """
    # Create normalized scores for content-based recommendations
    content_scores = pd.Series(
        np.linspace(1, 0, len(content_recs)), 
        index=content_recs['movie_id']
    ) * content_weight
    
    # Create normalized scores for collaborative recommendations
    collab_scores = pd.Series(
        np.linspace(1, 0, len(collab_recs)), 
        index=collab_recs['movie_id']
    ) * (1 - content_weight)
    
    # Combine scores using pandas operations
    combined_scores = pd.concat([content_scores, collab_scores])
    combined_scores = combined_scores.groupby(level=0).sum()
    
    # Sort by score and get top n
    combined_scores = combined_scores.sort_values(ascending=False).head(n)
    
    # Get the movie details for the combined recommendations
    final_recommendations = model_data['movies_df'][model_data['movies_df']['movie_id'].isin(combined_scores.index)]
    final_recommendations = final_recommendations.merge(
        combined_scores.to_frame('score'), 
        left_on='movie_id', 
        right_index=True
    )
    final_recommendations = final_recommendations.sort_values('score', ascending=False)
    
    return final_recommendations[['movie_id', 'genres', 'score']]

def get_hybrid_recommendations(user_id, content_weight=0.4, n=5):
    """
    Get hybrid recommendations for a user with specified content weight.
    """
    # Load model data
    model_data = load_model_data()
    
    # Get recommendations from both models
    content_recs = get_user_content_recommendations(user_id, model_data, n=10)
    collab_recs = get_user_collab_recommendations(user_id, model_data, n=10)
    
    if content_recs.empty and collab_recs.empty:
        return pd.DataFrame()  # Return empty DataFrame if no recommendations available
    
    # Combine recommendations
    return combine_recommendations(content_recs, collab_recs, model_data, content_weight, n)