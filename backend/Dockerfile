FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Create models directory and copy model file
RUN mkdir -p models
COPY model.zip models/

# Copy the rest of the application
COPY . .

# Run preprocessing and verify
RUN python preprocess_model.py && \
    ls -l models/preprocessed_model.pkl && \
    echo "Preprocessing completed successfully"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ,"--reload"]