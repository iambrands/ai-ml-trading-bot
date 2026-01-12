#!/bin/bash
# Refresh PostgreSQL statistics on Railway
# This script connects to Railway database and runs ANALYZE on all tables

set -e

echo "🔄 Refreshing PostgreSQL Statistics on Railway"
echo "=============================================="
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm i -g @railway/cli"
    exit 1
fi

# Check if we're linked to a service
echo "📋 Checking Railway connection..."
if ! railway status &> /dev/null; then
    echo "⚠️  Not linked to a Railway service. Linking now..."
    echo "   (This will prompt you to select a service)"
    railway link
fi

echo ""
echo "🔗 Connecting to PostgreSQL and running ANALYZE..."
echo ""

# Run ANALYZE commands via railway connect
# Note: railway connect postgres opens an interactive shell
# We'll create a SQL script and run it

cat << 'SQL' | railway connect postgres
-- Refresh statistics for all tables
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;

-- Verify indexes
SELECT 
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('signals', 'trades', 'portfolio_snapshots', 'predictions', 'markets')
GROUP BY tablename
ORDER BY tablename;
SQL

echo ""
echo "✅ Statistics refresh complete!"
echo ""
echo "Performance should improve now. Test endpoints to verify."


