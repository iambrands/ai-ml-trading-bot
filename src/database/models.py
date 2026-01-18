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

