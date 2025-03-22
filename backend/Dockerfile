FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Create models directory
RUN mkdir -p models

# Copy the application code
COPY backend/ .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["sh", "-c", "python preprocess_model.py && uvicorn main:app --host 0.0.0.0 --port 8000"]