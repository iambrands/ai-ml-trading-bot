"""SQLAlchemy models for database tables."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship

from .connection import Base


class Market(Base):
    """Market model."""

    __tablename__ = "markets"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(66), unique=True, nullable=False, index=True)
    condition_id = Column(String(66), nullable=False)
    question = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    resolution_date = Column(DateTime, nullable=True, index=True)
    outcome = Column(String(3), nullable=True, index=True)  # YES/NO/NULL
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    feature_snapshots = relationship("FeatureSnapshot", back_populates="market", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="market", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="market")


class FeatureSnapshot(Base):
    """Feature snapshot model."""

    __tablename__ = "feature_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(66), ForeignKey("markets.market_id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_time = Column(DateTime, nullable=False, index=True)
    features = Column(JSON, nullable=False)
    embeddings_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    market = relationship("Market", back_populates="feature_snapshots")

    __table_args__ = (UniqueConstraint("market_id", "snapshot_time", name="uq_feature_snapshot"),)


class Prediction(Base):
    """Model prediction."""

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(66), ForeignKey("markets.market_id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_time = Column(DateTime, nullable=False, index=True)
    model_probability = Column(Numeric(10, 6), nullable=False)
    market_price = Column(Numeric(10, 6), nullable=False)
    edge = Column(Numeric(10, 6), nullable=False)
    confidence = Column(Numeric(10, 6), nullable=False)
    model_version = Column(String(50), nullable=False)
    model_predictions = Column(JSON, nullable=True)  # Individual model outputs
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    market = relationship("Market", back_populates="predictions")
    signals = relationship("Signal", back_populates="prediction")


class Signal(Base):
    """Trading signal."""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True)
    market_id = Column(String(66), ForeignKey("markets.market_id"), nullable=False, index=True)
    side = Column(String(3), nullable=False)  # YES/NO
    signal_strength = Column(String(10), nullable=False)  # STRONG/MEDIUM/WEAK
    suggested_size = Column(Numeric(20, 8), nullable=True)
    executed = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    prediction = relationship("Prediction", back_populates="signals")
    market = relationship("Market", back_populates="signals")
    trades = relationship("Trade", back_populates="signal")


class Trade(Base):
    """Trade record."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)
    market_id = Column(String(66), nullable=False, index=True)
    side = Column(String(3), nullable=False)  # YES/NO
    entry_price = Column(Numeric(10, 6), nullable=False)
    size = Column(Numeric(20, 8), nullable=False)
    exit_price = Column(Numeric(10, 6), nullable=True)
    pnl = Column(Numeric(20, 8), nullable=True)
    status = Column(String(20), nullable=False, index=True)  # OPEN/CLOSED/CANCELLED
    paper_trading = Column(Boolean, default=False, nullable=False, index=True)
    entry_time = Column(DateTime, nullable=False, index=True)
    exit_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    signal = relationship("Signal", back_populates="trades")


class ModelPerformance(Base):
    """Model performance tracking."""

    __tablename__ = "model_performance"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False)
    model_version = Column(String(50), nullable=False)
    evaluation_date = Column(Date, nullable=False, index=True)
    accuracy = Column(Numeric(10, 6), nullable=True)
    brier_score = Column(Numeric(10, 6), nullable=True)
    log_loss = Column(Numeric(10, 6), nullable=True)
    auc_roc = Column(Numeric(10, 6), nullable=True)
    sample_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("model_name", "model_version", "evaluation_date", name="uq_model_performance"),)


