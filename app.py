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

def get_top_n_for_user(predictions, user_id, n=5):
    """
    Return the top-N recommendations for a given user from a set of predictions.

    Args:
        predictions (list of Prediction objects): The list of predictions, as returned by the test method of an algorithm.
        user_id (str or int): The user ID for whom to get recommendations.
        n (int): The number of recommendations to return. Default is 5.

    Returns:
        list or str: A sorted list of tuples [(item_id, estimated_rating), ...] of size n for the given user_id,
                     or a message if the user_id is not found.
    """

    # Filter predictions for the given user_id
    user_predictions = [(iid, est) for uid, iid, true_r, est, _ in predictions if uid == user_id]

    # If user_id is not found, return a message
    if not user_predictions:
        return f"User ID {user_id} not found in predictions."

    # Sort by estimated rating in descending order
    user_predictions.sort(key=lambda x: x[1], reverse=True)

    # Return top-N recommendations
    return user_predictions[:n]


with open("predictions.pkl", "rb") as file:
    predictions = pickle.load(file)

st.title("Movie Recommender System")

st.write("This app recommends movies based on your preferences.")

user_id = st.number_input("Enter your user ID", min_value=1, max_value=610, value=1)

if st.button("Get Recommendations"):
    recommendations = get_top_n_for_user(predictions, str(user_id))
    
    if isinstance(recommendations, str):
        st.write(recommendations)
    else:
        st.write("### Top 5 Movie Recommendations")
        
        # Create columns for the recommendations
        cols = st.columns(5)
        
        for idx, (movie_id, rating) in enumerate(recommendations):
            movie_details = fetch_movie_details(movie_id)
            
            with cols[idx]:
                if movie_details:
                    st.image(movie_details['poster_url'], caption=movie_details['title'])
                    st.write(f"**Rating:** {rating:.2f}")
                else:
                    st.write(f"Movie ID: {movie_id}")
                    st.write(f"Rating: {rating:.2f}")
