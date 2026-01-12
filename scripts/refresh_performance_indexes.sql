-- Refresh Performance Indexes
-- Run this script to re-analyze tables and refresh query planner statistics
-- This should improve query performance if statistics are stale

-- Re-analyze all tables to refresh statistics
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;

-- Verify indexes exist
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND (indexname LIKE 'idx_%_created_at%'
         OR indexname LIKE 'idx_%_entry_time%'
         OR indexname LIKE 'idx_%_snapshot_time%'
         OR indexname LIKE 'idx_%_prediction_time%')
ORDER BY tablename, indexname;

-- Show index counts per table
SELECT 
    tablename,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('signals', 'trades', 'portfolio_snapshots', 'predictions', 'markets')
GROUP BY tablename
ORDER BY tablename;

