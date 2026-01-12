-- Migration: Add alerts and paper trading support
-- Date: 2026-01-12

-- Alerts table for notification system
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) DEFAULT 'default',  -- For multi-user support later
    alert_type VARCHAR(50) NOT NULL,  -- SIGNAL, PORTFOLIO, PREDICTION, CUSTOM
    alert_rule JSONB NOT NULL,  -- Flexible rule configuration
    notification_method VARCHAR(50) NOT NULL,  -- EMAIL, WEBHOOK, TELEGRAM, SMS
    notification_target TEXT NOT NULL,  -- Email address, webhook URL, Telegram chat ID, etc.
    enabled BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_enabled ON alerts(enabled);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);

-- Alert history for tracking
CREATE TABLE IF NOT EXISTS alert_history (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL,
    signal_id INTEGER,
    market_id VARCHAR(66),
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_alert_history_alert ON alert_history(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_sent ON alert_history(sent_at);

-- Add paper_trading flag to trades table
ALTER TABLE trades ADD COLUMN IF NOT EXISTS paper_trading BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_trades_paper_trading ON trades(paper_trading);

-- Add paper_trading flag to portfolio_snapshots
ALTER TABLE portfolio_snapshots ADD COLUMN IF NOT EXISTS paper_trading BOOLEAN DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS idx_portfolio_paper_trading ON portfolio_snapshots(paper_trading);

-- Analytics cache table for performance
CREATE TABLE IF NOT EXISTS analytics_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON analytics_cache(expires_at);

