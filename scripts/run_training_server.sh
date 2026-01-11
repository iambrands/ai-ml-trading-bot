#!/bin/bash
# Run training on remote server with persistence

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Configuration
START_DATE="${1:-2022-01-09T00:00:00Z}"
END_DATE="${2:-2026-01-08T23:59:59Z}"
TIME_POINTS="${3:-1 3 7 14}"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_FILE="${PROJECT_ROOT}/.training.pid"
LOG_FILE="${LOG_DIR}/training_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p "$LOG_DIR"

# Check if training is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Training already running (PID: $OLD_PID)"
        echo "   To stop: kill $OLD_PID"
        exit 1
    else
        # Stale PID file
        rm "$PID_FILE"
    fi
fi

echo "🚀 Starting training on server..."
echo "   Start date: $START_DATE"
echo "   End date: $END_DATE"
echo "   Time points: $TIME_POINTS"
echo "   Log file: $LOG_FILE"
echo ""

# Run training in background with nohup
nohup python3 "$SCRIPT_DIR/train_models.py" \
    --start-date "$START_DATE" \
    --end-date "$END_DATE" \
    --time-points $TIME_POINTS \
    > "$LOG_FILE" 2>&1 &

TRAINING_PID=$!
echo $TRAINING_PID > "$PID_FILE"

echo "✅ Training started (PID: $TRAINING_PID)"
echo "   Log file: $LOG_FILE"
echo "   PID file: $PID_FILE"
echo ""
echo "📊 Monitor progress:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🛑 Stop training:"
echo "   kill $TRAINING_PID"
echo ""
echo "📈 Check status:"
echo "   ps -p $TRAINING_PID"


