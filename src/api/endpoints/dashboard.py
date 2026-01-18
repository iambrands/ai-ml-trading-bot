"""Dashboard endpoints for quick stats and settings."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_db
from ...database.models import Trade, PortfolioSnapshot, Signal, Prediction, Market
from ...config.settings import get_settings
from ...utils.logging import get_logger
from ...utils.datetime_utils import make_naive_utc, now_naive_utc


class TradingSettingsUpdate(BaseModel):
    """Model for trading settings update."""
    min_edge: Optional[float] = None
    min_confidence: Optional[float] = None
    min_liquidity: Optional[float] = None
    max_position_size: Optional[float] = None
    paper_trading_mode: Optional[bool] = None

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get quick stats for dashboard widget.
    
    Returns:
        Dictionary with portfolio value, P&L, win rate, active positions, etc.
    """
    try:
        settings = get_settings()
        paper_trading = getattr(settings, 'paper_trading_mode', True)
        
        # Get latest portfolio snapshot
        portfolio_result = await db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.paper_trading == paper_trading)
            .order_by(PortfolioSnapshot.snapshot_time.desc())
            .limit(1)
        )
        portfolio = portfolio_result.scalar_one_or_none()
        
        # Get today's date (naive UTC)
        today_start = make_naive_utc(datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0))
        
        # Get today's trades
        today_trades_result = await db.execute(
            select(Trade)
            .where(
                and_(
                    Trade.created_at >= today_start,
                    Trade.paper_trading == paper_trading
                )
            )
        )
        today_trades = today_trades_result.scalars().all()
        
        # Calculate today's P&L
        today_pnl = sum(float(t.pnl or 0) for t in today_trades if t.status == "CLOSED" and t.pnl is not None)
        
        # Get all closed trades for win rate
        closed_trades_result = await db.execute(
            select(Trade)
            .where(
                and_(
                    Trade.status == "CLOSED",
                    Trade.paper_trading == paper_trading,
                    Trade.pnl.isnot(None)
                )
            )
        )
        closed_trades = closed_trades_result.scalars().all()
        
        # Calculate win rate
        wins = len([t for t in closed_trades if float(t.pnl or 0) > 0])
        win_rate = (wins / len(closed_trades) * 100) if closed_trades else 0.0
        
        # Get active positions
        active_positions_result = await db.execute(
            select(func.count(Trade.id))
            .where(
                and_(
                    Trade.status == "OPEN",
                    Trade.paper_trading == paper_trading
                )
            )
        )
        active_positions = active_positions_result.scalar() or 0
        
        # Portfolio value and change
        portfolio_value = float(portfolio.total_value) if portfolio else 10000.0
        
        # Get previous portfolio snapshot for daily change
        # OPTIMIZED: Use index-friendly query with specific columns
        portfolio_change = 0.0
        if portfolio:
            try:
                prev_result = await db.execute(
                    select(
                        PortfolioSnapshot.id,
                        PortfolioSnapshot.snapshot_time,
                        PortfolioSnapshot.total_value
                    )
                    .where(
                        and_(
                            PortfolioSnapshot.paper_trading == paper_trading,
                            PortfolioSnapshot.snapshot_time < portfolio.snapshot_time
                        )
                    )
                    .order_by(PortfolioSnapshot.snapshot_time.desc())
                    .limit(1)
                )
                prev_portfolio = prev_result.first()
                if prev_portfolio:
                    portfolio_change = float(portfolio.total_value) - float(prev_portfolio.total_value)
            except Exception as e:
                logger.warning("Failed to get previous portfolio snapshot", error=str(e))
                # Don't fail entire request if previous snapshot unavailable
                portfolio_change = 0.0
        
        portfolio_change_pct = (portfolio_change / portfolio_value * 100) if portfolio_value > 0 else 0.0
        
        # Get bot status from health check (simplified - assume running if we can query DB)
        bot_status = "running"
        
        # Get recent activity count (last hour)
        one_hour_ago = make_naive_utc(datetime.now(timezone.utc) - timedelta(hours=1))
        recent_signals_result = await db.execute(
            select(func.count(Signal.id))
            .where(Signal.created_at >= one_hour_ago)
        )
        recent_signals = recent_signals_result.scalar() or 0
        
        recent_trades_result = await db.execute(
            select(func.count(Trade.id))
            .where(
                and_(
                    Trade.created_at >= one_hour_ago,
                    Trade.paper_trading == paper_trading
                )
            )
        )
        recent_trades = recent_trades_result.scalar() or 0
        
        return {
            "portfolio_value": round(portfolio_value, 2),
            "portfolio_change": round(portfolio_change, 2),
            "portfolio_change_pct": round(portfolio_change_pct, 2),
            "active_positions": active_positions,
            "today_pnl": round(today_pnl, 2),
            "today_trades": len(today_trades),
            "win_rate": round(win_rate, 1),
            "bot_status": bot_status,
            "paper_trading": paper_trading,
            "recent_activity": {
                "signals_last_hour": recent_signals,
                "trades_last_hour": recent_trades
            }
        }
        
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


