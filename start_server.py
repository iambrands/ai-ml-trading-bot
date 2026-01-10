#!/usr/bin/env python3
"""Startup script that reads PORT from environment and starts uvicorn."""
import os
import sys

# Add project root to path
sys.path.insert(0, '/app')

# Get PORT from environment or default to 8000
port = int(os.environ.get('PORT', 8000))

print(f"Starting uvicorn on port: {port}")

# Import and run uvicorn
import uvicorn
from src.api.app import app

uvicorn.run(app, host="0.0.0.0", port=port)

