#!/bin/bash
# Simple script to refresh PostgreSQL statistics
# Usage: ./refresh_stats_simple.sh
# 
# This script provides the SQL commands to run manually
# since railway connect requires interactive terminal

set -e

echo "🔄 PostgreSQL Statistics Refresh"
echo "================================"
echo ""
echo "Since Railway requires interactive connection,"
echo "please run these commands manually:"
echo ""
echo "1. Connect to Railway database:"
echo "   railway connect postgres"
echo ""
echo "2. Then paste these SQL commands:"
echo ""
echo "--- START SQL ---"
cat << 'SQL'
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
echo "--- END SQL ---"
echo ""
echo "3. Test performance after running ANALYZE"
echo ""


