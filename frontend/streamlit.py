import requests
import streamlit as st
import os

# Set page to wide mode and configure initial page settings
st.set_page_config(
    layout="wide",
    page_title="Movie Recommendation System",
    initial_sidebar_state="expanded"
)

# Health check endpoint
if st.query_params.get("health") == ["check"]:
    st.write({"status": "healthy"})
    st.stop()

# Custom CSS to increase text size and improve readability
st.markdown("""
    <style>
    .stMarkdown {
        font-size: 1.2rem;
    }
    .stButton>button {
        font-size: 1.2rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #00bcd4 !important;
        color: white !important;
        border-color: #00bcd4 !important;
    }
    .stNumberInput>div>div>input {
        font-size: 1.2rem;
    }
    h1 {
        font-size: 2.5rem !important;
    }
    h2 {
        font-size: 2rem !important;
    }
    h3 {
        font-size: 1.8rem !important;
    }
    </style>
""", unsafe_allow_html=True)

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
        response = requests.get(f"{BACKEND_URL}/recommendations/{user_id}?n=5")
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {str(e)}")
        return None

# Initialize session state for first load
if 'first_load' not in st.session_state:
    st.session_state.first_load = True

# Main content area
st.sidebar.title("MOVIE RECOMMENDATION")

st.sidebar.markdown("---")  # Add separator

# Add user input section to sidebar
user_id = st.sidebar.number_input("Enter a user ID to see their recommendations (1 to 610)", min_value=1, max_value=610, value=1)

if st.sidebar.button("Get Recommendations"):
    # Convert user_id to string before sending to backend
    st.session_state.first_load = False  # Update first load state
    recommendations = get_recommendations(str(user_id))
    
    if recommendations is None:
        st.error("Failed to get recommendations. Please try again.")
    else:
        if not recommendations['content_based'] and not recommendations['collaborative']:
            st.warning(f"No recommendations found for user ID {user_id}")
        else:
            # Display Top Rated Movies
            if recommendations['top_rated']:
                st.write("### Your Top Rated")
                with st.expander("*Learn more about your top rated movies*"):
                    st.write("These are the movies you've rated highest in your viewing history. They help us understand your preferences and generate personalized recommendations.")
                
                cols = st.columns(5)
                for idx, rec in enumerate(recommendations['top_rated'][:5]):
                    with cols[idx]:
                        movie_details = fetch_movie_details(rec['movie_id'])
                        if movie_details:
                            st.image(movie_details['poster_url'], caption=movie_details['title'])
                            if movie_details['genres']:
                                st.write("**Genres:** " + ", ".join(movie_details['genres']))
                        else:
                            st.write(f"Movie ID: {rec['movie_id']}")
            
            st.markdown("---")  # Add separator
            
            # Display Content-Based Recommendations
            if recommendations['content_based']:
                st.write("### We Recommend")
                with st.expander("*Learn more about your recommendations*"):
                    st.write("These recommendations are generated using a supervised machine learning model called **content-based filtering**. It uses the metadata of the movies you've watched to generate recommendations for similar movies.")
                cols = st.columns(5)
                for idx, rec in enumerate(recommendations['content_based'][:5]):
                    with cols[idx]:
                        movie_details = fetch_movie_details(rec['movie_id'])
                        if movie_details:
                            st.image(movie_details['poster_url'], caption=movie_details['title'])
                            if movie_details['genres']:
                                st.write("**Genres:** " + ", ".join(movie_details['genres']))
                        else:
                            st.write(f"Movie ID: {rec['movie_id']}")
            
            st.markdown("---")  # Add separator
            
            # Display Collaborative Filtering Recommendations
            if recommendations['collaborative']:
                st.write("### Others Are Watching")
                with st.expander("*Learn more about what others are watching*"):
                    st.write("These recommendations are generated using a unsupervised machine learning model called **collaborative filtering**. It identifies other user-movie interactions similar to yours and uses them to generate recommendations for movies you might like.")
                cols = st.columns(5)
                for idx, rec in enumerate(recommendations['collaborative'][:5]):
                    with cols[idx]:
                        movie_details = fetch_movie_details(rec['movie_id'])
                        if movie_details:
                            st.image(movie_details['poster_url'], caption=movie_details['title'])
                            if movie_details['genres']:
                                st.write("**Genres:** " + ", ".join(movie_details['genres']))
                        else:
                            st.write(f"Movie ID: {rec['movie_id']}")

# Display welcome message only if first_load is True and no recommendations have been shown
if st.session_state.first_load:
    st.markdown("""
    <div>
        <h2>Welcome! 👋 </h2>
        <p style='font-size: 1.2rem;'>Select a user ID on the left to start getting personalized movie recommendations.</p>
    </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")  # Add separator

with st.sidebar.expander("*Technical Details*"):
    st.write("#### Machine Learning Models")
    st.write("""
    - **Content-Based Filtering:**
      - Uses movie metadata (genres) to create feature vectors for each movie
      - Recommends movies with similar features

    - **Collaborative Filtering:**
      - Identifies patterns in user preferences via matrix factorization of user-movie ratings
      - Recommends movies based on other users with similar preferences
    """)

    st.write("#### Tech Stack")
    st.write("""
    - **Frontend:** Streamlit for interactive UI
    - **Backend:** FastAPI for high-performance API
    - **Machine Learning:** scikit-learn for content-based filtering and scikit-surprise for collaborative filtering
    - **Infrastructure:** Written using AWS CDK and deployed on AWS ECS Fargate
    """)