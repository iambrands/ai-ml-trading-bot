#!/bin/bash
# Railway entrypoint script to handle PORT environment variable

set -e

# Get PORT from environment or default to 8000
PORT="${PORT:-8000}"

# Debug output
echo "=== Starting Application ==="
echo "PORT environment variable: ${PORT}"
echo "Working directory: $(pwd)"
echo "Python path: ${PYTHONPATH:-not set}"

# Start uvicorn - use eval to ensure variable expansion
eval "exec python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT}"

