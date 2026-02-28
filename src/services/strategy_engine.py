"""Multi-Strategy Trading Engine - Run multiple strategies simultaneously."""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TradingStrategy, StrategyTrade, PriceHistory
from ..utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_STRATEGIES = [
    {
        "name": "ML Ensemble",
        "strategy_type": "ML_ENSEMBLE",
        "description": "Primary ML-based strategy using XGBoost + LightGBM ensemble predictions to identify mispriced markets",
        "parameters": {
            "min_edge": 0.05,
            "min_confidence": 0.55,
            "signal_strengths": ["STRONG", "MEDIUM"],
            "model_weights": {"xgboost": 0.6, "lightgbm": 0.4},
        },
    },
    {
        "name": "Trend Following",
        "strategy_type": "TREND_FOLLOWING",
        "description": "Identifies markets with sustained directional momentum and trades in the trend direction",
        "parameters": {
            "lookback_hours": 24,
            "min_trend_strength": 0.03,
            "confirmation_periods": 3,
            "exit_reversal_threshold": 0.02,
            "moving_avg_periods": [6, 12, 24],
        },
    },
    {
        "name": "Mean Reversion",
        "strategy_type": "MEAN_REVERSION",
        "description": "Identifies markets that have deviated significantly from their average and bets on reversion",
        "parameters": {
            "lookback_hours": 48,
            "z_score_entry": 2.0,
            "z_score_exit": 0.5,
            "min_samples": 10,
            "bollinger_period": 20,
            "bollinger_std": 2.0,
        },
    },
    {
        "name": "Momentum",
        "strategy_type": "MOMENTUM",
        "description": "Trades based on price momentum and volume surges across active markets",
        "parameters": {
            "momentum_window_hours": 12,
            "volume_surge_threshold": 2.0,
            "min_price_change": 0.05,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "rsi_period": 14,
        },
    },
    {
        "name": "Event Driven",
        "strategy_type": "EVENT_DRIVEN",
        "description": "Positions ahead of known catalysts like elections, economic events, and scheduled announcements",
        "parameters": {
            "pre_event_hours": 48,
            "post_event_hours": 24,
            "min_expected_move": 0.10,
            "event_categories": ["politics", "economics", "sports", "crypto"],
            "volatility_multiplier": 1.5,
        },
    },
    {
        "name": "Arbitrage Scanner",
        "strategy_type": "ARBITRAGE",
        "description": "Detects and exploits pricing inefficiencies where YES + NO prices deviate from $1.00",
        "parameters": {
            "min_profit_pct": 0.5,
            "min_liquidity": 1000,
            "max_execution_time_seconds": 30,
            "fee_estimate_pct": 0.2,
            "cross_platform": True,
        },
    },
]


