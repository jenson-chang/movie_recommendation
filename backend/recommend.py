import numpy as np
import pandas as pd
import os
import logging
import time
from typing import Optional
import pyarrow.parquet as pq
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from sklearn.linear_model import Ridge

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

def load_parquet_with_retry(file_path: str, max_retries: int = 3, chunk_size: Optional[int] = None) -> pd.DataFrame:
    """
    Load a parquet file with retry logic and optional chunked reading.
    
    Args:
        file_path: Path to the parquet file
        max_retries: Maximum number of retry attempts
        chunk_size: If provided, read the file in chunks of this size
    
    Returns:
        pd.DataFrame: Loaded dataframe
    """
    for attempt in range(max_retries):
        try:
            if chunk_size:
                # Read the file in chunks using pyarrow
                table = pq.read_table(file_path)
                num_rows = len(table)
                chunks = []
                
                for start in range(0, num_rows, chunk_size):
                    end = min(start + chunk_size, num_rows)
                    chunk = table.slice(start, end - start)
                    chunk_df = chunk.to_pandas()
                    chunks.append(chunk_df)
                
                return pd.concat(chunks, ignore_index=True)
            else:
                return pd.read_parquet(file_path)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed to load {file_path}: {str(e)}")
            time.sleep(2 ** attempt)  # Exponential backoff

