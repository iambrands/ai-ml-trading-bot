#!/bin/bash
# Railway entrypoint script to handle PORT environment variable

# Default to port 8000 if PORT is not set
PORT=${PORT:-8000}

# Start uvicorn with the port
exec python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port $PORT

