"""API endpoints for analytics and metrics."""

from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.analytics_service import AnalyticsService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/prediction-accuracy")
async def get_prediction_accuracy(
    days: int = Query(default=30, ge=1, le=365),
    paper_trading: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """Get prediction accuracy metrics."""
    try:
        service = AnalyticsService(db)
        return await service.get_prediction_accuracy(days=days, paper_trading=paper_trading)
    except Exception as e:
        logger.error("Failed to get prediction accuracy", error=str(e))
        return {"total": 0, "correct": 0, "accuracy": 0.0, "brier_score": 0.0}


@router.get("/trade-performance")
async def get_trade_performance(
    days: int = Query(default=30, ge=1, le=365),
    paper_trading: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """Get trade performance metrics."""
    try:
        service = AnalyticsService(db)
        return await service.get_trade_performance(days=days, paper_trading=paper_trading)
    except Exception as e:
        logger.error("Failed to get trade performance", error=str(e))
        return {"total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0}


@router.get("/edge-distribution")
async def get_edge_distribution(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """Get edge distribution for signals."""
    try:
        service = AnalyticsService(db)
        return await service.get_edge_distribution(days=days)
    except Exception as e:
        logger.error("Failed to get edge distribution", error=str(e))
        return {"bins": [], "counts": [], "mean": 0.0, "median": 0.0}


@router.get("/portfolio-metrics")
async def get_portfolio_metrics(
    days: int = Query(default=30, ge=1, le=365),
    paper_trading: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """Get portfolio performance metrics."""
    try:
        service = AnalyticsService(db)
        return await service.get_portfolio_metrics(days=days, paper_trading=paper_trading)
    except Exception as e:
        logger.error("Failed to get portfolio metrics", error=str(e))
        return {"total_return": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 0.0}


@router.get("/signal-strength-performance")
async def get_signal_strength_performance(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """Get performance by signal strength."""
    try:
        service = AnalyticsService(db)
        return await service.get_signal_strength_performance(days=days)
    except Exception as e:
        logger.error("Failed to get signal strength performance", error=str(e))
        return {}


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """Get comprehensive dashboard summary."""
    try:
        service = AnalyticsService(db)
        
        return {
            "prediction_accuracy": await service.get_prediction_accuracy(days=days),
            "trade_performance": await service.get_trade_performance(days=days),
            "edge_distribution": await service.get_edge_distribution(days=days),
            "portfolio_metrics": await service.get_portfolio_metrics(days=days),
            "signal_strength_performance": await service.get_signal_strength_performance(days=days),
            "paper_trading": {
                "trade_performance": await service.get_trade_performance(days=days, paper_trading=True),
                "portfolio_metrics": await service.get_portfolio_metrics(days=days, paper_trading=True),
            }
        }
    except Exception as e:
        logger.error("Failed to get dashboard summary", error=str(e))
        return {}


