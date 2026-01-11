#!/bin/bash
# Simple startup script that reads PORT from environment

PORT=${PORT:-8000}
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port $PORT


