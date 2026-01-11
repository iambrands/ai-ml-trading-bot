# Fix Empty Tabs - API Server Not Running

## Problem Identified

**Background service is running** but **API server is NOT running**!

The background service logs show:
```
[error] HTTP client error error="Cannot connect to host localhost:8002"
```

This means:
- ✅ Background service is running (PID 65400)
- ❌ API server is NOT running on port 8002
- ❌ Service can't generate predictions because it can't connect to API

---

## Solution: Start the API Server

### If Running Locally

**Start the API server**:

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8002
```

**Or use the startup script**:

```bash
./scripts/start_api.sh
```

**Keep it running** in a terminal window (or use `nohup` to run in background).

### If Using Railway

**Option 1: Use Railway API URL**

Update the background service to use Railway URL:

```bash
# Stop current service
kill $(cat logs/background_service.pid)

# Set Railway URL and restart
export API_BASE_URL="https://your-railway-url.railway.app"
nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
echo $! > logs/background_service.pid
```

**Option 2: Run Predictions Manually on Railway**

Instead of background service, manually trigger predictions:

```bash
# On Railway, call the API endpoint
curl -X POST https://your-railway-url.railway.app/predictions/generate
```

---

## Quick Fix: Generate Predictions Now

**While API server is not running**, you can generate predictions directly:

```bash
# Generate predictions directly (bypasses API server)
python scripts/generate_predictions.py --limit 20
```

This will:
1. Generate predictions for 20 markets
2. Save them to database
3. Automatically create signals (if edge > threshold)
4. Populate the Predictions and Signals tabs

**For trades**:
```bash
python scripts/generate_predictions.py --limit 20 --auto-trades
```

---

## Steps to Fix Everything

### Step 1: Start API Server (Local)

```bash
# Terminal 1: Start API server
uvicorn src.api.app:app --host 0.0.0.0 --port 8002
```

Keep this running!

### Step 2: Verify API Server is Running

```bash
# Check if port 8002 is listening
lsof -i :8002

# Or test the API
curl http://localhost:8002/health
```

Should return a response if server is running.

### Step 3: Generate Predictions

**Option A: Use API** (requires server running):
```bash
curl -X POST http://localhost:8002/predictions/generate
```

**Option B: Use Script** (works without server):
```bash
python scripts/generate_predictions.py --limit 20
```

### Step 4: Check Tabs

1. **Refresh browser**
2. **Predictions tab**: Should show predictions
3. **Signals tab**: Should show signals (if predictions meet criteria)
4. **Trades tab**: Empty (unless you used `--auto-trades`)
5. **Portfolio tab**: Empty (unless trades exist)

---

## Background Service Will Now Work

Once API server is running:

✅ Background service can connect to API  
✅ Will generate predictions every 5 minutes  
✅ Tabs will populate automatically  
✅ No manual intervention needed  

---

## Summary

**Problem**: API server not responding, so background service can't generate predictions

**Solution**: 
1. ✅ **Use direct script** (works without API server): `python scripts/generate_predictions.py --limit 20`
2. Or start API server: `uvicorn src.api.app:app --host 0.0.0.0 --port 8002`
3. Then generate predictions: `curl -X POST http://localhost:8002/predictions/generate`

**Result**: ✅ Predictions successfully generated! Tabs should now populate with data!

**Status**: Script worked perfectly - generated 5 predictions. Refresh browser to see them in Predictions tab!

