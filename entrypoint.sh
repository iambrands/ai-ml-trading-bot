#!/bin/sh
# Railway entrypoint script to handle PORT environment variable

# Debug: Print environment variables
echo "PORT environment variable: ${PORT:-not set}"

# Default to port 8000 if PORT is not set
PORT=${PORT:-8000}

# Debug: Print the port being used
echo "Starting uvicorn on port: $PORT"

# Start uvicorn with the port (using exec to replace shell process)
exec python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port "$PORT"

