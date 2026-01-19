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
    
    # Polymarket Official APIs (no authentication required for public data)
    GAMMA_API = "https://gamma-api.polymarket.com"
    CLOB_API = "https://clob.polymarket.com"
    
    # Thresholds
    MIN_WHALE_VOLUME = 10000  # $10k minimum to be whale
    LARGE_TRADE_THRESHOLD = 1000  # $1k+ triggers alert
    TOP_WHALE_COUNT = 100  # Track top 100 (API limits)
    
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
        Discover top traders from Polymarket Gamma API and CLOB order books.
        Returns list of whale wallets with stats.
        Falls back to mock data if APIs are unavailable.
        """
        logger.info("🐋 Discovering top whales from Polymarket APIs...")
        logger.info("   Using Gamma API for market data")
        logger.info("   Using CLOB API for order books")
        
        try:
            session = await self._get_session()
            
            # Get top markets to find active traders
            markets_url = f"{self.GAMMA_API}/markets"
            
            logger.debug(f"Fetching markets from {markets_url}")
            
            async with session.get(
                markets_url,
                params={
                    "limit": 100,
                    "active": "true"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    logger.warning(f"Gamma API returned {response.status}, using mock data")
                    return await self._get_mock_whales()
                
                markets_data = await response.json()
                
                # Handle different response formats
                if isinstance(markets_data, list):
                    markets = markets_data
                elif isinstance(markets_data, dict) and 'data' in markets_data:
                    markets = markets_data['data']
                elif isinstance(markets_data, dict) and 'results' in markets_data:
                    markets = markets_data['results']
                else:
                    logger.warning(f"Unexpected Gamma API response format: {type(markets_data)}")
                    return await self._get_mock_whales()
                
                logger.info(f"Found {len(markets)} markets from Gamma API")
            
            # Extract unique traders from order books
            whales_dict = {}
            markets_checked = 0
            
            for market in markets[:50]:  # Check top 50 markets
                market_id = market.get('condition_id') or market.get('id')
                if not market_id:
                    continue
                
                # Get order book for this market to find large traders
                try:
                    orderbook_url = f"{self.CLOB_API}/book"
                    async with session.get(
                        orderbook_url,
                        params={"token_id": market_id},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as ob_response:
                        if ob_response.status == 200:
                            orderbook = await ob_response.json()
                            
                            # Extract traders from bids/asks
                            for side in ['bids', 'asks']:
                                if side in orderbook:
                                    orders = orderbook[side]
                                    if isinstance(orders, list):
                                        for order in orders[:10]:  # Top 10 orders per side
                                            maker = order.get('maker_address') or order.get('maker')
                                            size = float(order.get('size', order.get('amount', 0)))
                                            
                                            if maker and size >= 100:  # $100+ orders
                                                if maker not in whales_dict:
                                                    whales_dict[maker] = {
                                                        'id': maker,
                                                        'volumeTraded': 0,
                                                        'numTrades': 0,
                                                        'realizedProfit': 0,
                                                        'positions': []
                                                    }
                                                
                                                whales_dict[maker]['volumeTraded'] += size
                                                whales_dict[maker]['numTrades'] += 1
                            
                            markets_checked += 1
                            
                except Exception as e:
                    logger.debug(f"Failed to get orderbook for {market_id}: {e}")
                    continue
            
            # Convert to list and sort by volume
            whales = list(whales_dict.values())
            whales.sort(key=lambda x: x['volumeTraded'], reverse=True)
            
            # Filter by minimum volume and take top 100
            whales = [w for w in whales if w['volumeTraded'] >= self.MIN_WHALE_VOLUME]
            whales = whales[:self.TOP_WHALE_COUNT]
            
            if whales:
                logger.info(f"✅ Discovered {len(whales)} whales from {markets_checked} market order books")
                return whales
            else:
                logger.warning("No whales found in order books, using mock data")
                return await self._get_mock_whales()
                
        except Exception as e:
            logger.error(f"❌ Failed to discover whales: {e}", exc_info=True)
            logger.warning("Falling back to mock data")
            return await self._get_mock_whales()
    
    async def _get_mock_whales(self) -> List[Dict]:
        """
        Fallback mock data for testing and development.
        Generates realistic-looking whale data.
        """
        logger.warning("⚠️  Using mock whale data - APIs unavailable or returned no data")
        
        mock_whales = []
        base_addresses = [
            "0x1234567890abcdef1234567890abcdef12345678",
            "0xabcdef1234567890abcdef1234567890abcdef12",
            "0x9876543210fedcba9876543210fedcba98765432",
            "0xfedcba9876543210fedcba9876543210fedcba98",
            "0x1111111111111111111111111111111111111111",
        ]
        
        for i in range(self.TOP_WHALE_COUNT):
            # Vary the addresses slightly
            base = base_addresses[i % len(base_addresses)]
            address = base[:-4] + f"{i:04x}"
            
            volume = 500000 - (i * 4000)  # Decreasing volume
            trades = 500 - (i * 4)  # Decreasing trade count
            profit = volume * 0.05  # 5% profit margin
            
            mock_whales.append({
                'id': address,
                'volumeTraded': str(volume),
                'numTrades': trades,
                'realizedProfit': str(profit),
                'positions': []
            })
        
        logger.info(f"Generated {len(mock_whales)} mock whales for testing")
        return mock_whales
    
    async def index_whales(self, whales: List[Dict]) -> int:
        """Index discovered whales into database"""
        logger.info(f"💾 Indexing {len(whales)} whales...")
        
        indexed_count = 0
        
        for rank, whale_data in enumerate(whales, start=1):
            try:
                wallet_address = whale_data['id'].lower()
                
                # Calculate win rate based on profit/volume
                win_rate = Decimal('0.5')  # Default 50%
                profit = Decimal(str(whale_data.get('realizedProfit', 0)))
                volume = Decimal(str(whale_data.get('volumeTraded', 0)))
                
                # Estimate win rate: higher profit/volume ratio = higher skill
                if volume > 0:
                    profit_ratio = profit / volume
                    # Normalize to 0.45-0.75 range based on profit ratio
                    win_rate = min(Decimal('0.75'), Decimal('0.45') + (profit_ratio * Decimal('3')))
                
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
        """
        Monitor recent trades from whale wallets.
        Note: Polymarket APIs don't provide direct trade history by wallet.
        This method would need to be implemented via blockchain indexing or
        a different data source. For now, returns empty list.
        """
        if not whale_addresses:
            return []
        
        logger.info(f"👀 Monitoring trades from {len(whale_addresses)} whales...")
        logger.warning("⚠️  Trade monitoring not yet implemented with new APIs")
        logger.info("   Would require blockchain indexing or alternative data source")
        
        # TODO: Implement via:
        # 1. Alchemy API for blockchain transaction monitoring
        # 2. Polymarket webhook integration (if available)
        # 3. Alternative data provider
        
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

