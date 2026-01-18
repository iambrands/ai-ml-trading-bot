-- Fix dashboard stats timeout by adding missing indexes
-- This migration fixes the "canceling statement due to statement timeout" error

-- Add composite index for dashboard stats query
-- Query: WHERE paper_trading = true AND snapshot_time < X ORDER BY snapshot_time DESC LIMIT 1
CREATE INDEX IF NOT EXISTS idx_portfolio_paper_snapshot 
ON portfolio_snapshots(paper_trading, snapshot_time DESC) 
WHERE paper_trading = true;

-- Add index on snapshot_time for sorting (if not exists)
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_time_desc 
ON portfolio_snapshots(snapshot_time DESC);

-- Add index on created_at if used in queries
CREATE INDEX IF NOT EXISTS idx_portfolio_created_at_desc 
ON portfolio_snapshots(created_at DESC);

-- Analyze table to update query planner statistics
ANALYZE portfolio_snapshots;

-- Verify indexes were created
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'portfolio_snapshots'
ORDER BY indexname;