class PortfolioSnapshot(Base):
    """Portfolio snapshot for tracking."""

    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_time = Column(DateTime, nullable=False, index=True)
    total_value = Column(Numeric(20, 8), nullable=False)
    cash = Column(Numeric(20, 8), nullable=False)
    positions_value = Column(Numeric(20, 8), nullable=False)
    total_exposure = Column(Numeric(20, 8), nullable=False)
    daily_pnl = Column(Numeric(20, 8), nullable=True)
    unrealized_pnl = Column(Numeric(20, 8), nullable=True)
    realized_pnl = Column(Numeric(20, 8), nullable=True)
    paper_trading = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Alert(Base):
    """Alert configuration."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), default="default", nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # SIGNAL, PORTFOLIO, PREDICTION, CUSTOM
    alert_rule = Column(JSON, nullable=False)  # Flexible rule configuration
    notification_method = Column(String(50), nullable=False)  # EMAIL, WEBHOOK, TELEGRAM, SMS
    notification_target = Column(Text, nullable=False)  # Email, webhook URL, etc.
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")


class AlertHistory(Base):
    """Alert history for tracking."""

    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)
    market_id = Column(String(66), nullable=True)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Relationships
    alert = relationship("Alert", back_populates="history")
    signal = relationship("Signal")


class AnalyticsCache(Base):
    """Analytics cache for performance."""

    __tablename__ = "analytics_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    cache_data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class WhaleWallet(Base):
    """Whale wallet model for tracking top traders."""

    __tablename__ = "whale_wallets"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    nickname = Column(String(100), nullable=True)
    total_volume = Column(Numeric(20, 2), default=0, nullable=False)
    total_trades = Column(Integer, default=0, nullable=False)
    win_rate = Column(Numeric(5, 4), default=0, nullable=False)
    total_profit = Column(Numeric(20, 2), default=0, nullable=False)
    rank = Column(Integer, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    first_seen_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    trades = relationship("WhaleTrade", back_populates="whale", cascade="all, delete-orphan")
    alerts = relationship("WhaleAlert", back_populates="whale", cascade="all, delete-orphan")


class WhaleTrade(Base):
    """Whale trade record."""

    __tablename__ = "whale_trades"

    id = Column(Integer, primary_key=True, index=True)
    whale_id = Column(Integer, ForeignKey("whale_wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)
    trade_type = Column(String(10), nullable=False)  # BUY/SELL
    outcome = Column(String(10), nullable=False)  # YES/NO
    amount = Column(Numeric(20, 2), nullable=False)
    price = Column(Numeric(10, 8), nullable=False)
    trade_value = Column(Numeric(20, 2), nullable=False, index=True)
    transaction_hash = Column(String(66), nullable=True)
    block_number = Column(Integer, nullable=True)
    trade_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    whale = relationship("WhaleWallet", back_populates="trades")
    alerts = relationship("WhaleAlert", back_populates="trade", cascade="all, delete-orphan")


class WhaleAlert(Base):
    """Whale alert for users."""

    __tablename__ = "whale_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, nullable=False, index=True)
    whale_id = Column(Integer, ForeignKey("whale_wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_id = Column(Integer, ForeignKey("whale_trades.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(50), default="large_trade", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    whale = relationship("WhaleWallet", back_populates="alerts")
    trade = relationship("WhaleTrade", back_populates="alerts")


class EconomicEvent(Base):
    """Economic calendar event model."""

    __tablename__ = "economic_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # FOMC, CPI, NFP, GDP
    event_name = Column(String(200), nullable=False)
    event_date = Column(DateTime, nullable=False, index=True)
    release_time = Column(String(10), nullable=True)
    country = Column(String(50), default="US", nullable=False)
    importance = Column(String(20), default="HIGH", nullable=False, index=True)  # HIGH, MEDIUM, LOW
    previous_value = Column(Numeric(10, 4), nullable=True)
    forecast_value = Column(Numeric(10, 4), nullable=True)
    actual_value = Column(Numeric(10, 4), nullable=True)
    currency = Column(String(10), default="USD", nullable=False)
    source = Column(String(100), default="Federal Reserve", nullable=False)
    description = Column(Text, nullable=True)
    external_url = Column(String(500), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    market_relationships = relationship("MarketEvent", back_populates="event", cascade="all, delete-orphan")
    alerts = relationship("EventAlert", back_populates="event", cascade="all, delete-orphan")
    impact_history = relationship("EventMarketImpact", back_populates="event", cascade="all, delete-orphan")


class MarketEvent(Base):
    """Market-event relationship model."""

    __tablename__ = "market_events"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("economic_events.id", ondelete="CASCADE"), nullable=False, index=True)
    relevance_score = Column(Numeric(3, 2), default=0.5, nullable=False, index=True)
    impact_prediction = Column(Text, nullable=True)
    price_before = Column(Numeric(10, 8), nullable=True)
    price_after = Column(Numeric(10, 8), nullable=True)
    measured_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    event = relationship("EconomicEvent", back_populates="market_relationships")

    __table_args__ = (UniqueConstraint("market_id", "event_id", name="uq_market_event"),)


class EventAlert(Base):
    """User event alert model."""

    __tablename__ = "event_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1, nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("economic_events.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_time = Column(DateTime, nullable=False, index=True)
    hours_before = Column(Integer, default=24, nullable=False)
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    event = relationship("EconomicEvent", back_populates="alerts")


class EventMarketImpact(Base):
    """Historical event market impact tracking."""

    __tablename__ = "event_market_impact"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("economic_events.id", ondelete="CASCADE"), nullable=False, index=True)
    market_id = Column(String(100), nullable=True, index=True)
    price_before = Column(Numeric(10, 8), nullable=True)
    price_after = Column(Numeric(10, 8), nullable=True)
    price_change_pct = Column(Numeric(10, 4), nullable=True)
    volume_before = Column(Numeric(20, 2), nullable=True)
    volume_after = Column(Numeric(20, 2), nullable=True)
    volume_change_pct = Column(Numeric(10, 4), nullable=True)
    measured_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    event = relationship("EconomicEvent", back_populates="impact_history")


# ============================================================================
# Copy Trading Models
# ============================================================================

class CopyTradingProfile(Base):
    """Wallet profile tracked for copy trading."""

    __tablename__ = "copy_trading_profiles"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    nickname = Column(String(100), nullable=True)
    total_profit = Column(Numeric(20, 2), default=0, nullable=False)
    win_rate = Column(Numeric(5, 4), default=0, nullable=False)
    total_trades = Column(Integer, default=0, nullable=False)
    avg_position_size = Column(Numeric(20, 2), default=0, nullable=False)
    roi_pct = Column(Numeric(10, 4), default=0, nullable=False)
    is_following = Column(Boolean, default=False, nullable=False, index=True)
    auto_copy = Column(Boolean, default=False, nullable=False)
    copy_percentage = Column(Numeric(5, 2), default=100, nullable=False)
    max_copy_size = Column(Numeric(20, 2), default=1000, nullable=False)
    min_trade_size = Column(Numeric(20, 2), default=10, nullable=False)
    copy_filter_markets = Column(JSON, nullable=True)
    first_seen_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_activity_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    copy_trades = relationship("CopyTrade", back_populates="profile", cascade="all, delete-orphan")


class CopyTrade(Base):
    """Trade copied from a followed wallet."""

    __tablename__ = "copy_trades"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("copy_trading_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    source_wallet = Column(String(42), nullable=False, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)
    side = Column(String(3), nullable=False)
    source_size = Column(Numeric(20, 2), nullable=False)
    copied_size = Column(Numeric(20, 2), nullable=False)
    entry_price = Column(Numeric(10, 6), nullable=False)
    exit_price = Column(Numeric(10, 6), nullable=True)
    pnl = Column(Numeric(20, 8), nullable=True)
    status = Column(String(20), default="OPEN", nullable=False, index=True)
    source_tx_hash = Column(String(66), nullable=True)
    copy_tx_hash = Column(String(66), nullable=True)
    copied_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    profile = relationship("CopyTradingProfile", back_populates="copy_trades")


# ============================================================================
# Multi-Strategy Engine Models
# ============================================================================

class TradingStrategy(Base):
    """Trading strategy configuration."""

    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    strategy_type = Column(String(50), nullable=False, index=True)  # TREND_FOLLOWING, MEAN_REVERSION, MOMENTUM, EVENT_DRIVEN, ARBITRAGE, ML_ENSEMBLE
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    allocation_pct = Column(Numeric(5, 2), default=20, nullable=False)
    max_positions = Column(Integer, default=10, nullable=False)
    max_position_size = Column(Numeric(20, 2), default=500, nullable=False)
    win_rate = Column(Numeric(5, 4), default=0, nullable=False)
    total_pnl = Column(Numeric(20, 8), default=0, nullable=False)
    total_trades = Column(Integer, default=0, nullable=False)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    last_signal_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    strategy_trades = relationship("StrategyTrade", back_populates="strategy", cascade="all, delete-orphan")


class StrategyTrade(Base):
    """Trade generated by a specific strategy."""

    __tablename__ = "strategy_trades"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="SET NULL"), nullable=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    side = Column(String(3), nullable=False)
    entry_price = Column(Numeric(10, 6), nullable=False)
    exit_price = Column(Numeric(10, 6), nullable=True)
    size = Column(Numeric(20, 8), nullable=False)
    pnl = Column(Numeric(20, 8), nullable=True)
    status = Column(String(20), default="OPEN", nullable=False, index=True)
    signal_data = Column(JSON, nullable=True)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    strategy = relationship("TradingStrategy", back_populates="strategy_trades")


# ============================================================================
# Advanced Order Management Models
# ============================================================================

class AdvancedOrder(Base):
    """Advanced order types: trailing stop, take-profit, OCO."""

    __tablename__ = "advanced_orders"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="CASCADE"), nullable=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    order_type = Column(String(30), nullable=False, index=True)  # TRAILING_STOP, TAKE_PROFIT, STOP_LOSS, OCO, BRACKET
    side = Column(String(3), nullable=False)
    trigger_price = Column(Numeric(10, 6), nullable=True)
    trail_amount = Column(Numeric(10, 6), nullable=True)
    trail_pct = Column(Numeric(5, 4), nullable=True)
    take_profit_price = Column(Numeric(10, 6), nullable=True)
    stop_loss_price = Column(Numeric(10, 6), nullable=True)
    highest_price = Column(Numeric(10, 6), nullable=True)
    lowest_price = Column(Numeric(10, 6), nullable=True)
    size = Column(Numeric(20, 8), nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, TRIGGERED, CANCELLED, EXPIRED
    triggered_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ============================================================================
# Price History & Technical Analysis Models
# ============================================================================

class PriceHistory(Base):
    """Historical price data for markets."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    yes_price = Column(Numeric(10, 6), nullable=False)
    no_price = Column(Numeric(10, 6), nullable=False)
    volume = Column(Numeric(20, 2), default=0, nullable=False)
    liquidity = Column(Numeric(20, 2), default=0, nullable=False)
    bid_price = Column(Numeric(10, 6), nullable=True)
    ask_price = Column(Numeric(10, 6), nullable=True)
    spread = Column(Numeric(10, 6), nullable=True)
    open_interest = Column(Numeric(20, 2), nullable=True)
    num_trades = Column(Integer, default=0, nullable=False)
    interval = Column(String(10), default="1h", nullable=False)  # 1m, 5m, 15m, 1h, 4h, 1d
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("market_id", "timestamp", "interval", name="uq_price_history"),)


