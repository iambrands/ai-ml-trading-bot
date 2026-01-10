# Viewing the App in Browser

## Quick Start

### 1. Start the API Server

Open a terminal and run:

```bash
# Option 1: Using the startup script
./scripts/start_api.sh

# Option 2: Using uvicorn directly
uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload

# Option 3: Using Python module
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
```

You should see output like:
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 2. Open in Browser

Once the server is running, open your web browser and visit:

#### **Interactive API Documentation (Swagger UI)**
```
http://localhost:8001/docs
```
or
```
http://127.0.0.1:8001/docs
```

This provides:
- ✅ Interactive API explorer
- ✅ Try out endpoints directly
- ✅ See request/response schemas
- ✅ Test all API endpoints

#### **Alternative Documentation (ReDoc)**
```
http://localhost:8001/redoc
```

#### **API Root (Health Check)**
```
http://localhost:8001/
```
or
```
http://localhost:8001/health
```

This returns JSON:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-08T12:00:00Z",
  "version": "0.1.0"
}
```

## Available Endpoints

### Markets
- **GET** `/markets` - List all markets
- **GET** `/markets/{market_id}` - Get specific market

### Predictions
- **GET** `/predictions` - List model predictions
- Filter by `market_id` query parameter

### Signals
- **GET** `/signals` - List trading signals
- Filter by `market_id` or `executed` status

### Trades
- **GET** `/trades` - List trades
- Filter by `market_id` or `status` (OPEN/CLOSED/CANCELLED)

### Portfolio
- **GET** `/portfolio/snapshots` - Portfolio history
- **GET** `/portfolio/latest` - Latest portfolio state

## Using the Swagger UI

1. **Navigate to** `http://localhost:8001/docs`

2. **Explore Endpoints**:
   - Click on any endpoint to expand it
   - See request parameters and response schemas

3. **Try It Out**:
   - Click "Try it out" button
   - Enter parameters (if any)
   - Click "Execute"
   - See the response below

4. **Example - Get Markets**:
   - Expand `GET /markets`
   - Click "Try it out"
   - Set `limit` to 10
   - Click "Execute"
   - See the list of markets returned

## Troubleshooting

### "Connection Refused" or "Can't reach this page"

**Check:**
1. Is the server running? Look for the uvicorn output
2. Are you using the correct port? (8001, not 8000)
3. Try `127.0.0.1` instead of `localhost`

### "Module not found" errors

**Solution:**
```bash
pip install -r requirements.txt
```

### Server won't start

**Check logs for:**
- Database connection errors (OK if DB not set up)
- Port already in use (try different port)
- Missing dependencies

### Browser shows "This site can't be reached"

**Try:**
1. Use `127.0.0.1:8001` instead of `localhost:8001`
2. Check firewall settings
3. Verify server is actually running (check terminal output)

## Testing with curl

If browser doesn't work, test with curl:

```bash
# Health check
curl http://localhost:8001/health

# Get markets
curl http://localhost:8001/markets?limit=5

# Get latest portfolio
curl http://localhost:8001/portfolio/latest
```

## Next Steps

Once you can view the API:

1. **Train Models** (see TRAINING_GUIDE.md)
2. **Initialize Database** (optional):
   ```bash
   python scripts/init_db.py
   ```
3. **Start Trading Bot**:
   ```bash
   python src/main.py
   ```
4. **Monitor via API** - Use the endpoints to track:
   - Model predictions
   - Trading signals
   - Portfolio performance
   - Trade history

