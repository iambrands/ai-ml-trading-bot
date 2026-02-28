"""Trade Journal API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.trade_journal_service import TradeJournalService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/journal", tags=["trade-journal"])


class CreateJournalEntry(BaseModel):
    market_id: str
    trade_id: Optional[int] = None
    market_question: Optional[str] = None
    entry_reason: Optional[str] = None
    strategy_used: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    pre_trade_analysis: Optional[str] = None
    emotional_state: Optional[str] = None
    entry_price: Optional[float] = None


class UpdateJournalEntry(BaseModel):
    exit_reason: Optional[str] = None
    post_trade_review: Optional[str] = None
    lesson_learned: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("")
async def get_journal_entries(
    strategy: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get trade journal entries."""
    service = TradeJournalService(db)
    return await service.get_entries(strategy=strategy, tag=tag, limit=limit, offset=offset)


@router.get("/stats")
async def get_journal_stats(db: AsyncSession = Depends(get_db)):
    """Get journal statistics and insights."""
    service = TradeJournalService(db)
    return await service.get_journal_stats()


@router.get("/{entry_id}")
async def get_journal_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single journal entry."""
    service = TradeJournalService(db)
    result = await service.get_entry(entry_id)
    if not result:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return result


@router.post("")
async def create_journal_entry(request: CreateJournalEntry, db: AsyncSession = Depends(get_db)):
    """Create a new trade journal entry."""
    service = TradeJournalService(db)
    result = await service.create_entry(
        market_id=request.market_id,
        trade_id=request.trade_id,
        market_question=request.market_question,
        entry_reason=request.entry_reason,
        strategy_used=request.strategy_used,
        tags=request.tags,
        notes=request.notes,
        pre_trade_analysis=request.pre_trade_analysis,
        emotional_state=request.emotional_state,
        entry_price=request.entry_price,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create journal entry")
    return result


@router.put("/{entry_id}")
async def update_journal_entry(entry_id: int, request: UpdateJournalEntry, db: AsyncSession = Depends(get_db)):
    """Update a journal entry with post-trade review."""
    service = TradeJournalService(db)
    result = await service.update_entry(
        entry_id=entry_id,
        exit_reason=request.exit_reason,
        post_trade_review=request.post_trade_review,
        lesson_learned=request.lesson_learned,
        rating=request.rating,
        exit_price=request.exit_price,
        pnl=request.pnl,
        notes=request.notes,
        tags=request.tags,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return result


@router.delete("/{entry_id}")
async def delete_journal_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a journal entry."""
    service = TradeJournalService(db)
    success = await service.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"status": "deleted", "entry_id": entry_id}
