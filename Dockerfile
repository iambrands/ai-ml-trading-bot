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
COPY entrypoint.sh start.sh ./
RUN chmod +x entrypoint.sh start.sh && \
    sed -i 's/\r$//' entrypoint.sh start.sh 2>/dev/null || true

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Use simple shell command that directly reads PORT
# Use double quotes to allow variable expansion
CMD bash -c "python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port \${PORT:-8000}"