class TechnicalIndicator(Base):
    """Computed technical indicators for markets."""

    __tablename__ = "technical_indicators"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    indicator_type = Column(String(30), nullable=False, index=True)  # SMA, EMA, RSI, MACD, BOLLINGER, VWAP
    period = Column(Integer, nullable=False)
    value = Column(Numeric(20, 8), nullable=False)
    signal_value = Column(Numeric(20, 8), nullable=True)
    upper_band = Column(Numeric(20, 8), nullable=True)
    lower_band = Column(Numeric(20, 8), nullable=True)
    histogram = Column(Numeric(20, 8), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("market_id", "indicator_type", "period", "timestamp", name="uq_technical_indicator"),)


# ============================================================================
# Market Correlation Models
# ============================================================================

class MarketCorrelation(Base):
    """Correlation between market pairs."""

    __tablename__ = "market_correlations"

    id = Column(Integer, primary_key=True, index=True)
    market_id_a = Column(String(100), nullable=False, index=True)
    market_id_b = Column(String(100), nullable=False, index=True)
    correlation = Column(Numeric(6, 4), nullable=False)
    correlation_type = Column(String(20), default="price", nullable=False)  # price, volume, sentiment
    lookback_hours = Column(Integer, default=168, nullable=False)
    sample_count = Column(Integer, nullable=False)
    p_value = Column(Numeric(10, 8), nullable=True)
    category_a = Column(String(50), nullable=True)
    category_b = Column(String(50), nullable=True)
    calculated_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("market_id_a", "market_id_b", "correlation_type", name="uq_market_correlation"),)


