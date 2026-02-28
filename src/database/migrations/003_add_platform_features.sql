-- Migration 003: Add all top Polymarket platform features
-- Copy Trading, Multi-Strategy, Advanced Orders, Price History, Technical Analysis,
-- Market Correlations, Insider Detection, AI Summaries, Leaderboard, Watchlists,
-- Trade Journal, Cross-Platform Odds, Order Book Analysis, News Aggregation, Backtesting

-- Copy Trading
CREATE TABLE IF NOT EXISTS copy_trading_profiles (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) UNIQUE NOT NULL,
    nickname VARCHAR(100),
    total_profit NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    win_rate NUMERIC(5, 4) DEFAULT 0 NOT NULL,
    total_trades INTEGER DEFAULT 0 NOT NULL,
    avg_position_size NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    roi_pct NUMERIC(10, 4) DEFAULT 0 NOT NULL,
    is_following BOOLEAN DEFAULT FALSE NOT NULL,
    auto_copy BOOLEAN DEFAULT FALSE NOT NULL,
    copy_percentage NUMERIC(5, 2) DEFAULT 100 NOT NULL,
    max_copy_size NUMERIC(20, 2) DEFAULT 1000 NOT NULL,
    min_trade_size NUMERIC(20, 2) DEFAULT 10 NOT NULL,
    copy_filter_markets JSONB,
    first_seen_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_activity_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_copy_profiles_following ON copy_trading_profiles(is_following);
CREATE INDEX IF NOT EXISTS idx_copy_profiles_activity ON copy_trading_profiles(last_activity_at);

CREATE TABLE IF NOT EXISTS copy_trades (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES copy_trading_profiles(id) ON DELETE CASCADE NOT NULL,
    source_wallet VARCHAR(42) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    market_question TEXT,
    side VARCHAR(3) NOT NULL,
    source_size NUMERIC(20, 2) NOT NULL,
    copied_size NUMERIC(20, 2) NOT NULL,
    entry_price NUMERIC(10, 6) NOT NULL,
    exit_price NUMERIC(10, 6),
    pnl NUMERIC(20, 8),
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
    source_tx_hash VARCHAR(66),
    copy_tx_hash VARCHAR(66),
    copied_at TIMESTAMP DEFAULT NOW() NOT NULL,
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_copy_trades_profile ON copy_trades(profile_id);
CREATE INDEX IF NOT EXISTS idx_copy_trades_status ON copy_trades(status);
CREATE INDEX IF NOT EXISTS idx_copy_trades_market ON copy_trades(market_id);

-- Multi-Strategy Engine
CREATE TABLE IF NOT EXISTS trading_strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    strategy_type VARCHAR(50) NOT NULL,
    description TEXT,
    parameters JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    allocation_pct NUMERIC(5, 2) DEFAULT 20 NOT NULL,
    max_positions INTEGER DEFAULT 10 NOT NULL,
    max_position_size NUMERIC(20, 2) DEFAULT 500 NOT NULL,
    win_rate NUMERIC(5, 4) DEFAULT 0 NOT NULL,
    total_pnl NUMERIC(20, 8) DEFAULT 0 NOT NULL,
    total_trades INTEGER DEFAULT 0 NOT NULL,
    sharpe_ratio NUMERIC(10, 4),
    last_signal_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_strategies_type ON trading_strategies(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON trading_strategies(is_active);

CREATE TABLE IF NOT EXISTS strategy_trades (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES trading_strategies(id) ON DELETE CASCADE NOT NULL,
    trade_id INTEGER REFERENCES trades(id) ON DELETE SET NULL,
    market_id VARCHAR(100) NOT NULL,
    side VARCHAR(3) NOT NULL,
    entry_price NUMERIC(10, 6) NOT NULL,
    exit_price NUMERIC(10, 6),
    size NUMERIC(20, 8) NOT NULL,
    pnl NUMERIC(20, 8),
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
    signal_data JSONB,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_strategy_trades_strategy ON strategy_trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_strategy_trades_status ON strategy_trades(status);

-- Advanced Orders
CREATE TABLE IF NOT EXISTS advanced_orders (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id) ON DELETE CASCADE,
    market_id VARCHAR(100) NOT NULL,
    order_type VARCHAR(30) NOT NULL,
    side VARCHAR(3) NOT NULL,
    trigger_price NUMERIC(10, 6),
    trail_amount NUMERIC(10, 6),
    trail_pct NUMERIC(5, 4),
    take_profit_price NUMERIC(10, 6),
    stop_loss_price NUMERIC(10, 6),
    highest_price NUMERIC(10, 6),
    lowest_price NUMERIC(10, 6),
    size NUMERIC(20, 8) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    triggered_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_advanced_orders_market ON advanced_orders(market_id);
CREATE INDEX IF NOT EXISTS idx_advanced_orders_status ON advanced_orders(status);
CREATE INDEX IF NOT EXISTS idx_advanced_orders_type ON advanced_orders(order_type);

-- Price History
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL,
    yes_price NUMERIC(10, 6) NOT NULL,
    no_price NUMERIC(10, 6) NOT NULL,
    volume NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    liquidity NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    bid_price NUMERIC(10, 6),
    ask_price NUMERIC(10, 6),
    spread NUMERIC(10, 6),
    open_interest NUMERIC(20, 2),
    num_trades INTEGER DEFAULT 0 NOT NULL,
    interval VARCHAR(10) DEFAULT '1h' NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(market_id, timestamp, interval)
);
CREATE INDEX IF NOT EXISTS idx_price_history_market ON price_history(market_id);
CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp);

-- Technical Indicators
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL,
    indicator_type VARCHAR(30) NOT NULL,
    period INTEGER NOT NULL,
    value NUMERIC(20, 8) NOT NULL,
    signal_value NUMERIC(20, 8),
    upper_band NUMERIC(20, 8),
    lower_band NUMERIC(20, 8),
    histogram NUMERIC(20, 8),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(market_id, indicator_type, period, timestamp)
);
CREATE INDEX IF NOT EXISTS idx_technical_market ON technical_indicators(market_id);
CREATE INDEX IF NOT EXISTS idx_technical_type ON technical_indicators(indicator_type);

