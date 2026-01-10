# API Documentation

FastAPI REST API for the Polymarket AI Trading Bot.

## Quick Start

### Start the API Server

```bash
# Using uvicorn directly
uvicorn src.api.app:app --host 0.0.0.0 --port 8002 --reload

# Or using the Python module
python -m src.api.app
```

### Initialize Database

```bash
# Run the database initialization script
python scripts/init_db.py
```

Or manually using the SQL schema:

```bash
psql -U postgres -d polymarket_trader -f src/database/schema.sql
```

## API Endpoints

### Health Check

- **GET** `/` - Root endpoint (health check)
- **GET** `/health` - Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-08T12:00:00Z",
  "version": "0.1.0"
}
```

### Markets

- **GET** `/markets` - Get list of markets
  - Query parameters:
    - `limit` (int, default: 100, max: 1000) - Number of results
    - `offset` (int, default: 0) - Pagination offset
    - `outcome` (string, optional) - Filter by outcome (YES/NO)

- **GET** `/markets/{market_id}` - Get market by ID

**Example:**
```bash
curl http://localhost:8002/markets?limit=10&outcome=YES
```

### Predictions

- **GET** `/predictions` - Get model predictions
  - Query parameters:
    - `market_id` (string, optional) - Filter by market ID
    - `limit` (int, default: 100, max: 1000)
    - `offset` (int, default: 0)

**Example:**
```bash
curl http://localhost:8000/predictions?market_id=0x123...
```

### Signals

- **GET** `/signals` - Get trading signals
  - Query parameters:
    - `market_id` (string, optional) - Filter by market ID
    - `executed` (boolean, optional) - Filter by execution status
    - `limit` (int, default: 100, max: 1000)
    - `offset` (int, default: 0)

**Example:**
```bash
curl http://localhost:8000/signals?executed=false
```

### Trades

- **GET** `/trades` - Get trades
  - Query parameters:
    - `market_id` (string, optional) - Filter by market ID
    - `status` (string, optional) - Filter by status (OPEN/CLOSED/CANCELLED)
    - `limit` (int, default: 100, max: 1000)
    - `offset` (int, default: 0)

**Example:**
```bash
curl http://localhost:8000/trades?status=OPEN
```

### Portfolio

- **GET** `/portfolio/snapshots` - Get portfolio snapshots
  - Query parameters:
    - `limit` (int, default: 100, max: 1000)
    - `offset` (int, default: 0)

- **GET** `/portfolio/latest` - Get latest portfolio snapshot

**Example:**
```bash
curl http://localhost:8000/portfolio/latest
```

## Interactive API Documentation

When the server is running, visit:

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## Database Schema

The API uses PostgreSQL with the following main tables:

- `markets` - Market information
- `feature_snapshots` - Feature data for training/inference
- `predictions` - Model predictions
- `signals` - Trading signals
- `trades` - Trade records
- `model_performance` - Model performance metrics
- `portfolio_snapshots` - Portfolio state snapshots

See `src/database/schema.sql` for the complete schema.

## Configuration

Database connection is configured via environment variables in `.env`:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=polymarket_trader
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `404` - Resource not found
- `422` - Validation error
- `500` - Internal server error

Error responses include a `detail` field with the error message.

## CORS

CORS is enabled for all origins by default. Configure `allow_origins` in `src/api/app.py` for production.

