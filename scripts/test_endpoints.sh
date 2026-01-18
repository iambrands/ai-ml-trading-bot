#!/bin/bash
# Test all PredictEdge API endpoints

BASE_URL="https://web-production-c490dd.up.railway.app"

echo "🧪 Testing PredictEdge Endpoints"
echo "================================="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: Health check
echo "1️⃣ Testing health endpoint..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/health" || echo "❌ FAILED"
echo ""

# Test 2: Root endpoint
echo "2️⃣ Testing root endpoint..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/" || echo "❌ FAILED"
echo ""

# Test 3: Dashboard stats (without /api prefix)
echo "3️⃣ Testing dashboard stats (/dashboard/stats)..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/dashboard/stats" || echo "❌ FAILED"
echo ""

# Test 4: Dashboard stats (with /api prefix - if exists)
echo "4️⃣ Testing dashboard stats (/api/dashboard/stats)..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/api/dashboard/stats" || echo "❌ FAILED"
echo ""

# Test 5: Markets
echo "5️⃣ Testing markets endpoint..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/markets?limit=5" || echo "❌ FAILED"
echo ""

# Test 6: Markets with /api prefix
echo "6️⃣ Testing markets endpoint (/api/markets)..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/api/markets?limit=5" || echo "❌ FAILED"
echo ""

# Test 7: Predictions
echo "7️⃣ Testing predictions endpoint..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/predictions?limit=5" || echo "❌ FAILED"
echo ""

# Test 8: Signals
echo "8️⃣ Testing signals endpoint..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/signals?limit=5" || echo "❌ FAILED"
echo ""

# Test 9: Trades
echo "9️⃣ Testing trades endpoint..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/trades?limit=5" || echo "❌ FAILED"
echo ""

# Test 10: Portfolio
echo "🔟 Testing portfolio endpoint..."
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" "$BASE_URL/portfolio/latest" || echo "❌ FAILED"
echo ""

echo "================================="
echo "✅ Tests complete"
echo ""
echo "📊 Summary:"
echo "  - Check Status codes (200 = OK, 404 = Not Found, 500 = Error)"
echo "  - Check Time values (should be < 2 seconds for most endpoints)"
echo "  - Failed tests show ❌"

