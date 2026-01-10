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

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Use entrypoint script to handle PORT variable
ENTRYPOINT ["/entrypoint.sh"]

