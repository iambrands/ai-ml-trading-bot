"""
Economic Calendar Service
Fetches and matches economic events to Polymarket markets.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.logging import get_logger
from ..utils.datetime_utils import now_naive_utc
from ..database.models import EconomicEvent, MarketEvent, EventAlert, EventMarketImpact, Market

logger = get_logger(__name__)


class EconomicCalendar:
    """Manage economic calendar events and market matching"""
    
    # Event type keywords for market matching
    EVENT_KEYWORDS = {
        'FOMC': ['fed', 'federal reserve', 'interest rate', 'rate hike', 'rate cut', 
                 'monetary policy', 'jerome powell', 'fomc', 'basis points', 'bps'],
        'CPI': ['inflation', 'cpi', 'consumer price', 'price index', 'pce', 
                'core inflation', 'headline inflation'],
        'NFP': ['jobs', 'employment', 'unemployment', 'payroll', 'nfp', 'labor', 
                'job market', 'jobless', 'employment report'],
        'GDP': ['gdp', 'economic growth', 'recession', 'economy', 'gross domestic',
                'growth rate', 'economic output'],
        'RETAIL': ['retail sales', 'consumer spending', 'retail'],
        'HOUSING': ['housing', 'home sales', 'housing starts', 'real estate']
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def initialize_2026_calendar(self) -> int:
        """
        Initialize calendar with known 2026 events.
        Returns count of events created.
        """
        logger.info("📅 Initializing 2026 economic calendar...")
        
        events = []
        
        # FOMC Meetings 2026 (8 scheduled meetings)
        fomc_dates = [
            ("2026-01-29", "14:00", "FOMC Meeting - January"),
            ("2026-03-18", "14:00", "FOMC Meeting - March"),
            ("2026-04-29", "14:00", "FOMC Meeting - April"),
            ("2026-06-17", "14:00", "FOMC Meeting - June"),
            ("2026-07-29", "14:00", "FOMC Meeting - July"),
            ("2026-09-16", "14:00", "FOMC Meeting - September"),
            ("2026-10-28", "14:00", "FOMC Meeting - October"),
            ("2026-12-16", "14:00", "FOMC Meeting - December"),
        ]
        
        for date_str, time_str, name in fomc_dates:
            event_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            events.append({
                'event_type': 'FOMC',
                'event_name': name,
                'event_date': event_date,
                'release_time': time_str,
                'importance': 'HIGH',
                'description': 'Federal Open Market Committee announces monetary policy decision and interest rate guidance',
                'external_url': 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'
            })
        
        # CPI Releases 2026 (monthly, typically 13th of month at 8:30 AM)
        cpi_months = [
            ("2026-02-13", "January 2026"),
            ("2026-03-13", "February 2026"),
            ("2026-04-13", "March 2026"),
            ("2026-05-13", "April 2026"),
            ("2026-06-13", "May 2026"),
            ("2026-07-13", "June 2026"),
            ("2026-08-13", "July 2026"),
            ("2026-09-13", "August 2026"),
            ("2026-10-13", "September 2026"),
            ("2026-11-13", "October 2026"),
            ("2026-12-13", "November 2026"),
        ]
        
        for date_str, month_label in cpi_months:
            event_date = datetime.strptime(f"{date_str} 08:30", "%Y-%m-%d %H:%M")
            events.append({
                'event_type': 'CPI',
                'event_name': f'Consumer Price Index - {month_label}',
                'event_date': event_date,
                'release_time': '08:30',
                'importance': 'HIGH',
                'description': 'Monthly inflation data measuring changes in prices paid by urban consumers',
                'external_url': 'https://www.bls.gov/cpi/'
            })
        
        # Non-Farm Payroll (NFP) - First Friday of each month at 8:30 AM
        nfp_dates = self._calculate_first_fridays_2026()
        for date_str, month_label in nfp_dates:
            event_date = datetime.strptime(f"{date_str} 08:30", "%Y-%m-%d %H:%M")
            events.append({
                'event_type': 'NFP',
                'event_name': f'Non-Farm Payroll - {month_label}',
                'event_date': event_date,
                'release_time': '08:30',
                'importance': 'HIGH',
                'description': 'Monthly employment data showing job creation and unemployment rate',
                'external_url': 'https://www.bls.gov/news.release/empsit.toc.htm'
            })
        
        # GDP Releases 2026 (quarterly with advance, second, final estimates)
        gdp_dates = [
            ("2026-01-29", "Q4 2025 Advance"),
            ("2026-02-27", "Q4 2025 Second Estimate"),
            ("2026-03-26", "Q4 2025 Final"),
            ("2026-04-30", "Q1 2026 Advance"),
            ("2026-05-28", "Q1 2026 Second Estimate"),
            ("2026-06-25", "Q1 2026 Final"),
            ("2026-07-30", "Q2 2026 Advance"),
            ("2026-08-27", "Q2 2026 Second Estimate"),
            ("2026-09-24", "Q2 2026 Final"),
            ("2026-10-29", "Q3 2026 Advance"),
            ("2026-11-25", "Q3 2026 Second Estimate"),
            ("2026-12-23", "Q3 2026 Final"),
        ]
        
        for date_str, quarter_label in gdp_dates:
            event_date = datetime.strptime(f"{date_str} 08:30", "%Y-%m-%d %H:%M")
            events.append({
                'event_type': 'GDP',
                'event_name': f'GDP Release - {quarter_label}',
                'event_date': event_date,
                'release_time': '08:30',
                'importance': 'HIGH',
                'description': 'Quarterly economic growth data measuring total value of goods and services',
                'external_url': 'https://www.bea.gov/data/gdp'
            })
        
        # Store all events
        stored_count = await self._store_events(events)
        
        logger.info(f"✅ Initialized {stored_count} economic events for 2026")
        return stored_count
    
    def _calculate_first_fridays_2026(self) -> List[tuple]:
        """Calculate first Friday of each month in 2026"""
        first_fridays = []
        
        for month in range(1, 13):
            # Get first day of month
            first_day = datetime(2026, month, 1)
            
            # Calculate days until Friday (weekday 4)
            days_until_friday = (4 - first_day.weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7  # If 1st is Friday, go to 2nd Friday
            
            first_friday = first_day + timedelta(days=days_until_friday)
            
            # Skip if it's in the past
            if first_friday > datetime.now():
                date_str = first_friday.strftime("%Y-%m-%d")
                month_label = first_friday.strftime("%B %Y")
                first_fridays.append((date_str, month_label))
        
        return first_fridays
    
    async def _store_events(self, events: List[Dict]) -> int:
        """Store economic events in database"""
        stored_count = 0
        
        for event_data in events:
            try:
                # Check if event already exists
                existing = await self.db.execute(
                    select(EconomicEvent).where(
                        EconomicEvent.event_type == event_data['event_type'],
                        EconomicEvent.event_name == event_data['event_name'],
                        EconomicEvent.event_date == event_data['event_date']
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # Event already exists
                
                # Create new event
                event = EconomicEvent(
                    event_type=event_data['event_type'],
                    event_name=event_data['event_name'],
                    event_date=event_data['event_date'],
                    release_time=event_data['release_time'],
                    importance=event_data['importance'],
                    description=event_data.get('description', ''),
                    external_url=event_data.get('external_url', ''),
                    is_completed=False
                )
                self.db.add(event)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store event {event_data.get('event_name')}: {e}", exc_info=True)
        
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to commit events: {e}")
            await self.db.rollback()
        
        return stored_count
    
    async def match_markets_to_events(self) -> int:
        """
        Match Polymarket markets to economic events using keyword analysis.
        Returns count of market-event relationships created.
        """
        logger.info("🔗 Matching markets to economic events...")
        
        # Get upcoming events (next 90 days)
        cutoff_date = now_naive_utc() + timedelta(days=90)
        result = await self.db.execute(
            select(EconomicEvent).where(
                EconomicEvent.event_date > now_naive_utc(),
                EconomicEvent.event_date < cutoff_date,
                EconomicEvent.is_completed == False
            ).order_by(EconomicEvent.event_date.asc())
        )
        events = result.scalars().all()
        
        # Get active markets
        markets_result = await self.db.execute(
            select(Market).where(
                Market.resolution_date.is_(None)
            )
        )
        markets = markets_result.scalars().all()
        
        matched_count = 0
        
        for event in events:
            event_keywords = self.EVENT_KEYWORDS.get(event.event_type, [])
            
            for market in markets:
                # Combine question and category for matching
                market_text = (
                    (market.question or '') + ' ' + 
                    (market.category or '')
                ).lower()
                
                # Calculate relevance score
                relevance = self._calculate_relevance(market_text, event_keywords)
                
                if relevance >= 0.3:  # 30% relevance threshold
                    try:
                        # Check if relationship already exists
                        existing = await self.db.execute(
                            select(MarketEvent).where(
                                MarketEvent.market_id == market.market_id,
                                MarketEvent.event_id == event.id
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue  # Relationship already exists
                        
                        # Generate impact prediction
                        impact = self._predict_impact(event.event_type, market_text)
                        
                        # Create market-event relationship
                        market_event = MarketEvent(
                            market_id=market.market_id,
                            event_id=event.id,
                            relevance_score=Decimal(str(relevance)),
                            impact_prediction=impact
                        )
                        self.db.add(market_event)
                        matched_count += 1
                    except Exception as e:
                        logger.error(f"Failed to match market to event: {e}", exc_info=True)
        
        try:
            await self.db.commit()
            logger.info(f"✅ Created {matched_count} market-event relationships")
        except Exception as e:
            logger.error(f"Failed to commit market-event relationships: {e}")
            await self.db.rollback()
        
        return matched_count
    
    def _calculate_relevance(self, market_text: str, keywords: List[str]) -> float:
        """Calculate relevance score between market text and keywords"""
        if not keywords:
            return 0.0
        
        market_lower = market_text.lower()
        matches = sum(1 for keyword in keywords if keyword.lower() in market_lower)
        
        # Weight by keyword specificity
        base_score = matches / len(keywords)
        
        # Bonus for multiple keyword matches
        if matches >= 3:
            base_score *= 1.5
        elif matches >= 2:
            base_score *= 1.2
        
        return min(base_score, 1.0)
    
    def _predict_impact(self, event_type: str, market_text: str) -> str:
        """Generate simple impact prediction based on event type"""
        predictions = {
            'FOMC': 'Interest rate decisions typically impact markets related to inflation, economy, and Fed policy',
            'CPI': 'Inflation data directly affects markets about price trends and Fed policy expectations',
            'NFP': 'Employment data impacts markets about job growth, unemployment, and economic health',
            'GDP': 'Growth data affects markets about recession risk and overall economic performance'
        }
        return predictions.get(event_type, 'Economic data may impact related prediction markets')
    
    async def get_upcoming_events(
        self,
        days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get upcoming economic events within next N days"""
        cutoff_date = now_naive_utc() + timedelta(days=days)
        
        from ...database.models import MarketEvent
        
        query = select(
            EconomicEvent.id,
            EconomicEvent.event_type,
            EconomicEvent.event_name,
            EconomicEvent.event_date,
            EconomicEvent.importance,
            EconomicEvent.description,
            EconomicEvent.external_url,
            func.count(func.distinct(MarketEvent.market_id)).label('related_markets_count')
        ).outerjoin(
            MarketEvent, EconomicEvent.id == MarketEvent.event_id
        ).where(
            EconomicEvent.event_date > now_naive_utc(),
            EconomicEvent.event_date < cutoff_date,
            EconomicEvent.is_completed == False
        )
        
        if event_types:
            query = query.where(EconomicEvent.event_type.in_(event_types))
        
        query = query.group_by(EconomicEvent.id).order_by(EconomicEvent.event_date.asc())
        
        result = await self.db.execute(query)
        rows = result.all()
        
        events = []
        for row in rows:
            days_until = (row.event_date - now_naive_utc().replace(tzinfo=None)).total_seconds() / 86400
            events.append({
                'id': row.id,
                'event_type': row.event_type,
                'event_name': row.event_name,
                'event_date': row.event_date,
                'importance': row.importance,
                'description': row.description,
                'external_url': row.external_url,
                'related_markets_count': row.related_markets_count or 0,
                'days_until': days_until
            })
        
        return events
    
    async def get_event_markets(self, event_id: int) -> List[Dict]:
        """Get markets related to a specific economic event"""
        result = await self.db.execute(
            select(MarketEvent, Market).join(
                Market, MarketEvent.market_id == Market.market_id
            ).where(
                MarketEvent.event_id == event_id
            ).order_by(MarketEvent.relevance_score.desc()).limit(50)
        )
        
        markets = []
        for market_event, market in result.all():
            # Get latest prediction for price
            from ..database.models import Prediction
            price_result = await self.db.execute(
                select(Prediction.market_price).where(
                    Prediction.market_id == market.market_id
                ).order_by(Prediction.prediction_time.desc()).limit(1)
            )
            price_row = price_result.scalar_one_or_none()
            price = float(price_row[0]) if price_row else 0.5
            
            markets.append({
                'id': market.market_id,
                'question': market.question,
                'price': price,
                'volume': 0,  # Volume not stored in Market model
                'relevance': float(market_event.relevance_score),
                'impact_prediction': market_event.impact_prediction
            })
        
        return markets

