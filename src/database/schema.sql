-- Markets table (historical and active)
CREATE TABLE IF NOT EXISTS markets (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(66) UNIQUE NOT NULL,
    condition_id VARCHAR(66) NOT NULL,
    question TEXT NOT NULL,
    category VARCHAR(50),
    resolution_date TIMESTAMP,
    outcome VARCHAR(3),  -- YES/NO/NULL
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_markets_resolution_date ON markets(resolution_date);
CREATE INDEX IF NOT EXISTS idx_markets_outcome ON markets(outcome);

-- Feature snapshots (for training and inference)
CREATE TABLE IF NOT EXISTS feature_snapshots (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(66) NOT NULL,
    snapshot_time TIMESTAMP NOT NULL,
    features JSONB NOT NULL,
    embeddings_path VARCHAR(255),  -- Path to embedding file
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(market_id, snapshot_time),
    FOREIGN KEY (market_id) REFERENCES markets(market_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_features_market_time ON feature_snapshots(market_id, snapshot_time);

-- Model predictions
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(66) NOT NULL,
    prediction_time TIMESTAMP NOT NULL,
    model_probability DECIMAL(10, 6) NOT NULL,
    market_price DECIMAL(10, 6) NOT NULL,
    edge DECIMAL(10, 6) NOT NULL,
    confidence DECIMAL(10, 6) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_predictions JSONB,  -- Individual model outputs
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (market_id) REFERENCES markets(market_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_predictions_market_time ON predictions(market_id, prediction_time);

-- Trading signals
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER,
    market_id VARCHAR(66) NOT NULL,
    side VARCHAR(3) NOT NULL,
    signal_strength VARCHAR(10) NOT NULL,
    suggested_size DECIMAL(20, 8),
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_signals_market ON signals(market_id);
CREATE INDEX IF NOT EXISTS idx_signals_executed ON signals(executed);

-- Trades
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER,
    market_id VARCHAR(66) NOT NULL,
    side VARCHAR(3) NOT NULL,
    entry_price DECIMAL(10, 6) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(10, 6),
    pnl DECIMAL(20, 8),
    status VARCHAR(20) NOT NULL,  -- OPEN, CLOSED, CANCELLED
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_market ON trades(market_id);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);

-- Model performance tracking
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    evaluation_date DATE NOT NULL,
    accuracy DECIMAL(10, 6),
    brier_score DECIMAL(10, 6),
    log_loss DECIMAL(10, 6),
    auc_roc DECIMAL(10, 6),
    sample_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_name, model_version, evaluation_date)
);

CREATE INDEX IF NOT EXISTS idx_model_perf_date ON model_performance(evaluation_date);

-- Portfolio snapshots (for tracking)
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_time TIMESTAMP NOT NULL,
    total_value DECIMAL(20, 8) NOT NULL,
    cash DECIMAL(20, 8) NOT NULL,
    positions_value DECIMAL(20, 8) NOT NULL,
    total_exposure DECIMAL(20, 8) NOT NULL,
    daily_pnl DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    realized_pnl DECIMAL(20, 8),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshot_time ON portfolio_snapshots(snapshot_time);

