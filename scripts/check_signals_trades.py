#!/usr/bin/env python3
"""
Script to check signals and trades in the database.
This helps verify if signals/trades are being created.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func, desc
from src.database import AsyncSessionLocal
from src.database.models import Signal, Trade, PortfolioSnapshot


async def check_signals_and_trades():
    """Check signals and trades in the database."""
    print("=" * 60)
    print("Checking Signals and Trades in Database")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as db:
        try:
            # Check signals
            print("1. SIGNALS:")
            print("-" * 60)
            
            # Total count
            result = await db.execute(select(func.count(Signal.id)))
            total_signals = result.scalar() or 0
            print(f"   Total signals: {total_signals}")
            
            if total_signals > 0:
                # Recent signals
                result = await db.execute(
                    select(Signal)
                    .order_by(desc(Signal.created_at))
                    .limit(5)
                )
                recent_signals = result.scalars().all()
                
                print(f"   Recent signals (last 5):")
                for signal in recent_signals:
                    print(f"   - ID: {signal.id}, Market: {signal.market_id[:20]}..., "
                          f"Side: {signal.side}, Strength: {signal.signal_strength}, "
                          f"Created: {signal.created_at}, Executed: {signal.executed}")
                
                # Today's signals
                today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                result = await db.execute(
                    select(func.count(Signal.id))
                    .where(Signal.created_at >= today)
                )
                today_signals = result.scalar() or 0
                print(f"   Signals created today: {today_signals}")
                
                # Executed vs not executed
                result = await db.execute(
                    select(func.count(Signal.id))
                    .where(Signal.executed == True)
                )
                executed_signals = result.scalar() or 0
                print(f"   Executed signals: {executed_signals}")
                print(f"   Unexecuted signals: {total_signals - executed_signals}")
            else:
                print("   ⚠️  No signals found in database")
            
            print()
            
            # Check trades
            print("2. TRADES:")
            print("-" * 60)
            
            # Total count
            result = await db.execute(select(func.count(Trade.id)))
            total_trades = result.scalar() or 0
            print(f"   Total trades: {total_trades}")
            
            if total_trades > 0:
                # Recent trades
                result = await db.execute(
                    select(Trade)
                    .order_by(desc(Trade.entry_time))
                    .limit(5)
                )
                recent_trades = result.scalars().all()
                
                print(f"   Recent trades (last 5):")
                for trade in recent_trades:
                    print(f"   - ID: {trade.id}, Market: {trade.market_id[:20]}..., "
                          f"Side: {trade.side}, Status: {trade.status}, "
                          f"Size: ${trade.size}, Entry: {trade.entry_time}")
                
                # Today's trades
                today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                result = await db.execute(
                    select(func.count(Trade.id))
                    .where(Trade.entry_time >= today)
                )
                today_trades = result.scalar() or 0
                print(f"   Trades created today: {today_trades}")
                
                # By status
                result = await db.execute(
                    select(Trade.status, func.count(Trade.id))
                    .group_by(Trade.status)
                )
                trades_by_status = result.all()
                print(f"   Trades by status:")
                for status, count in trades_by_status:
                    print(f"   - {status}: {count}")
            else:
                print("   ⚠️  No trades found in database")
            
            print()
            
            # Check portfolio snapshots
            print("3. PORTFOLIO SNAPSHOTS:")
            print("-" * 60)
            
            result = await db.execute(select(func.count(PortfolioSnapshot.id)))
            total_snapshots = result.scalar() or 0
            print(f"   Total snapshots: {total_snapshots}")
            
            if total_snapshots > 0:
                result = await db.execute(
                    select(PortfolioSnapshot)
                    .order_by(desc(PortfolioSnapshot.snapshot_time))
                    .limit(1)
                )
                latest = result.scalar_one_or_none()
                if latest:
                    print(f"   Latest snapshot:")
                    print(f"   - Time: {latest.snapshot_time}")
                    print(f"   - Total Value: ${latest.total_value}")
                    print(f"   - Cash: ${latest.cash}")
                    print(f"   - Positions Value: ${latest.positions_value}")
                    print(f"   - Total Exposure: ${latest.total_exposure}")
                    print(f"   - Realized P&L: ${latest.realized_pnl or 0}")
                    print(f"   - Unrealized P&L: ${latest.unrealized_pnl or 0}")
            else:
                print("   ⚠️  No portfolio snapshots found")
            
            print()
            print("=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Signals: {total_signals} total, {today_signals if total_signals > 0 else 0} today")
            print(f"Trades: {total_trades} total, {today_trades if total_trades > 0 else 0} today")
            print(f"Portfolio Snapshots: {total_snapshots}")
            print()
            
            if total_signals == 0:
                print("❌ NO SIGNALS FOUND")
                print("   This is the root cause - signals are not being created")
                print("   Need to fix signal generation logic")
            elif total_trades == 0:
                print("⚠️  SIGNALS FOUND BUT NO TRADES")
                print("   Signals are being created but trades are not")
                print("   Need to check trade creation logic")
            else:
                print("✅ SIGNALS AND TRADES FOUND")
                print("   Both are being created successfully")
            
        except Exception as e:
            print(f"❌ Error checking database: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_signals_and_trades())


