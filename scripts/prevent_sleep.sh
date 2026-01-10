#!/bin/bash
# Prevent Mac from sleeping (useful for training on server)

set -e

echo "🛡️  Preventing Mac from sleeping..."
echo ""

# Method 1: Use caffeinate (temporary - until reboot)
echo "Method 1: Using caffeinate (temporary)"
echo "   This prevents sleep until you reboot or cancel"
echo ""

# Check if training is running
PID_FILE=".training.pid"
if [ -f "$PID_FILE" ]; then
    TRAINING_PID=$(cat "$PID_FILE")
    if ps -p "$TRAINING_PID" > /dev/null 2>&1; then
        echo "✅ Training is running (PID: $TRAINING_PID)"
        echo "   Preventing sleep while training runs..."
        caffeinate -w "$TRAINING_PID" &
        CAFFEINATE_PID=$!
        echo "$CAFFEINATE_PID" > .caffeinate.pid
        echo "   Caffeinate running (PID: $CAFFEINATE_PID)"
        echo "   Will stop automatically when training completes"
    else
        echo "⚠️  Training not running, preventing sleep indefinitely"
        caffeinate -d &
        CAFFEINATE_PID=$!
        echo "$CAFFEINATE_PID" > .caffeinate.pid
        echo "   Caffeinate running (PID: $CAFFEINATE_PID)"
        echo "   To stop: kill $CAFFEINATE_PID"
    fi
else
    echo "⚠️  No training PID found, preventing sleep indefinitely"
    caffeinate -d &
    CAFFEINATE_PID=$!
    echo "$CAFFEINATE_PID" > .caffeinate.pid
    echo "   Caffeinate running (PID: $CAFFEINATE_PID)"
    echo "   To stop: kill $CAFFEINATE_PID"
fi

echo ""
echo "✅ Sleep prevention active!"
echo ""
echo "📊 Check status:"
echo "   ps -p $CAFFEINATE_PID"
echo ""
echo "🛑 Stop sleep prevention:"
echo "   kill $CAFFEINATE_PID"
echo "   or"
echo "   ./scripts/stop_prevent_sleep.sh"

