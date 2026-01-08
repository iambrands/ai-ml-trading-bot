"""Convert model predictions to trading signals."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from ..data.models import Market
from ..models.ensemble import EnsemblePrediction
from ..config.settings import get_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TradingSignal:
    """Trading signal data."""

    market_id: str
    side: str  # YES or NO
    model_probability: float
    market_probability: float
    edge: float
    confidence: float
    suggested_size: float = 0.0
    signal_strength: str = "WEAK"  # STRONG, MEDIUM, WEAK
    timestamp: datetime = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class SignalGenerator:
    """Convert model predictions to trading signals."""

    def __init__(
        self,
        min_edge: Optional[float] = None,
        min_confidence: Optional[float] = None,
        min_liquidity: Optional[float] = None,
    ):
        """
        Initialize signal generator.

        Args:
            min_edge: Minimum edge required (default from settings)
            min_confidence: Minimum model confidence (default from settings)
            min_liquidity: Minimum market liquidity (default from settings)
        """
        settings = get_settings()
        self.min_edge = min_edge if min_edge is not None else settings.min_edge
        self.min_confidence = min_confidence if min_confidence is not None else settings.min_confidence
        self.min_liquidity = min_liquidity if min_liquidity is not None else settings.min_liquidity

    def generate_signal(
        self, market: Market, prediction: EnsemblePrediction
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal if conditions are met.

        Args:
            market: Market object
            prediction: EnsemblePrediction object

        Returns:
            TradingSignal object or None if conditions not met
        """
        market_prob = float(market.yes_price)
        model_prob = prediction.probability

        # Calculate edge
        edge = model_prob - market_prob
        abs_edge = abs(edge)

        # Check thresholds
        if abs_edge < self.min_edge:
            logger.debug("Edge too small", market_id=market.id, edge=abs_edge, min_edge=self.min_edge)
            return None

        if prediction.confidence < self.min_confidence:
            logger.debug(
                "Confidence too low",
                market_id=market.id,
                confidence=prediction.confidence,
                min_confidence=self.min_confidence,
            )
            return None

        if market.volume_24h < self.min_liquidity:
            logger.debug(
                "Liquidity too low",
                market_id=market.id,
                volume=market.volume_24h,
                min_liquidity=self.min_liquidity,
            )
            return None

        # Determine side
        side = "YES" if edge > 0 else "NO"

        # Calculate signal strength
        if abs_edge > 0.15:
            strength = "STRONG"
        elif abs_edge > 0.10:
            strength = "MEDIUM"
        else:
            strength = "WEAK"

        return TradingSignal(
            market_id=market.id,
            side=side,
            model_probability=model_prob,
            market_probability=market_prob,
            edge=edge,
            confidence=prediction.confidence,
            signal_strength=strength,
        )

    def filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Filter out low-quality signals.

        Args:
            signals: List of trading signals

        Returns:
            Filtered list of signals
        """
        # Filter by signal strength and confidence
        filtered = [
            s
            for s in signals
            if s.signal_strength in ["STRONG", "MEDIUM"] and s.confidence >= self.min_confidence
        ]

        return filtered

    def rank_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Rank signals by expected value.

        Args:
            signals: List of trading signals

        Returns:
            Ranked list of signals (best first)
        """
        # Rank by edge * confidence (expected value proxy)
        ranked = sorted(
            signals, key=lambda s: abs(s.edge) * s.confidence, reverse=True
        )

        return ranked

