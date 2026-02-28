"""Copy Trading Service - Follow and auto-copy trades from top wallets."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import CopyTradingProfile, CopyTrade, WhaleTrade, WhaleWallet
from ..utils.logging import get_logger

logger = get_logger(__name__)


class CopyTradingService:
    """Service for following top wallets and copying their trades."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_followed_profiles(self, only_active: bool = True) -> List[Dict]:
        """Get all profiles being followed."""
        try:
            query = select(CopyTradingProfile)
            if only_active:
                query = query.where(CopyTradingProfile.is_following == True)
            query = query.order_by(desc(CopyTradingProfile.total_profit))

            result = await self.db.execute(query)
            profiles = result.scalars().all()

            return [self._profile_to_dict(p) for p in profiles]
        except Exception as e:
            logger.error("Failed to get followed profiles", error=str(e))
            return []

    async def follow_wallet(
        self,
        wallet_address: str,
        nickname: Optional[str] = None,
        auto_copy: bool = False,
        copy_percentage: float = 100.0,
        max_copy_size: float = 1000.0,
        min_trade_size: float = 10.0,
    ) -> Optional[Dict]:
        """Start following a wallet for copy trading."""
        try:
            existing = await self.db.execute(
                select(CopyTradingProfile).where(
                    CopyTradingProfile.wallet_address == wallet_address
                )
            )
            profile = existing.scalar_one_or_none()

            if profile:
                profile.is_following = True
                profile.auto_copy = auto_copy
                profile.copy_percentage = copy_percentage
                profile.max_copy_size = max_copy_size
                profile.min_trade_size = min_trade_size
                if nickname:
                    profile.nickname = nickname
            else:
                profile = CopyTradingProfile(
                    wallet_address=wallet_address,
                    nickname=nickname or f"Trader_{wallet_address[:8]}",
                    is_following=True,
                    auto_copy=auto_copy,
                    copy_percentage=copy_percentage,
                    max_copy_size=max_copy_size,
                    min_trade_size=min_trade_size,
                )
                self.db.add(profile)

            await self.db.commit()
            await self.db.refresh(profile)
            logger.info("Now following wallet", wallet=wallet_address, auto_copy=auto_copy)
            return self._profile_to_dict(profile)
        except Exception as e:
            logger.error("Failed to follow wallet", wallet=wallet_address, error=str(e))
            await self.db.rollback()
            return None

    async def unfollow_wallet(self, wallet_address: str) -> bool:
        """Stop following a wallet."""
        try:
            result = await self.db.execute(
                update(CopyTradingProfile)
                .where(CopyTradingProfile.wallet_address == wallet_address)
                .values(is_following=False, auto_copy=False)
            )
            await self.db.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error("Failed to unfollow wallet", wallet=wallet_address, error=str(e))
            await self.db.rollback()
            return False

    async def update_copy_settings(
        self,
        wallet_address: str,
        auto_copy: Optional[bool] = None,
        copy_percentage: Optional[float] = None,
        max_copy_size: Optional[float] = None,
    ) -> Optional[Dict]:
        """Update copy trading settings for a followed wallet."""
        try:
            result = await self.db.execute(
                select(CopyTradingProfile).where(
                    CopyTradingProfile.wallet_address == wallet_address
                )
            )
            profile = result.scalar_one_or_none()
            if not profile:
                return None

            if auto_copy is not None:
                profile.auto_copy = auto_copy
            if copy_percentage is not None:
                profile.copy_percentage = copy_percentage
            if max_copy_size is not None:
                profile.max_copy_size = max_copy_size

            await self.db.commit()
            await self.db.refresh(profile)
            return self._profile_to_dict(profile)
        except Exception as e:
            logger.error("Failed to update copy settings", error=str(e))
            await self.db.rollback()
            return None

    async def execute_copy_trade(
        self,
        profile_id: int,
        market_id: str,
        side: str,
        source_size: float,
        entry_price: float,
        market_question: Optional[str] = None,
        source_tx_hash: Optional[str] = None,
    ) -> Optional[Dict]:
        """Execute a copy trade based on a followed wallet's activity."""
        try:
            result = await self.db.execute(
                select(CopyTradingProfile).where(CopyTradingProfile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
            if not profile or not profile.is_following or not profile.auto_copy:
                return None

            copied_size = min(
                source_size * (float(profile.copy_percentage) / 100.0),
                float(profile.max_copy_size),
            )

            if copied_size < float(profile.min_trade_size):
                logger.info("Copy trade too small, skipping", size=copied_size)
                return None

            copy_trade = CopyTrade(
                profile_id=profile_id,
                source_wallet=profile.wallet_address,
                market_id=market_id,
                market_question=market_question,
                side=side,
                source_size=source_size,
                copied_size=copied_size,
                entry_price=entry_price,
                source_tx_hash=source_tx_hash,
                status="OPEN",
            )
            self.db.add(copy_trade)
            await self.db.commit()
            await self.db.refresh(copy_trade)

            logger.info(
                "Executed copy trade",
                source=profile.wallet_address,
                market=market_id,
                size=copied_size,
            )
            return self._copy_trade_to_dict(copy_trade)
        except Exception as e:
            logger.error("Failed to execute copy trade", error=str(e))
            await self.db.rollback()
            return None

    async def get_copy_trades(
        self,
        wallet_address: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get copy trade history."""
        try:
            query = select(CopyTrade)
            if wallet_address:
                query = query.where(CopyTrade.source_wallet == wallet_address)
            if status:
                query = query.where(CopyTrade.status == status.upper())
            query = query.order_by(desc(CopyTrade.copied_at)).limit(limit)

            result = await self.db.execute(query)
            trades = result.scalars().all()
            return [self._copy_trade_to_dict(t) for t in trades]
        except Exception as e:
            logger.error("Failed to get copy trades", error=str(e))
            return []

    async def get_copy_trading_stats(self) -> Dict:
        """Get overall copy trading statistics."""
        try:
            profiles_result = await self.db.execute(
                select(func.count(CopyTradingProfile.id)).where(
                    CopyTradingProfile.is_following == True
                )
            )
            following_count = profiles_result.scalar() or 0

            trades_result = await self.db.execute(
                select(
                    func.count(CopyTrade.id),
                    func.sum(CopyTrade.pnl),
                    func.count(CopyTrade.id).filter(CopyTrade.status == "OPEN"),
                )
            )
            row = trades_result.one()
            total_trades = row[0] or 0
            total_pnl = float(row[1]) if row[1] else 0.0
            open_trades = row[2] or 0

            winning = await self.db.execute(
                select(func.count(CopyTrade.id)).where(CopyTrade.pnl > 0)
            )
            winning_trades = winning.scalar() or 0

            return {
                "following_count": following_count,
                "total_copy_trades": total_trades,
                "open_copy_trades": open_trades,
                "total_pnl": round(total_pnl, 2),
                "win_rate": round(winning_trades / total_trades, 4) if total_trades > 0 else 0,
            }
        except Exception as e:
            logger.error("Failed to get copy trading stats", error=str(e))
            return {"following_count": 0, "total_copy_trades": 0, "open_copy_trades": 0, "total_pnl": 0, "win_rate": 0}

    async def discover_top_traders(self, min_profit: float = 5000, min_trades: int = 50, limit: int = 20) -> List[Dict]:
        """Discover top-performing wallets from whale data."""
        try:
            query = (
                select(WhaleWallet)
                .where(
                    WhaleWallet.total_profit >= min_profit,
                    WhaleWallet.total_trades >= min_trades,
                    WhaleWallet.is_active == True,
                )
                .order_by(desc(WhaleWallet.total_profit))
                .limit(limit)
            )
            result = await self.db.execute(query)
            wallets = result.scalars().all()

            if not wallets:
                return []

            traders = []
            for w in wallets:
                already_following = await self.db.execute(
                    select(CopyTradingProfile.is_following).where(
                        CopyTradingProfile.wallet_address == w.wallet_address
                    )
                )
                is_following = already_following.scalar() or False

                traders.append({
                    "wallet_address": w.wallet_address,
                    "nickname": w.nickname,
                    "total_profit": float(w.total_profit),
                    "win_rate": float(w.win_rate),
                    "total_trades": w.total_trades,
                    "total_volume": float(w.total_volume),
                    "rank": w.rank,
                    "is_following": is_following,
                    "last_activity": w.last_activity_at.isoformat() if w.last_activity_at else None,
                })
            return traders
        except Exception as e:
            logger.error("Failed to discover top traders", error=str(e))
            return []

    def _profile_to_dict(self, profile: CopyTradingProfile) -> Dict:
        return {
            "id": profile.id,
            "wallet_address": profile.wallet_address,
            "nickname": profile.nickname,
            "total_profit": float(profile.total_profit),
            "win_rate": float(profile.win_rate),
            "total_trades": profile.total_trades,
            "avg_position_size": float(profile.avg_position_size),
            "roi_pct": float(profile.roi_pct),
            "is_following": profile.is_following,
            "auto_copy": profile.auto_copy,
            "copy_percentage": float(profile.copy_percentage),
            "max_copy_size": float(profile.max_copy_size),
            "min_trade_size": float(profile.min_trade_size),
            "last_activity": profile.last_activity_at.isoformat() if profile.last_activity_at else None,
        }

    def _copy_trade_to_dict(self, trade: CopyTrade) -> Dict:
        return {
            "id": trade.id,
            "profile_id": trade.profile_id,
            "source_wallet": trade.source_wallet,
            "market_id": trade.market_id,
            "market_question": trade.market_question,
            "side": trade.side,
            "source_size": float(trade.source_size),
            "copied_size": float(trade.copied_size),
            "entry_price": float(trade.entry_price),
            "exit_price": float(trade.exit_price) if trade.exit_price else None,
            "pnl": float(trade.pnl) if trade.pnl else None,
            "status": trade.status,
            "copied_at": trade.copied_at.isoformat() if trade.copied_at else None,
        }