def load_model_data():
    """
    Load all necessary data for recommendations.
    Returns a dictionary of successfully loaded dataframes.
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
        collab_predictions_df = load_parquet_with_retry(collab_path)
        logger.info(f"Successfully loaded collaborative predictions with shape: {collab_predictions_df.shape}")
        # Convert IDs to strings and create index for faster lookups
        collab_predictions_df['movie_id'] = collab_predictions_df['movie_id'].astype(str)
        collab_predictions_df['user_id'] = collab_predictions_df['user_id'].astype(str)
        collab_predictions_df.set_index('user_id', inplace=True)
        model_data['collab_predictions_df'] = collab_predictions_df
        logger.info("Collaborative predictions loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load collaborative predictions from {collab_path}: {str(e)}")
        logger.warning("Continuing with remaining files despite collaborative predictions failure")

    # Load content predictions with chunked reading
    try:
        content_path = os.path.join(models_dir, 'content_predictions.parquet')
        logger.info(f"Attempting to load content predictions from {content_path}")
        # Use chunked reading with a reasonable chunk size
        content_predictions_df = load_parquet_with_retry(content_path, chunk_size=100000)
        logger.info(f"Successfully loaded content predictions with shape: {content_predictions_df.shape}")
        # Convert IDs to strings and create index for faster lookups
        content_predictions_df['movie_id'] = content_predictions_df['movie_id'].astype(str)
        content_predictions_df['user_id'] = content_predictions_df['user_id'].astype(str)
        content_predictions_df.set_index('user_id', inplace=True)
        model_data['content_predictions_df'] = content_predictions_df
        logger.info("Content predictions loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load content predictions from {content_path}: {str(e)}")
        logger.warning("Continuing with remaining files despite content predictions failure")

    # Load current ratings
    try:
        ratings_path = os.path.join(models_dir, 'current_ratings.parquet')
        logger.info(f"Attempting to load current ratings from {ratings_path}")
        current_ratings_df = load_parquet_with_retry(ratings_path)
        logger.info(f"Successfully loaded current ratings with shape: {current_ratings_df.shape}")
        # Convert IDs to strings and create index for faster lookups
        current_ratings_df['movie_id'] = current_ratings_df['movie_id'].astype(str)
        current_ratings_df['user_id'] = current_ratings_df['user_id'].astype(str)
        current_ratings_df.set_index('user_id', inplace=True)
        model_data['current_ratings_df'] = current_ratings_df
        logger.info("Current ratings loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load current ratings from {ratings_path}: {str(e)}")
        logger.warning("Continuing with remaining files despite current ratings failure")

    # Load genre data
    try:
        genre_path = os.path.join(models_dir, 'movie_genres.parquet')
        logger.info(f"Attempting to load genre data from {genre_path}")
        genre_df = load_parquet_with_retry(genre_path)
        logger.info(f"Successfully loaded genre data with shape: {genre_df.shape}")
        # Convert index to strings for consistency
        genre_df.index = genre_df.index.astype(str)
        model_data['genre_df'] = genre_df
        logger.info("Genre data loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load genre data from {genre_path}: {str(e)}")
        logger.warning("Continuing with remaining files despite genre data failure")

    # Load top 100 movies
    try:
        top_100_path = os.path.join(models_dir, 'top_100_movies.parquet')
        logger.info(f"Attempting to load top 100 movies from {top_100_path}")
        top_100_df = load_parquet_with_retry(top_100_path)
        logger.info(f"Successfully loaded top 100 movies with shape: {top_100_df.shape}")
        # Convert movie_id to strings for consistency
        top_100_df['movie_id'] = top_100_df['movie_id'].astype(str)
        model_data['top_100_df'] = top_100_df
        logger.info("Top 100 movies loaded and stored in model_data")
    except Exception as e:
        logger.error(f"Failed to load top 100 movies from {top_100_path}: {str(e)}")
        logger.warning("Continuing with remaining files despite top 100 movies failure")
    
    if not model_data:
        logger.error("No model data was successfully loaded")
        raise RuntimeError("Failed to load any model data")
    
    logger.info(f"Successfully loaded {len(model_data)} out of 5 data files")
    return model_data

@timing_decorator
def get_user_content_recommendations(user_id, model_data, n=10):
    """
    Get content-based recommendations for a user.
    
    Args:
        user_id: The user ID to get recommendations for
        model_data: Dictionary containing loaded model data
        n: Number of recommendations to return
    
    Returns:
        pd.DataFrame: DataFrame with a single 'movie_id' column containing the top N recommended movie IDs
    """
    logger.info(f"Getting content-based recommendations for user {user_id}")
    
    # Check if content predictions are available
    if 'content_predictions_df' not in model_data:
        logger.warning("Content predictions not available, returning empty recommendations")
        return pd.DataFrame(columns=['movie_id'])
    
    # Get predictions for the user using index lookup
    user_id_str = str(user_id)
    if user_id_str not in model_data['content_predictions_df'].index:
        logger.info(f"No content-based predictions found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    user_predictions = model_data['content_predictions_df'].loc[user_id_str]
    
    if user_predictions.empty:
        logger.info(f"No content-based predictions found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    logger.debug(f"Found {len(user_predictions)} predictions for user {user_id}")
    
    # Use nlargest with vectorized operations
    top_predictions = user_predictions.nlargest(n, 'rating')[['movie_id']]
    logger.debug(f"Top {n} content-based recommendations for user {user_id}: {top_predictions['movie_id'].tolist()}")
    
    return top_predictions

@timing_decorator
def get_user_collab_recommendations(user_id, model_data, n=5):
    """
    Get collaborative filtering recommendations for a user.
    
    Args:
        user_id: The user ID to get recommendations for
        model_data: Dictionary containing loaded model data
        n: Number of recommendations to return
    
    Returns:
        pd.DataFrame: DataFrame with a single 'movie_id' column containing the top N recommended movie IDs
    """
    logger.info(f"Getting collaborative filtering recommendations for user {user_id}")
    
    # Check if collaborative predictions are available
    if 'collab_predictions_df' not in model_data:
        logger.warning("Collaborative predictions not available, returning empty recommendations")
        return pd.DataFrame(columns=['movie_id'])
    
    # Get predictions for the user using index lookup
    user_id_str = str(user_id)
    if user_id_str not in model_data['collab_predictions_df'].index:
        logger.info(f"No collaborative filtering predictions found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    user_predictions = model_data['collab_predictions_df'].loc[user_id_str]
    
    if user_predictions.empty:
        logger.info(f"No collaborative filtering predictions found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    logger.debug(f"Found {len(user_predictions)} predictions for user {user_id}")
    
    # Use nlargest with vectorized operations
    top_predictions = user_predictions.nlargest(n, 'rating')[['movie_id']]
    logger.debug(f"Top {n} collaborative recommendations for user {user_id}: {top_predictions['movie_id'].tolist()}")
    
    return top_predictions

@timing_decorator
def get_user_top_rated_movies(user_id, model_data, n=5):
    """
    Get the top n highest rated movies for a given user from their current ratings.
    
    Args:
        user_id: The user ID to get top rated movies for
        model_data: Dictionary containing loaded model data
        n: Number of movies to return
    
    Returns:
        pd.DataFrame: DataFrame with a single 'movie_id' column containing the top N rated movie IDs
    """
    logger.info(f"Getting top {n} rated movies for user {user_id}")
    
    # Check if current ratings are available
    if 'current_ratings_df' not in model_data:
        logger.warning("Current ratings not available, returning empty recommendations")
        return pd.DataFrame(columns=['movie_id'])
    
    # Get ratings for the user using index lookup
    user_id_str = str(user_id)
    if user_id_str not in model_data['current_ratings_df'].index:
        logger.info(f"No ratings found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    user_ratings = model_data['current_ratings_df'].loc[user_id_str]
    
    if user_ratings.empty:
        logger.info(f"No ratings found for user {user_id}")
        return pd.DataFrame(columns=['movie_id'])
    
    logger.debug(f"Found {len(user_ratings)} ratings for user {user_id}")
    
    # Use nlargest with vectorized operations
    top_rated = user_ratings.nlargest(n, 'rating')[['movie_id']]
    logger.debug(f"Top {n} rated movies for user {user_id}: {top_rated['movie_id'].tolist()}")
    
    return top_rated

@timing_decorator
def get_hybrid_recommendations(user_id, model_data=None, n=10, content_weight=0.5):
    """
    Get hybrid recommendations by combining content-based and collaborative filtering models.
    Uses a weight parameter to control the influence of each model.
    
    Args:
        user_id: The user ID to get recommendations for
        model_data: Optional pre-loaded model data. If None, will load data
        n: Number of final recommendations to return
        content_weight: Weight for content-based recommendations (0 to 1)
                       - 1.0: Only content-based
                       - 0.0: Only collaborative
                       - 0.5: Equal mix (default)
    
    Returns:
        pd.DataFrame: DataFrame with a single 'movie_id' column containing the top N recommended movie IDs
    """
    try:
        # Load model data only if not provided (outside timing)
        if model_data is None:
            logger.info("No cached model data provided, loading fresh data...")
            model_data = load_model_data()
        else:
            logger.info("Using cached model data for hybrid recommendations")
        
        # Get recommendations from both models
        with ThreadPoolExecutor(max_workers=2) as executor:
            content_future = executor.submit(get_user_content_recommendations, user_id, model_data, n)
            collab_future = executor.submit(get_user_collab_recommendations, user_id, model_data, n)
            
            # Get results
            content_recs = content_future.result()
            collab_recs = collab_future.result()
        
        # If either model returned no recommendations, return empty DataFrame
        if content_recs.empty and collab_recs.empty:
            logger.warning(f"No recommendations found for user {user_id}")
            return pd.DataFrame(columns=['movie_id'])
        
        # Combine recommendations
        combined_recs = pd.DataFrame()
        
        # Process content-based recommendations
        if not content_recs.empty:
            # Get the full predictions for the user to access ratings
            user_content_predictions = model_data['content_predictions_df'].loc[str(user_id)]
            content_recs = content_recs.merge(
                user_content_predictions[['movie_id', 'rating']],
                on='movie_id',
                how='left'
            )
            content_recs['score'] = content_recs['rating'] * content_weight
            combined_recs = pd.concat([combined_recs, content_recs])
        
        # Process collaborative recommendations
        if not collab_recs.empty:
            # Get the full predictions for the user to access ratings
            user_collab_predictions = model_data['collab_predictions_df'].loc[str(user_id)]
            collab_recs = collab_recs.merge(
                user_collab_predictions[['movie_id', 'rating']],
                on='movie_id',
                how='left'
            )
            collab_recs['score'] = collab_recs['rating'] * (1 - content_weight)
            combined_recs = pd.concat([combined_recs, collab_recs])
        
        # Group by movie_id and sum the scores
        combined_recs = combined_recs.groupby('movie_id')['score'].sum().reset_index()
        
        # Get top N recommendations
        top_recs = combined_recs.nlargest(n, 'score')[['movie_id']]
        
        logger.info(f"Generated {len(top_recs)} hybrid recommendations for user {user_id}")
        return top_recs
        
    except Exception as e:
        logger.error(f"Error in hybrid recommendations for user {user_id}: {str(e)}")
        return pd.DataFrame(columns=['movie_id'])

def get_cold_start_recommendations(movies_list, model_data, n=5):
    """
    Get recommendations for a new user based on their liked movies using genre-based content filtering.
    
    Args:
        movies_list: List of movie IDs that the new user has liked
        model_data: Dictionary containing loaded model data
        n: Number of recommendations to return
    
    Returns:
        pd.DataFrame: DataFrame with a single 'movie_id' column containing the top N recommended movie IDs
    """
    try:
        logger.info(f"Getting cold-start recommendations for {len(movies_list)} liked movies")
        
        # Load genre data if not already loaded
        if 'genre_df' not in model_data:
            try:
                genre_path = os.path.join(get_project_root(), 'models', 'movie_genres.parquet')
                logger.info(f"Loading genre data from {genre_path}")
                genre_df = load_parquet_with_retry(genre_path)
                model_data['genre_df'] = genre_df
            except Exception as e:
                logger.error(f"Failed to load genre data: {str(e)}")
                return pd.DataFrame(columns=['movie_id'])
        
        genre_df = model_data['genre_df']
        
        # Convert movie IDs to strings for consistency
        movies = [str(movie_id) for movie_id in movies_list]
        
        # Check if all movies exist in genre data
        valid_movies = [movie_id for movie_id in movies if movie_id in genre_df.index]
        if not valid_movies:
            logger.warning("No valid movies found in genre data")
            return pd.DataFrame(columns=['movie_id'])
        
        # Get genre features for the liked movies
        X_train = genre_df.loc[valid_movies].values
        y_train = np.full(len(valid_movies), 5.0)  # Assume high rating for liked movies
        
        # Train Ridge model for the new user
        new_user_model = Ridge(alpha=1.0)
        new_user_model.fit(X_train, y_train)
        
        # Predict ratings for all movies the user hasn't rated
        unseen_movie_ids = genre_df.index.difference(valid_movies)
        X_test = genre_df.loc[unseen_movie_ids].values
        predicted_ratings = new_user_model.predict(X_test)
        
        # Create recommendations DataFrame
        recommendations = pd.DataFrame({
            'movie_id': unseen_movie_ids,
            'rating': predicted_ratings
        })
        
        # Get top N recommendations
        top_recs = recommendations.nlargest(n, 'rating')[['movie_id']]
        
        logger.info(f"Generated {len(top_recs)} cold-start recommendations")
        return top_recs
        
    except Exception as e:
        logger.error(f"Error in cold-start recommendations: {str(e)}")
        return pd.DataFrame(columns=['movie_id'])

@timing_decorator
def get_cold_start_movies(model_data, n=20):
    """
    Get n random movies from the top 100 movies list for cold-start recommendations.
    
    Args:
        model_data: Dictionary containing loaded model data
        n: Number of random movies to return (default: 20)
    
    Returns:
        pd.DataFrame: DataFrame with a single 'movie_id' column containing n random movie IDs from top 100
    """
    try:
        logger.info(f"Getting {n} random movies from top 100 for cold-start recommendations")
        
        # Check if top 100 movies are available
        if 'top_100_df' not in model_data:
            logger.warning("Top 100 movies not available, returning empty recommendations")
            return pd.DataFrame(columns=['movie_id'])
        
        top_100_df = model_data['top_100_df']
        
        if top_100_df.empty:
            logger.warning("Top 100 movies DataFrame is empty")
            return pd.DataFrame(columns=['movie_id'])
        
        # Get n random movies from top 100
        random_movies = top_100_df.sample(n=min(n, len(top_100_df)), random_state=42)[['movie_id']]
        
        logger.info(f"Selected {len(random_movies)} random movies from top 100")
        return random_movies
        
    except Exception as e:
        logger.error(f"Error getting cold-start movies: {str(e)}")
        return pd.DataFrame(columns=['movie_id'])