-- Market Correlations
CREATE TABLE IF NOT EXISTS market_correlations (
    id SERIAL PRIMARY KEY,
    market_id_a VARCHAR(100) NOT NULL,
    market_id_b VARCHAR(100) NOT NULL,
    correlation NUMERIC(6, 4) NOT NULL,
    correlation_type VARCHAR(20) DEFAULT 'price' NOT NULL,
    lookback_hours INTEGER DEFAULT 168 NOT NULL,
    sample_count INTEGER NOT NULL,
    p_value NUMERIC(10, 8),
    category_a VARCHAR(50),
    category_b VARCHAR(50),
    calculated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(market_id_a, market_id_b, correlation_type)
);
CREATE INDEX IF NOT EXISTS idx_correlations_a ON market_correlations(market_id_a);
CREATE INDEX IF NOT EXISTS idx_correlations_b ON market_correlations(market_id_b);

-- Suspicious Activity
CREATE TABLE IF NOT EXISTS suspicious_activities (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    market_question TEXT,
    activity_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    description TEXT NOT NULL,
    trade_amount NUMERIC(20, 2),
    price_at_detection NUMERIC(10, 6),
    price_impact_pct NUMERIC(10, 4),
    confidence_score NUMERIC(5, 4) NOT NULL,
    evidence JSONB,
    is_reviewed BOOLEAN DEFAULT FALSE NOT NULL,
    detected_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_suspicious_wallet ON suspicious_activities(wallet_address);
CREATE INDEX IF NOT EXISTS idx_suspicious_market ON suspicious_activities(market_id);
CREATE INDEX IF NOT EXISTS idx_suspicious_type ON suspicious_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_suspicious_severity ON suspicious_activities(severity);
CREATE INDEX IF NOT EXISTS idx_suspicious_detected ON suspicious_activities(detected_at);

-- AI Market Summaries
CREATE TABLE IF NOT EXISTS ai_market_summaries (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL,
    market_question TEXT,
    summary TEXT NOT NULL,
    key_factors JSONB,
    sentiment_score NUMERIC(5, 4),
    probability_assessment NUMERIC(5, 4),
    confidence NUMERIC(5, 4),
    risk_level VARCHAR(20),
    recommendation VARCHAR(20),
    news_sources JSONB,
    model_used VARCHAR(50) DEFAULT 'internal' NOT NULL,
    expires_at TIMESTAMP,
    generated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(market_id, generated_at)
);
CREATE INDEX IF NOT EXISTS idx_ai_summaries_market ON ai_market_summaries(market_id);
CREATE INDEX IF NOT EXISTS idx_ai_summaries_generated ON ai_market_summaries(generated_at);

-- Leaderboard
CREATE TABLE IF NOT EXISTS leaderboard_entries (
    id SERIAL PRIMARY KEY,
    wallet_address VARCHAR(42) NOT NULL,
    nickname VARCHAR(100),
    rank INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL,
    total_profit NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    total_volume NUMERIC(20, 2) DEFAULT 0 NOT NULL,
    win_rate NUMERIC(5, 4) DEFAULT 0 NOT NULL,
    total_trades INTEGER DEFAULT 0 NOT NULL,
    roi_pct NUMERIC(10, 4) DEFAULT 0 NOT NULL,
    sharpe_ratio NUMERIC(10, 4),
    max_drawdown NUMERIC(10, 4),
    best_trade_pnl NUMERIC(20, 2),
    worst_trade_pnl NUMERIC(20, 2),
    avg_hold_time_hours NUMERIC(10, 2),
    active_positions INTEGER DEFAULT 0 NOT NULL,
    score NUMERIC(20, 4) DEFAULT 0 NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(wallet_address, period, calculated_at)
);
CREATE INDEX IF NOT EXISTS idx_leaderboard_rank ON leaderboard_entries(rank);
CREATE INDEX IF NOT EXISTS idx_leaderboard_period ON leaderboard_entries(period);
CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard_entries(score);

-- Watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) DEFAULT 'default' NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, name)
);
CREATE INDEX IF NOT EXISTS idx_watchlists_user ON watchlists(user_id);

