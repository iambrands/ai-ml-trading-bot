# Polymarket AI/ML Probability Trading Bot

A production-ready AI-powered trading system for Polymarket that uses machine learning models to estimate true event probabilities, identifies mispriced markets, and executes trades when model predictions diverge significantly from market prices.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

This trading bot combines multiple data sources (news, social media, market data) with advanced ML models to identify trading opportunities on Polymarket prediction markets. It uses ensemble models (XGBoost, LightGBM) with sentiment analysis to predict event outcomes and execute trades when model predictions diverge from market prices.

## Features

### Core Trading Features ✅
- **Multi-source Data Aggregation**: News, social media (Twitter, Reddit), and market data
- **Advanced Feature Engineering**: Market, sentiment, temporal, and text embedding features
- **Ensemble ML Models**: XGBoost + LightGBM ensemble for robust predictions
- **Intelligent Signal Generation**: Automatic signal creation with edge and confidence thresholds
- **Kelly Criterion Position Sizing**: Optimal position sizing with risk management
- **Automated Trading**: Fully automated prediction generation, signal creation, and trade execution
- **Risk Management**: Position limits, drawdown monitoring, circuit breakers

### Advanced Features ✅ (Recently Implemented)
- **Real-Time Alerts & Notifications**: Webhook/Email/Telegram alerts for high-confidence signals
- **Paper Trading Mode**: Risk-free virtual trading with separate portfolio tracking (default mode)
- **Advanced Analytics Dashboard**: Comprehensive metrics, performance tracking, and insights
- **Live Market Data**: Real-time prices from Polymarket CLOB + Gamma API
- **Performance Optimization**: Database indexes, connection pooling, query optimization

### Deployment & Infrastructure ✅
- **Production Deployment**: Deployed on Railway with auto-deploy from GitHub
- **Automated Cron Jobs**: Predictions generated every 5 minutes automatically
- **Database Migrations**: Full schema with alerts, paper trading, and analytics support
- **API Documentation**: FastAPI with interactive docs at `/docs`

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

### Production Deployment (Railway) ✅

**Live Dashboard**: `https://web-production-c490dd.up.railway.app/`

The platform is **fully deployed and operational** on Railway with:
- ✅ Automated prediction generation (every 5 minutes)
- ✅ Paper trading mode enabled (safe for demo)
- ✅ All features implemented and working
- ✅ Auto-deploy from GitHub

### Local Development

#### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Railway CLI (for database access)

#### Installation

```bash
# Clone repository
git clone https://github.com/iambrands/ai-ml-trading-bot.git
cd ai-ml-trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys and credentials

# Initialize database (or use Railway database)
psql -U postgres -d polymarket_trader -f src/database/schema.sql

# Run migrations (for new features)
psql $DATABASE_URL -f src/database/migrations/add_alerts_and_paper_trading.sql
```

### Configuration

Edit `config/model_params.yaml`, `config/trading_params.yaml`, and `config/data_sources.yaml` to customize:

- Model hyperparameters
- Trading thresholds and position sizing
- Data source settings

### Running

#### Production (Railway)
The system runs automatically on Railway:
- ✅ API server on port 8001
- ✅ Cron job generates predictions every 5 minutes
- ✅ All endpoints available at Railway URL

#### Local Development

```bash
# Train models (if needed)
python scripts/train_models.py

# Start API server
uvicorn src.api.app:app --host 0.0.0.0 --port 8001

# Generate predictions manually (or use cron job)
curl -X POST http://localhost:8001/predictions/generate?limit=20&auto_signals=true&auto_trades=true

# Or use Python script
python scripts/generate_predictions.py --limit 20 --auto-signals --auto-trades
```

#### Automated Cron Job Setup
```bash
# Set up cron job to run every 5 minutes
# URL: https://your-railway-url/predictions/generate?limit=20&auto_signals=true&auto_trades=true
# Use cron-job.org or similar service
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

### Getting Started
- [Platform Overview](PLATFORM_OVERVIEW.md) - High-level overview of capabilities
- [Simple User Guide](SIMPLE_USER_GUIDE.md) - Step-by-step user instructions
- [Platform User Guide](PLATFORM_USER_GUIDE.md) - Comprehensive user manual
- [Platform Status](PLATFORM_STATUS.md) - Current operational status

### Technical Documentation
- [Technical Architecture](TECHNICAL_ARCHITECTURE.md) - System architecture and design
- [Features Usage Guide](FEATURES_USAGE_GUIDE.md) - How to use alerts, paper trading, analytics
- [Auto Trading Status](AUTO_TRADING_STATUS.md) - Paper vs real trading explanation

### Setup & Configuration
- [API Keys Setup Guide](API_KEYS_GUIDE.md)
- [Paper Trading Setup](PAPER_TRADING_SETUP.md) - Paper trading configuration
- [Run Migration](RUN_MIGRATION_NOW.md) - Database migration instructions

### Deployment
- [Railway Deployment](RAILWAY_DEPLOYMENT.md) - Deployment guide
- [Current Setup Status](CURRENT_SETUP.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

⚠️ **This software is for educational purposes only. Trading involves substantial risk of loss. Past performance does not guarantee future results. Use at your own risk.**

# Deployment trigger - Sun Jan 11 21:31:32 CST 2026
