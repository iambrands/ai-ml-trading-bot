"""AI Analysis endpoints for explaining data on each page."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ...database.connection import get_db
from ...database.models import Market, Prediction, Signal, Trade, PortfolioSnapshot
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ai", tags=["ai-analysis"])


@router.get("/explain/predictions")
async def explain_predictions(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Explain the predictions page - what the data means and how to interpret it.
    
    This endpoint provides AI-generated explanations of:
    - What predictions are
    - How to read the data
    - What the metrics mean
    - How to use the information
    """
    try:
        # Get sample predictions for context
        result = await db.execute(
            select(Prediction)
            .order_by(desc(Prediction.prediction_time))
            .limit(min(limit, 5))
        )
        predictions = result.scalars().all()
        
        # Get summary statistics
        result = await db.execute(select(func.count(Prediction.id)))
        total_predictions = result.scalar()
        
        result = await db.execute(
            select(func.avg(Prediction.edge)).where(Prediction.edge > 0)
        )
        avg_edge = result.scalar() or 0.0
        
        # Generate explanation (cost-effective: use simple template, not expensive API)
        explanation = _generate_predictions_explanation(predictions, total_predictions, avg_edge)
        
        return {
            "page": "Predictions",
            "explanation": explanation,
            "summary": {
                "total_predictions": total_predictions,
                "average_edge": float(avg_edge) if avg_edge else 0.0,
                "sample_count": len(predictions),
            },
        }
    except Exception as e:
        logger.error("Failed to generate predictions explanation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


@router.get("/explain/signals")
async def explain_signals(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Explain the signals page."""
    try:
        result = await db.execute(
            select(Signal)
            .order_by(desc(Signal.created_at))
            .limit(min(limit, 5))
        )
        signals = result.scalars().all()
        
        result = await db.execute(select(func.count(Signal.id)))
        total_signals = result.scalar()
        
        # Count by strength
        result = await db.execute(
            select(func.count(Signal.id)).where(Signal.signal_strength == "STRONG")
        )
        strong_signals = result.scalar()
        
        explanation = _generate_signals_explanation(signals, total_signals, strong_signals)
        
        return {
            "page": "Signals",
            "explanation": explanation,
            "summary": {
                "total_signals": total_signals,
                "strong_signals": strong_signals,
                "sample_count": len(signals),
            },
        }
    except Exception as e:
        logger.error("Failed to generate signals explanation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


@router.get("/explain/trades")
async def explain_trades(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Explain the trades page."""
    try:
        result = await db.execute(
            select(Trade)
            .order_by(desc(Trade.entry_time))
            .limit(min(limit, 5))
        )
        trades = result.scalars().all()
        
        result = await db.execute(select(func.count(Trade.id)))
        total_trades = result.scalar()
        
        result = await db.execute(
            select(func.count(Trade.id)).where(Trade.status == "OPEN")
        )
        open_trades = result.scalar()
        
        explanation = _generate_trades_explanation(trades, total_trades, open_trades)
        
        return {
            "page": "Trades",
            "explanation": explanation,
            "summary": {
                "total_trades": total_trades,
                "open_trades": open_trades,
                "sample_count": len(trades),
            },
        }
    except Exception as e:
        logger.error("Failed to generate trades explanation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


@router.get("/explain/portfolio")
async def explain_portfolio(db: AsyncSession = Depends(get_db)):
    """Explain the portfolio page."""
    try:
        result = await db.execute(
            select(PortfolioSnapshot)
            .order_by(desc(PortfolioSnapshot.snapshot_time))
            .limit(1)
        )
        portfolio = result.scalar_one_or_none()
        
        explanation = _generate_portfolio_explanation(portfolio)
        
        return {
            "page": "Portfolio",
            "explanation": explanation,
            "summary": {
                "has_portfolio": portfolio is not None,
                "total_value": float(portfolio.total_value) if portfolio else 0.0,
            },
        }
    except Exception as e:
        logger.error("Failed to generate portfolio explanation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


@router.get("/explain/markets")
async def explain_markets(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Explain the markets page."""
    try:
        result = await db.execute(
            select(Market)
            .order_by(desc(Market.created_at))
            .limit(min(limit, 5))
        )
        markets = result.scalars().all()
        
        result = await db.execute(select(func.count(Market.id)))
        total_markets = result.scalar()
        
        explanation = _generate_markets_explanation(markets, total_markets)
        
        return {
            "page": "Markets",
            "explanation": explanation,
            "summary": {
                "total_markets": total_markets,
                "sample_count": len(markets),
            },
        }
    except Exception as e:
        logger.error("Failed to generate markets explanation", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


# Cost-effective explanation generators (no expensive API calls)
def _generate_predictions_explanation(predictions, total: int, avg_edge: float) -> str:
    """Generate explanation for predictions page."""
    if not predictions:
        return (
            "**Predictions Page**\n\n"
            "This page shows model predictions for active markets. "
            "When you generate predictions, you'll see:\n\n"
            "- **Model Probability**: What the AI model thinks the probability is\n"
            "- **Market Price**: Current market price\n"
            "- **Edge**: The difference (opportunity) - positive means model thinks it's undervalued\n"
            "- **Confidence**: How confident the model is in its prediction\n\n"
            "**How to use**: Look for predictions with high edge (>10%) and high confidence (>60%) for best opportunities."
        )
    
    return (
        f"**Predictions Page** - {total} total predictions\n\n"
        f"**What you're seeing:**\n"
        f"- Model predictions for {len(predictions)} markets\n"
        f"- Average edge: {avg_edge*100:.1f}% (opportunity)\n\n"
        f"**Understanding the data:**\n"
        f"- **Model Probability**: AI's prediction (0-100%)\n"
        f"- **Market Price**: Current market price\n"
        f"- **Edge**: Difference between model and market (positive = opportunity)\n"
        f"- **Confidence**: Model's confidence level\n\n"
        f"**How to use:**\n"
        f"- Look for **high edge** (>10%) = model sees opportunity\n"
        f"- Look for **high confidence** (>60%) = model is sure\n"
        f"- **Green edge** = model thinks YES is undervalued\n"
        f"- **Red edge** = model thinks NO is undervalued\n\n"
        f"**Next step**: Check the Signals tab to see which predictions generated trading signals."
    )


def _generate_signals_explanation(signals, total: int, strong: int) -> str:
    """Generate explanation for signals page."""
    if not signals:
        return (
            "**Signals Page**\n\n"
            "This page shows trading signals generated from predictions. "
            "Signals are created when predictions have significant edge (>5%).\n\n"
            "- **Side**: YES or NO (which way to bet)\n"
            "- **Strength**: STRONG/MEDIUM/WEAK (based on edge size)\n"
            "- **Edge**: Opportunity percentage\n"
            "- **Executed**: Whether a trade was opened\n\n"
            "**How to use**: Focus on STRONG signals with high edge for best opportunities."
        )
    
    return (
        f"**Signals Page** - {total} total signals ({strong} strong)\n\n"
        f"**What you're seeing:**\n"
        f"- Trading signals from {len(signals)} predictions\n"
        f"- {strong} STRONG signals (best opportunities)\n\n"
        f"**Understanding the data:**\n"
        f"- **Side**: YES (bet it happens) or NO (bet it doesn't)\n"
        f"- **Strength**: STRONG (>15% edge), MEDIUM (10-15%), WEAK (5-10%)\n"
        f"- **Edge**: Opportunity percentage (higher = better)\n"
        f"- **Executed**: Whether a trade was opened from this signal\n\n"
        f"**How to use:**\n"
        f"- **STRONG signals** = Best opportunities, consider trading\n"
        f"- **MEDIUM signals** = Good opportunities, review carefully\n"
        f"- **WEAK signals** = Small edge, may not be worth it\n\n"
        f"**Next step**: Check the Trades tab to see which signals were executed."
    )


def _generate_trades_explanation(trades, total: int, open: int) -> str:
    """Generate explanation for trades page."""
    if not trades:
        return (
            "**Trades Page**\n\n"
            "This page shows all executed trades. "
            "Trades are created when signals are executed.\n\n"
            "- **Side**: YES or NO position\n"
            "- **Entry Price**: Price when trade was opened\n"
            "- **Size**: Position size in USD\n"
            "- **Status**: OPEN, CLOSED, or CANCELLED\n"
            "- **P&L**: Profit/Loss (if closed)\n\n"
            "**How to use**: Monitor open trades and their performance."
        )
    
    return (
        f"**Trades Page** - {total} total trades ({open} open)\n\n"
        f"**What you're seeing:**\n"
        f"- {len(trades)} recent trades\n"
        f"- {open} currently open positions\n\n"
        f"**Understanding the data:**\n"
        f"- **Side**: YES or NO position\n"
        f"- **Entry Price**: Price when you entered\n"
        f"- **Size**: Position size in USD\n"
        f"- **Status**: OPEN (active), CLOSED (completed), CANCELLED\n"
        f"- **P&L**: Profit/Loss (shown when closed)\n\n"
        f"**How to use:**\n"
        f"- Monitor **OPEN trades** for active positions\n"
        f"- Review **P&L** on closed trades for performance\n"
        f"- Check **entry prices** vs current market prices\n\n"
        f"**Next step**: Check the Portfolio tab to see overall performance."
    )


def _generate_portfolio_explanation(portfolio) -> str:
    """Generate explanation for portfolio page."""
    if not portfolio:
        return (
            "**Portfolio Page**\n\n"
            "This page shows your overall trading portfolio performance.\n\n"
            "- **Total Value**: Total portfolio value (cash + positions)\n"
            "- **Cash**: Available cash\n"
            "- **Positions Value**: Value of open positions\n"
            "- **Total Exposure**: Total amount at risk\n"
            "- **P&L**: Profit/Loss (realized + unrealized)\n\n"
            "**How to use**: Monitor your portfolio health and performance over time."
        )
    
    return (
        f"**Portfolio Page** - Current Snapshot\n\n"
        f"**What you're seeing:**\n"
        f"- Total Value: ${float(portfolio.total_value):,.2f}\n"
        f"- Cash: ${float(portfolio.cash):,.2f}\n"
        f"- Positions: ${float(portfolio.positions_value):,.2f}\n"
        f"- Exposure: ${float(portfolio.total_exposure):,.2f}\n\n"
        f"**Understanding the metrics:**\n"
        f"- **Total Value**: Your entire portfolio (cash + positions + P&L)\n"
        f"- **Cash**: Money available for new trades\n"
        f"- **Positions Value**: Current value of open positions\n"
        f"- **Total Exposure**: Total amount at risk in open trades\n"
        f"- **Daily P&L**: Profit/Loss today\n"
        f"- **Unrealized P&L**: Profit/Loss on open positions\n"
        f"- **Realized P&L**: Profit/Loss on closed trades\n\n"
        f"**How to use:**\n"
        f"- Monitor **Total Value** for overall performance\n"
        f"- Keep **Cash** available for new opportunities\n"
        f"- Watch **Exposure** to manage risk\n"
        f"- Track **P&L** to see if strategy is working"
    )


def _generate_markets_explanation(markets, total: int) -> str:
    """Generate explanation for markets page."""
    if not markets:
        return (
            "**Markets Page**\n\n"
            "This page shows all available prediction markets from Polymarket.\n\n"
            "- **Question**: The market question\n"
            "- **YES/NO Price**: Current market prices\n"
            "- **Outcome**: Active, Resolved, or Closed\n"
            "- **Resolution Date**: When the market resolves\n\n"
            "**How to use**: Browse markets to find opportunities, then generate predictions."
        )
    
    return (
        f"**Markets Page** - {total} total markets\n\n"
        f"**What you're seeing:**\n"
        f"- {len(markets)} prediction markets\n"
        f"- Active markets you can trade\n\n"
        f"**Understanding the data:**\n"
        f"- **Question**: What the market is predicting\n"
        f"- **YES Price**: Cost to bet YES (0-100%)\n"
        f"- **NO Price**: Cost to bet NO (0-100%)\n"
        f"- **Outcome**: ACTIVE (trading), RESOLVED (finished), CLOSED\n"
        f"- **Resolution Date**: When the market will resolve\n\n"
        f"**How to use:**\n"
        f"- Browse markets to find interesting questions\n"
        f"- Click **Load Live Data** to fetch latest markets\n"
        f"- Generate predictions for markets you're interested in\n"
        f"- Look for markets with good liquidity and clear questions\n\n"
        f"**Next step**: Generate predictions for markets you want to analyze."
    )


