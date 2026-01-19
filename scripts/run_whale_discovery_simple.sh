#!/bin/bash
# Simple Whale Discovery - Just run the script with Railway
# This is the simplest approach: run directly on Railway

set -e

echo "======================================================================"
echo "  SIMPLE WHALE DISCOVERY (Running on Railway)"
echo "======================================================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found"
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

echo "✅ Running whale discovery directly on Railway..."
echo "   (This should work without needing a tunnel)"
echo ""

# Run directly on Railway
railway run --service web python scripts/init_whale_discovery.py

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Success! Whales have been indexed."
else
    echo "❌ Failed. See error messages above."
    echo ""
    echo "If you see connection errors, you may need to use the tunnel method:"
    echo "  ./scripts/run_whale_discovery_automated.sh"
fi

exit $EXIT_CODE

