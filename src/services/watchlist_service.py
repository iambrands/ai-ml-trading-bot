"""Watchlist System Service."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Watchlist, WatchlistItem
from ..utils.logging import get_logger

logger = get_logger(__name__)


class WatchlistService:
    """Service for managing market watchlists."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_watchlist(
        self,
        name: str,
        description: Optional[str] = None,
        user_id: str = "default",
    ) -> Optional[Dict]:
        """Create a new watchlist."""
        try:
            watchlist = Watchlist(
                user_id=user_id,
                name=name,
                description=description,
            )
            self.db.add(watchlist)
            await self.db.commit()
            await self.db.refresh(watchlist)
            return self._watchlist_to_dict(watchlist)
        except Exception as e:
            logger.error("Failed to create watchlist", name=name, error=str(e))
            await self.db.rollback()
            return None

    async def get_watchlists(self, user_id: str = "default") -> List[Dict]:
        """Get all watchlists for a user."""
        try:
            result = await self.db.execute(
                select(Watchlist)
                .where(Watchlist.user_id == user_id)
                .order_by(desc(Watchlist.updated_at))
            )
            watchlists = result.scalars().all()

            results = []
            for w in watchlists:
                wdict = self._watchlist_to_dict(w)
                count_result = await self.db.execute(
                    select(func.count(WatchlistItem.id)).where(
                        WatchlistItem.watchlist_id == w.id
                    )
                )
                wdict["item_count"] = count_result.scalar() or 0
                results.append(wdict)

            return results
        except Exception as e:
            logger.error("Failed to get watchlists", error=str(e))
            return []

    async def get_watchlist(self, watchlist_id: int) -> Optional[Dict]:
        """Get a watchlist with all its items."""
        try:
            result = await self.db.execute(
                select(Watchlist).where(Watchlist.id == watchlist_id)
            )
            watchlist = result.scalar_one_or_none()
            if not watchlist:
                return None

            items_result = await self.db.execute(
                select(WatchlistItem)
                .where(WatchlistItem.watchlist_id == watchlist_id)
                .order_by(desc(WatchlistItem.added_at))
            )
            items = items_result.scalars().all()

            wdict = self._watchlist_to_dict(watchlist)
            wdict["items"] = [self._item_to_dict(i) for i in items]
            return wdict
        except Exception as e:
            logger.error("Failed to get watchlist", id=watchlist_id, error=str(e))
            return None

    async def delete_watchlist(self, watchlist_id: int) -> bool:
        """Delete a watchlist and all its items."""
        try:
            result = await self.db.execute(
                select(Watchlist).where(Watchlist.id == watchlist_id)
            )
            watchlist = result.scalar_one_or_none()
            if not watchlist:
                return False
            await self.db.delete(watchlist)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete watchlist", error=str(e))
            await self.db.rollback()
            return False

    async def add_item(
        self,
        watchlist_id: int,
        market_id: str,
        market_question: Optional[str] = None,
        notes: Optional[str] = None,
        target_price: Optional[float] = None,
        alert_on_price: bool = False,
        price_at_add: Optional[float] = None,
    ) -> Optional[Dict]:
        """Add a market to a watchlist."""
        try:
            existing = await self.db.execute(
                select(WatchlistItem).where(
                    WatchlistItem.watchlist_id == watchlist_id,
                    WatchlistItem.market_id == market_id,
                )
            )
            if existing.scalar_one_or_none():
                return None

            item = WatchlistItem(
                watchlist_id=watchlist_id,
                market_id=market_id,
                market_question=market_question,
                notes=notes,
                target_price=target_price,
                alert_on_price=alert_on_price,
                price_at_add=price_at_add,
            )
            self.db.add(item)
            await self.db.commit()
            await self.db.refresh(item)
            return self._item_to_dict(item)
        except Exception as e:
            logger.error("Failed to add watchlist item", error=str(e))
            await self.db.rollback()
            return None

    async def remove_item(self, watchlist_id: int, market_id: str) -> bool:
        """Remove a market from a watchlist."""
        try:
            result = await self.db.execute(
                select(WatchlistItem).where(
                    WatchlistItem.watchlist_id == watchlist_id,
                    WatchlistItem.market_id == market_id,
                )
            )
            item = result.scalar_one_or_none()
            if not item:
                return False
            await self.db.delete(item)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error("Failed to remove watchlist item", error=str(e))
            await self.db.rollback()
            return False

    async def update_item_notes(self, item_id: int, notes: str) -> Optional[Dict]:
        """Update notes for a watchlist item."""
        try:
            result = await self.db.execute(
                select(WatchlistItem).where(WatchlistItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            if not item:
                return None
            item.notes = notes
            await self.db.commit()
            await self.db.refresh(item)
            return self._item_to_dict(item)
        except Exception as e:
            logger.error("Failed to update item notes", error=str(e))
            await self.db.rollback()
            return None

    def _watchlist_to_dict(self, watchlist: Watchlist) -> Dict:
        return {
            "id": watchlist.id,
            "user_id": watchlist.user_id,
            "name": watchlist.name,
            "description": watchlist.description,
            "is_default": watchlist.is_default,
            "created_at": watchlist.created_at.isoformat() if watchlist.created_at else None,
            "updated_at": watchlist.updated_at.isoformat() if watchlist.updated_at else None,
        }

    def _item_to_dict(self, item: WatchlistItem) -> Dict:
        return {
            "id": item.id,
            "watchlist_id": item.watchlist_id,
            "market_id": item.market_id,
            "market_question": item.market_question,
            "notes": item.notes,
            "target_price": float(item.target_price) if item.target_price else None,
            "alert_on_price": item.alert_on_price,
            "price_at_add": float(item.price_at_add) if item.price_at_add else None,
            "added_at": item.added_at.isoformat() if item.added_at else None,
        }
