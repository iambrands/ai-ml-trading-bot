#!/bin/bash
# Check training status on remote server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="${PROJECT_ROOT}/.training.pid"
LOG_DIR="${PROJECT_ROOT}/logs"
MODELS_DIR="${PROJECT_ROOT}/data/models"

echo "📊 Training Status Check"
echo "========================"
echo ""

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Training is RUNNING (PID: $PID)"
        
        # Show process info
        echo ""
        echo "Process details:"
        ps -p "$PID" -o pid,etime,pcpu,pmem,command | tail -1
        
        # Show latest log
        LATEST_LOG=$(ls -t "$LOG_DIR"/training_*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            echo ""
            echo "Latest log: $LATEST_LOG"
            echo "Last 5 lines:"
            tail -5 "$LATEST_LOG" | sed 's/^/  /'
        fi
    else
        echo "❌ Training process NOT FOUND (stale PID file)"
        echo "   PID was: $PID"
        rm "$PID_FILE"
    fi
else
    echo "ℹ️  No training process found (no PID file)"
fi

# Check for model files
echo ""
echo "Model Files:"
if [ -d "$MODELS_DIR" ]; then
    if ls "$MODELS_DIR"/*.pkl 1> /dev/null 2>&1; then
        echo "✅ Models found:"
        ls -lh "$MODELS_DIR"/*.pkl 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
        
        # Check if models are recent (within last hour)
        LATEST_MODEL=$(ls -t "$MODELS_DIR"/*.pkl 2>/dev/null | head -1)
        if [ -n "$LATEST_MODEL" ]; then
            MODEL_TIME=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$LATEST_MODEL" 2>/dev/null || stat -c "%y" "$LATEST_MODEL" 2>/dev/null | cut -d' ' -f1-2)
            echo "   Latest model updated: $MODEL_TIME"
        fi
    else
        echo "❌ No model files found"
    fi
else
    echo "❌ Models directory not found"
fi

# Check disk space
echo ""
echo "Disk Space:"
df -h "$PROJECT_ROOT" | tail -1 | awk '{print "   Available: " $4 " / " $2 " (" $5 " used)"}'

