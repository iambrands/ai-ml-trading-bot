"""Watchlist System API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.watchlist_service import WatchlistService
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/watchlists", tags=["watchlists"])


class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class AddItemRequest(BaseModel):
    market_id: str
    market_question: Optional[str] = None
    notes: Optional[str] = None
    target_price: Optional[float] = Field(default=None, ge=0.01, le=0.99)
    alert_on_price: bool = False
    price_at_add: Optional[float] = None


class UpdateNotesRequest(BaseModel):
    notes: str


@router.get("")
async def get_watchlists(
    user_id: str = Query(default="default"),
    db: AsyncSession = Depends(get_db),
):
    """Get all watchlists."""
    service = WatchlistService(db)
    return await service.get_watchlists(user_id=user_id)


@router.post("")
async def create_watchlist(request: CreateWatchlistRequest, db: AsyncSession = Depends(get_db)):
    """Create a new watchlist."""
    service = WatchlistService(db)
    result = await service.create_watchlist(name=request.name, description=request.description)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to create watchlist (name may already exist)")
    return result


@router.get("/{watchlist_id}")
async def get_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    """Get a watchlist with all its items."""
    service = WatchlistService(db)
    result = await service.get_watchlist(watchlist_id)
    if not result:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return result


@router.delete("/{watchlist_id}")
async def delete_watchlist(watchlist_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a watchlist."""
    service = WatchlistService(db)
    success = await service.delete_watchlist(watchlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"status": "deleted", "watchlist_id": watchlist_id}


@router.post("/{watchlist_id}/items")
async def add_item(watchlist_id: int, request: AddItemRequest, db: AsyncSession = Depends(get_db)):
    """Add a market to a watchlist."""
    service = WatchlistService(db)
    result = await service.add_item(
        watchlist_id=watchlist_id,
        market_id=request.market_id,
        market_question=request.market_question,
        notes=request.notes,
        target_price=request.target_price,
        alert_on_price=request.alert_on_price,
        price_at_add=request.price_at_add,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to add item (may already exist)")
    return result


@router.delete("/{watchlist_id}/items/{market_id}")
async def remove_item(watchlist_id: int, market_id: str, db: AsyncSession = Depends(get_db)):
    """Remove a market from a watchlist."""
    service = WatchlistService(db)
    success = await service.remove_item(watchlist_id, market_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "removed", "market_id": market_id}


@router.put("/items/{item_id}/notes")
async def update_notes(item_id: int, request: UpdateNotesRequest, db: AsyncSession = Depends(get_db)):
    """Update notes for a watchlist item."""
    service = WatchlistService(db)
    result = await service.update_item_notes(item_id, request.notes)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
