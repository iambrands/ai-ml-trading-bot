#!/bin/bash
# Performance Diagnostic Script

echo "=== Performance Diagnostic ==="
echo ""

echo "1. Checking Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 10 "https://web-production-c490dd.up.railway.app/health" 2>&1)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health endpoint responding (HTTP $HTTP_CODE)"
    echo "$BODY" | python3 -m json.tool 2>/dev/null | head -30
else
    echo "❌ Health endpoint failed (HTTP $HTTP_CODE)"
    echo "$BODY"
fi

echo ""
echo "2. Checking Recent Predictions..."
curl -s --max-time 10 "https://web-production-c490dd.up.railway.app/predictions?limit=5" 2>&1 | python3 -m json.tool 2>/dev/null | head -20

echo ""
echo "3. Testing Prediction Generation Endpoint..."
GEN_RESPONSE=$(curl -s -w "\n%{http_code}" --max-time 15 -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5&auto_signals=false&auto_trades=false" 2>&1)
GEN_CODE=$(echo "$GEN_RESPONSE" | tail -n 1)
GEN_BODY=$(echo "$GEN_RESPONSE" | head -n -1)

if [ "$GEN_CODE" = "200" ]; then
    echo "✅ Prediction endpoint responding (HTTP $GEN_CODE)"
    echo "$GEN_BODY" | python3 -m json.tool 2>/dev/null
else
    echo "❌ Prediction endpoint failed (HTTP $GEN_CODE)"
    echo "$GEN_BODY"
fi

echo ""
echo "=== Diagnostic Complete ==="

