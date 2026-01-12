-- Add performance indexes for faster queries
-- Run this on Railway database to improve page load times

-- Signals: Index on created_at for ORDER BY queries
CREATE INDEX IF NOT EXISTS idx_signals_created_at_desc ON signals(created_at DESC);

-- Trades: Index on entry_time for ORDER BY queries (may already exist, but ensure DESC)
CREATE INDEX IF NOT EXISTS idx_trades_entry_time_desc ON trades(entry_time DESC);

-- Portfolio: Index on snapshot_time for ORDER BY queries (may already exist, but ensure DESC)
CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_time_desc ON portfolio_snapshots(snapshot_time DESC);

-- Predictions: Index on prediction_time for ORDER BY queries
CREATE INDEX IF NOT EXISTS idx_predictions_prediction_time_desc ON predictions(prediction_time DESC);

-- Markets: Index on created_at for ORDER BY queries
CREATE INDEX IF NOT EXISTS idx_markets_created_at_desc ON markets(created_at DESC);

-- Composite indexes for common query patterns

-- Signals: Index for filtering by market_id and ordering by created_at
CREATE INDEX IF NOT EXISTS idx_signals_market_created_at ON signals(market_id, created_at DESC);

-- Signals: Index for filtering by executed and ordering by created_at
CREATE INDEX IF NOT EXISTS idx_signals_executed_created_at ON signals(executed, created_at DESC);

-- Trades: Index for filtering by status and ordering by entry_time
CREATE INDEX IF NOT EXISTS idx_trades_status_entry_time ON trades(status, entry_time DESC);

-- Trades: Index for filtering by market_id and ordering by entry_time
CREATE INDEX IF NOT EXISTS idx_trades_market_entry_time ON trades(market_id, entry_time DESC);

-- Predictions: Index for filtering by market_id and ordering by prediction_time
CREATE INDEX IF NOT EXISTS idx_predictions_market_prediction_time ON predictions(market_id, prediction_time DESC);

-- Analyze tables to update statistics
ANALYZE signals;
ANALYZE trades;
ANALYZE portfolio_snapshots;
ANALYZE predictions;
ANALYZE markets;

