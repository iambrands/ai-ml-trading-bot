"""Economic Calendar API Endpoints"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...database.connection import get_db
from ...utils.logging import get_logger
from ..cache import cache_response

# Import EconomicCalendar with fallback for import errors
try:
    from ...services.economic_calendar import EconomicCalendar
except ImportError:
    # Fallback to absolute import if relative import fails
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.services.economic_calendar import EconomicCalendar

logger = get_logger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


class EventResponse(BaseModel):
    """Economic event response model."""
    id: int
    event_type: str
    event_name: str
    event_date: str
    importance: str
    description: Optional[str]
    external_url: Optional[str]
    related_markets_count: int
    days_until: float


class MarketResponse(BaseModel):
    """Market response for event details."""
    id: str
    question: str
    price: float
    volume: float
    relevance: float
    impact_prediction: Optional[str]


@router.get("/upcoming", response_model=List[EventResponse])
@cache_response(seconds=3600)  # Cache for 1 hour (events don't change frequently)
async def get_upcoming_events(
    days: int = Query(default=30, ge=1, le=365),
    event_types: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
) -> List[EventResponse]:
    """
    Get upcoming economic events.
    
    Returns events within the specified number of days.
    """
    try:
        calendar = EconomicCalendar(db)
        
        types_list = None
        if event_types:
            types_list = [t.strip() for t in event_types.split(',')]
        
        events = await calendar.get_upcoming_events(days=days, event_types=types_list)
        
        return [EventResponse(
            id=e['id'],
            event_type=e['event_type'],
            event_name=e['event_name'],
            event_date=e['event_date'].isoformat(),
            importance=e['importance'],
            description=e.get('description'),
            external_url=e.get('external_url'),
            related_markets_count=e['related_markets_count'],
            days_until=e['days_until']
        ) for e in events]
        
    except Exception as e:
        logger.error(f"Failed to get upcoming events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_id}/markets", response_model=dict)
@cache_response(seconds=600)  # Cache for 10 minutes
async def get_event_markets(
    event_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get markets related to a specific economic event.
    """
    try:
        calendar = EconomicCalendar(db)
        
        # Get event details
        from ...database.models import EconomicEvent
        from sqlalchemy import select
        
        event_result = await db.execute(
            select(EconomicEvent).where(EconomicEvent.id == event_id)
        )
        event = event_result.scalar_one_or_none()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Get related markets
        markets = await calendar.get_event_markets(event_id)
        
        return {
            "event": {
                "id": event.id,
                "type": event.event_type,
                "name": event.event_name,
                "date": event.event_date.isoformat(),
                "importance": event.importance
            },
            "related_markets": [MarketResponse(**m) for m in markets],
            "total": len(markets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event markets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize_calendar(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Initialize calendar with 2026 events (admin only).
    
    Creates all known economic events for 2026 and matches them to markets.
    """
    try:
        calendar = EconomicCalendar(db)
        
        # Initialize events
        event_count = await calendar.initialize_2026_calendar()
        
        # Match markets to events
        match_count = await calendar.match_markets_to_events()
        
        return {
            "success": True,
            "events_created": event_count,
            "market_matches": match_count
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize calendar: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
@cache_response(seconds=3600)  # Cache for 1 hour
async def get_calendar_stats(
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get calendar statistics"""
    try:
        from ...database.models import EconomicEvent, MarketEvent
        from sqlalchemy import select, func
        
        # Count events by type
        type_stats_result = await db.execute(
            select(
                EconomicEvent.event_type,
                func.count(EconomicEvent.id).label('count'),
                func.count(
                    func.case((EconomicEvent.event_date > datetime.now(), 1))
                ).label('upcoming')
            ).where(
                EconomicEvent.is_completed == False
            ).group_by(EconomicEvent.event_type).order_by(func.count(EconomicEvent.id).desc())
        )
        
        type_stats = []
        for row in type_stats_result.all():
            type_stats.append({
                "type": row.event_type,
                "total": row.count,
                "upcoming": row.upcoming
            })
        
        # Get next 3 events
        next_events_result = await db.execute(
            select(EconomicEvent).where(
                EconomicEvent.event_date > datetime.now(),
                EconomicEvent.is_completed == False
            ).order_by(EconomicEvent.event_date.asc()).limit(3)
        )
        
        next_events = []
        for event in next_events_result.scalars().all():
            next_events.append({
                "type": event.event_type,
                "name": event.event_name,
                "date": event.event_date.isoformat()
            })
        
        return {
            "by_type": type_stats,
            "next_events": next_events
        }
        
    except Exception as e:
        logger.error(f"Failed to get calendar stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

