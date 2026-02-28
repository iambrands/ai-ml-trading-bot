"""Natural Language Strategy Builder - Describe strategies in plain English.

Users describe trading ideas like "Buy YES when price drops below 30 cents
and RSI is oversold, sell when it reaches 60 cents" and the system converts
it to executable rules. No competitor offers this for prediction markets.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import NLStrategy
from ..utils.logging import get_logger

logger = get_logger(__name__)

RULE_PATTERNS = {
    "price_below": r"(?:price|yes_price)\s+(?:drops?\s+)?(?:below|under|<)\s+\$?([\d.]+)",
    "price_above": r"(?:price|yes_price)\s+(?:rises?\s+)?(?:above|over|>)\s+\$?([\d.]+)",
    "rsi_oversold": r"rsi\s+(?:is\s+)?(?:oversold|below\s+(\d+))",
    "rsi_overbought": r"rsi\s+(?:is\s+)?(?:overbought|above\s+(\d+))",
    "volume_spike": r"volume\s+(?:spike|surge|increases?\s+(?:by\s+)?(\d+))",
    "edge_threshold": r"edge\s+(?:is\s+)?(?:above|over|>|greater\s+than)\s+([\d.]+)",
    "confidence_threshold": r"confidence\s+(?:is\s+)?(?:above|over|>)\s+([\d.]+)",
    "buy_yes": r"(?:buy|long|go\s+long)\s+yes",
    "buy_no": r"(?:buy|long|go\s+long)\s+no",
    "sell": r"(?:sell|close|exit)\s+(?:when|if|at)",
    "take_profit": r"(?:take\s+profit|tp|sell)\s+(?:at|when)\s+\$?([\d.]+)",
    "stop_loss": r"(?:stop\s+loss|sl|cut\s+loss)\s+(?:at|when)\s+\$?([\d.]+)",
    "trailing_stop": r"trailing\s+stop\s+(?:of\s+)?([\d.]+)%?",
    "max_position": r"(?:max|maximum)\s+(?:position|size)\s+\$?([\d.]+)",
    "category_filter": r"(?:only|focus\s+on)\s+(politics|crypto|sports|economics|science)",
    "smart_money": r"(?:follow|copy|when)\s+smart\s+money\s+(?:buys|enters)",
    "whale_alert": r"(?:when|if)\s+whale\s+(?:buys|trades|enters)",
    "sentiment": r"(?:when|if)\s+sentiment\s+(?:is\s+)?(positive|negative|bullish|bearish)",
}


class NLStrategyService:
    """Converts natural language descriptions into executable trading strategies."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_strategy(self, name: str, description: str, user_id: str = "default") -> Optional[Dict]:
        """Parse a natural language strategy description into executable rules."""
        try:
            parsed_rules = self._parse_description(description)
            strategy_type = self._infer_strategy_type(parsed_rules)
            parameters = self._build_parameters(parsed_rules)

            strategy = NLStrategy(
                user_id=user_id,
                name=name,
                natural_language_input=description,
                parsed_rules=parsed_rules,
                strategy_type=strategy_type,
                parameters=parameters,
                is_active=False,
            )
            self.db.add(strategy)
            await self.db.commit()
            await self.db.refresh(strategy)

            logger.info("NL strategy created", name=name, rules=len(parsed_rules.get("entry_rules", [])))
            return self._strategy_to_dict(strategy)
        except Exception as e:
            logger.error("Failed to create NL strategy", error=str(e))
            await self.db.rollback()
            return None

    async def get_strategies(self, user_id: str = "default", active_only: bool = False) -> List[Dict]:
        """Get all NL strategies for a user."""
        try:
            query = select(NLStrategy).where(NLStrategy.user_id == user_id)
            if active_only:
                query = query.where(NLStrategy.is_active == True)
            query = query.order_by(desc(NLStrategy.created_at))

            result = await self.db.execute(query)
            strategies = result.scalars().all()
            return [self._strategy_to_dict(s) for s in strategies]
        except Exception as e:
            logger.error("Failed to get NL strategies", error=str(e))
            return []

    async def get_strategy(self, strategy_id: int) -> Optional[Dict]:
        """Get a single NL strategy."""
        try:
            result = await self.db.execute(
                select(NLStrategy).where(NLStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            return self._strategy_to_dict(strategy) if strategy else None
        except Exception as e:
            logger.error("Failed to get NL strategy", error=str(e))
            return None

    async def activate_strategy(self, strategy_id: int) -> Optional[Dict]:
        """Activate a strategy for live signal generation."""
        try:
            result = await self.db.execute(
                select(NLStrategy).where(NLStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                return None
            strategy.is_active = True
            await self.db.commit()
            await self.db.refresh(strategy)
            return self._strategy_to_dict(strategy)
        except Exception as e:
            logger.error("Failed to activate strategy", error=str(e))
            await self.db.rollback()
            return None

    async def deactivate_strategy(self, strategy_id: int) -> Optional[Dict]:
        """Deactivate a strategy."""
        try:
            result = await self.db.execute(
                select(NLStrategy).where(NLStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                return None
            strategy.is_active = False
            await self.db.commit()
            await self.db.refresh(strategy)
            return self._strategy_to_dict(strategy)
        except Exception as e:
            logger.error("Failed to deactivate strategy", error=str(e))
            await self.db.rollback()
            return None

    async def evaluate_market(self, strategy_id: int, market_data: Dict) -> Dict:
        """Evaluate whether a market matches a NL strategy's rules."""
        try:
            result = await self.db.execute(
                select(NLStrategy).where(NLStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                return {"match": False, "reason": "Strategy not found"}

            rules = strategy.parsed_rules or {}
            entry_matches = []
            entry_failures = []

            for rule in rules.get("entry_rules", []):
                matched, reason = self._check_rule(rule, market_data)
                if matched:
                    entry_matches.append(reason)
                else:
                    entry_failures.append(reason)

            all_matched = len(entry_failures) == 0 and len(entry_matches) > 0
            side = rules.get("side", "YES")

            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "match": all_matched,
                "side": side,
                "matched_rules": entry_matches,
                "failed_rules": entry_failures,
                "confidence": len(entry_matches) / max(len(entry_matches) + len(entry_failures), 1),
                "market_data": market_data,
            }
        except Exception as e:
            logger.error("Failed to evaluate market", error=str(e))
            return {"match": False, "reason": str(e)}

    async def delete_strategy(self, strategy_id: int) -> bool:
        """Delete a NL strategy."""
        try:
            result = await self.db.execute(
                select(NLStrategy).where(NLStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            if not strategy:
                return False
            await self.db.delete(strategy)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error("Failed to delete NL strategy", error=str(e))
            await self.db.rollback()
            return False

    def _parse_description(self, description: str) -> Dict:
        """Parse natural language into structured rules."""
        text = description.lower().strip()
        entry_rules = []
        exit_rules = []
        side = "YES"

        for pattern_name, pattern in RULE_PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1) if match.lastindex else None

                if pattern_name == "buy_no":
                    side = "NO"
                elif pattern_name == "buy_yes":
                    side = "YES"
                elif pattern_name in ("price_below", "price_above", "rsi_oversold", "rsi_overbought", "volume_spike", "edge_threshold", "confidence_threshold", "smart_money", "whale_alert", "sentiment"):
                    entry_rules.append({"type": pattern_name, "value": float(value) if value else None, "raw": match.group(0)})
                elif pattern_name in ("take_profit", "stop_loss", "trailing_stop", "sell"):
                    exit_rules.append({"type": pattern_name, "value": float(value) if value else None, "raw": match.group(0)})
                elif pattern_name in ("max_position", "category_filter"):
                    entry_rules.append({"type": pattern_name, "value": value, "raw": match.group(0)})

        if not entry_rules:
            sentences = text.split(".")
            for s in sentences:
                s = s.strip()
                if any(kw in s for kw in ["buy", "enter", "when", "if"]):
                    entry_rules.append({"type": "custom", "value": None, "raw": s})
                elif any(kw in s for kw in ["sell", "exit", "close", "take profit"]):
                    exit_rules.append({"type": "custom", "value": None, "raw": s})

        return {"side": side, "entry_rules": entry_rules, "exit_rules": exit_rules, "original": description}

    def _infer_strategy_type(self, rules: Dict) -> str:
        types = [r["type"] for r in rules.get("entry_rules", [])]
        if any(t in types for t in ["rsi_oversold", "rsi_overbought"]):
            return "MEAN_REVERSION"
        if any(t in types for t in ["price_above", "volume_spike"]):
            return "MOMENTUM"
        if any(t in types for t in ["smart_money", "whale_alert"]):
            return "COPY_TRADING"
        if any(t in types for t in ["sentiment"]):
            return "SENTIMENT"
        if any(t in types for t in ["edge_threshold", "confidence_threshold"]):
            return "ML_SIGNAL"
        return "CUSTOM"

    def _build_parameters(self, rules: Dict) -> Dict:
        params = {}
        for rule in rules.get("entry_rules", []) + rules.get("exit_rules", []):
            if rule["type"] == "price_below":
                params["entry_price_below"] = rule["value"]
            elif rule["type"] == "price_above":
                params["entry_price_above"] = rule["value"]
            elif rule["type"] == "take_profit":
                params["take_profit"] = rule["value"]
            elif rule["type"] == "stop_loss":
                params["stop_loss"] = rule["value"]
            elif rule["type"] == "trailing_stop":
                params["trailing_stop_pct"] = rule["value"]
            elif rule["type"] == "max_position":
                params["max_position_size"] = rule["value"]
            elif rule["type"] == "edge_threshold":
                params["min_edge"] = rule["value"]
            elif rule["type"] == "confidence_threshold":
                params["min_confidence"] = rule["value"]
        return params

    def _check_rule(self, rule: Dict, market_data: Dict) -> tuple:
        rule_type = rule.get("type")
        value = rule.get("value")
        price = market_data.get("yes_price", 0.5)

        if rule_type == "price_below" and value:
            matched = price < value
            return matched, f"Price {price:.4f} {'<' if matched else '>='} {value}"
        elif rule_type == "price_above" and value:
            matched = price > value
            return matched, f"Price {price:.4f} {'>' if matched else '<='} {value}"
        elif rule_type == "edge_threshold" and value:
            edge = market_data.get("edge", 0)
            matched = abs(edge) > value
            return matched, f"Edge {edge:.4f} {'>' if matched else '<='} {value}"
        elif rule_type == "confidence_threshold" and value:
            conf = market_data.get("confidence", 0)
            matched = conf > value
            return matched, f"Confidence {conf:.4f} {'>' if matched else '<='} {value}"

        return True, f"Rule '{rule.get('raw', rule_type)}' passed (default)"

    def _strategy_to_dict(self, strategy: NLStrategy) -> Dict:
        return {
            "id": strategy.id, "name": strategy.name, "user_id": strategy.user_id,
            "natural_language_input": strategy.natural_language_input,
            "parsed_rules": strategy.parsed_rules, "strategy_type": strategy.strategy_type,
            "parameters": strategy.parameters, "is_active": strategy.is_active,
            "total_trades": strategy.total_trades, "total_pnl": float(strategy.total_pnl),
            "win_rate": float(strategy.win_rate),
            "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
        }
