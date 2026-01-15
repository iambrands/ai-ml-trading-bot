#!/bin/bash
# Full Diagnostic Script for Polymarket Bot

echo "=== POLYMARKET BOT DIAGNOSTIC ==="
echo ""

echo "1. Project Location:"
pwd
echo ""

echo "2. Tech Stack:"
echo "  - Framework: FastAPI (Python)"
echo "  - Database: PostgreSQL (Railway)"
echo "  - Deployment: Railway"
echo "  - URL: https://web-production-c490dd.up.railway.app"
echo ""

echo "3. Testing Health Endpoint..."
HEALTH=$(curl -s --max-time 10 "https://web-production-c490dd.up.railway.app/health" 2>&1)
if [ $? -eq 0 ]; then
    echo "  ✅ Health endpoint responding"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null | head -20
else
    echo "  ❌ Health endpoint not responding"
    echo "$HEALTH"
fi
echo ""

echo "4. Testing Polymarket CLOB API..."
CLOB=$(curl -s --max-time 10 "https://clob.polymarket.com/markets?limit=3" 2>&1)
if [ $? -eq 0 ]; then
    echo "  ✅ CLOB API responding"
    echo "$CLOB" | python3 -m json.tool 2>/dev/null | head -15
else
    echo "  ❌ CLOB API not responding"
fi
echo ""

echo "5. Testing Polymarket Gamma API..."
GAMMA=$(curl -s --max-time 10 "https://gamma-api.polymarket.com/markets?limit=3&active=true" 2>&1)
if [ $? -eq 0 ]; then
    echo "  ✅ Gamma API responding"
    echo "$GAMMA" | python3 -m json.tool 2>/dev/null | head -15
else
    echo "  ❌ Gamma API not responding"
fi
echo ""

echo "6. Testing Predictions Endpoint..."
PRED=$(curl -s --max-time 10 "https://web-production-c490dd.up.railway.app/predictions?limit=3" 2>&1)
if [ $? -eq 0 ]; then
    echo "  ✅ Predictions endpoint responding"
    echo "$PRED" | python3 -m json.tool 2>/dev/null | head -15
else
    echo "  ❌ Predictions endpoint not responding"
fi
echo ""

echo "7. API Endpoints Available:"
echo "  - GET /health"
echo "  - GET /markets"
echo "  - GET /predictions"
echo "  - POST /predictions/generate"
echo "  - GET /signals"
echo "  - GET /trades"
echo "  - GET /portfolio/latest"
echo "  - GET /analytics/performance"
echo "  - GET /arbitrage/opportunities"
echo "  - GET /dashboard/stats"
echo ""

echo "=== DIAGNOSTIC COMPLETE ==="