# ============================================================================
# Insider / Suspicious Activity Detection Models
# ============================================================================

class SuspiciousActivity(Base):
    """Detected suspicious or insider trading activity."""

    __tablename__ = "suspicious_activities"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)
    activity_type = Column(String(50), nullable=False, index=True)  # LARGE_POSITION, PRE_EVENT_SPIKE, WASH_TRADING, UNUSUAL_TIMING, COORDINATED
    severity = Column(String(20), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    trade_amount = Column(Numeric(20, 2), nullable=True)
    price_at_detection = Column(Numeric(10, 6), nullable=True)
    price_impact_pct = Column(Numeric(10, 4), nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    evidence = Column(JSON, nullable=True)
    is_reviewed = Column(Boolean, default=False, nullable=False, index=True)
    detected_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ============================================================================
# AI Market Summaries Models
# ============================================================================

class AIMarketSummary(Base):
    """AI-generated market analysis summaries."""

    __tablename__ = "ai_market_summaries"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)
    summary = Column(Text, nullable=False)
    key_factors = Column(JSON, nullable=True)
    sentiment_score = Column(Numeric(5, 4), nullable=True)
    probability_assessment = Column(Numeric(5, 4), nullable=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    risk_level = Column(String(20), nullable=True)
    recommendation = Column(String(20), nullable=True)  # BUY_YES, BUY_NO, HOLD, AVOID
    news_sources = Column(JSON, nullable=True)
    model_used = Column(String(50), default="internal", nullable=False)
    expires_at = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("market_id", "generated_at", name="uq_ai_summary"),)


# ============================================================================
# Leaderboard & Rankings Models
# ============================================================================

class LeaderboardEntry(Base):
    """Leaderboard rankings for traders."""

    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    nickname = Column(String(100), nullable=True)
    rank = Column(Integer, nullable=False, index=True)
    period = Column(String(20), nullable=False, index=True)  # DAILY, WEEKLY, MONTHLY, ALL_TIME
    total_profit = Column(Numeric(20, 2), default=0, nullable=False)
    total_volume = Column(Numeric(20, 2), default=0, nullable=False)
    win_rate = Column(Numeric(5, 4), default=0, nullable=False)
    total_trades = Column(Integer, default=0, nullable=False)
    roi_pct = Column(Numeric(10, 4), default=0, nullable=False)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown = Column(Numeric(10, 4), nullable=True)
    best_trade_pnl = Column(Numeric(20, 2), nullable=True)
    worst_trade_pnl = Column(Numeric(20, 2), nullable=True)
    avg_hold_time_hours = Column(Numeric(10, 2), nullable=True)
    active_positions = Column(Integer, default=0, nullable=False)
    score = Column(Numeric(20, 4), default=0, nullable=False, index=True)
    calculated_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("wallet_address", "period", "calculated_at", name="uq_leaderboard_entry"),)


