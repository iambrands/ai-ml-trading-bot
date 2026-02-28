"""Trade Journal Service - Detailed trade logging with notes and analysis."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TradeJournalEntry, Trade
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TradeJournalService:
    """Service for maintaining a detailed trade journal."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_entry(
        self,
        market_id: str,
        trade_id: Optional[int] = None,
        market_question: Optional[str] = None,
        entry_reason: Optional[str] = None,
        strategy_used: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None,
        pre_trade_analysis: Optional[str] = None,
        emotional_state: Optional[str] = None,
        entry_price: Optional[float] = None,
    ) -> Optional[Dict]:
        """Create a new journal entry."""
        try:
            entry = TradeJournalEntry(
                trade_id=trade_id,
                market_id=market_id,
                market_question=market_question,
                entry_reason=entry_reason,
                strategy_used=strategy_used,
                tags=tags,
                notes=notes,
                pre_trade_analysis=pre_trade_analysis,
                emotional_state=emotional_state,
                entry_price=entry_price,
            )
            self.db.add(entry)
            await self.db.commit()
            await self.db.refresh(entry)
            return self._entry_to_dict(entry)
        except Exception as e:
            logger.error("Failed to create journal entry", error=str(e))
            await self.db.rollback()
            return None

    async def update_entry(
        self,
        entry_id: int,
        exit_reason: Optional[str] = None,
        post_trade_review: Optional[str] = None,
        lesson_learned: Optional[str] = None,
        rating: Optional[int] = None,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Update an existing journal entry."""
        try:
            result = await self.db.execute(
                select(TradeJournalEntry).where(TradeJournalEntry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            if not entry:
                return None

            if exit_reason is not None:
                entry.exit_reason = exit_reason
            if post_trade_review is not None:
                entry.post_trade_review = post_trade_review
            if lesson_learned is not None:
                entry.lesson_learned = lesson_learned
            if rating is not None:
                entry.rating = max(1, min(5, rating))
            if exit_price is not None:
                entry.exit_price = exit_price
            if pnl is not None:
                entry.pnl = pnl
            if notes is not None:
                entry.notes = notes
            if tags is not None:
                entry.tags = tags

            await self.db.commit()
            await self.db.refresh(entry)
            return self._entry_to_dict(entry)
        except Exception as e:
            logger.error("Failed to update journal entry", error=str(e))
            await self.db.rollback()
            return None

    async def get_entries(
        self,
        strategy: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict]:
        """Get journal entries with optional filters."""
        try:
            query = select(TradeJournalEntry)
            if strategy:
                query = query.where(TradeJournalEntry.strategy_used == strategy)
            query = query.order_by(desc(TradeJournalEntry.created_at)).limit(limit).offset(offset)

            result = await self.db.execute(query)
            entries = result.scalars().all()
            return [self._entry_to_dict(e) for e in entries]
        except Exception as e:
            logger.error("Failed to get journal entries", error=str(e))
            return []

    async def get_entry(self, entry_id: int) -> Optional[Dict]:
        """Get a single journal entry."""
        try:
            result = await self.db.execute(
                select(TradeJournalEntry).where(TradeJournalEntry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            return self._entry_to_dict(entry) if entry else None
        except Exception as e:
            logger.error("Failed to get journal entry", error=str(e))
            return None

    async def delete_entry(self, entry_id: int) -> bool:
        """Delete a journal entry."""
        try:
            result = await self.db.execute(
                select(TradeJournalEntry).where(TradeJournalEntry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            if not entry:
                return False
            await self.db.delete(entry)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete journal entry", error=str(e))
            await self.db.rollback()
            return False

    async def get_journal_stats(self) -> Dict:
        """Get journal statistics and insights."""
        try:
            total_result = await self.db.execute(
                select(func.count(TradeJournalEntry.id))
            )
            total = total_result.scalar() or 0

            rated_result = await self.db.execute(
                select(func.avg(TradeJournalEntry.rating)).where(
                    TradeJournalEntry.rating.isnot(None)
                )
            )
            avg_rating = rated_result.scalar()

            strategy_result = await self.db.execute(
                select(
                    TradeJournalEntry.strategy_used,
                    func.count(TradeJournalEntry.id),
                    func.avg(TradeJournalEntry.pnl),
                )
                .where(TradeJournalEntry.strategy_used.isnot(None))
                .group_by(TradeJournalEntry.strategy_used)
            )
            strategies = {
                row[0]: {"count": row[1], "avg_pnl": round(float(row[2]), 2) if row[2] else 0}
                for row in strategy_result.all()
            }

            emotion_result = await self.db.execute(
                select(
                    TradeJournalEntry.emotional_state,
                    func.count(TradeJournalEntry.id),
                    func.avg(TradeJournalEntry.pnl),
                )
                .where(TradeJournalEntry.emotional_state.isnot(None))
                .group_by(TradeJournalEntry.emotional_state)
            )
            emotions = {
                row[0]: {"count": row[1], "avg_pnl": round(float(row[2]), 2) if row[2] else 0}
                for row in emotion_result.all()
            }

            lessons_result = await self.db.execute(
                select(TradeJournalEntry.lesson_learned)
                .where(TradeJournalEntry.lesson_learned.isnot(None))
                .order_by(desc(TradeJournalEntry.created_at))
                .limit(10)
            )
            recent_lessons = [row[0] for row in lessons_result.all()]

            return {
                "total_entries": total,
                "avg_trade_rating": round(float(avg_rating), 2) if avg_rating else None,
                "strategy_breakdown": strategies,
                "emotion_analysis": emotions,
                "recent_lessons": recent_lessons,
            }
        except Exception as e:
            logger.error("Failed to get journal stats", error=str(e))
            return {"total_entries": 0}

    def _entry_to_dict(self, entry: TradeJournalEntry) -> Dict:
        return {
            "id": entry.id,
            "trade_id": entry.trade_id,
            "market_id": entry.market_id,
            "market_question": entry.market_question,
            "entry_reason": entry.entry_reason,
            "exit_reason": entry.exit_reason,
            "strategy_used": entry.strategy_used,
            "tags": entry.tags,
            "notes": entry.notes,
            "pre_trade_analysis": entry.pre_trade_analysis,
            "post_trade_review": entry.post_trade_review,
            "emotional_state": entry.emotional_state,
            "lesson_learned": entry.lesson_learned,
            "entry_price": float(entry.entry_price) if entry.entry_price else None,
            "exit_price": float(entry.exit_price) if entry.exit_price else None,
            "pnl": float(entry.pnl) if entry.pnl else None,
            "rating": entry.rating,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }
