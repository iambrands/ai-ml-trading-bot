#!/bin/bash
# Script to manually refresh all data on Railway

echo "🔄 Refreshing All Data on Railway"
echo "=================================="
echo ""

RAILWAY_URL="https://web-production-c490dd.up.railway.app"

echo "📊 Step 1: Triggering Prediction Generation..."
echo "URL: ${RAILWAY_URL}/predictions/generate?limit=20&auto_signals=true&auto_trades=true"
echo ""

response=$(curl -s -X POST "${RAILWAY_URL}/predictions/generate?limit=20&auto_signals=true&auto_trades=true" \
  -H "Content-Type: application/json" \
  -w "\nHTTP_CODE:%{http_code}")

http_code=$(echo "$response" | grep "HTTP_CODE" | cut -d: -f2)
body=$(echo "$response" | sed '/HTTP_CODE/d')

echo "Response:"
echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
echo ""
echo "HTTP Status: $http_code"
echo ""

if [ "$http_code" = "200" ]; then
    echo "✅ Prediction generation started successfully!"
    echo ""
    echo "⏱️  Predictions are being generated in the background..."
    echo "   This typically takes 2-5 minutes."
    echo ""
    echo "📊 Check the dashboard in a few minutes:"
    echo "   ${RAILWAY_URL}/"
    echo ""
    echo "📝 Monitor Railway logs to see progress:"
    echo "   1. Go to Railway Dashboard"
    echo "   2. Select web service"
    echo "   3. Go to 'Logs' tab"
    echo ""
else
    echo "❌ Failed to trigger prediction generation"
    echo "   HTTP Status: $http_code"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "   1. Check if Railway service is running"
    echo "   2. Check Railway logs for errors"
    echo "   3. Verify the URL is correct: ${RAILWAY_URL}"
    exit 1
fi

echo ""
echo "✅ Refresh initiated! Check the dashboard in a few minutes."

