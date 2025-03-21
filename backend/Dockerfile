FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create models directory
RUN mkdir -p models

# Copy model file first
COPY model.pkl models/

# Copy the rest of the application
COPY . .

# Run preprocessing
RUN python preprocess_model.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ,"--reload"]