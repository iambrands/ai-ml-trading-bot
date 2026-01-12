-- Performance indexes migration
-- Run this migration to add critical indexes for query performance

-- Drop existing indexes if they exist (idempotent)
DROP INDEX IF EXISTS idx_predictions_market_timestamp;
DROP INDEX IF EXISTS idx_predictions_recent;
DROP INDEX IF EXISTS idx_signals_active_edge;
DROP INDEX IF EXISTS idx_trades_user_timestamp;
DROP INDEX IF EXISTS idx_markets_created_at_desc;
DROP INDEX IF EXISTS idx_predictions_created_at_desc;
DROP INDEX IF EXISTS idx_signals_created_at_desc;
DROP INDEX IF EXISTS idx_trades_created_at_desc;
DROP INDEX IF EXISTS idx_portfolio_snapshots_created_at_desc;
DROP INDEX IF EXISTS idx_signals_market_id_created_at;
DROP INDEX IF EXISTS idx_trades_market_id_entry_time;
DROP INDEX IF EXISTS idx_trades_status_entry_time;

-- Critical indexes for performance
-- Note: CONCURRENTLY requires exclusive lock, so we use regular CREATE INDEX
-- Run during low-traffic periods if needed

-- Predictions indexes
CREATE INDEX IF NOT EXISTS idx_predictions_market_timestamp 
ON predictions(market_id, created_at DESC);

-- Note: Partial index with NOW() not possible (NOW() is not immutable)
-- Use full index instead - PostgreSQL will still use it efficiently for recent queries
CREATE INDEX IF NOT EXISTS idx_predictions_recent 
ON predictions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at_desc 
ON predictions(created_at DESC);

-- Signals indexes
-- Note: signals table doesn't have 'edge' column - edge is in predictions table
CREATE INDEX IF NOT EXISTS idx_signals_active 
ON signals(created_at DESC) 
WHERE executed = false;

CREATE INDEX IF NOT EXISTS idx_signals_created_at_desc 
ON signals(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_signals_market_id_created_at 
ON signals(market_id, created_at DESC);

-- Trades indexes
CREATE INDEX IF NOT EXISTS idx_trades_user_timestamp
ON trades(entry_time DESC);

CREATE INDEX IF NOT EXISTS idx_trades_created_at_desc 
ON trades(entry_time DESC);

CREATE INDEX IF NOT EXISTS idx_trades_market_id_entry_time 
ON trades(market_id, entry_time DESC);

CREATE INDEX IF NOT EXISTS idx_trades_status_entry_time 
ON trades(status, entry_time DESC);

-- Markets indexes
CREATE INDEX IF NOT EXISTS idx_markets_created_at_desc 
ON markets(created_at DESC);

-- Portfolio snapshots indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_created_at_desc 
ON portfolio_snapshots(created_at DESC);

-- Analyze tables to update query planner statistics
ANALYZE predictions;
ANALYZE signals;
ANALYZE trades;
ANALYZE markets;
ANALYZE portfolio_snapshots;

