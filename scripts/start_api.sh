#!/bin/bash
# Start the FastAPI server

echo "Starting Polymarket AI Trading Bot API on port 8002..."
echo "Access the API at: http://localhost:8002"
echo "Swagger UI at: http://localhost:8002/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")/.."
uvicorn src.api.app:app --host 127.0.0.1 --port 8002 --reload

