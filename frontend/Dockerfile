FROM python:3.11

COPY requirements.txt app/requirements.txt
WORKDIR /app

RUN pip install -r requirements.txt
COPY . /app

# Expose both HTTP and WebSocket ports
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

ENTRYPOINT ["streamlit", "run", "streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]