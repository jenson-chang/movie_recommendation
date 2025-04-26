FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Create models directory
RUN mkdir -p models

# Copy both frontend and backend code
COPY frontend /app/frontend
COPY backend /app/backend

# Add backend directory to Python path
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Set environment variables
ENV TMDB_API_KEY=${TMDB_API_KEY}
ENV REACT_APP_API_URL=http://localhost:8000

# Expose ports for both services
EXPOSE 8000 8501

# Create a startup script
RUN echo '#!/bin/bash\n\
uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
streamlit run frontend/streamlit.py --server.port 8501 --server.address 0.0.0.0' > /app/start.sh && \
chmod +x /app/start.sh

# Set the startup script as the entrypoint
ENTRYPOINT ["/app/start.sh"] 