# ============================================================================
# Watchlist Models
# ============================================================================

class Watchlist(Base):
    """User watchlist for tracking specific markets."""

    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), default="default", nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_watchlist_name"),)


class WatchlistItem(Base):
    """Individual market in a watchlist."""

    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    target_price = Column(Numeric(10, 6), nullable=True)
    alert_on_price = Column(Boolean, default=False, nullable=False)
    price_at_add = Column(Numeric(10, 6), nullable=True)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)

    watchlist = relationship("Watchlist", back_populates="items")

    __table_args__ = (UniqueConstraint("watchlist_id", "market_id", name="uq_watchlist_item"),)


# ============================================================================
# Trade Journal Models
# ============================================================================

class TradeJournalEntry(Base):
    """Detailed trade journal with notes, tags, and analysis."""

    __tablename__ = "trade_journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id", ondelete="SET NULL"), nullable=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    market_question = Column(Text, nullable=True)
    entry_reason = Column(Text, nullable=True)
    exit_reason = Column(Text, nullable=True)
    strategy_used = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    pre_trade_analysis = Column(Text, nullable=True)
    post_trade_review = Column(Text, nullable=True)
    emotional_state = Column(String(30), nullable=True)  # CONFIDENT, NEUTRAL, ANXIOUS, FOMO, DISCIPLINED
    lesson_learned = Column(Text, nullable=True)
    screenshots = Column(JSON, nullable=True)
    entry_price = Column(Numeric(10, 6), nullable=True)
    exit_price = Column(Numeric(10, 6), nullable=True)
    pnl = Column(Numeric(20, 8), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 self-rating of trade quality
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# ============================================================================
# Cross-Platform Odds Comparison Models
# ============================================================================

class CrossPlatformOdds(Base):
    """Odds comparison across prediction market platforms."""

    __tablename__ = "cross_platform_odds"

    id = Column(Integer, primary_key=True, index=True)
    market_question = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, index=True)
    polymarket_id = Column(String(100), nullable=True, index=True)
    kalshi_id = Column(String(100), nullable=True)
    predictit_id = Column(String(100), nullable=True)
    metaculus_id = Column(String(100), nullable=True)
    polymarket_yes = Column(Numeric(10, 6), nullable=True)
    polymarket_no = Column(Numeric(10, 6), nullable=True)
    polymarket_volume = Column(Numeric(20, 2), nullable=True)
    kalshi_yes = Column(Numeric(10, 6), nullable=True)
    kalshi_no = Column(Numeric(10, 6), nullable=True)
    kalshi_volume = Column(Numeric(20, 2), nullable=True)
    predictit_yes = Column(Numeric(10, 6), nullable=True)
    predictit_no = Column(Numeric(10, 6), nullable=True)
    metaculus_prediction = Column(Numeric(10, 6), nullable=True)
    max_spread = Column(Numeric(10, 6), nullable=True)
    arbitrage_opportunity = Column(Boolean, default=False, nullable=False, index=True)
    arbitrage_profit_pct = Column(Numeric(10, 4), nullable=True)
    matched_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("polymarket_id", "matched_at", name="uq_cross_platform"),)


