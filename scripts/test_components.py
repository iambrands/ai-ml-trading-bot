"""Comprehensive test script for all components."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.data.processors.sentiment import SentimentAnalyzer
from src.data.sources.aggregator import DataAggregator
from src.data.sources.news import NewsDataSource
from src.data.sources.polymarket import PolymarketDataSource
from src.features.pipeline import FeaturePipeline
from src.models.ensemble import EnsembleModel
from src.models.lightgbm_model import LightGBMProbabilityModel
from src.models.xgboost_model import XGBoostProbabilityModel
from src.risk.circuit_breaker import CircuitBreaker
from src.risk.drawdown import DrawdownMonitor
from src.risk.limits import RiskLimits
from src.trading.portfolio import Portfolio
from src.trading.position_sizer import PositionSizer
from src.trading.signal_generator import SignalGenerator
from src.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def test_data_sources():
    """Test all data sources."""
    print("\n" + "=" * 60)
    print("TESTING DATA SOURCES")
    print("=" * 60)

    settings = get_settings()

    # Test Polymarket
    print("\n1. Testing Polymarket Data Source...")
    async with PolymarketDataSource() as polymarket:
        markets = await polymarket.fetch_active_markets(limit=3)
        print(f"   ✅ Fetched {len(markets)} active markets")
        if markets:
            print(f"   Sample: {markets[0].question[:60]}...")

    # Test NewsAPI
    print("\n2. Testing NewsAPI...")
    if settings.newsapi_key:
        news_source = NewsDataSource(api_key=settings.newsapi_key)
        articles = await news_source.fetch("Bitcoin", days_back=1)
        print(f"   ✅ Fetched {len(articles)} news articles")
    else:
        print("   ⚠️  NEWSAPI_KEY not configured (skipping)")

    # Test Data Aggregator
    print("\n3. Testing Data Aggregator...")
    async with PolymarketDataSource() as polymarket:
        aggregator = DataAggregator(polymarket=polymarket)
        markets = await polymarket.fetch_active_markets(limit=1)
        if markets:
            market = markets[0]
            data = await aggregator.fetch_all_for_market(market)
            print(f"   ✅ Aggregated data for market: {market.question[:50]}...")
            print(f"   News articles: {len(data.news)}")
            print(f"   Social sentiment: {data.social is not None}")


async def test_sentiment_analyzer():
    """Test sentiment analysis."""
    print("\n" + "=" * 60)
    print("TESTING SENTIMENT ANALYZER")
    print("=" * 60)

    print("\nInitializing Sentiment Analyzer...")
    analyzer = SentimentAnalyzer()
    print("   ✅ Sentiment analyzer initialized")

    # Test single text
    print("\nTesting sentiment analysis on sample texts...")
    test_texts = [
        "Bitcoin price surges to new all-time high!",
        "Market crash causes massive losses for investors.",
        "The market remains stable with moderate gains.",
    ]

    for text in test_texts:
        result = analyzer.analyze_text(text)
        print(f"   Text: {text[:50]}...")
        print(f"   Sentiment: {result.label} (score: {result.score:.3f}, confidence: {result.confidence:.3f})")


async def test_feature_pipeline():
    """Test feature engineering pipeline."""
    print("\n" + "=" * 60)
    print("TESTING FEATURE ENGINEERING PIPELINE")
    print("=" * 60)

    print("\nInitializing Feature Pipeline...")
    pipeline = FeaturePipeline()
    print("   ✅ Feature pipeline initialized")

    # Get a market and data
    async with PolymarketDataSource() as polymarket:
        markets = await polymarket.fetch_active_markets(limit=1)
        if markets:
            market = markets[0]
            aggregator = DataAggregator(polymarket=polymarket)
            data = await aggregator.fetch_all_for_market(market)

            print(f"\nGenerating features for: {market.question[:50]}...")
            features = await pipeline.generate_features(market, data)
            feature_names = pipeline.get_feature_names()

            # Features is a FeatureVector object, convert to array for length
            import numpy as np
            features_array = np.array(features.values) if hasattr(features, 'values') else features
            print(f"   ✅ Generated features (shape: {features_array.shape if hasattr(features_array, 'shape') else 'N/A'})")
            print(f"   Feature names: {len(feature_names)}")
            print(f"   Sample features: {list(feature_names[:5])}")


async def test_ml_models():
    """Test ML models."""
    print("\n" + "=" * 60)
    print("TESTING ML MODELS")
    print("=" * 60)

    # Test XGBoost
    print("\n1. Testing XGBoost Model...")
    xgb_model = XGBoostProbabilityModel()
    print("   ✅ XGBoost model initialized")

    # Test LightGBM
    print("\n2. Testing LightGBM Model...")
    lgb_model = LightGBMProbabilityModel()
    print("   ✅ LightGBM model initialized")

    # Test Ensemble
    print("\n3. Testing Ensemble Model...")
    ensemble = EnsembleModel(models=[xgb_model, lgb_model])
    print("   ✅ Ensemble model initialized")

    # Test prediction (with dummy features)
    print("\n4. Testing predictions...")
    dummy_features = [[0.5] * 50]  # 50 dummy features
    try:
        xgb_pred = xgb_model.predict_proba(dummy_features)
        print(f"   ✅ XGBoost prediction shape: {xgb_pred.shape if hasattr(xgb_pred, 'shape') else 'N/A'}")
    except Exception as e:
        print(f"   ⚠️  XGBoost prediction failed (expected - model not trained): {e}")

    try:
        ensemble_pred = ensemble.predict_proba(dummy_features)
        print(f"   ✅ Ensemble prediction shape: {ensemble_pred.shape if hasattr(ensemble_pred, 'shape') else 'N/A'}")
    except Exception as e:
        print(f"   ⚠️  Ensemble prediction failed (expected - model not trained): {e}")


async def test_trading_modules():
    """Test trading modules."""
    print("\n" + "=" * 60)
    print("TESTING TRADING MODULES")
    print("=" * 60)

    settings = get_settings()

    # Test Signal Generator
    print("\n1. Testing Signal Generator...")
    signal_gen = SignalGenerator(
        min_edge=settings.min_edge,
        min_confidence=settings.min_confidence,
        min_liquidity=settings.min_liquidity,
    )
    print("   ✅ Signal generator initialized")

    # Test with dummy market and prediction
    from src.data.models import Market
    from src.models.ensemble import EnsemblePrediction
    
    dummy_market = Market(
        id="test",
        condition_id="test",
        question="Test market",
        yes_price=0.50,
        no_price=0.50,
        volume_24h=5000.0,
    )
    
    dummy_prediction = EnsemblePrediction(
        probability=0.65,
        confidence=0.75,
        model_predictions={"xgboost": 0.65, "lightgbm": 0.65},
    )
    
    signal = signal_gen.generate_signal(dummy_market, dummy_prediction)
    if signal:
        print(f"   ✅ Generated signal: {signal.side} (edge: {signal.edge:.3f}, confidence: {signal.confidence:.3f})")
    else:
        print("   ⚠️  No signal generated (thresholds not met)")

    # Test Position Sizer
    print("\n2. Testing Position Sizer...")
    position_sizer = PositionSizer(
        kelly_fraction=settings.kelly_fraction,
        max_position_pct=settings.max_position_pct,
    )
    print("   ✅ Position sizer initialized")

    position_size = position_sizer.calculate_position_size(
        signal=signal,
        bankroll=settings.initial_capital,
    )
    print(f"   ✅ Calculated position size: ${position_size:.2f}")

    # Test Portfolio
    print("\n3. Testing Portfolio...")
    portfolio = Portfolio(initial_capital=settings.initial_capital, cash=settings.initial_capital)
    print("   ✅ Portfolio initialized")
    print(f"   Initial cash: ${portfolio.cash:.2f}")
    print(f"   Total value: ${portfolio.total_value:.2f}")


async def test_risk_management():
    """Test risk management modules."""
    print("\n" + "=" * 60)
    print("TESTING RISK MANAGEMENT")
    print("=" * 60)

    settings = get_settings()

    # Test Risk Limits
    print("\n1. Testing Risk Limits...")
    risk_limits = RiskLimits(
        max_position_pct=settings.max_position_pct,
        max_total_exposure=settings.max_total_exposure,
        max_daily_loss=settings.max_daily_loss,
    )
    print("   ✅ Risk limits initialized")

    # Test checks
    from src.trading.portfolio import Portfolio
    test_portfolio = Portfolio(initial_capital=10000.0, cash=10000.0)
    is_valid = risk_limits.check_position_limit(test_portfolio, 1000.0)
    print(f"   ✅ Position size check: {is_valid}")

    # Test Drawdown Monitor
    print("\n2. Testing Drawdown Monitor...")
    drawdown_monitor = DrawdownMonitor()
    print("   ✅ Drawdown monitor initialized")

    # Add some portfolio values
    from src.trading.portfolio import Portfolio
    portfolio1 = Portfolio(initial_capital=10000.0, cash=10000.0)
    portfolio2 = Portfolio(initial_capital=10000.0, cash=9500.0)
    portfolio3 = Portfolio(initial_capital=10000.0, cash=9000.0)
    drawdown_monitor.update(portfolio1)
    drawdown_monitor.update(portfolio2)
    drawdown_monitor.update(portfolio3)
    current_dd = drawdown_monitor.get_current_drawdown()
    max_dd = drawdown_monitor.get_max_drawdown()
    print(f"   ✅ Current drawdown: {current_dd:.2%}")
    print(f"   ✅ Max drawdown: {max_dd:.2%}")

    # Test Circuit Breaker
    print("\n3. Testing Circuit Breaker...")
    circuit_breaker = CircuitBreaker()
    print("   ✅ Circuit breaker initialized")
    print(f"   Current state: {circuit_breaker.state.value}")


async def main():
    """Run all component tests."""
    configure_logging()
    print("\n" + "=" * 60)
    print("COMPREHENSIVE COMPONENT TESTING")
    print("=" * 60)

    try:
        await test_data_sources()
        await test_sentiment_analyzer()
        await test_feature_pipeline()
        await test_ml_models()
        await test_trading_modules()
        await test_risk_management()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        logger.error("Test failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())

