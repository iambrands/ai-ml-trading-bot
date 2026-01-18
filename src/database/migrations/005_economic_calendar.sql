-- Economic Calendar Migration
-- Tracks FOMC, CPI, NFP, GDP events and their impact on markets

-- Economic events table
CREATE TABLE IF NOT EXISTS economic_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- 'FOMC', 'CPI', 'NFP', 'GDP', etc.
    event_name VARCHAR(200) NOT NULL,
    event_date TIMESTAMP NOT NULL,
    release_time TIME,
    country VARCHAR(50) DEFAULT 'US',
    importance VARCHAR(20) DEFAULT 'HIGH', -- 'HIGH', 'MEDIUM', 'LOW'
    previous_value DECIMAL(10, 4),
    forecast_value DECIMAL(10, 4),
    actual_value DECIMAL(10, 4),
    currency VARCHAR(10) DEFAULT 'USD',
    source VARCHAR(100) DEFAULT 'Federal Reserve',
    description TEXT,
    external_url VARCHAR(500),
    is_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Market-event relationships (which markets are affected by which events)
CREATE TABLE IF NOT EXISTS market_events (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL,
    event_id INTEGER REFERENCES economic_events(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3, 2) DEFAULT 0.5, -- 0.0 to 1.0
    impact_prediction TEXT,
    price_before DECIMAL(10, 8),
    price_after DECIMAL(10, 8),
    measured_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(market_id, event_id)
);

-- User event alerts
CREATE TABLE IF NOT EXISTS event_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL DEFAULT 1, -- Default to 1 for single-user system
    event_id INTEGER REFERENCES economic_events(id) ON DELETE CASCADE,
    alert_time TIMESTAMP NOT NULL,
    hours_before INTEGER DEFAULT 24, -- Alert 24h before event
    notification_sent BOOLEAN DEFAULT false,
    notification_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Historical event impact tracking
CREATE TABLE IF NOT EXISTS event_market_impact (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES economic_events(id) ON DELETE CASCADE,
    market_id VARCHAR(100),
    price_before DECIMAL(10, 8),
    price_after DECIMAL(10, 8),
    price_change_pct DECIMAL(10, 4),
    volume_before DECIMAL(20, 2),
    volume_after DECIMAL(20, 2),
    volume_change_pct DECIMAL(10, 4),
    measured_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_economic_events_date ON economic_events(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_economic_events_type ON economic_events(event_type);
CREATE INDEX IF NOT EXISTS idx_economic_events_importance ON economic_events(importance);
CREATE INDEX IF NOT EXISTS idx_economic_events_completed ON economic_events(is_completed, event_date);
CREATE INDEX IF NOT EXISTS idx_market_events_market_id ON market_events(market_id);
CREATE INDEX IF NOT EXISTS idx_market_events_event_id ON market_events(event_id);
CREATE INDEX IF NOT EXISTS idx_market_events_relevance ON market_events(relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_event_alerts_user_event ON event_alerts(user_id, event_id);
CREATE INDEX IF NOT EXISTS idx_event_alerts_time ON event_alerts(alert_time);
CREATE INDEX IF NOT EXISTS idx_event_market_impact_event ON event_market_impact(event_id);

-- Update timestamp trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_economic_events_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for economic_events updated_at
DROP TRIGGER IF EXISTS update_economic_events_timestamp ON economic_events;
CREATE TRIGGER update_economic_events_timestamp 
    BEFORE UPDATE ON economic_events
    FOR EACH ROW EXECUTE FUNCTION update_economic_events_updated_at();

-- Analyze tables for query optimization
ANALYZE economic_events;
ANALYZE market_events;
ANALYZE event_alerts;
ANALYZE event_market_impact;

