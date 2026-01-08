# Polymarket AI/ML Probability Trading Bot

A production-ready AI-powered trading system for Polymarket that uses machine learning models to estimate true event probabilities, identifies mispriced markets, and executes trades when model predictions diverge significantly from market prices.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

This trading bot combines multiple data sources (news, social media, market data) with advanced ML models to identify trading opportunities on Polymarket prediction markets. It uses ensemble models (XGBoost, LightGBM) with sentiment analysis to predict event outcomes and execute trades when model predictions diverge from market prices.

## Features

- **Multi-source Data Aggregation**: News, social media (Twitter, Reddit), and on-chain data
- **Advanced Feature Engineering**: Market, sentiment, whale, temporal, and text embedding features
- **Ensemble ML Models**: XGBoost, LightGBM, Neural Networks, and NLP models
- **Intelligent Signal Generation**: Converts predictions to trading signals with confidence thresholds
- **Kelly Criterion Position Sizing**: Optimal position sizing with risk management
- **Comprehensive Backtesting**: Historical simulation with proper time-series validation
- **Risk Management**: Position limits, drawdown monitoring, circuit breakers
- **Production Monitoring**: MLflow tracking, Prometheus metrics, Grafana dashboards

## Architecture

```
polymarket-ai-trader/
├── src/                    # Main source code
│   ├── data/              # Data sources and processing
│   ├── features/          # Feature engineering
│   ├── models/            # ML models and training
│   ├── trading/           # Signal generation and execution
│   ├── risk/              # Risk management
│   ├── backtesting/       # Backtesting engine
│   ├── api/               # FastAPI endpoints
│   └── monitoring/        # Monitoring and metrics
├── config/                # Configuration files
├── data/                  # Data storage
├── notebooks/             # Jupyter notebooks for exploration
├── tests/                 # Test suite
└── docker/                # Docker configuration
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/iabadvisors/ai-ml-trading-bot.git
cd ai-ml-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys and credentials

# Initialize database
psql -U postgres -d polymarket_trader -f src/database/schema.sql
```

### Configuration

Edit `config/model_params.yaml`, `config/trading_params.yaml`, and `config/data_sources.yaml` to customize:

- Model hyperparameters
- Trading thresholds and position sizing
- Data source settings

### Running

```bash
# Train models
python scripts/train_models.py

# Run backtest
python scripts/backtest.py --start-date 2024-01-01 --end-date 2024-06-30

# Start trading bot
python src/main.py

# Start API server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d
```

## Development

### Project Structure

- `src/data/`: Data fetching and processing
- `src/features/`: Feature engineering pipeline
- `src/models/`: ML model implementations
- `src/trading/`: Trading logic and execution
- `src/risk/`: Risk management
- `src/backtesting/`: Historical simulation
- `src/api/`: FastAPI REST API

### Testing

```bash
pytest tests/ -v --cov=src
```

### Code Quality

```bash
black src/
ruff check src/
mypy src/
```

## Configuration

Key configuration files:

- `config/model_params.yaml`: Model hyperparameters
- `config/trading_params.yaml`: Trading parameters
- `config/data_sources.yaml`: Data source settings

## Performance Targets

- **Accuracy**: >55% on held-out data
- **Brier Score**: <0.25 on test set
- **Backtest Returns**: >50% annually
- **Sharpe Ratio**: >1.5
- **Max Drawdown**: <20%

## API Keys Setup

See [API_KEYS_GUIDE.md](API_KEYS_GUIDE.md) for instructions on obtaining API keys for:
- NewsAPI (free tier available)
- Reddit API (requires approval)
- Twitter/X API (may require paid plan)
- Polymarket (use official py-clob-client)

## Documentation

- [API Keys Setup Guide](API_KEYS_GUIDE.md)
- [Reddit API Form Template](REDDIT_API_FORM_TEMPLATE.md)
- [Polymarket py-clob-client Setup](POLYMARKET_PY_CLOB_SETUP.md)
- [Current Setup Status](CURRENT_SETUP.md)
- [Quick Start Guide](QUICK_START.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **This software is for educational purposes only. Trading involves substantial risk of loss. Past performance does not guarantee future results. Use at your own risk.**

