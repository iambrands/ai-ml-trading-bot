# Generate Predictions on Railway

## Quick Start

**Railway URL**: `https://web-production-c490dd.up.railway.app/`

**Generate Predictions**:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

---

## What This Does

1. ✅ Fetches active markets from Polymarket
2. ✅ Generates features (sentiment, market data, etc.)
3. ✅ Runs ML models to create predictions
4. ✅ Saves predictions to Railway database
5. ✅ Automatically creates signals (if edge > threshold)

---

## Timeline

- **API Call**: Immediate (command executes)
- **Processing**: 1-5 minutes (depends on number of markets)
- **Completion**: Predictions saved to Railway database
- **UI Update**: Refresh browser after 1-2 minutes

---

## Steps to Generate Predictions

### Step 1: Call the API Endpoint

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

**Parameters**:
- `limit=20`: Number of markets to process (default: 10)
- Can also add `auto_trades=true` to create trades automatically

### Step 2: Wait for Processing

**Typical processing time**:
- 10 markets: ~1-2 minutes
- 20 markets: ~2-4 minutes
- 50 markets: ~5-10 minutes

**What's happening**:
- Fetching markets from Polymarket
- Generating features (may take time for sentiment analysis)
- Running ML models (XGBoost, LightGBM, Ensemble)
- Saving to database

### Step 3: Refresh Dashboard

1. **Wait 1-2 minutes** after API call completes
2. **Open Railway dashboard**: `https://web-production-c490dd.up.railway.app/dashboard`
3. **Refresh browser** (or wait for auto-refresh)
4. **Check Predictions tab** - should show predictions!

---

## Options

### Generate Predictions Only

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

**Result**: Predictions + Signals (automatically created)

### Generate Predictions + Trades

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_trades=true"
```

**Result**: Predictions + Signals + Trades + Portfolio updates

---

## Checking Status

### Option 1: Check Railway Logs

1. Go to Railway dashboard
2. Click on your service
3. Go to "Logs" tab
4. Look for prediction generation messages

### Option 2: Check Dashboard

1. Open: `https://web-production-c490dd.up.railway.app/dashboard`
2. Go to Predictions tab
3. If empty, predictions are still processing
4. Wait and refresh

### Option 3: Check API Response

The API endpoint should return:
```json
{
  "status": "completed",
  "message": "Predictions generated successfully",
  "limit": 20
}
```

Or if running in background:
```json
{
  "status": "started",
  "message": "Prediction generation started in background",
  "limit": 20
}
```

---

## Troubleshooting

### No Predictions After 5 Minutes

**Possible causes**:
1. **Models not deployed**: Check if models exist in Railway (should be in git)
2. **Database not connected**: Check Railway database connection
3. **API error**: Check Railway logs for errors

**Solution**:
- Check Railway logs for error messages
- Verify database is connected in Railway
- Verify models are deployed (check `data/models/` in Railway)

### API Returns Error

**Common errors**:
- `500 Internal Server Error`: Check Railway logs
- `503 Service Unavailable`: Database not connected
- `Timeout`: Processing taking too long (normal for many markets)

**Solution**:
- Check Railway logs
- Try with smaller limit: `limit=5`
- Verify database connection in Railway

### Predictions Tab Still Empty

**Possible causes**:
1. **Still processing**: Wait longer (may take 5+ minutes for 20 markets)
2. **Database issue**: Predictions not saved
3. **API endpoint issue**: Predictions endpoint not working

**Solution**:
- Wait 5 minutes, then refresh
- Check Railway logs for completion messages
- Verify predictions were saved (check database or logs)

---

## Automated Generation (Background Service)

To generate predictions automatically every 5 minutes on Railway:

### Option 1: Use Railway Cron Job

Create a cron job in Railway to call the API endpoint every 5 minutes.

### Option 2: Update Background Service for Railway

The background service can be configured to use Railway URL:

```bash
# Set Railway URL
export API_BASE_URL="https://web-production-c490dd.up.railway.app"

# Start background service
python scripts/background_prediction_service.py
```

**Note**: This would run on your local machine, calling Railway API. For true automation on Railway, use Railway's cron/scheduled tasks.

---

## Summary

**Quick Command**:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

**What Happens**:
1. API call triggers prediction generation
2. Processing takes 1-5 minutes
3. Predictions saved to Railway database
4. Refresh dashboard to see results

**Result**:
- Predictions tab populated
- Signals tab populated (if predictions meet criteria)
- Trades tab populated (if `auto_trades=true`)

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*


