import numpy as np
import logging
from surprise import Dataset, SVD, Reader
import pandas as pd
import zipfile
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Load predictions from parquet
    predictions_df = pd.read_parquet('models/model.parquet')
    
    # Convert to numpy arrays for faster loading and querying
    user_ids = predictions_df['user_id'].values
    movie_ids = predictions_df['movie_id'].values
    estimated_ratings = predictions_df['estimated_rating'].values
    
    # Create a structured array for efficient storage and querying
    predictions_array = np.zeros(len(predictions_df), dtype=[
        ('user_id', 'U20'),  # String type for user_id
        ('movie_id', 'U20'),  # String type for movie_id
        ('estimated_rating', 'f8')  # Float64 for ratings
    ])
    
    predictions_array['user_id'] = user_ids
    predictions_array['movie_id'] = movie_ids
    predictions_array['estimated_rating'] = estimated_ratings
    
    # Create user_id to indices mapping for O(1) lookup
    user_id_to_indices = {}
    for i, uid in enumerate(user_ids):
        if uid not in user_id_to_indices:
            user_id_to_indices[uid] = []
        user_id_to_indices[uid].append(i)
    
    # Save both the predictions array and the mapping
    np.savez_compressed('models/model.npz', 
                       predictions=predictions_array,
                       user_id_to_indices=user_id_to_indices)
    
    logger.info("Successfully converted parquet to numpy format") 