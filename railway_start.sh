#!/bin/bash
# Railway startup script
# This ensures the Python path is set correctly

export PYTHONPATH="${PYTHONPATH}:${PWD}"
cd /app || cd "${PWD}"
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port "${PORT:-8000}"

