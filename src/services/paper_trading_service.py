"""Paper trading service for virtual portfolio management."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.settings import get_settings
from ..database.models import Trade, PortfolioSnapshot, Signal
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PaperTradingService:
    """Service for managing paper trading (virtual portfolio)."""

    def __init__(self, db: AsyncSession, initial_capital: Optional[float] = None):
        """Initialize paper trading service."""
        self.db = db
        settings = get_settings()
        self.initial_capital = Decimal(str(initial_capital or settings.initial_capital))
        self.paper_trading_flag = True

    async def get_paper_portfolio(self) -> Optional[PortfolioSnapshot]:
        """Get latest paper trading portfolio snapshot."""
        try:
            query = select(PortfolioSnapshot).where(
                PortfolioSnapshot.paper_trading == True
            ).order_by(
                PortfolioSnapshot.snapshot_time.desc()
            ).limit(1)
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to get paper portfolio", error=str(e))
            return None

    async def create_paper_trade(self, signal: Signal, entry_price: float, size: float) -> Optional[Trade]:
        """
        Create a paper trade from a signal.
        
        Args:
            signal: Signal to create trade from
            entry_price: Entry price for the trade
            size: Position size in USD
            
        Returns:
            Trade object if successful, None otherwise
        """
        try:
            # Check if we have enough capital
            portfolio = await self.get_paper_portfolio()
            if not portfolio:
                # Initialize paper portfolio
                portfolio = await self._initialize_paper_portfolio()
            
            cash = float(portfolio.cash)
            if cash < size:
                logger.warning("Insufficient paper trading capital", cash=cash, size=size)
                return None
            
            # Create paper trade
            trade = Trade(
                signal_id=signal.id,
                market_id=signal.market_id,
                side=signal.side,
                entry_price=Decimal(str(entry_price)),
                size=Decimal(str(size)),
                status="OPEN",
                paper_trading=True,
                entry_time=datetime.now(timezone.utc)
            )
            
            self.db.add(trade)
            await self.db.commit()
            await self.db.refresh(trade)
            
            # Update portfolio
            await self._update_paper_portfolio()
            
            logger.info("Paper trade created", trade_id=trade.id, market_id=signal.market_id, size=size)
            return trade
        except Exception as e:
            logger.error("Failed to create paper trade", error=str(e))
            await self.db.rollback()
            return None

    async def close_paper_trade(self, trade: Trade, exit_price: float) -> bool:
        """
        Close a paper trade.
        
        Args:
            trade: Trade to close
            exit_price: Exit price for the trade
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not trade.paper_trading:
                logger.warning("Attempted to close non-paper trade as paper trade", trade_id=trade.id)
                return False
            
            if trade.status != "OPEN":
                logger.warning("Attempted to close non-open trade", trade_id=trade.id, status=trade.status)
                return False
            
            # Calculate P&L
            entry_price = float(trade.entry_price)
            size = float(trade.size)
            
            if trade.side == "YES":
                pnl = (exit_price - entry_price) * size
            else:  # NO
                pnl = (entry_price - exit_price) * size
            
            # Update trade
            trade.exit_price = Decimal(str(exit_price))
            trade.pnl = Decimal(str(pnl))
            trade.status = "CLOSED"
            trade.exit_time = datetime.now(timezone.utc)
            
            await self.db.commit()
            
            # Update portfolio
            await self._update_paper_portfolio()
            
            logger.info("Paper trade closed", trade_id=trade.id, pnl=pnl)
            return True
        except Exception as e:
            logger.error("Failed to close paper trade", trade_id=trade.id, error=str(e))
            await self.db.rollback()
            return False

    async def _initialize_paper_portfolio(self) -> PortfolioSnapshot:
        """Initialize paper trading portfolio."""
        try:
            snapshot = PortfolioSnapshot(
                snapshot_time=datetime.now(timezone.utc),
                total_value=self.initial_capital,
                cash=self.initial_capital,
                positions_value=Decimal("0"),
                total_exposure=Decimal("0"),
                daily_pnl=Decimal("0"),
                unrealized_pnl=Decimal("0"),
                realized_pnl=Decimal("0"),
                paper_trading=True
            )
            
            self.db.add(snapshot)
            await self.db.commit()
            await self.db.refresh(snapshot)
            
            logger.info("Paper portfolio initialized", initial_capital=float(self.initial_capital))
            return snapshot
        except Exception as e:
            logger.error("Failed to initialize paper portfolio", error=str(e))
            await self.db.rollback()
            raise

    async def _update_paper_portfolio(self):
        """Update paper trading portfolio snapshot."""
        try:
            # Get all open paper trades
            query = select(Trade).where(
                Trade.paper_trading == True,
                Trade.status == "OPEN"
            )
            result = await self.db.execute(query)
            open_trades = result.scalars().all()
            
            # Get all closed paper trades
            query = select(Trade).where(
                Trade.paper_trading == True,
                Trade.status == "CLOSED"
            )
            result = await self.db.execute(query)
            closed_trades = result.scalars().all()
            
            # Calculate portfolio values
            positions_value = Decimal("0")
            unrealized_pnl = Decimal("0")
            realized_pnl = sum(Decimal(str(t.pnl or 0)) for t in closed_trades)
            
            # For open trades, calculate unrealized P&L (simplified - would need current prices)
            # For now, just use entry prices
            for trade in open_trades:
                positions_value += Decimal(str(trade.size))
            
            # Get latest portfolio or initialize
            portfolio = await self.get_paper_portfolio()
            if not portfolio:
                portfolio = await self._initialize_paper_portfolio()
            
            # Calculate new values
            initial_cash = self.initial_capital
            cash_used = sum(Decimal(str(t.size)) for t in open_trades)
            cash = initial_cash - cash_used + realized_pnl  # Simplified calculation
            
            total_value = cash + positions_value + unrealized_pnl
            
            # Create new snapshot
            snapshot = PortfolioSnapshot(
                snapshot_time=datetime.now(timezone.utc),
                total_value=total_value,
                cash=cash,
                positions_value=positions_value,
                total_exposure=positions_value,
                daily_pnl=total_value - portfolio.total_value if portfolio else Decimal("0"),
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                paper_trading=True
            )
            
            self.db.add(snapshot)
            await self.db.commit()
            
            logger.debug("Paper portfolio updated", total_value=float(total_value), cash=float(cash))
        except Exception as e:
            logger.error("Failed to update paper portfolio", error=str(e))
            await self.db.rollback()