CREATE TABLE IF NOT EXISTS watchlist_items (
    id SERIAL PRIMARY KEY,
    watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE CASCADE NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    market_question TEXT,
    notes TEXT,
    target_price NUMERIC(10, 6),
    alert_on_price BOOLEAN DEFAULT FALSE NOT NULL,
    price_at_add NUMERIC(10, 6),
    added_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(watchlist_id, market_id)
);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_list ON watchlist_items(watchlist_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_market ON watchlist_items(market_id);

-- Trade Journal
CREATE TABLE IF NOT EXISTS trade_journal_entries (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id) ON DELETE SET NULL,
    market_id VARCHAR(100) NOT NULL,
    market_question TEXT,
    entry_reason TEXT,
    exit_reason TEXT,
    strategy_used VARCHAR(100),
    tags JSONB,
    notes TEXT,
    pre_trade_analysis TEXT,
    post_trade_review TEXT,
    emotional_state VARCHAR(30),
    lesson_learned TEXT,
    screenshots JSONB,
    entry_price NUMERIC(10, 6),
    exit_price NUMERIC(10, 6),
    pnl NUMERIC(20, 8),
    rating INTEGER,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_journal_market ON trade_journal_entries(market_id);
CREATE INDEX IF NOT EXISTS idx_journal_created ON trade_journal_entries(created_at);

-- Cross-Platform Odds
CREATE TABLE IF NOT EXISTS cross_platform_odds (
    id SERIAL PRIMARY KEY,
    market_question TEXT NOT NULL,
    category VARCHAR(50),
    polymarket_id VARCHAR(100),
    kalshi_id VARCHAR(100),
    predictit_id VARCHAR(100),
    metaculus_id VARCHAR(100),
    polymarket_yes NUMERIC(10, 6),
    polymarket_no NUMERIC(10, 6),
    polymarket_volume NUMERIC(20, 2),
    kalshi_yes NUMERIC(10, 6),
    kalshi_no NUMERIC(10, 6),
    kalshi_volume NUMERIC(20, 2),
    predictit_yes NUMERIC(10, 6),
    predictit_no NUMERIC(10, 6),
    metaculus_prediction NUMERIC(10, 6),
    max_spread NUMERIC(10, 6),
    arbitrage_opportunity BOOLEAN DEFAULT FALSE NOT NULL,
    arbitrage_profit_pct NUMERIC(10, 4),
    matched_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(polymarket_id, matched_at)
);
CREATE INDEX IF NOT EXISTS idx_cross_platform_poly ON cross_platform_odds(polymarket_id);
CREATE INDEX IF NOT EXISTS idx_cross_platform_arb ON cross_platform_odds(arbitrage_opportunity);

-- Order Book Snapshots
CREATE TABLE IF NOT EXISTS order_book_snapshots (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(100) NOT NULL,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    best_bid NUMERIC(10, 6),
    best_ask NUMERIC(10, 6),
    mid_price NUMERIC(10, 6),
    spread NUMERIC(10, 6),
    spread_pct NUMERIC(10, 6),
    bid_depth_10pct NUMERIC(20, 2),
    ask_depth_10pct NUMERIC(20, 2),
    imbalance_ratio NUMERIC(10, 6),
    total_bid_volume NUMERIC(20, 2),
    total_ask_volume NUMERIC(20, 2),
    snapshot_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orderbook_market ON order_book_snapshots(market_id);
CREATE INDEX IF NOT EXISTS idx_orderbook_time ON order_book_snapshots(snapshot_time);

-- News Articles
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    summary TEXT,
    content_snippet TEXT,
    author VARCHAR(200),
    category VARCHAR(50),
    sentiment_score NUMERIC(5, 4),
    sentiment_label VARCHAR(20),
    relevance_score NUMERIC(5, 4),
    image_url VARCHAR(500),
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_news_source ON news_articles(source);
CREATE INDEX IF NOT EXISTS idx_news_category ON news_articles(category);
CREATE INDEX IF NOT EXISTS idx_news_published ON news_articles(published_at);

CREATE TABLE IF NOT EXISTS news_market_links (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES news_articles(id) ON DELETE CASCADE NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    relevance_score NUMERIC(5, 4) DEFAULT 0.5 NOT NULL,
    impact_direction VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(article_id, market_id)
);
CREATE INDEX IF NOT EXISTS idx_news_links_article ON news_market_links(article_id);
CREATE INDEX IF NOT EXISTS idx_news_links_market ON news_market_links(market_id);

-- Backtesting
CREATE TABLE IF NOT EXISTS backtest_runs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    strategy_params JSONB NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    initial_capital NUMERIC(20, 2) NOT NULL,
    final_capital NUMERIC(20, 2),
    total_return_pct NUMERIC(10, 4),
    annualized_return_pct NUMERIC(10, 4),
    sharpe_ratio NUMERIC(10, 4),
    sortino_ratio NUMERIC(10, 4),
    max_drawdown_pct NUMERIC(10, 4),
    win_rate NUMERIC(5, 4),
    profit_factor NUMERIC(10, 4),
    total_trades INTEGER DEFAULT 0 NOT NULL,
    avg_trade_pnl NUMERIC(20, 8),
    avg_hold_time_hours NUMERIC(10, 2),
    calmar_ratio NUMERIC(10, 4),
    equity_curve JSONB,
    monthly_returns JSONB,
    status VARCHAR(20) DEFAULT 'RUNNING' NOT NULL,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_runs(strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_status ON backtest_runs(status);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id SERIAL PRIMARY KEY,
    backtest_id INTEGER REFERENCES backtest_runs(id) ON DELETE CASCADE NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    side VARCHAR(3) NOT NULL,
    entry_price NUMERIC(10, 6) NOT NULL,
    exit_price NUMERIC(10, 6),
    size NUMERIC(20, 8) NOT NULL,
    pnl NUMERIC(20, 8),
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    signal_strength VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_run ON backtest_trades(backtest_id);

-- Run ANALYZE on all new tables
ANALYZE copy_trading_profiles;
ANALYZE copy_trades;
ANALYZE trading_strategies;
ANALYZE strategy_trades;
ANALYZE advanced_orders;
ANALYZE price_history;
ANALYZE technical_indicators;
ANALYZE market_correlations;
ANALYZE suspicious_activities;
ANALYZE ai_market_summaries;
ANALYZE leaderboard_entries;
ANALYZE watchlists;
ANALYZE watchlist_items;
ANALYZE trade_journal_entries;
ANALYZE cross_platform_odds;
ANALYZE order_book_snapshots;
ANALYZE news_articles;
ANALYZE news_market_links;
ANALYZE backtest_runs;
ANALYZE backtest_trades;
