"""Alert service for sending notifications."""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Alert, AlertHistory, Signal
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AlertService:
    """Service for managing and sending alerts."""

    def __init__(self, db: AsyncSession):
        """Initialize alert service."""
        self.db = db

    async def check_and_send_alerts(self, signal: Signal, market_data: Optional[Dict] = None) -> List[Dict]:
        """
        Check alert rules and send notifications for a new signal.
        
        Args:
            signal: Signal object that was just created
            market_data: Optional market data for context
            
        Returns:
            List of alert results (success/failure)
        """
        try:
            # Get all enabled alerts that match this signal
            query = select(Alert).where(
                Alert.enabled == True,
                Alert.alert_type == "SIGNAL"
            )
            result = await self.db.execute(query)
            alerts = result.scalars().all()
            
            if not alerts:
                return []
            
            results = []
            for alert in alerts:
                try:
                    # Check if alert rule matches
                    if await self._check_alert_rule(alert, signal, market_data):
                        # Send notification
                        success = await self._send_notification(alert, signal, market_data)
                        
                        # Record in history
                        await self._record_alert_history(alert, signal, success)
                        
                        # Update alert stats
                        alert.last_triggered = datetime.now(timezone.utc)
                        alert.trigger_count += 1
                        await self.db.commit()
                        
                        results.append({
                            "alert_id": alert.id,
                            "success": success,
                            "method": alert.notification_method
                        })
                except Exception as e:
                    logger.error("Failed to process alert", alert_id=alert.id, error=str(e))
                    results.append({
                        "alert_id": alert.id,
                        "success": False,
                        "error": str(e)
                    })
            
            return results
        except Exception as e:
            logger.error("Failed to check alerts", error=str(e))
            return []

    async def _check_alert_rule(self, alert: Alert, signal: Signal, market_data: Optional[Dict]) -> bool:
        """Check if alert rule matches the signal."""
        try:
            rule = alert.alert_rule if isinstance(alert.alert_rule, dict) else json.loads(alert.alert_rule)
            
            # Default rule: alert on all signals
            if not rule:
                return True
            
            # Check signal strength
            if "min_signal_strength" in rule:
                strength_map = {"STRONG": 3, "MEDIUM": 2, "WEAK": 1}
                min_strength = strength_map.get(rule["min_signal_strength"], 0)
                signal_strength = strength_map.get(signal.signal_strength, 0)
                if signal_strength < min_strength:
                    return False
            
            # Check edge threshold
            if "min_edge" in rule and signal.prediction:
                edge = float(signal.prediction.edge)
                if abs(edge) < rule["min_edge"]:
                    return False
            
            # Check confidence threshold
            if "min_confidence" in rule and signal.prediction:
                confidence = float(signal.prediction.confidence)
                if confidence < rule["min_confidence"]:
                    return False
            
            return True
        except Exception as e:
            logger.warning("Failed to check alert rule", alert_id=alert.id, error=str(e))
            return True  # Default to sending if rule check fails

    async def _send_notification(self, alert: Alert, signal: Signal, market_data: Optional[Dict]) -> bool:
        """Send notification via configured method."""
        try:
            method = alert.notification_method.upper()
            target = alert.notification_target
            
            # Build message
            message = self._build_alert_message(alert, signal, market_data)
            
            if method == "WEBHOOK":
                return await self._send_webhook(target, message, signal, market_data)
            elif method == "EMAIL":
                return await self._send_email(target, message, signal)
            elif method == "TELEGRAM":
                return await self._send_telegram(target, message, signal)
            else:
                logger.warning("Unknown notification method", method=method)
                return False
        except Exception as e:
            logger.error("Failed to send notification", alert_id=alert.id, error=str(e))
            return False

    def _build_alert_message(self, alert: Alert, signal: Signal, market_data: Optional[Dict]) -> str:
        """Build alert message."""
        edge = float(signal.prediction.edge) if signal.prediction else 0.0
        confidence = float(signal.prediction.confidence) if signal.prediction else 0.0
        
        message = f"🚨 New Trading Signal\n\n"
        message += f"Market: {signal.market.market.question[:100] if signal.market else 'Unknown'}\n"
        message += f"Side: {signal.side}\n"
        message += f"Signal Strength: {signal.signal_strength}\n"
        message += f"Edge: {edge:.2%}\n"
        message += f"Confidence: {confidence:.2%}\n"
        if signal.suggested_size:
            message += f"Suggested Size: ${float(signal.suggested_size):.2f}\n"
        message += f"\nTime: {signal.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        return message

    async def _send_webhook(self, url: str, message: str, signal: Signal, market_data: Optional[Dict]) -> bool:
        """Send webhook notification."""
        try:
            payload = {
                "message": message,
                "signal": {
                    "id": signal.id,
                    "market_id": signal.market_id,
                    "side": signal.side,
                    "signal_strength": signal.signal_strength,
                    "edge": float(signal.prediction.edge) if signal.prediction else None,
                    "confidence": float(signal.prediction.confidence) if signal.prediction else None,
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status == 200
        except Exception as e:
            logger.error("Webhook send failed", url=url, error=str(e))
            return False

    async def _send_email(self, email: str, message: str, signal: Signal) -> bool:
        """Send email notification (placeholder - requires email service)."""
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        logger.info("Email notification (not implemented)", email=email, signal_id=signal.id)
        return False

    async def _send_telegram(self, chat_id: str, message: str, signal: Signal) -> bool:
        """Send Telegram notification (placeholder - requires bot token)."""
        # TODO: Integrate with Telegram Bot API
        logger.info("Telegram notification (not implemented)", chat_id=chat_id, signal_id=signal.id)
        return False

    async def _record_alert_history(self, alert: Alert, signal: Signal, success: bool, error: Optional[str] = None):
        """Record alert in history."""
        try:
            message = self._build_alert_message(alert, signal, None)
            history = AlertHistory(
                alert_id=alert.id,
                signal_id=signal.id,
                market_id=signal.market_id,
                message=message,
                success=success,
                error_message=error
            )
            self.db.add(history)
            await self.db.commit()
        except Exception as e:
            logger.error("Failed to record alert history", error=str(e))
            await self.db.rollback()

