-- Whale Tracking System Migration
-- Tracks top 500 Polymarket traders and their activity

-- Whale wallets table
CREATE TABLE IF NOT EXISTS whale_wallets (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) UNIQUE NOT NULL,
    nickname VARCHAR(100),
    total_volume DECIMAL(20, 2) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5, 4) DEFAULT 0,
    total_profit DECIMAL(20, 2) DEFAULT 0,
    rank INTEGER,
    is_active BOOLEAN DEFAULT true,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Whale trades table
CREATE TABLE IF NOT EXISTS whale_trades (
    id SERIAL PRIMARY KEY,
    whale_id INTEGER REFERENCES whale_wallets(id) ON DELETE CASCADE,
    wallet_address VARCHAR(42) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    market_question TEXT,
    trade_type VARCHAR(10) NOT NULL, -- 'BUY' or 'SELL'
    outcome VARCHAR(10) NOT NULL, -- 'YES' or 'NO'
    amount DECIMAL(20, 2) NOT NULL,
    price DECIMAL(10, 8) NOT NULL,
    trade_value DECIMAL(20, 2) NOT NULL,
    transaction_hash VARCHAR(66),
    block_number BIGINT,
    trade_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Whale alerts for users
CREATE TABLE IF NOT EXISTS whale_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1, -- Default to 1 for single-user system
    whale_id INTEGER REFERENCES whale_wallets(id) ON DELETE CASCADE,
    trade_id INTEGER REFERENCES whale_trades(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) DEFAULT 'large_trade',
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_whale_trades_whale_id ON whale_trades(whale_id);
CREATE INDEX IF NOT EXISTS idx_whale_trades_market_id ON whale_trades(market_id);
CREATE INDEX IF NOT EXISTS idx_whale_trades_trade_time ON whale_trades(trade_time DESC);
CREATE INDEX IF NOT EXISTS idx_whale_trades_value ON whale_trades(trade_value DESC);
CREATE INDEX IF NOT EXISTS idx_whale_wallets_rank ON whale_wallets(rank);
CREATE INDEX IF NOT EXISTS idx_whale_wallets_volume ON whale_wallets(total_volume DESC);
CREATE INDEX IF NOT EXISTS idx_whale_wallets_profit ON whale_wallets(total_profit DESC);
CREATE INDEX IF NOT EXISTS idx_whale_wallets_address ON whale_wallets(wallet_address);
CREATE INDEX IF NOT EXISTS idx_whale_alerts_user ON whale_alerts(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_whale_alerts_created ON whale_alerts(created_at DESC);

-- Update timestamp trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for whale_wallets updated_at
DROP TRIGGER IF EXISTS update_whale_wallets_updated_at ON whale_wallets;
CREATE TRIGGER update_whale_wallets_updated_at 
    BEFORE UPDATE ON whale_wallets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Analyze tables for query optimization
ANALYZE whale_wallets;
ANALYZE whale_trades;
ANALYZE whale_alerts;

