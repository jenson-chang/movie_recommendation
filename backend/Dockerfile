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

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create models directory
RUN mkdir -p models

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]