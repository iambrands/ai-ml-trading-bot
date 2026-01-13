"""API endpoints for arbitrage detection."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ...database.connection import get_db
from ...database.models import Market as DBMarket
from ...data.models import Market
from ...services.arbitrage_detector import ArbitrageDetector, ArbitrageOpportunity
from ...config.settings import get_settings
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


@router.get("/opportunities")
async def get_arbitrage_opportunities(
    min_profit: float = Query(0.025, description="Minimum profit threshold (default: 0.025 = 2.5%)"),
    min_liquidity: float = Query(100.0, description="Minimum liquidity required (default: $100)"),
    limit: int = Query(50, description="Maximum number of opportunities to return"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get current arbitrage opportunities.
    
    Arbitrage opportunities occur when YES + NO prices < $1.00,
    creating a guaranteed profit opportunity.
    
    Args:
        min_profit: Minimum profit threshold (0.025 = 2.5%)
        min_liquidity: Minimum liquidity required
        limit: Maximum number of opportunities to return
        db: Database session
    
    Returns:
        Dictionary with opportunities and statistics
    """
    try:
        # Initialize detector
        detector = ArbitrageDetector(
            min_profit=min_profit,
            min_liquidity=min_liquidity,
        )
        
        # Get active markets from database
        result = await db.execute(
            select(DBMarket)
            .where(DBMarket.resolution_date.is_(None))  # Active markets only
            .order_by(desc(DBMarket.created_at))
            .limit(limit * 2)  # Get more to filter
        )
        db_markets = result.scalars().all()
        
        if not db_markets:
            return {
                "opportunities": [],
                "stats": {
                    "total_opportunities": 0,
                    "total_profit_potential": 0.0,
                    "avg_profit_percent": 0.0,
                },
                "message": "No active markets found",
            }
        
        # Convert to Market objects using latest predictions from database
        # This is much faster than fetching from Polymarket API for each market
        from ...database.models import Prediction
        
        markets = []
        for db_market in db_markets:
            try:
                # Get latest prediction for this market
                pred_result = await db.execute(
                    select(Prediction)
                    .where(Prediction.market_id == db_market.market_id)
                    .order_by(desc(Prediction.created_at))
                    .limit(1)
                )
                latest_pred = pred_result.scalar_one_or_none()
                
                if latest_pred:
                    # Create Market object with prices from prediction
                    market = Market(
                        id=db_market.market_id,
                        condition_id=db_market.condition_id or "",
                        question=db_market.question,
                        category=db_market.category,
                        resolution_date=db_market.resolution_date,
                        outcome=db_market.outcome,
                        yes_price=float(latest_pred.market_price),
                        no_price=1.0 - float(latest_pred.market_price),
                    )
                    markets.append(market)
            except Exception as e:
                logger.warning(
                    "Failed to create market object",
                    market_id=db_market.market_id,
                    error=str(e),
                )
                continue
        
        # Detect arbitrage opportunities
        opportunities = detector.detect_arbitrage_batch(markets)
        
        # Limit results
        opportunities = opportunities[:limit]
        
        # Get statistics
        stats = detector.get_arbitrage_stats(opportunities)
        
        # Convert to dict
        opportunities_dict = [opp.to_dict() for opp in opportunities]
        
        logger.info(
            "Arbitrage opportunities retrieved",
            count=len(opportunities_dict),
            total_profit_potential=f"${stats.get('total_profit_potential', 0):.2f}",
        )
        
        return {
            "opportunities": opportunities_dict,
            "stats": stats,
        }
        
    except Exception as e:
        logger.error("Failed to get arbitrage opportunities", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get arbitrage opportunities: {str(e)}")


@router.get("/opportunities/{market_id}")
async def get_arbitrage_opportunity(
    market_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get arbitrage opportunity for a specific market.
    
    Args:
        market_id: Market ID to check
        db: Database session
    
    Returns:
        ArbitrageOpportunity if found, error otherwise
    """
    try:
        # Initialize detector
        detector = ArbitrageDetector()
        
        # Fetch market data
        from ...data.sources.polymarket import PolymarketDataSource
        
        async with PolymarketDataSource() as polymarket:
            market = await polymarket.fetch_market(market_id)
            
            if not market:
                raise HTTPException(status_code=404, detail="Market not found")
            
            # Detect arbitrage
            opportunity = detector.detect_arbitrage(market)
            
            if not opportunity:
                return {
                    "opportunity": None,
                    "message": "No arbitrage opportunity found for this market",
                }
            
            return {
                "opportunity": opportunity.to_dict(),
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get arbitrage opportunity",
            market_id=market_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get arbitrage opportunity: {str(e)}",
        )


@router.post("/calculate/{market_id}")
async def calculate_arbitrage_execution(
    market_id: str,
    trade_size: float = Query(100.0, description="Trade size in dollars (default: $100)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Calculate execution details for an arbitrage trade.
    
    Args:
        market_id: Market ID
        trade_size: Size of trade in dollars
        db: Database session
    
    Returns:
        Execution details with costs and profit
    """
    try:
        # Initialize detector
        detector = ArbitrageDetector()
        
        # Get market from database with latest prediction
        from ...database.models import Prediction
        
        # Get market from database
        market_result = await db.execute(
            select(DBMarket).where(DBMarket.market_id == market_id)
        )
        db_market = market_result.scalar_one_or_none()
        
        if not db_market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Get latest prediction for prices
        pred_result = await db.execute(
            select(Prediction)
            .where(Prediction.market_id == market_id)
            .order_by(desc(Prediction.created_at))
            .limit(1)
        )
        latest_pred = pred_result.scalar_one_or_none()
        
        if not latest_pred:
            raise HTTPException(
                status_code=400,
                detail="No price data available for this market",
            )
        
        # Create Market object
        market = Market(
            id=db_market.market_id,
            condition_id=db_market.condition_id or "",
            question=db_market.question,
            category=db_market.category,
            resolution_date=db_market.resolution_date,
            outcome=db_market.outcome,
            yes_price=float(latest_pred.market_price),
            no_price=1.0 - float(latest_pred.market_price),
        )
        
        # Detect arbitrage
        opportunity = detector.detect_arbitrage(market)
        
        if not opportunity:
            raise HTTPException(
                status_code=400,
                detail="No arbitrage opportunity found for this market",
            )
        
        # Calculate execution
        execution = detector.calculate_execution_cost(opportunity, trade_size)
        
        return execution
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to calculate arbitrage execution",
            market_id=market_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate arbitrage execution: {str(e)}",
        )


@router.get("/stats")
async def get_arbitrage_stats(
    min_profit: float = Query(0.025, description="Minimum profit threshold"),
    min_liquidity: float = Query(100.0, description="Minimum liquidity required"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get statistics about current arbitrage opportunities.
    
    Args:
        min_profit: Minimum profit threshold
        min_liquidity: Minimum liquidity required
        db: Database session
    
    Returns:
        Statistics about arbitrage opportunities
    """
    try:
        # Get opportunities
        opportunities_response = await get_arbitrage_opportunities(
            min_profit=min_profit,
            min_liquidity=min_liquidity,
            limit=100,
            db=db,
        )
        
        stats = opportunities_response.get("stats", {})
        
        return {
            "stats": stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.error("Failed to get arbitrage stats", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get arbitrage stats: {str(e)}")

