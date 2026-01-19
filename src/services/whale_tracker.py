"""
Whale Tracking Service
Monitors top 500 Polymarket traders and their trading activity.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from decimal import Decimal
import aiohttp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.logging import get_logger
from ..utils.datetime_utils import now_naive_utc
from ..database.models import WhaleWallet, WhaleTrade, WhaleAlert

logger = get_logger(__name__)


class WhaleTracker:
    """Track and analyze whale wallet activity on Polymarket"""
    
    # Polymarket subgraph endpoint (using The Graph)
    POLYMARKET_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/polymarket/matic-markets"
    
    # Thresholds
    MIN_WHALE_VOLUME = 10000  # $10k minimum to be whale
    LARGE_TRADE_THRESHOLD = 1000  # $1k+ triggers alert
    TOP_WHALE_COUNT = 500
    
    def __init__(self, db: AsyncSession, alchemy_api_key: Optional[str] = None):
        self.db = db
        self.alchemy_api_key = alchemy_api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def discover_whales(self) -> List[Dict]:
        """
        Discover top 500 traders by volume from Polymarket subgraph.
        Returns list of whale wallets with stats.
        """
        logger.info("🐋 Discovering top whales from Polymarket...")
        
        query = """
        {
          users(
            first: 500,
            orderBy: volumeTraded,
            orderDirection: desc,
            where: { volumeTraded_gt: "10000" }
          ) {
            id
            volumeTraded
            numTrades
            realizedProfit
            positions(first: 10, orderBy: value, orderDirection: desc) {
              market {
                id
                question
              }
              outcome
              value
            }
          }
        }
        """
        
        try:
            session = await self._get_session()
            async with session.post(
                self.POLYMARKET_SUBGRAPH,
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    logger.error(f"Subgraph returned status {response.status}")
                    return []
                
                data = await response.json()
                
                # Check for GraphQL errors
                if 'errors' in data:
                    error_messages = [err.get('message', str(err)) for err in data['errors']]
                    logger.error(f"GraphQL errors from subgraph: {error_messages}")
                    # Log full error details for debugging
                    for err in data['errors']:
                        logger.error(f"  Error details: {err}")
                    logger.debug(f"Full error response: {data}")
                    return []
                
                if 'data' in data and 'users' in data['data']:
                    whales = data['data']['users']
                    logger.info(f"✅ Discovered {len(whales)} whales")
                    return whales
                else:
                    logger.warning(f"Unexpected response structure: {list(data.keys())}")
                    if 'data' in data:
                        logger.warning(f"Data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else 'not a dict'}")
                    logger.debug(f"Full response: {data}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to discover whales: {e}", exc_info=True)
            return []
    
    async def index_whales(self, whales: List[Dict]) -> int:
        """Index discovered whales into database"""
        logger.info(f"💾 Indexing {len(whales)} whales...")
        
        indexed_count = 0
        
        for rank, whale_data in enumerate(whales, start=1):
            try:
                wallet_address = whale_data['id'].lower()
                
                # Calculate win rate if we have positions data
                win_rate = Decimal('0.5')  # Default 50%
                if 'positions' in whale_data and whale_data['positions']:
                    # Simplified win rate calculation based on profit
                    profit = Decimal(str(whale_data.get('realizedProfit', 0)))
                    # Normalize to 0.5-0.9 range based on profit
                    win_rate = min(Decimal('0.9'), Decimal('0.5') + (profit / Decimal('10000')))
                
                # Get or create whale wallet
                result = await self.db.execute(
                    select(WhaleWallet).where(WhaleWallet.wallet_address == wallet_address)
                )
                whale = result.scalar_one_or_none()
                
                if whale:
                    # Update existing whale
                    await self.db.execute(
                        update(WhaleWallet)
                        .where(WhaleWallet.id == whale.id)
                        .values(
                            total_volume=Decimal(str(whale_data.get('volumeTraded', 0))),
                            total_trades=int(whale_data.get('numTrades', 0)),
                            total_profit=Decimal(str(whale_data.get('realizedProfit', 0))),
                            win_rate=win_rate,
                            rank=rank,
                            last_activity_at=now_naive_utc(),
                            updated_at=now_naive_utc(),
                            is_active=True
                        )
                    )
                else:
                    # Create new whale
                    whale = WhaleWallet(
                        wallet_address=wallet_address,
                        nickname=f"Whale #{rank}",
                        total_volume=Decimal(str(whale_data.get('volumeTraded', 0))),
                        total_trades=int(whale_data.get('numTrades', 0)),
                        total_profit=Decimal(str(whale_data.get('realizedProfit', 0))),
                        win_rate=win_rate,
                        rank=rank,
                        is_active=True,
                        first_seen_at=now_naive_utc(),
                        last_activity_at=now_naive_utc()
                    )
                    self.db.add(whale)
                
                indexed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to index whale {wallet_address}: {e}", exc_info=True)
        
        try:
            await self.db.commit()
            logger.info(f"✅ Indexed {indexed_count} whales")
        except Exception as e:
            logger.error(f"Failed to commit whales: {e}")
            await self.db.rollback()
        
        return indexed_count
    
    async def monitor_whale_trades(self, whale_addresses: List[str]) -> List[Dict]:
        """Monitor recent trades from whale wallets"""
        if not whale_addresses:
            return []
        
        logger.info(f"👀 Monitoring trades from {len(whale_addresses)} whales...")
        
        # Get trades from last 10 minutes
        cutoff_timestamp = int((datetime.utcnow() - timedelta(minutes=10)).timestamp())
        
        # Format addresses for GraphQL array (limit to 100 for query size)
        addresses = whale_addresses[:100]
        addresses_str = '["' + '","'.join(addresses) + '"]'
        
        query = f"""
        {{
          trades(
            first: 100,
            orderBy: timestamp,
            orderDirection: desc,
            where: {{
              user_in: {addresses_str},
              timestamp_gt: {cutoff_timestamp}
            }}
          ) {{
            id
            user
            market {{
              id
              question
            }}
            outcome
            type
            tokensTraded
            tokensBought
            tokensSold
            collateralAmount
            timestamp
            transactionHash
          }}
        }}
        """
        
        try:
            session = await self._get_session()
            async with session.post(
                self.POLYMARKET_SUBGRAPH,
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                
                if 'data' in data and 'trades' in data['data']:
                    trades = data['data']['trades']
                    logger.info(f"📊 Found {len(trades)} recent whale trades")
                    return trades
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Failed to monitor trades: {e}", exc_info=True)
            return []
    
    async def record_whale_trade(self, trade_data: Dict) -> Optional[int]:
        """Record a whale trade in database"""
        try:
            # Get whale_id
            result = await self.db.execute(
                select(WhaleWallet).where(
                    WhaleWallet.wallet_address == trade_data['user'].lower()
                )
            )
            whale = result.scalar_one_or_none()
            
            if not whale:
                logger.warning(f"Whale not found: {trade_data['user']}")
                return None
            
            # Calculate amount and price
            tokens_traded = Decimal(str(trade_data.get('tokensTraded', 0)))
            collateral = Decimal(str(trade_data.get('collateralAmount', 0)))
            price = collateral / tokens_traded if tokens_traded > 0 else Decimal(0)
            trade_value = collateral  # Use collateral as trade value
            
            # Check if trade already exists
            existing = await self.db.execute(
                select(WhaleTrade).where(
                    WhaleTrade.transaction_hash == trade_data.get('transactionHash')
                )
            )
            if existing.scalar_one_or_none():
                return None  # Trade already recorded
            
            # Insert trade
            trade = WhaleTrade(
                whale_id=whale.id,
                wallet_address=trade_data['user'].lower(),
                market_id=trade_data['market']['id'],
                market_question=trade_data['market'].get('question', ''),
                trade_type=trade_data['type'],
                outcome=trade_data['outcome'],
                amount=collateral,
                price=price,
                trade_value=trade_value,
                transaction_hash=trade_data.get('transactionHash'),
                trade_time=datetime.fromtimestamp(int(trade_data['timestamp']))
            )
            
            self.db.add(trade)
            await self.db.flush()  # Get the ID
            
            # Update whale's last activity
            await self.db.execute(
                update(WhaleWallet)
                .where(WhaleWallet.id == whale.id)
                .values(last_activity_at=now_naive_utc())
            )
            
            await self.db.commit()
            
            # Create alerts if trade is large
            if trade_value >= self.LARGE_TRADE_THRESHOLD:
                await self._create_large_trade_alert(whale.id, trade.id)
            
            logger.debug(f"✅ Recorded whale trade {trade.id} (value: ${trade_value})")
            return trade.id
            
        except Exception as e:
            logger.error(f"Failed to record trade: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def _create_large_trade_alert(self, whale_id: int, trade_id: int):
        """Create alerts for users watching this whale"""
        try:
            # Check if alert already exists
            existing = await self.db.execute(
                select(WhaleAlert).where(WhaleAlert.trade_id == trade_id)
            )
            if existing.scalar_one_or_none():
                return  # Alert already exists
            
            # Create alert for default user (user_id=1)
            alert = WhaleAlert(
                user_id=1,
                whale_id=whale_id,
                trade_id=trade_id,
                alert_type='large_trade',
                is_read=False
            )
            self.db.add(alert)
            await self.db.commit()
            
            logger.info(f"🚨 Created alert for large trade {trade_id}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}", exc_info=True)
            await self.db.rollback()
    
    async def get_whale_leaderboard(self, limit: int = 100) -> List[Dict]:
        """Get top whales by volume"""
        result = await self.db.execute(
            select(WhaleWallet)
            .where(WhaleWallet.is_active == True)
            .order_by(WhaleWallet.rank.asc().nulls_last())
            .limit(limit)
        )
        whales = result.scalars().all()
        
        leaderboard = []
        for whale in whales:
            hours_since = (datetime.utcnow() - whale.last_activity_at.replace(tzinfo=None)).total_seconds() / 3600
            leaderboard.append({
                "id": whale.id,
                "rank": whale.rank,
                "wallet_address": whale.wallet_address,
                "nickname": whale.nickname or f"Whale #{whale.rank}",
                "total_volume": float(whale.total_volume),
                "total_trades": whale.total_trades,
                "total_profit": float(whale.total_profit),
                "win_rate": float(whale.win_rate) * 100,
                "hours_since_trade": hours_since
            })
        
        return leaderboard
    
    async def get_recent_whale_activity(
        self,
        hours: int = 24,
        min_value: float = 1000
    ) -> List[Dict]:
        """Get recent significant whale trades"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(WhaleTrade, WhaleWallet)
            .join(WhaleWallet, WhaleTrade.whale_id == WhaleWallet.id)
            .where(
                WhaleTrade.trade_time >= cutoff_time,
                WhaleTrade.trade_value >= Decimal(str(min_value))
            )
            .order_by(WhaleTrade.trade_time.desc())
            .limit(100)
        )
        
        trades = []
        for trade, whale in result.all():
            hours_ago = (datetime.utcnow() - trade.trade_time.replace(tzinfo=None)).total_seconds() / 3600
            trades.append({
                "whale_rank": whale.rank,
                "whale_address": whale.wallet_address[:10] + "..." + whale.wallet_address[-8:],
                "whale_nickname": whale.nickname or f"Whale #{whale.rank}",
                "market": trade.market_question or trade.market_id,
                "action": f"{trade.trade_type} {trade.outcome}",
                "amount": float(trade.amount),
                "price": float(trade.price),
                "value": float(trade.trade_value),
                "time": trade.trade_time.isoformat(),
                "hours_ago": hours_ago
            })
        
        return trades
    
    async def close(self):
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()

