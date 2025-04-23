FROM python:3.11

# Install system dependencies required by TensorFlow
RUN apt-get update && apt-get install -y \
    libhdf5-dev \
    libc-ares-dev \
    libeigen3-dev \
    gcc \
    gfortran \
    libgfortran5 \
    libatlas-base-dev \
    libopenblas-dev \
    libblas-dev \
    liblapack-dev \
    cython3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p models

# Copy both frontend and backend code
COPY backend /app/backend
COPY frontend /app/frontend

# Expose both ports
EXPOSE 8000 8501

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Create startup script
RUN echo '#!/bin/bash\n\
uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
streamlit run frontend/streamlit.py --server.port=8501 --server.address=0.0.0.0' > /app/start.sh && \
chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"] 