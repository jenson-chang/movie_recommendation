import pickle
import requests
import streamlit as st

# TMDb API configuration
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]  # Store your API key in Streamlit secrets
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def fetch_movie_details(movie_id):
    """
    Fetch movie details including poster path from TMDb API.
    """
    try:
        # First, search for the movie by ID
        search_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        response = requests.get(search_url, params={
            'api_key': TMDB_API_KEY,
        })
        response.raise_for_status()
        movie_data = response.json()
        
        if movie_data.get('poster_path'):
            poster_url = f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
            return {
                'title': movie_data['title'],
                'poster_url': poster_url
            }
        return None
    except Exception as e:
        st.error(f"Error fetching movie details: {str(e)}")
        return None

def get_top_n_for_user(predictions_dict, user_id, n=10):
    """
    Return the top-N recommendations for a given user from the predictions dictionary.

    Args:
        predictions_dict (dict): Dictionary containing predictions for all users.
        user_id (str or int): The user ID for whom to get recommendations.
        n (int): The number of recommendations to return. Default is 10.

    Returns:
        list or str: A sorted list of tuples [(item_id, estimated_rating), ...] of size n for the given user_id,
                     or a message if the user_id is not found.
    """
    # Convert user_id to string to match dictionary keys
    user_id = str(user_id)
    
    # If user_id is not found, return a message
    if user_id not in predictions_dict:
        return f"User ID {user_id} not found in predictions."
    
    # Get predictions for the user and sort by estimated rating
    user_predictions = predictions_dict[user_id]
    user_predictions.sort(key=lambda x: x[1], reverse=True)
    
    # Return top-N recommendations
    return user_predictions[:n]


with open("predictions_dict.pkl", "rb") as file:
    predictions_dict = pickle.load(file)

st.title("Movie Recommender System")

st.write("This app recommends movies based on your preferences.")

user_id = st.number_input("Enter your user ID", min_value=1, max_value=610, value=1)

if st.button("Get Recommendations"):
    recommendations = get_top_n_for_user(predictions_dict, str(user_id))
    
    if isinstance(recommendations, str):
        st.write(recommendations)
    else:
        if not recommendations:
            st.warning(f"No recommendations found for user ID {user_id}")
        else:
            st.write("### Top 5 Movie Recommendations")
            
            # Create dynamic columns based on number of recommendations
            num_cols = min(5, len(recommendations))  # Limit to 5 columns max
            cols = st.columns([1] * num_cols)
            
            for idx, (movie_id, rating) in enumerate(recommendations[:num_cols]):
                movie_details = fetch_movie_details(movie_id)
                
                with cols[idx]:
                    if movie_details:
                        st.image(movie_details['poster_url'], caption=movie_details['title'])
                        st.write(f"**Rating:** {rating:.2f}")
                    else:
                        st.write(f"Movie ID: {movie_id}")
                        st.write(f"Rating: {rating:.2f}")
