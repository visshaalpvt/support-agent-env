FROM python:3.10-slim

WORKDIR /app

# Upgrade pip first for better reliability
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY requirements.txt .

# Install with retry logic
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt || \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt || \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy the rest of the application
COPY . .

# Create server directory if not exists
RUN mkdir -p server

# Expose the port
EXPOSE 7860

# Run the FastAPI app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
