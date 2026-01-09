# Technical Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Data Flow](#data-flow)
4. [Data Sources](#data-sources)
5. [Feature Engineering](#feature-engineering)
6. [Machine Learning Models](#machine-learning-models)
7. [Trading System](#trading-system)
8. [Risk Management](#risk-management)
9. [Database Schema](#database-schema)
10. [API Architecture](#api-architecture)
11. [Automation Pipeline](#automation-pipeline)
12. [Deployment Architecture](#deployment-architecture)
13. [Configuration](#configuration)
14. [Monitoring & Logging](#monitoring--logging)

---

## System Overview

The AI-ML Trading Bot is a production-ready prediction market trading system that uses machine learning to identify and execute profitable trades on Polymarket. The system operates in an automated, "set it and forget it" mode, continuously analyzing markets, generating predictions, creating trading signals, and executing trades.

### Key Components

1. **Data Ingestion Layer**: Fetches market data, news, and social media signals
2. **Feature Engineering Pipeline**: Transforms raw data into ML-ready features
3. **ML Prediction Engine**: Ensemble of models predicting market outcomes
4. **Signal Generation**: Converts predictions into actionable trading signals
5. **Trade Execution**: Executes trades based on signals and risk parameters
6. **Portfolio Management**: Tracks positions, P&L, and risk metrics
7. **Risk Management**: Enforces position limits, drawdown controls, and circuit breakers
8. **Web Interface**: Real-time dashboard for monitoring and configuration

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│  (FastAPI + HTML/JS Dashboard - Port 8001)                      │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                        │
│  • REST Endpoints                                               │
│  • WebSocket (future)                                           │
│  • Authentication & Authorization                               │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Prediction  │  │   Signal     │  │    Trade     │         │
│  │   Engine     │→ │  Generator   │→ │  Executor    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                  │
│         └──────────────────┴──────────────────┘                │
│                            │                                     │
│                            ▼                                     │
│                  ┌──────────────────┐                           │
│                  │ Auto Processor    │                           │
│                  │ (Orchestration)   │                           │
│                  └──────────────────┘                           │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Processing Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Feature    │  │  Sentiment   │  │  Embeddings  │         │
│  │   Pipeline   │  │   Analysis   │  │   Generator  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Ingestion Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Polymarket  │  │    News      │  │   Social     │         │
│  │   Client    │  │   Sources    │  │   Media      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ PostgreSQL   │  │    Redis     │  │   ChromaDB   │         │
│  │  (Primary)   │  │   (Cache)    │  │  (Vectors)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Data Ingestion Flow

```
External APIs → Data Aggregator → Feature Pipeline → ML Models → Predictions
     │                │                  │              │            │
     │                │                  │              │            │
     ▼                ▼                  ▼              ▼            ▼
Polymarket      Raw Data Store    Feature Store    Model Store   Database
NewsAPI         (Memory/DB)       (Database)       (Pickle)      (PostgreSQL)
Twitter API
Reddit API
RSS Feeds
```

### 2. Prediction Generation Flow

```
Active Markets → Feature Extraction → ML Models → Ensemble → Predictions
     │                  │                 │           │            │
     │                  │                 │           │            │
     ▼                  ▼                 ▼           ▼            ▼
Market Data    Market Features    XGBoost      Weighted      Prediction
News Data      Sentiment          LightGBM     Average       Database
Social Data    Temporal           NLP Model    Confidence    Signal Gen
Whale Data     Embeddings         Ensemble     Edge Calc     Trade Exec
```

### 3. Trading Execution Flow

```
Predictions → Signal Generator → Position Sizer → Risk Check → Trade Executor
     │              │                 │              │              │
     │              │                 │              │              │
     ▼              ▼                 ▼              ▼              ▼
Edge > 5%    Signal Strength    Kelly Criterion  Limits OK?    Polymarket
Confidence   (STRONG/MEDIUM/     Position Size    Drawdown OK?  Order Book
> 60%        WEAK)               Calculation      Circuit OK?   Execution
```

---

## Data Sources

### 1. Polymarket (Primary Market Data)

**Client**: `py-clob-client` (Official Polymarket Python SDK)

**Endpoints Used**:
- `get_markets()`: Fetch active markets
- `get_market(market_id)`: Get specific market details
- `get_order_book(token_id)`: Get orderbook for pricing
- `get_midpoint(token_id)`: Get current market price

**Data Retrieved**:
- Market questions and descriptions
- YES/NO token prices
- Orderbook depth
- Market status (active, closed, resolved)
- Resolution dates
- Historical market data

**Rate Limits**: 
- No official limits documented
- Implemented retry logic with exponential backoff
- Caching to reduce API calls

**Configuration**:
```python
# src/config/settings.py
polymarket_api_key: Optional[str]
polymarket_private_key: Optional[str]
polymarket_api_url: str = "https://clob.polymarket.com"
```

### 2. News Sources

#### RSS News (Primary - Free)
- **Sources**: Google News RSS, Reuters RSS
- **Module**: `src/data/sources/rss_news.py`
- **Rate Limits**: None (RSS feeds)
- **Data**: News articles with title, description, published date

#### NewsAPI (Fallback - Paid)
- **Module**: `src/data/sources/news.py`
- **Rate Limits**: 100 requests/24h (free tier)
- **Data**: News articles with sentiment, relevance scores

### 3. Social Media

#### Twitter/X API
- **Module**: `src/data/sources/twitter.py`
- **Status**: Requires API access (pending user approval)
- **Data**: Tweets, engagement metrics, sentiment

#### Reddit API
- **Module**: `src/data/sources/reddit.py`
- **Status**: Requires API access (pending user approval)
- **Data**: Posts, comments, upvotes, sentiment

### 4. Data Aggregation

**Module**: `src/data/sources/aggregator.py`

**Process**:
1. Fetch all data sources in parallel (async)
2. Combine into `AggregatedData` object
3. Handle errors gracefully (continue if one source fails)
4. Cache results to reduce API calls

---

## Feature Engineering

### Feature Categories

#### 1. Market Features (`src/features/market_features.py`)

**Price Features**:
- Current YES/NO prices
- Price spread (bid-ask)
- Price momentum (recent price changes)
- Price volatility (historical variance)

**Volume Features**:
- Trading volume (24h, 7d)
- Volume trend (increasing/decreasing)
- Volume-to-price ratio

**Market Structure**:
- Time to resolution (days remaining)
- Market category/type
- Historical resolution rate

**Orderbook Features**:
- Bid depth (total bids)
- Ask depth (total asks)
- Imbalance ratio (bids/asks)
- Midpoint price

#### 2. Sentiment Features (`src/features/sentiment_features.py`)

**News Sentiment**:
- FinBERT sentiment score (-1 to +1)
- Sentiment polarity (positive/negative/neutral)
- News volume (articles per day)
- Recent news impact (weighted by recency)

**Social Media Sentiment**:
- Twitter sentiment (when available)
- Reddit sentiment (when available)
- Engagement metrics (likes, retweets, upvotes)
- Social volume (mentions per day)

**Aggregated Sentiment**:
- Weighted average sentiment
- Sentiment momentum (trending positive/negative)
- Sentiment divergence (news vs social)

#### 3. Temporal Features (`src/features/temporal_features.py`)

**Time-Based**:
- Day of week (cyclical encoding)
- Hour of day
- Days until resolution
- Time since market creation

**Historical Patterns**:
- Similar markets resolution patterns
- Category-specific trends
- Seasonal effects

#### 4. Text Embeddings (`src/data/processors/embeddings.py`)

**Model**: `sentence-transformers/all-MiniLM-L6-v2`

**Embeddings Generated**:
- Market question embedding (384 dimensions)
- News article embeddings
- Social media post embeddings

**Use Cases**:
- Similarity matching (find similar markets)
- Semantic search
- Clustering

#### 5. Whale Activity Features

**Data Source**: Polymarket large trades

**Features**:
- Large trade volume
- Whale trade direction (YES/NO)
- Whale trade timing
- Whale success rate (historical)

### Feature Pipeline (`src/features/pipeline.py`)

**Process**:
1. **Input**: `AggregatedData` (raw data from all sources)
2. **Extract Features**:
   - Market features
   - Sentiment features
   - Temporal features
   - Text embeddings
3. **Combine**: Create `FeatureVector` object
4. **Output**: Feature vector ready for ML models

**Feature Vector Structure**:
```python
@dataclass
class FeatureVector:
    market_id: str
    timestamp: datetime
    features: Dict[str, float]  # All features as key-value pairs
    metadata: Dict[str, Any]     # Additional context
```

---

## Machine Learning Models

### Model Architecture

The system uses an **ensemble approach** combining multiple models for robust predictions.

### 1. XGBoost Model (`src/models/xgboost_model.py`)

**Type**: Gradient Boosting Classifier

**Hyperparameters** (from `config/model_params.yaml`):
```yaml
xgboost:
  n_estimators: 200
  max_depth: 6
  learning_rate: 0.1
  subsample: 0.8
  colsample_bytree: 0.8
  min_child_weight: 3
  gamma: 0.1
  reg_alpha: 0.1
  reg_lambda: 1.0
  early_stopping_rounds: 20
```

**Features Used**:
- All market features
- Sentiment features
- Temporal features
- Numerical embeddings (flattened)

**Output**: Probability distribution (YES probability, NO probability)

**Training**:
- Time-series cross-validation
- Recency weighting (recent markets weighted higher)
- Handles class imbalance

**Serialization**: Pickle (`.pkl` files)

### 2. LightGBM Model (`src/models/lightgbm_model.py`)

**Type**: Gradient Boosting Classifier (LightGBM)

**Hyperparameters**:
```yaml
lightgbm:
  n_estimators: 200
  max_depth: 6
  learning_rate: 0.1
  num_leaves: 31
  subsample: 0.8
  colsample_bytree: 0.8
  min_child_samples: 20
  reg_alpha: 0.1
  reg_lambda: 1.0
  early_stopping_rounds: 20
```

**Advantages**:
- Faster training than XGBoost
- Better handling of categorical features
- Lower memory usage

**Output**: Probability distribution

**Serialization**: Pickle (`.pkl` files)

### 3. NLP Model (Future Enhancement)

**Planned**: Transformer-based model for text understanding

**Potential Models**:
- BERT for market question understanding
- Fine-tuned on prediction market data

### 4. Ensemble Model (`src/models/ensemble.py`)

**Type**: Weighted Average Ensemble

**Combination Method**:
```python
final_probability = (
    w1 * xgboost_prob + 
    w2 * lightgbm_prob + 
    w3 * nlp_prob
) / (w1 + w2 + w3)
```

**Default Weights**:
- XGBoost: 0.4
- LightGBM: 0.4
- NLP: 0.2 (when available)

**Confidence Calculation**:
- Model agreement (higher when models agree)
- Prediction certainty (distance from 0.5)
- Historical accuracy

**Output**:
```python
@dataclass
class EnsemblePrediction:
    market_id: str
    timestamp: datetime
    probability: float  # Final YES probability
    confidence: float   # 0-1 confidence score
    edge: float        # Difference from market price
    model_predictions: Dict[str, float]  # Individual model outputs
```

### Model Training (`src/models/training/trainer.py`)

**Training Process**:

1. **Data Collection**:
   - Fetch resolved markets from Polymarket
   - Sample features at multiple time points (T-7d, T-3d, T-1d, T-0)
   - Create training examples with known outcomes

2. **Time-Series Cross-Validation**:
   - Split by time (not random)
   - Train on older data, validate on newer data
   - Prevents data leakage

3. **Recency Weighting**:
   - Recent markets weighted higher
   - Formula: `weight = exp(-days_old / 30)`

4. **Training**:
   - Train each model independently
   - Early stopping to prevent overfitting
   - Hyperparameter tuning (optional)

5. **Evaluation**:
   - Accuracy
   - Precision/Recall
   - Brier Score (probability calibration)
   - Log Loss

6. **Model Persistence**:
   - Save to `data/models/`
   - Files: `xgboost_model.pkl`, `lightgbm_model.pkl`, `ensemble_weights.json`

**Training Script**: `scripts/train_models.py`

---

## Trading System

### 1. Signal Generation (`src/trading/signal_generator.py`)

**Trigger Conditions**:
- Prediction edge > 5% (configurable)
- Confidence > 60% (configurable)
- Market is active and accepting orders

**Signal Strength Classification**:
- **STRONG**: Edge > 15%
- **MEDIUM**: Edge 10-15%
- **WEAK**: Edge 5-10%

**Signal Output**:
```python
@dataclass
class TradingSignal:
    market_id: str
    side: str  # "YES" or "NO"
    signal_strength: str  # "STRONG", "MEDIUM", "WEAK"
    suggested_size: float  # Position size in USD
    edge: float
    confidence: float
    created_at: datetime
```

### 2. Position Sizing (`src/trading/position_sizer.py`)

**Strategy**: Kelly Criterion (fractional)

**Formula**:
```
f = (p * b - q) / b

Where:
- f = fraction of bankroll to bet
- p = probability of winning (from model)
- q = probability of losing (1 - p)
- b = odds (1 / market_price - 1)
```

**Risk Adjustments**:
- Maximum position size cap (configurable, default: 5% of bankroll)
- Minimum position size (configurable, default: $10)
- Signal strength multiplier:
  - STRONG: 1.0x
  - MEDIUM: 0.7x
  - WEAK: 0.5x

**Output**: Position size in USD

### 3. Trade Execution (`src/trading/executor.py`)

**Execution Flow**:
1. Check risk limits (position size, drawdown, circuit breaker)
2. Get current market price from orderbook
3. Calculate entry price (midpoint or limit order)
4. Submit order to Polymarket (via `py-clob-client`)
5. Monitor order status
6. Update portfolio on fill

**Order Types**:
- Market orders (immediate execution)
- Limit orders (price protection)

**Status Tracking**:
- PENDING: Order submitted
- FILLED: Order executed
- PARTIAL: Partially filled
- CANCELLED: Order cancelled
- REJECTED: Order rejected

### 4. Portfolio Management (`src/trading/portfolio.py`)

**Portfolio State**:
```python
@dataclass
class Portfolio:
    initial_capital: float
    cash: float
    positions: Dict[str, Position]  # market_id -> Position
    total_value: float  # cash + positions_value + P&L
    total_exposure: float  # Sum of position sizes
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float
```

**Position Tracking**:
```python
@dataclass
class Position:
    market_id: str
    side: str  # "YES" or "NO"
    entry_price: float
    size: float  # USD
    current_price: float
    unrealized_pnl: float
    entry_time: datetime
```

**Portfolio Snapshots**:
- Created after each trade
- Stored in database
- Used for performance tracking

### 5. Auto Processor (`src/trading/auto_processor.py`)

**Orchestration Module**: Automatically processes predictions into signals, trades, and portfolio updates.

**Process**:
1. **Process Prediction**:
   - Check if prediction meets signal criteria
   - Generate signal if edge > threshold
   - Save signal to database

2. **Process Signal**:
   - Calculate position size
   - Check risk limits
   - Execute trade if approved
   - Save trade to database

3. **Update Portfolio**:
   - Recalculate portfolio metrics
   - Create portfolio snapshot
   - Save to database

**Integration**: Called automatically after prediction generation

---

## Risk Management

### 1. Position Limits (`src/risk/limits.py`)

**Checks**:
- Maximum position size per market (default: 5% of bankroll)
- Maximum total exposure (default: 50% of bankroll)
- Maximum number of open positions (default: 20)

**Configuration**:
```python
class RiskLimits:
    max_position_size_pct: float = 0.05  # 5%
    max_total_exposure_pct: float = 0.50  # 50%
    max_open_positions: int = 20
```

### 2. Drawdown Monitor (`src/risk/drawdown.py`)

**Tracks**:
- Peak portfolio value
- Current drawdown percentage
- Maximum drawdown threshold (default: 20%)

**Actions**:
- Alert when drawdown > 10%
- Stop trading when drawdown > 20%
- Resume trading when drawdown recovers

### 3. Circuit Breaker (`src/risk/circuit_breaker.py`)

**Triggers**:
- Consecutive losses (default: 5)
- Rapid drawdown (default: 10% in 1 hour)
- System errors

**Actions**:
- Pause trading
- Alert administrator
- Require manual intervention to resume

### 4. Risk Configuration

**User Settings** (from Settings tab):
- Risk Level: Conservative, Moderate, Aggressive
- Max Position Size: $ amount
- Min Edge Threshold: % (default: 10%)
- Min Confidence: % (default: 60%)

---

## Database Schema

### PostgreSQL Database

**Connection**: Async SQLAlchemy with `asyncpg`

**Tables**:

#### 1. `markets`
```sql
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) UNIQUE NOT NULL,
    condition_id VARCHAR(255),
    question TEXT NOT NULL,
    category VARCHAR(100),
    resolution_date TIMESTAMP,
    outcome VARCHAR(10),  -- 'YES', 'NO', NULL
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);
```

#### 2. `predictions`
```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) REFERENCES markets(market_id),
    prediction_time TIMESTAMP NOT NULL,
    model_probability FLOAT NOT NULL,  -- YES probability
    market_price FLOAT NOT NULL,
    edge FLOAT NOT NULL,  -- model_prob - market_price
    confidence FLOAT NOT NULL,
    model_version VARCHAR(50),
    model_predictions JSONB,  -- Individual model outputs
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. `signals`
```sql
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) REFERENCES markets(market_id),
    prediction_id INTEGER REFERENCES predictions(id),
    side VARCHAR(10) NOT NULL,  -- 'YES' or 'NO'
    signal_strength VARCHAR(20),  -- 'STRONG', 'MEDIUM', 'WEAK'
    suggested_size FLOAT,
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. `trades`
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    market_id VARCHAR(255) REFERENCES markets(market_id),
    signal_id INTEGER REFERENCES signals(id),
    side VARCHAR(10) NOT NULL,
    entry_price FLOAT NOT NULL,
    size FLOAT NOT NULL,
    exit_price FLOAT,
    pnl FLOAT,
    status VARCHAR(20),  -- 'OPEN', 'CLOSED', 'CANCELLED'
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP
);
```

#### 5. `portfolio_snapshots`
```sql
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_time TIMESTAMP NOT NULL,
    total_value FLOAT NOT NULL,
    cash FLOAT NOT NULL,
    positions_value FLOAT NOT NULL,
    total_exposure FLOAT NOT NULL,
    daily_pnl FLOAT,
    unrealized_pnl FLOAT,
    realized_pnl FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Models**: Defined in `src/database/models.py` using SQLAlchemy ORM

---

## API Architecture

### FastAPI Application (`src/api/app.py`)

**Port**: 8001

**Endpoints**:

#### Market Endpoints
- `GET /markets` - List markets (with pagination, filtering)
- `GET /markets/{market_id}` - Get specific market
- `GET /live/markets` - Fetch live markets from Polymarket API

#### Prediction Endpoints
- `GET /predictions` - List predictions
- `GET /predictions/{prediction_id}` - Get specific prediction
- `POST /predictions/generate` - Trigger prediction generation (automated)

#### Signal Endpoints
- `GET /signals` - List trading signals
- `GET /signals/{signal_id}` - Get specific signal

#### Trade Endpoints
- `GET /trades` - List trades
- `GET /trades/{trade_id}` - Get specific trade

#### Portfolio Endpoints
- `GET /portfolio/snapshots` - List portfolio snapshots
- `GET /portfolio/latest` - Get latest portfolio snapshot

#### Settings Endpoints
- `GET /settings` - Get user preferences
- `POST /settings` - Save user preferences

#### Deposit Endpoints
- `POST /deposit` - Process deposit (simulated or real)

#### Health Endpoints
- `GET /health` - Health check

**Response Models**: Pydantic models for type safety and validation

**Error Handling**: Graceful degradation (returns empty lists if DB unavailable)

---

## Automation Pipeline

### Current State

**Important**: The automation pipeline is **NOT currently running automatically**. Predictions must be triggered manually or via API.

### How It Works (When Active)

1. **Prediction Generation**:
   - Triggered via `POST /predictions/generate` endpoint
   - Fetches active markets from Polymarket
   - Generates features for each market
   - Runs ML models to get predictions
   - Saves predictions to database

2. **Signal Generation** (Automatic):
   - After prediction is saved, `AutoProcessor` checks if edge > threshold
   - If yes, generates signal automatically
   - Saves signal to database

3. **Trade Execution** (Automatic, if enabled):
   - After signal is generated, `AutoProcessor` calculates position size
   - Checks risk limits
   - Executes trade if approved
   - Saves trade to database

4. **Portfolio Update** (Automatic):
   - After trade execution, updates portfolio
   - Creates portfolio snapshot
   - Saves to database

### Making It Fully Automated

**Option 1: Scheduled API Calls**
```bash
# Cron job (every 5 minutes)
*/5 * * * * curl -X POST http://localhost:8001/predictions/generate
```

**Option 2: Celery Task Queue** (Future Enhancement)
- Use Celery + Redis for background tasks
- Scheduled tasks for prediction generation
- Async task processing

**Option 3: Background Service**
- Python script running continuously
- Polls for new markets
- Generates predictions automatically

### Current Manual Process

To generate predictions manually:
```bash
# Option 1: API call
curl -X POST http://localhost:8001/predictions/generate

# Option 2: Python script
python scripts/generate_predictions.py --auto-trades
```

---

## Deployment Architecture

### Development Setup

**Requirements**:
- Python 3.11+
- PostgreSQL 14+
- Redis (optional, for caching)
- ChromaDB (optional, for vector storage)

**Installation**:
```bash
pip install -r requirements.txt
```

**Database Setup**:
```bash
python scripts/init_db.py
```

**Start API**:
```bash
uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
```

### Production Deployment

**Recommended Stack**:
- **Web Server**: Nginx (reverse proxy)
- **API Server**: Gunicorn + Uvicorn workers
- **Database**: PostgreSQL (managed service recommended)
- **Cache**: Redis (for rate limiting, caching)
- **Vector DB**: ChromaDB or Pinecone (for embeddings)
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or CloudWatch

**Docker Deployment**:
```bash
docker-compose up -d
```

**Environment Variables** (`.env`):
```env
# Database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=polymarket_trader
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# API Keys
POLYMARKET_API_KEY=your_key
POLYMARKET_PRIVATE_KEY=your_private_key
NEWSAPI_KEY=your_key
TWITTER_API_KEY=your_key
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret

# Trading
INITIAL_CAPITAL=100.0
MAX_POSITION_SIZE=5.0
MIN_EDGE_THRESHOLD=0.10
MIN_CONFIDENCE=0.60
```

---

## Configuration

### Model Parameters (`config/model_params.yaml`)

XGBoost and LightGBM hyperparameters, ensemble weights, training settings.

### Trading Parameters (`config/trading_params.yaml`)

Signal thresholds, position sizing parameters, risk limits.

### Data Sources (`config/data_sources.yaml`)

API endpoints, rate limits, retry settings.

### Settings (`src/config/settings.py`)

Pydantic-based settings management from environment variables.

---

## Monitoring & Logging

### Logging

**Framework**: Python `logging` module with structured logging

**Log Levels**:
- DEBUG: Detailed information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

**Log Files**:
- `logs/trading_bot.log` - General application logs
- `logs/training_*.log` - Model training logs
- `logs/errors.log` - Error logs

### Monitoring

**Metrics to Track**:
- Prediction accuracy
- Signal-to-trade conversion rate
- Trade win rate
- Portfolio performance (Sharpe ratio, max drawdown)
- API response times
- Database query performance
- Model inference latency

**Future Enhancements**:
- MLflow for model tracking
- Prometheus metrics export
- Grafana dashboards
- Alerting (email, Slack, PagerDuty)

---

## Data Update Verification

### How to Check if Data is Updating

1. **Check Database Timestamps**:
```sql
-- Check latest predictions
SELECT prediction_time, market_id, edge, confidence 
FROM predictions 
ORDER BY prediction_time DESC 
LIMIT 10;

-- Check latest signals
SELECT created_at, market_id, signal_strength, executed 
FROM signals 
ORDER BY created_at DESC 
LIMIT 10;

-- Check latest trades
SELECT entry_time, market_id, status, pnl 
FROM trades 
ORDER BY entry_time DESC 
LIMIT 10;
```

2. **Check API Endpoints**:
```bash
# Get latest predictions
curl http://localhost:8001/predictions?limit=5

# Check prediction generation endpoint
curl -X POST http://localhost:8001/predictions/generate
```

3. **UI Indicators**:
- "Last updated" timestamp on each tab
- Data refresh every 30 seconds (automatic)
- New rows appearing in tables

4. **Manual Trigger**:
```bash
# Generate predictions manually
python scripts/generate_predictions.py --auto-trades
```

### Why Data Might Not Be Updating

1. **No Automation Running**: Predictions must be triggered manually or via scheduled job
2. **No Active Markets**: System only processes active markets
3. **Thresholds Not Met**: Predictions need edge > 5% and confidence > 60% to generate signals
4. **Risk Limits**: Trades might be blocked by risk management
5. **API Issues**: External API failures (Polymarket, NewsAPI, etc.)

---

## Future Enhancements

1. **Automated Scheduling**: Celery tasks for continuous prediction generation
2. **WebSocket Updates**: Real-time data push to UI
3. **Advanced ML Models**: Transformer models, reinforcement learning
4. **Backtesting Engine**: Historical strategy validation
5. **Multi-Exchange Support**: Support for other prediction markets
6. **Mobile App**: Native mobile application
7. **Social Features**: Share trades, leaderboards
8. **Advanced Analytics**: Performance attribution, risk decomposition

---

## Conclusion

This document provides a comprehensive overview of the AI-ML Trading Bot's technical architecture. For specific implementation details, refer to the source code in the `src/` directory.

**Key Takeaways**:
- Modular, extensible architecture
- Ensemble ML approach for robust predictions
- Comprehensive risk management
- Automated pipeline (when configured)
- Production-ready infrastructure

For questions or contributions, refer to the main README.md or open an issue on GitHub.

