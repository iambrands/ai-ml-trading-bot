#!/bin/bash

# Performance Testing Script for PredictEdge Dashboard
# Tests all tabs and measures response times

BASE_URL="https://web-production-c490dd.up.railway.app"
TOTAL_TIME=0
PASSED=0
FAILED=0

echo "=========================================="
echo "  PREDICTEDGE PERFORMANCE TEST"
echo "=========================================="
echo ""
echo "Base URL: $BASE_URL"
echo "Timestamp: $(date)"
echo ""

test_endpoint() {
    local name=$1
    local endpoint=$2
    local method=${3:-GET}
    
    echo -n "Testing $name... "
    
    if [ "$method" = "POST" ]; then
        START=$(date +%s.%N)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 -X POST "$BASE_URL$endpoint" -H "Content-Type: application/json" -d '{}' 2>&1)
        END=$(date +%s.%N)
    else
        START=$(date +%s.%N)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "$BASE_URL$endpoint" 2>&1)
        END=$(date +%s.%N)
    fi
    
    DURATION=$(echo "$END - $START" | bc)
    DURATION_MS=$(echo "$DURATION * 1000" | bc | cut -d. -f1)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        if [ "$DURATION_MS" -lt 3000 ]; then
            echo "✅ ${DURATION_MS}ms (HTTP $HTTP_CODE) - FAST"
            PASSED=$((PASSED + 1))
        elif [ "$DURATION_MS" -lt 10000 ]; then
            echo "⚠️  ${DURATION_MS}ms (HTTP $HTTP_CODE) - SLOW"
            FAILED=$((FAILED + 1))
        else
            echo "❌ ${DURATION_MS}ms (HTTP $HTTP_CODE) - VERY SLOW"
            FAILED=$((FAILED + 1))
        fi
        TOTAL_TIME=$(echo "$TOTAL_TIME + $DURATION" | bc)
    else
        echo "❌ FAILED (HTTP $HTTP_CODE) - ${DURATION_MS}ms"
        FAILED=$((FAILED + 1))
    fi
}

echo "=== CRITICAL ENDPOINTS ==="
echo ""
test_endpoint "Health Check" "/health"
test_endpoint "Markets (limit=20)" "/markets?limit=20"
test_endpoint "Predictions (limit=20)" "/predictions?limit=20"
test_endpoint "Signals (limit=20)" "/signals?limit=20"
test_endpoint "Trades (limit=20)" "/trades?limit=20"
test_endpoint "Portfolio Latest" "/portfolio/latest"

echo ""
echo "=== DASHBOARD ENDPOINTS ==="
echo ""
test_endpoint "Dashboard Stats" "/dashboard/stats"
test_endpoint "Dashboard Activity" "/dashboard/activity?limit=20"
test_endpoint "Dashboard Settings" "/dashboard/settings"

echo ""
echo "=== FEATURE ENDPOINTS ==="
echo ""
test_endpoint "Analytics Summary" "/analytics/dashboard-summary?paper_trading=false"
test_endpoint "Alerts List" "/alerts"
test_endpoint "Live Markets" "/live/markets?limit=20"

echo ""
echo "=========================================="
echo "  TEST SUMMARY"
echo "=========================================="
echo "Total Tests: $((PASSED + FAILED))"
echo "✅ Passed (Fast): $PASSED"
echo "❌ Failed (Slow): $FAILED"
TOTAL_MS=$(echo "$TOTAL_TIME * 1000" | bc | cut -d. -f1)
echo "Total Time: ${TOTAL_MS}ms ($(echo "scale=2; $TOTAL_TIME" | bc)s)"
echo ""
if [ "$FAILED" -eq 0 ]; then
    echo "✅ ALL TESTS PASSED - System is performing well!"
    exit 0
else
    echo "⚠️  PERFORMANCE ISSUES DETECTED - See details above"
    exit 1
fi