@router.get("/activity")
async def get_recent_activity(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get recent activity feed (trades and signals).
    
    Args:
        limit: Maximum number of activities to return
        
    Returns:
        List of recent activities
    """
    try:
        settings = get_settings()
        paper_trading = getattr(settings, 'paper_trading_mode', True)
        
        # Get recent trades
        trades_result = await db.execute(
            select(Trade)
            .where(Trade.paper_trading == paper_trading)
            .order_by(Trade.created_at.desc())
            .limit(limit)
        )
        trades = trades_result.scalars().all()
        
        # Get recent signals
        signals_result = await db.execute(
            select(Signal)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        )
        signals = signals_result.scalars().all()
        
        # Combine and sort by time
        activities = []
        
        for trade in trades:
            activities.append({
                "type": "trade",
                "id": trade.id,
                "time": trade.created_at.isoformat() if trade.created_at else None,
                "action": f"{trade.side} {trade.status}",
                "market_id": trade.market_id,
                "amount": float(trade.size) if trade.size else 0.0,
                "price": float(trade.entry_price) if trade.entry_price else 0.0,
                "pnl": float(trade.pnl) if trade.pnl else None,
                "status": trade.status
            })
        
        # OPTIMIZED: Batch fetch markets and predictions to avoid N+1 queries
        signal_market_ids = [s.market_id for s in signals if s.market_id]
        signal_prediction_ids = [s.prediction_id for s in signals if s.prediction_id]
        
        # Batch fetch markets
        markets_dict = {}
        if signal_market_ids:
            markets_result = await db.execute(
                select(Market)
                .where(Market.market_id.in_(signal_market_ids))
            )
            markets_dict = {m.market_id: m for m in markets_result.scalars().all()}
        
        # Batch fetch predictions
        predictions_dict = {}
        if signal_prediction_ids:
            predictions_result = await db.execute(
                select(Prediction)
                .where(Prediction.id.in_(signal_prediction_ids))
            )
            predictions_dict = {p.id: p for p in predictions_result.scalars().all()}
        
        for signal in signals:
            # Get market question from batch-fetched dict
            market = markets_dict.get(signal.market_id)
            market_question = market.question if market else signal.market_id[:30]
            
            # Get prediction for edge from batch-fetched dict
            edge = 0.0
            if signal.prediction_id:
                prediction = predictions_dict.get(signal.prediction_id)
                edge = float(prediction.edge) if prediction and prediction.edge else 0.0
            
            activities.append({
                "type": "signal",
                "id": signal.id,
                "time": signal.created_at.isoformat() if signal.created_at else None,
                "action": f"SIGNAL {signal.side}",
                "market_id": signal.market_id,
                "market_question": market_question,
                "edge": round(edge * 100, 2),  # Convert to percentage
                "strength": signal.signal_strength,
                "executed": getattr(signal, 'executed', False)
            })
        
        # Sort by time (most recent first)
        activities.sort(key=lambda x: x.get("time") or "", reverse=True)
        activities = activities[:limit]
        
        return {
            "activities": activities,
            "count": len(activities)
        }
        
    except Exception as e:
        logger.error("Failed to get recent activity", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get recent activity: {str(e)}")


@router.get("/settings")
async def get_trading_settings() -> dict:
    """
    Get current trading settings.
    
    Returns:
        Dictionary with current trading settings
    """
    try:
        settings = get_settings()
        
        return {
            "min_edge": getattr(settings, 'min_edge', 0.05),
            "min_confidence": getattr(settings, 'min_confidence', 0.55),
            "min_liquidity": getattr(settings, 'min_liquidity', 500.0),
            "max_position_size": getattr(settings, 'max_position_size', 100.0),
            "paper_trading_mode": getattr(settings, 'paper_trading_mode', True),
            "auto_signals": True,  # Always enabled
            "auto_trades": getattr(settings, 'auto_trades', False)
        }
        
    except Exception as e:
        logger.error("Failed to get trading settings", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get trading settings: {str(e)}")


@router.post("/settings")
async def update_trading_settings(
    settings_update: TradingSettingsUpdate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Update trading settings.
    
    Note: This updates the settings object but doesn't persist to file.
    For production, you'd want to save to database or config file.
    
    Args:
        min_edge: Minimum edge threshold (0.01 = 1%)
        min_confidence: Minimum confidence threshold (0.50 = 50%)
        min_liquidity: Minimum liquidity threshold
        max_position_size: Maximum position size
        paper_trading_mode: Enable/disable paper trading
        
    Returns:
        Updated settings
    """
    try:
        settings = get_settings()
        
        # Update settings if provided
        if settings_update.min_edge is not None:
            settings.min_edge = settings_update.min_edge
        if settings_update.min_confidence is not None:
            settings.min_confidence = settings_update.min_confidence
        if settings_update.min_liquidity is not None:
            settings.min_liquidity = settings_update.min_liquidity
        if settings_update.max_position_size is not None:
            settings.max_position_size = settings_update.max_position_size
        if settings_update.paper_trading_mode is not None:
            settings.paper_trading_mode = settings_update.paper_trading_mode
        
        logger.info("Trading settings updated",
                    min_edge=settings.min_edge,
                    min_confidence=settings.min_confidence,
                    paper_trading_mode=settings.paper_trading_mode)
        
        return {
            "status": "updated",
            "settings": {
                "min_edge": settings.min_edge,
                "min_confidence": settings.min_confidence,
                "min_liquidity": settings.min_liquidity,
                "max_position_size": getattr(settings, 'max_position_size', 100.0),
                "paper_trading_mode": settings.paper_trading_mode
            }
        }
        
    except Exception as e:
        logger.error("Failed to update trading settings", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update trading settings: {str(e)}")