# ============================================================================
# Order Book Analysis Models
# ============================================================================

class OrderBookSnapshot(Base):
    """Order book depth snapshots for analysis."""

    __tablename__ = "order_book_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    bids = Column(JSON, nullable=False)
    asks = Column(JSON, nullable=False)
    best_bid = Column(Numeric(10, 6), nullable=True)
    best_ask = Column(Numeric(10, 6), nullable=True)
    mid_price = Column(Numeric(10, 6), nullable=True)
    spread = Column(Numeric(10, 6), nullable=True)
    spread_pct = Column(Numeric(10, 6), nullable=True)
    bid_depth_10pct = Column(Numeric(20, 2), nullable=True)
    ask_depth_10pct = Column(Numeric(20, 2), nullable=True)
    imbalance_ratio = Column(Numeric(10, 6), nullable=True)
    total_bid_volume = Column(Numeric(20, 2), nullable=True)
    total_ask_volume = Column(Numeric(20, 2), nullable=True)
    snapshot_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


# ============================================================================
# News Aggregation Models
# ============================================================================

class NewsArticle(Base):
    """Aggregated news articles relevant to markets."""

    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    content_snippet = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    category = Column(String(50), nullable=True, index=True)
    sentiment_score = Column(Numeric(5, 4), nullable=True)
    sentiment_label = Column(String(20), nullable=True)  # POSITIVE, NEGATIVE, NEUTRAL
    relevance_score = Column(Numeric(5, 4), nullable=True)
    image_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=False, index=True)
    fetched_at = Column(DateTime, server_default=func.now(), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    market_links = relationship("NewsMarketLink", back_populates="article", cascade="all, delete-orphan")


class NewsMarketLink(Base):
    """Link between news articles and markets."""

    __tablename__ = "news_market_links"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    market_id = Column(String(100), nullable=False, index=True)
    relevance_score = Column(Numeric(5, 4), default=0.5, nullable=False)
    impact_direction = Column(String(10), nullable=True)  # UP, DOWN, NEUTRAL
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    article = relationship("NewsArticle", back_populates="market_links")

    __table_args__ = (UniqueConstraint("article_id", "market_id", name="uq_news_market_link"),)


# ============================================================================
# Backtesting Models
# ============================================================================

class BacktestRun(Base):
    """Backtesting run results."""

    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    strategy_name = Column(String(100), nullable=False, index=True)
    strategy_params = Column(JSON, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Numeric(20, 2), nullable=False)
    final_capital = Column(Numeric(20, 2), nullable=True)
    total_return_pct = Column(Numeric(10, 4), nullable=True)
    annualized_return_pct = Column(Numeric(10, 4), nullable=True)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    sortino_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown_pct = Column(Numeric(10, 4), nullable=True)
    win_rate = Column(Numeric(5, 4), nullable=True)
    profit_factor = Column(Numeric(10, 4), nullable=True)
    total_trades = Column(Integer, default=0, nullable=False)
    avg_trade_pnl = Column(Numeric(20, 8), nullable=True)
    avg_hold_time_hours = Column(Numeric(10, 2), nullable=True)
    calmar_ratio = Column(Numeric(10, 4), nullable=True)
    equity_curve = Column(JSON, nullable=True)
    monthly_returns = Column(JSON, nullable=True)
    status = Column(String(20), default="RUNNING", nullable=False, index=True)  # RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    backtest_trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")


class BacktestTrade(Base):
    """Individual trade within a backtest run."""

    __tablename__ = "backtest_trades"

    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    market_id = Column(String(100), nullable=False)
    side = Column(String(3), nullable=False)
    entry_price = Column(Numeric(10, 6), nullable=False)
    exit_price = Column(Numeric(10, 6), nullable=True)
    size = Column(Numeric(20, 8), nullable=False)
    pnl = Column(Numeric(20, 8), nullable=True)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    signal_strength = Column(String(10), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    backtest_run = relationship("BacktestRun", back_populates="backtest_trades")

