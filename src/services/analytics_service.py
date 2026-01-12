"""Analytics service for dashboard metrics and charts."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

import numpy as np
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Prediction, Signal, Trade, PortfolioSnapshot
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for calculating analytics and metrics."""

    def __init__(self, db: AsyncSession):
        """Initialize analytics service."""
        self.db = db

    async def get_prediction_accuracy(self, days: int = 30, paper_trading: bool = False) -> Dict:
        """
        Calculate prediction accuracy metrics.
        
        Args:
            days: Number of days to look back
            paper_trading: Filter by paper trading trades
            
        Returns:
            Dictionary with accuracy metrics
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get resolved predictions (markets that have outcomes)
            query = select(Prediction).join(
                Prediction.market
            ).where(
                and_(
                    Prediction.prediction_time >= cutoff_date,
                    Prediction.market.has(outcome__isnot=None)
                )
            )
            
            result = await self.db.execute(query)
            predictions = result.scalars().all()
            
            if not predictions:
                return {
                    "total": 0,
                    "correct": 0,
                    "accuracy": 0.0,
                    "brier_score": 0.0
                }
            
            correct = 0
            total = 0
            brier_scores = []
            
            for pred in predictions:
                market = pred.market
                if not market.outcome:
                    continue
                
                # Check if prediction was correct
                model_prob = float(pred.model_probability)
                actual_outcome = 1.0 if market.outcome == "YES" else 0.0
                
                # Prediction is correct if model_prob > 0.5 and outcome is YES, or model_prob < 0.5 and outcome is NO
                predicted_yes = model_prob > 0.5
                actual_yes = market.outcome == "YES"
                
                if predicted_yes == actual_yes:
                    correct += 1
                total += 1
                
                # Calculate Brier score
                brier = (model_prob - actual_outcome) ** 2
                brier_scores.append(brier)
            
            accuracy = (correct / total) if total > 0 else 0.0
            avg_brier = np.mean(brier_scores) if brier_scores else 0.0
            
            return {
                "total": total,
                "correct": correct,
                "accuracy": round(accuracy, 4),
                "brier_score": round(avg_brier, 4),
                "days": days
            }
        except Exception as e:
            logger.error("Failed to calculate prediction accuracy", error=str(e))
            return {"total": 0, "correct": 0, "accuracy": 0.0, "brier_score": 0.0}

    async def get_trade_performance(self, days: int = 30, paper_trading: bool = False) -> Dict:
        """
        Calculate trade performance metrics.
        
        Args:
            days: Number of days to look back
            paper_trading: Filter by paper trading
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = select(Trade).where(
                and_(
                    Trade.entry_time >= cutoff_date,
                    Trade.paper_trading == paper_trading
                )
            )
            
            result = await self.db.execute(query)
            trades = result.scalars().all()
            
            if not trades:
                return {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "avg_pnl": 0.0,
                    "profit_factor": 0.0
                }
            
            closed_trades = [t for t in trades if t.status == "CLOSED" and t.pnl is not None]
            open_trades = [t for t in trades if t.status == "OPEN"]
            
            if not closed_trades:
                return {
                    "total_trades": len(trades),
                    "open_trades": len(open_trades),
                    "closed_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "avg_pnl": 0.0,
                    "profit_factor": 0.0
                }
            
            # Calculate metrics
            wins = [t for t in closed_trades if float(t.pnl) > 0]
            losses = [t for t in closed_trades if float(t.pnl) <= 0]
            
            win_rate = len(wins) / len(closed_trades) if closed_trades else 0.0
            total_pnl = sum(float(t.pnl) for t in closed_trades)
            avg_pnl = total_pnl / len(closed_trades) if closed_trades else 0.0
            
            # Profit factor = total wins / total losses (absolute)
            total_wins = sum(float(t.pnl) for t in wins)
            total_losses = abs(sum(float(t.pnl) for t in losses))
            profit_factor = total_wins / total_losses if total_losses > 0 else (total_wins if total_wins > 0 else 0.0)
            
            return {
                "total_trades": len(trades),
                "open_trades": len(open_trades),
                "closed_trades": len(closed_trades),
                "win_rate": round(win_rate, 4),
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "profit_factor": round(profit_factor, 2),
                "days": days
            }
        except Exception as e:
            logger.error("Failed to calculate trade performance", error=str(e))
            return {"total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0}

    async def get_edge_distribution(self, days: int = 30) -> Dict:
        """
        Get edge distribution for signals.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with edge distribution data
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = select(Signal).join(
                Signal.prediction
            ).where(
                Signal.created_at >= cutoff_date
            )
            
            result = await self.db.execute(query)
            signals = result.scalars().all()
            
            if not signals:
                return {
                    "bins": [],
                    "counts": [],
                    "mean": 0.0,
                    "median": 0.0
                }
            
            edges = [abs(float(s.prediction.edge)) for s in signals if s.prediction]
            
            if not edges:
                return {"bins": [], "counts": [], "mean": 0.0, "median": 0.0}
            
            # Create histogram
            bins = np.linspace(0, max(edges) if edges else 0.5, 10)
            counts, bin_edges = np.histogram(edges, bins=bins)
            
            return {
                "bins": [round(float(b), 4) for b in bin_edges],
                "counts": [int(c) for c in counts],
                "mean": round(float(np.mean(edges)), 4),
                "median": round(float(np.median(edges)), 4),
                "total_signals": len(signals)
            }
        except Exception as e:
            logger.error("Failed to calculate edge distribution", error=str(e))
            return {"bins": [], "counts": [], "mean": 0.0, "median": 0.0}

    async def get_portfolio_metrics(self, days: int = 30, paper_trading: bool = False) -> Dict:
        """
        Get portfolio performance metrics.
        
        Args:
            days: Number of days to look back
            paper_trading: Filter by paper trading
            
        Returns:
            Dictionary with portfolio metrics
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = select(PortfolioSnapshot).where(
                and_(
                    PortfolioSnapshot.snapshot_time >= cutoff_date,
                    PortfolioSnapshot.paper_trading == paper_trading
                )
            ).order_by(
                PortfolioSnapshot.snapshot_time
            )
            
            result = await self.db.execute(query)
            snapshots = result.scalars().all()
            
            if not snapshots or len(snapshots) < 2:
                return {
                    "total_return": 0.0,
                    "daily_returns": [],
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0
                }
            
            # Calculate returns
            values = [float(s.total_value) for s in snapshots]
            initial_value = values[0]
            final_value = values[-1]
            total_return = ((final_value - initial_value) / initial_value) if initial_value > 0 else 0.0
            
            # Daily returns
            daily_returns = []
            for i in range(1, len(values)):
                if values[i-1] > 0:
                    daily_return = (values[i] - values[i-1]) / values[i-1]
                    daily_returns.append(daily_return)
            
            # Sharpe ratio (simplified - annualized)
            if daily_returns:
                mean_return = np.mean(daily_returns)
                std_return = np.std(daily_returns)
                sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0.0
            else:
                sharpe = 0.0
            
            # Max drawdown
            peak = values[0]
            max_dd = 0.0
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else 0.0
                if drawdown > max_dd:
                    max_dd = drawdown
            
            return {
                "total_return": round(total_return, 4),
                "daily_returns": [round(r, 6) for r in daily_returns],
                "sharpe_ratio": round(sharpe, 4),
                "max_drawdown": round(max_dd, 4),
                "initial_value": round(initial_value, 2),
                "final_value": round(final_value, 2),
                "days": days
            }
        except Exception as e:
            logger.error("Failed to calculate portfolio metrics", error=str(e))
            return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 0.0}

    async def get_signal_strength_performance(self, days: int = 30) -> Dict:
        """
        Get performance by signal strength.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with performance by signal strength
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = select(Signal).where(
                Signal.created_at >= cutoff_date
            )
            
            result = await self.db.execute(query)
            signals = result.scalars().all()
            
            if not signals:
                return {}
            
            # Group by signal strength
            strength_groups = {"STRONG": [], "MEDIUM": [], "WEAK": []}
            
            for signal in signals:
                strength = signal.signal_strength
                if strength in strength_groups:
                    # Get associated trades
                    trades = [t for t in signal.trades if t.status == "CLOSED" and t.pnl is not None]
                    if trades:
                        strength_groups[strength].extend([float(t.pnl) for t in trades])
            
            performance = {}
            for strength, pnls in strength_groups.items():
                if pnls:
                    performance[strength] = {
                        "count": len(pnls),
                        "avg_pnl": round(float(np.mean(pnls)), 2),
                        "win_rate": round(len([p for p in pnls if p > 0]) / len(pnls), 4),
                        "total_pnl": round(float(sum(pnls)), 2)
                    }
                else:
                    performance[strength] = {
                        "count": 0,
                        "avg_pnl": 0.0,
                        "win_rate": 0.0,
                        "total_pnl": 0.0
                    }
            
            return performance
        except Exception as e:
            logger.error("Failed to calculate signal strength performance", error=str(e))
            return {}

