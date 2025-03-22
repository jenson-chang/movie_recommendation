import requests
import streamlit as st
import os

# TMDb API configuration
try:
    # Try to get API key from environment variable (production)
    TMDB_API_KEY = os.environ["TMDB_API_KEY"]
except KeyError:
    # Fall back to Streamlit secrets (local development)
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]

TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Configure backend URL based on environment
try:
    # Try to get backend URL from environment variable (production)
    BACKEND_URL = os.environ["REACT_APP_API_URL"]
except KeyError:
    # Fall back to local Docker service name
    BACKEND_URL = "http://backend:8000"

# Add sidebar with product case study information
st.sidebar.title("Product Case Study")

st.sidebar.header("Problem")
st.sidebar.write("""
- Users struggle to find movies they might enjoy in vast streaming catalogs
- Traditional recommendation systems often lack personalization
- Time wasted browsing through irrelevant content
""")

st.sidebar.header("Solution")
st.sidebar.write("""
- Personalized movie recommendation system
- Leverages collaborative filtering to understand user preferences
- Integration with TMDb API for rich movie metadata
- User-friendly interface with visual movie posters and details
""")

st.sidebar.header("AI Model Used")
st.sidebar.write("""
- Collaborative Filtering using Matrix Factorization
- Predicts user preferences based on historical ratings
- Identifies patterns in user-movie interactions
- Scalable solution that improves with more user data
""")

st.sidebar.header("Business Impact")
st.sidebar.write("""
- Increased user engagement and satisfaction
- Reduced time-to-content for users
- Better content discovery leading to higher watch time
- Data-driven insights for content acquisition
""")

st.sidebar.header("Tech Stack")
st.sidebar.write("""
- **Frontend:** Streamlit for interactive UI
- **Backend:** FastAPI for high-performance API
- **Machine Learning:** scikit-surprise for collaborative filtering
- **Infrastructure:** AWS CDK and ECS Fargate for scalable deployment
""")

def fetch_movie_details(movie_id):
    """
    Fetch movie details including poster path and genres from TMDb API.
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
            # Extract genres
            genres = [genre['name'] for genre in movie_data.get('genres', [])]
            return {
                'title': movie_data['title'],
                'poster_url': poster_url,
                'genres': genres
            }
        return None
    except Exception as e:
        st.error(f"Error fetching movie details: {str(e)}")
        return None

def get_recommendations(user_id: int):
    """
    Get movie recommendations from the backend API.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/recommendations/{user_id}?top_n=5")
        response.raise_for_status()
        data = response.json()
        return data["recommendations"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return None

st.title("Movie Recommendation System")

st.write("This app recommends movies based on your preferences.")

user_id = st.number_input("Enter your user ID", min_value=1, max_value=610, value=1)

if st.button("Get Recommendations"):
    # Convert user_id to string before sending to backend
    recommendations = get_recommendations(str(user_id))
    
    if recommendations is None:
        st.error("Failed to get recommendations. Please try again.")
    else:
        if not recommendations:
            st.warning(f"No recommendations found for user ID {user_id}")
        else:
            st.write("### Top Movie Recommendations")
            
            # Create dynamic columns based on number of recommendations
            num_cols = min(5, len(recommendations))  # Limit to 5 columns max
            cols = st.columns([1] * num_cols)
            
            for idx, rec in enumerate(recommendations[:num_cols]):
                movie_details = fetch_movie_details(rec['movie_id'])
                
                with cols[idx]:
                    if movie_details:
                        st.image(movie_details['poster_url'], caption=movie_details['title'])
                        st.write(f"**Rating:** {rec['estimated_rating']:.2f}")
                        if movie_details['genres']:
                            st.write("**Genres:** " + ", ".join(movie_details['genres']))
                    else:
                        st.write(f"Movie ID: {rec['movie_id']}")
                        st.write(f"Rating: {rec['estimated_rating']:.2f}")
