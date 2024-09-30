FROM python:3.12

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the requirements.txt file to the working directory
COPY ./requirements.txt /app/requirements.txt

# Step 4: Install the Python dependencies specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Step 5: Copy the entire application code to the working directory
# COPY ./main.py /app/main.py
COPY ./app.py /app/app.py

# Expose the ports for FastAPI (8000) and Streamlit (8501)
# EXPOSE 8000
EXPOSE 8501

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Command to start Streamlit first, then FastAPI
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