class StrategyEngine:
    """Multi-strategy trading engine running multiple strategies simultaneously."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def initialize_strategies(self) -> List[Dict]:
        """Initialize default strategies if they don't exist."""
        created = []
        for strat_def in DEFAULT_STRATEGIES:
            try:
                existing = await self.db.execute(
                    select(TradingStrategy).where(TradingStrategy.name == strat_def["name"])
                )
                if existing.scalar_one_or_none():
                    continue

                strategy = TradingStrategy(
                    name=strat_def["name"],
                    strategy_type=strat_def["strategy_type"],
                    description=strat_def["description"],
                    parameters=strat_def["parameters"],
                    is_active=True,
                    allocation_pct=round(100 / len(DEFAULT_STRATEGIES), 2),
                )
                self.db.add(strategy)
                created.append(strat_def["name"])
            except Exception as e:
                logger.error("Failed to create strategy", name=strat_def["name"], error=str(e))

        if created:
            await self.db.commit()
            logger.info("Initialized strategies", count=len(created), names=created)
        return [{"name": n, "status": "created"} for n in created]

    async def get_all_strategies(self) -> List[Dict]:
        """Get all trading strategies with their performance metrics."""
        try:
            result = await self.db.execute(
                select(TradingStrategy).order_by(desc(TradingStrategy.total_pnl))
            )
            strategies = result.scalars().all()

            if not strategies:
                await self.initialize_strategies()
                result = await self.db.execute(
                    select(TradingStrategy).order_by(desc(TradingStrategy.total_pnl))
                )
                strategies = result.scalars().all()

            return [self._strategy_to_dict(s) for s in strategies]
        except Exception as e:
            logger.error("Failed to get strategies", error=str(e))
            return [self._default_strategy_dict(s) for s in DEFAULT_STRATEGIES]

    async def get_strategy(self, strategy_id: int) -> Optional[Dict]:
        """Get a single strategy by ID."""
        try:
            result = await self.db.execute(
                select(TradingStrategy).where(TradingStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            return self._strategy_to_dict(strategy) if strategy else None
        except Exception as e:
            logger.error("Failed to get strategy", id=strategy_id, error=str(e))
            return None

    async def toggle_strategy(self, strategy_id: int, is_active: bool) -> Optional[Dict]:
        """Enable or disable a strategy."""
        try:
            result = await self.db.execute(
                select(TradingStrategy).where(TradingStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                return None

            strategy.is_active = is_active
            await self.db.commit()
            await self.db.refresh(strategy)
            logger.info("Strategy toggled", name=strategy.name, active=is_active)
            return self._strategy_to_dict(strategy)
        except Exception as e:
            logger.error("Failed to toggle strategy", error=str(e))
            await self.db.rollback()
            return None

    async def update_strategy_params(self, strategy_id: int, parameters: Dict) -> Optional[Dict]:
        """Update strategy parameters."""
        try:
            result = await self.db.execute(
                select(TradingStrategy).where(TradingStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                return None

            current_params = strategy.parameters or {}
            current_params.update(parameters)
            strategy.parameters = current_params
            await self.db.commit()
            await self.db.refresh(strategy)
            return self._strategy_to_dict(strategy)
        except Exception as e:
            logger.error("Failed to update strategy params", error=str(e))
            await self.db.rollback()
            return None

    async def run_trend_following(self, market_id: str, prices: List[float]) -> Optional[Dict]:
        """Run trend following strategy on price data."""
        if len(prices) < 6:
            return None

        sma_short = sum(prices[-6:]) / 6
        sma_long = sum(prices[-24:]) / max(len(prices[-24:]), 1)
        current = prices[-1]

        trend_strength = (sma_short - sma_long) / sma_long if sma_long != 0 else 0

        if abs(trend_strength) < 0.03:
            return None

        return {
            "market_id": market_id,
            "strategy": "TREND_FOLLOWING",
            "side": "YES" if trend_strength > 0 else "NO",
            "signal_strength": "STRONG" if abs(trend_strength) > 0.08 else "MEDIUM",
            "trend_strength": round(trend_strength, 4),
            "sma_short": round(sma_short, 4),
            "sma_long": round(sma_long, 4),
            "current_price": current,
        }

    async def run_mean_reversion(self, market_id: str, prices: List[float]) -> Optional[Dict]:
        """Run mean reversion strategy on price data."""
        if len(prices) < 10:
            return None

        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std = math.sqrt(variance) if variance > 0 else 0.001
        current = prices[-1]
        z_score = (current - mean) / std

        if abs(z_score) < 2.0:
            return None

        return {
            "market_id": market_id,
            "strategy": "MEAN_REVERSION",
            "side": "NO" if z_score > 2.0 else "YES",
            "signal_strength": "STRONG" if abs(z_score) > 3.0 else "MEDIUM",
            "z_score": round(z_score, 4),
            "mean_price": round(mean, 4),
            "std_dev": round(std, 4),
            "current_price": current,
        }

    async def run_momentum(self, market_id: str, prices: List[float], volumes: Optional[List[float]] = None) -> Optional[Dict]:
        """Run momentum strategy on price and volume data."""
        if len(prices) < 3:
            return None

        price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] != 0 else 0

        volume_surge = 1.0
        if volumes and len(volumes) > 1:
            avg_vol = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else 1
            volume_surge = volumes[-1] / avg_vol if avg_vol > 0 else 1

        rsi = self._calculate_rsi(prices)

        if abs(price_change) < 0.05 and volume_surge < 2.0:
            return None

        if rsi is not None and (rsi > 70 or rsi < 30):
            side = "NO" if rsi > 70 else "YES"
            signal = "STRONG"
        elif price_change > 0.05:
            side = "YES"
            signal = "STRONG" if price_change > 0.10 else "MEDIUM"
        elif price_change < -0.05:
            side = "NO"
            signal = "STRONG" if price_change < -0.10 else "MEDIUM"
        else:
            return None

        return {
            "market_id": market_id,
            "strategy": "MOMENTUM",
            "side": side,
            "signal_strength": signal,
            "price_change_pct": round(price_change * 100, 2),
            "volume_surge": round(volume_surge, 2),
            "rsi": round(rsi, 2) if rsi else None,
            "current_price": prices[-1],
        }

    async def get_strategy_performance(self) -> Dict:
        """Get combined performance across all strategies."""
        try:
            result = await self.db.execute(select(TradingStrategy))
            strategies = result.scalars().all()

            total_pnl = sum(float(s.total_pnl) for s in strategies)
            total_trades = sum(s.total_trades for s in strategies)
            active_strategies = sum(1 for s in strategies if s.is_active)

            return {
                "total_strategies": len(strategies),
                "active_strategies": active_strategies,
                "total_pnl": round(total_pnl, 2),
                "total_trades": total_trades,
                "strategy_breakdown": [
                    {
                        "name": s.name,
                        "type": s.strategy_type,
                        "is_active": s.is_active,
                        "pnl": float(s.total_pnl),
                        "trades": s.total_trades,
                        "win_rate": float(s.win_rate),
                        "allocation_pct": float(s.allocation_pct),
                    }
                    for s in strategies
                ],
            }
        except Exception as e:
            logger.error("Failed to get strategy performance", error=str(e))
            return {"total_strategies": 0, "active_strategies": 0, "total_pnl": 0, "total_trades": 0, "strategy_breakdown": []}

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI from price series."""
        if len(prices) < period + 1:
            return None

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _strategy_to_dict(self, strategy: TradingStrategy) -> Dict:
        return {
            "id": strategy.id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "description": strategy.description,
            "parameters": strategy.parameters,
            "is_active": strategy.is_active,
            "allocation_pct": float(strategy.allocation_pct),
            "max_positions": strategy.max_positions,
            "max_position_size": float(strategy.max_position_size),
            "win_rate": float(strategy.win_rate),
            "total_pnl": float(strategy.total_pnl),
            "total_trades": strategy.total_trades,
            "sharpe_ratio": float(strategy.sharpe_ratio) if strategy.sharpe_ratio else None,
            "last_signal_at": strategy.last_signal_at.isoformat() if strategy.last_signal_at else None,
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
        }

    def _default_strategy_dict(self, strat_def: Dict) -> Dict:
        return {
            "id": None,
            "name": strat_def["name"],
            "strategy_type": strat_def["strategy_type"],
            "description": strat_def["description"],
            "parameters": strat_def["parameters"],
            "is_active": True,
            "allocation_pct": round(100 / len(DEFAULT_STRATEGIES), 2),
            "max_positions": 10,
            "max_position_size": 500,
            "win_rate": 0,
            "total_pnl": 0,
            "total_trades": 0,
            "sharpe_ratio": None,
            "last_signal_at": None,
            "created_at": None,
        }
