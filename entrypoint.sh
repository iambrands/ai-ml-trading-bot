#!/bin/sh
# Railway entrypoint script to handle PORT environment variable

# Export PORT to ensure it's available
export PORT=${PORT:-8000}

# Debug: Print the port being used
echo "Starting uvicorn on port: $PORT"

# Start uvicorn with the port (using exec to replace shell process)
exec python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port $PORT

