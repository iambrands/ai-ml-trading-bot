#!/bin/bash
# Stop sleep prevention

PID_FILE=".caffeinate.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "🛑 Stopping sleep prevention (PID: $PID)..."
        kill "$PID"
        rm "$PID_FILE"
        echo "✅ Sleep prevention stopped"
    else
        echo "⚠️  Caffeinate process not found (stale PID file)"
        rm "$PID_FILE"
    fi
else
    echo "ℹ️  No sleep prevention active"
fi


