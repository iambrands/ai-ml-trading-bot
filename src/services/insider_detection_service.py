"""Insider / Suspicious Activity Detection Service."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import SuspiciousActivity, WhaleTrade, WhaleWallet, Trade, PriceHistory
from ..utils.logging import get_logger

logger = get_logger(__name__)


class InsiderDetectionService:
    """Detects suspicious trading patterns and potential insider activity."""

    ACTIVITY_TYPES = {
        "LARGE_POSITION": "Unusually large position relative to market liquidity",
        "PRE_EVENT_SPIKE": "Significant trading activity before a major event resolution",
        "WASH_TRADING": "Potential wash trading detected (same wallet buying and selling)",
        "UNUSUAL_TIMING": "Trading at unusual times or patterns suggesting automated insider bot",
        "COORDINATED": "Multiple wallets acting in coordinated fashion on same market",
        "FRONT_RUNNING": "Activity suggesting front-running of large orders",
        "CONCENTRATION": "Extreme position concentration in a single market",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_for_suspicious_activity(self, hours: int = 24) -> List[Dict]:
        """Run all detection algorithms and return findings."""
        findings = []
        try:
            large = await self._detect_large_positions(hours)
            findings.extend(large)

            pre_event = await self._detect_pre_event_spikes(hours)
            findings.extend(pre_event)

            coordinated = await self._detect_coordinated_activity(hours)
            findings.extend(coordinated)

            concentration = await self._detect_concentration(hours)
            findings.extend(concentration)

            for finding in findings:
                await self._save_finding(finding)

            if findings:
                await self.db.commit()

            logger.info("Suspicious activity scan complete", findings=len(findings))
            return findings
        except Exception as e:
            logger.error("Failed to scan for suspicious activity", error=str(e))
            await self.db.rollback()
            return []

    async def get_recent_alerts(
        self,
        severity: Optional[str] = None,
        activity_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Get recent suspicious activity alerts."""
        try:
            query = select(SuspiciousActivity)
            if severity:
                query = query.where(SuspiciousActivity.severity == severity.upper())
            if activity_type:
                query = query.where(SuspiciousActivity.activity_type == activity_type.upper())
            query = query.order_by(desc(SuspiciousActivity.detected_at)).limit(limit)

            result = await self.db.execute(query)
            activities = result.scalars().all()
            return [self._activity_to_dict(a) for a in activities]
        except Exception as e:
            logger.error("Failed to get suspicious activities", error=str(e))
            return []

    async def get_suspicious_wallets(self, limit: int = 20) -> List[Dict]:
        """Get wallets with the most suspicious activity."""
        try:
            result = await self.db.execute(
                select(
                    SuspiciousActivity.wallet_address,
                    func.count(SuspiciousActivity.id).label("alert_count"),
                    func.max(SuspiciousActivity.severity).label("max_severity"),
                    func.max(SuspiciousActivity.detected_at).label("latest"),
                )
                .group_by(SuspiciousActivity.wallet_address)
                .order_by(desc("alert_count"))
                .limit(limit)
            )
            rows = result.all()

            return [
                {
                    "wallet_address": row[0],
                    "alert_count": row[1],
                    "max_severity": row[2],
                    "latest_detection": row[3].isoformat() if row[3] else None,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("Failed to get suspicious wallets", error=str(e))
            return []

    async def get_market_risk_score(self, market_id: str) -> Dict:
        """Calculate a risk score for a market based on suspicious activity."""
        try:
            result = await self.db.execute(
                select(
                    func.count(SuspiciousActivity.id),
                    func.avg(SuspiciousActivity.confidence_score),
                )
                .where(SuspiciousActivity.market_id == market_id)
            )
            row = result.one()
            alert_count = row[0] or 0
            avg_confidence = float(row[1]) if row[1] else 0

            severity_result = await self.db.execute(
                select(SuspiciousActivity.severity, func.count(SuspiciousActivity.id))
                .where(SuspiciousActivity.market_id == market_id)
                .group_by(SuspiciousActivity.severity)
            )
            severity_breakdown = {row[0]: row[1] for row in severity_result.all()}

            severity_weights = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 5}
            weighted_score = sum(
                severity_weights.get(sev, 1) * count
                for sev, count in severity_breakdown.items()
            )

            risk_score = min(100, weighted_score * 10)
            risk_level = (
                "CRITICAL" if risk_score >= 80
                else "HIGH" if risk_score >= 60
                else "MEDIUM" if risk_score >= 30
                else "LOW"
            )

            return {
                "market_id": market_id,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "total_alerts": alert_count,
                "avg_confidence": round(avg_confidence, 4),
                "severity_breakdown": severity_breakdown,
            }
        except Exception as e:
            logger.error("Failed to get market risk score", error=str(e))
            return {"market_id": market_id, "risk_score": 0, "risk_level": "UNKNOWN"}

    async def mark_reviewed(self, activity_id: int) -> bool:
        """Mark a suspicious activity as reviewed."""
        try:
            result = await self.db.execute(
                select(SuspiciousActivity).where(SuspiciousActivity.id == activity_id)
            )
            activity = result.scalar_one_or_none()
            if activity:
                activity.is_reviewed = True
                await self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error("Failed to mark reviewed", error=str(e))
            await self.db.rollback()
            return False

    async def _detect_large_positions(self, hours: int) -> List[Dict]:
        """Detect unusually large positions."""
        findings = []
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(WhaleTrade)
                .where(
                    WhaleTrade.trade_time >= cutoff,
                    WhaleTrade.trade_value >= 50000,
                )
                .order_by(desc(WhaleTrade.trade_value))
                .limit(20)
            )
            trades = result.scalars().all()

            for trade in trades:
                severity = "CRITICAL" if float(trade.trade_value) >= 500000 else "HIGH" if float(trade.trade_value) >= 100000 else "MEDIUM"
                findings.append({
                    "wallet_address": trade.wallet_address,
                    "market_id": trade.market_id,
                    "market_question": trade.market_question,
                    "activity_type": "LARGE_POSITION",
                    "severity": severity,
                    "description": f"Large {trade.trade_type} of ${float(trade.trade_value):,.2f} on market",
                    "trade_amount": float(trade.trade_value),
                    "price_at_detection": float(trade.price),
                    "confidence_score": 0.85,
                    "evidence": {"trade_id": trade.id, "trade_type": trade.trade_type, "amount": float(trade.amount)},
                })
        except Exception as e:
            logger.error("Failed to detect large positions", error=str(e))
        return findings

    async def _detect_pre_event_spikes(self, hours: int) -> List[Dict]:
        """Detect spikes in activity before event resolution."""
        findings = []
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(
                    WhaleTrade.market_id,
                    func.count(WhaleTrade.id).label("trade_count"),
                    func.sum(WhaleTrade.trade_value).label("total_value"),
                )
                .where(WhaleTrade.trade_time >= cutoff)
                .group_by(WhaleTrade.market_id)
                .having(func.count(WhaleTrade.id) >= 5)
                .order_by(desc("total_value"))
                .limit(10)
            )
            rows = result.all()

            for row in rows:
                if float(row[2] or 0) >= 100000:
                    findings.append({
                        "wallet_address": "MULTIPLE",
                        "market_id": row[0],
                        "market_question": None,
                        "activity_type": "PRE_EVENT_SPIKE",
                        "severity": "HIGH",
                        "description": f"{row[1]} trades totaling ${float(row[2]):,.2f} in {hours}h window",
                        "trade_amount": float(row[2]),
                        "confidence_score": 0.70,
                        "evidence": {"trade_count": row[1], "total_value": float(row[2])},
                    })
        except Exception as e:
            logger.error("Failed to detect pre-event spikes", error=str(e))
        return findings

    async def _detect_coordinated_activity(self, hours: int) -> List[Dict]:
        """Detect coordinated trading from multiple wallets."""
        findings = []
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(
                    WhaleTrade.market_id,
                    WhaleTrade.outcome,
                    func.count(func.distinct(WhaleTrade.wallet_address)).label("wallet_count"),
                    func.sum(WhaleTrade.trade_value).label("total_value"),
                )
                .where(
                    WhaleTrade.trade_time >= cutoff,
                    WhaleTrade.trade_type == "BUY",
                )
                .group_by(WhaleTrade.market_id, WhaleTrade.outcome)
                .having(func.count(func.distinct(WhaleTrade.wallet_address)) >= 3)
                .order_by(desc("total_value"))
                .limit(10)
            )
            rows = result.all()

            for row in rows:
                if row[2] >= 3:
                    findings.append({
                        "wallet_address": "COORDINATED",
                        "market_id": row[0],
                        "market_question": None,
                        "activity_type": "COORDINATED",
                        "severity": "HIGH",
                        "description": f"{row[2]} wallets bought {row[1]} totaling ${float(row[3]):,.2f}",
                        "trade_amount": float(row[3]),
                        "confidence_score": 0.65,
                        "evidence": {"wallet_count": row[2], "side": row[1], "total_value": float(row[3])},
                    })
        except Exception as e:
            logger.error("Failed to detect coordinated activity", error=str(e))
        return findings

    async def _detect_concentration(self, hours: int) -> List[Dict]:
        """Detect extreme position concentration."""
        findings = []
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            result = await self.db.execute(
                select(
                    WhaleTrade.wallet_address,
                    WhaleTrade.market_id,
                    func.sum(WhaleTrade.trade_value).label("total_value"),
                )
                .where(WhaleTrade.trade_time >= cutoff, WhaleTrade.trade_type == "BUY")
                .group_by(WhaleTrade.wallet_address, WhaleTrade.market_id)
                .having(func.sum(WhaleTrade.trade_value) >= 200000)
                .order_by(desc("total_value"))
                .limit(10)
            )
            rows = result.all()

            for row in rows:
                findings.append({
                    "wallet_address": row[0],
                    "market_id": row[1],
                    "market_question": None,
                    "activity_type": "CONCENTRATION",
                    "severity": "MEDIUM",
                    "description": f"Concentrated ${float(row[2]):,.2f} in single market",
                    "trade_amount": float(row[2]),
                    "confidence_score": 0.60,
                    "evidence": {"total_value": float(row[2])},
                })
        except Exception as e:
            logger.error("Failed to detect concentration", error=str(e))
        return findings

    async def _save_finding(self, finding: Dict):
        """Save a suspicious activity finding to database."""
        try:
            activity = SuspiciousActivity(
                wallet_address=finding["wallet_address"],
                market_id=finding["market_id"],
                market_question=finding.get("market_question"),
                activity_type=finding["activity_type"],
                severity=finding["severity"],
                description=finding["description"],
                trade_amount=finding.get("trade_amount"),
                price_at_detection=finding.get("price_at_detection"),
                confidence_score=finding["confidence_score"],
                evidence=finding.get("evidence"),
            )
            self.db.add(activity)
        except Exception as e:
            logger.error("Failed to save finding", error=str(e))

    def _activity_to_dict(self, activity: SuspiciousActivity) -> Dict:
        return {
            "id": activity.id,
            "wallet_address": activity.wallet_address,
            "market_id": activity.market_id,
            "market_question": activity.market_question,
            "activity_type": activity.activity_type,
            "severity": activity.severity,
            "description": activity.description,
            "trade_amount": float(activity.trade_amount) if activity.trade_amount else None,
            "price_at_detection": float(activity.price_at_detection) if activity.price_at_detection else None,
            "price_impact_pct": float(activity.price_impact_pct) if activity.price_impact_pct else None,
            "confidence_score": float(activity.confidence_score),
            "evidence": activity.evidence,
            "is_reviewed": activity.is_reviewed,
            "detected_at": activity.detected_at.isoformat() if activity.detected_at else None,
        }
