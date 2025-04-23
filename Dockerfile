FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Create models directory
RUN mkdir -p models

# Copy the application code
COPY . .

# Expose ports for both services
EXPOSE 8000 8501

# Create a startup script
RUN echo '#!/bin/bash\n\
uvicorn main:app --host 0.0.0.0 --port 8000 & \
streamlit run streamlit.py --server.port 8501 --server.address 0.0.0.0' > /app/start.sh && \
chmod +x /app/start.sh

# Command to run both services
CMD ["/app/start.sh"] 