"""Whale Tracking API Endpoints"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...database.connection import get_db
from ...services.whale_tracker import WhaleTracker
from ...utils.logging import get_logger
from ..cache import cache_response

logger = get_logger(__name__)

router = APIRouter(prefix="/whales", tags=["whales"])


@router.post("/initialize")
async def initialize_whales(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Initialize whale tracker by discovering and indexing top whales.
    This endpoint runs the full initialization process on Railway infrastructure.
    No tunnel needed - just call this endpoint!
    """
    try:
        tracker = WhaleTracker(db, None)
        
        # Discover whales from Polymarket APIs
        logger.info("Starting whale discovery...")
        whales = await tracker.discover_whales()
        
        if not whales:
            await tracker.close()
            raise HTTPException(
                status_code=500,
                detail="Failed to discover whales from Polymarket APIs"
            )
        
        logger.info(f"Discovered {len(whales)} whales, now indexing...")
        
        # Index whales using the tracker's method
        indexed_count = await tracker.index_whales(whales)
        
        await tracker.close()
        
        return {
            "success": True,
            "discovered": len(whales),
            "indexed": indexed_count,
            "message": f"Successfully indexed {indexed_count} whales"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize whales: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize whales: {str(e)}"
        )


class WhaleResponse(BaseModel):
    """Whale leaderboard response model."""
    id: int
    rank: Optional[int]
    wallet_address: str
    nickname: str
    total_volume: float
    total_trades: int
    total_profit: float
    win_rate: float
    hours_since_trade: float


class WhaleActivityResponse(BaseModel):
    """Whale activity response model."""
    whale_rank: Optional[int]
    whale_address: str
    whale_nickname: str
    market: str
    action: str
    amount: float
    price: float
    value: float
    time: str
    hours_ago: float


@router.get("/leaderboard", response_model=List[WhaleResponse])
@cache_response(seconds=300)  # Cache for 5 minutes
async def get_whale_leaderboard(
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
) -> List[WhaleResponse]:
    """
    Get whale leaderboard sorted by rank.
    
    Returns top whales by trading volume.
    """
    try:
        tracker = WhaleTracker(db)
        whales = await tracker.get_whale_leaderboard(limit=limit)
        await tracker.close()
        
        return [WhaleResponse(**whale) for whale in whales]
        
    except Exception as e:
        logger.error(f"Failed to get whale leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-activity", response_model=List[WhaleActivityResponse])
@cache_response(seconds=60)  # Cache for 1 minute
async def get_recent_activity(
    hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    min_value: float = Query(default=1000, ge=0),
    db: AsyncSession = Depends(get_db)
) -> List[WhaleActivityResponse]:
    """
    Get recent whale trading activity.
    
    Returns significant trades from whales in the specified time window.
    """
    try:
        tracker = WhaleTracker(db)
        trades = await tracker.get_recent_whale_activity(hours=hours, min_value=min_value)
        await tracker.close()
        
        return [WhaleActivityResponse(**trade) for trade in trades]
        
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
@cache_response(seconds=30)  # Cache for 30 seconds
async def get_whale_alerts(
    user_id: int = Query(default=1),
    unread_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get unread whale alerts for current user.
    
    Returns alerts for large whale trades.
    """
    try:
        from ...database.models import WhaleAlert, WhaleWallet, WhaleTrade
        from sqlalchemy import select
        
        query = select(WhaleAlert, WhaleWallet, WhaleTrade).join(
            WhaleWallet, WhaleAlert.whale_id == WhaleWallet.id
        ).join(
            WhaleTrade, WhaleAlert.trade_id == WhaleTrade.id
        ).where(
            WhaleAlert.user_id == user_id
        )
        
        if unread_only:
            query = query.where(WhaleAlert.is_read == False)
        
        query = query.order_by(WhaleAlert.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        rows = result.all()
        
        alerts = []
        for alert, whale, trade in rows:
            alerts.append({
                "id": alert.id,
                "whale_rank": whale.rank,
                "whale_nickname": whale.nickname or f"Whale #{whale.rank}",
                "market": trade.market_question or trade.market_id,
                "action": f"{trade.trade_type} {trade.outcome}",
                "value": float(trade.trade_value),
                "time": alert.created_at.isoformat(),
                "is_read": alert.is_read
            })
        
        return {
            "alerts": alerts,
            "unread_count": len([a for a in alerts if not a["is_read"]])
        }
        
    except Exception as e:
        logger.error(f"Failed to get whale alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Mark whale alert as read"""
    try:
        from ...database.models import WhaleAlert
        from sqlalchemy import update
        
        result = await db.execute(
            update(WhaleAlert)
            .where(WhaleAlert.id == alert_id)
            .values(is_read=True)
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        await db.commit()
        return {"success": True, "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark alert as read: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

