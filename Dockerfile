# Railway-optimized Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy startup scripts
COPY entrypoint.sh start.sh start_server.py ./
RUN chmod +x entrypoint.sh start.sh start_server.py && \
    sed -i 's/\r$//' entrypoint.sh start.sh start_server.py 2>/dev/null || true

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Use Python script to read PORT from environment
# This avoids shell variable expansion issues
# Use absolute path to ensure it's found
CMD ["python3", "/app/start_server.py"]

