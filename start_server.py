#!/usr/bin/env python3
"""Startup script that reads PORT from environment and starts uvicorn."""
import os
import sys

# Add project root to path
sys.path.insert(0, '/app')

# Get PORT from environment - Railway should set this, but default to 8000
# Check all possible PORT variable names
port_str = (
    os.environ.get('PORT') or
    os.environ.get('RAILWAY_ENVIRONMENT_PORT') or
    os.environ.get('PORT_NUMBER') or
    '8000'
)

try:
    port = int(port_str)
except (ValueError, TypeError):
    print(f"Warning: Invalid PORT value '{port_str}', defaulting to 8000")
    port = 8000

# Debug: Print environment info
print("=" * 50)
print("Environment Variables Check:")
print(f"  PORT: {os.environ.get('PORT', 'NOT SET')}")
print(f"  RAILWAY_ENVIRONMENT_PORT: {os.environ.get('RAILWAY_ENVIRONMENT_PORT', 'NOT SET')}")
print(f"  Using port: {port}")
print("=" * 50)

# Import and run uvicorn
import uvicorn
from src.api.app import app

print(f"Starting uvicorn on host 0.0.0.0 port {port}...")
uvicorn.run(app, host="0.0.0.0", port=port)

