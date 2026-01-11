# Fix: Database Session Issue in Background Prediction Generation

## Problem

Predictions were not being generated because `generate_predictions` was using:

```python
async for db in get_db():
    # Process predictions...
```

This doesn't work correctly in background tasks because:
- `get_db()` is designed for FastAPI dependency injection
- Can't be used directly in background tasks
- Database session wasn't being created correctly
- Errors were failing silently

---

## Solution

Changed to use `AsyncSessionLocal()` directly with an async context manager:

```python
async with AsyncSessionLocal() as db:
    # Process predictions...
    for market in markets:
        # Save prediction...
```

This properly creates a database session in background tasks.

---

## Changes Made

### File: `scripts/generate_predictions.py`

1. **Import**: Added `AsyncSessionLocal` to imports
   ```python
   from src.database.connection import AsyncSessionLocal, get_db
   ```

2. **Database Session**: Changed from:
   ```python
   async for db in get_db():
   ```
   To:
   ```python
   async with AsyncSessionLocal() as db:
   ```

3. **Error Handling**: Added `exc_info=True` to error logging for better debugging

---

## Testing

### Step 1: Wait for Railway Deployment

1. Go to Railway Dashboard
2. Check deployment status
3. Wait for deployment to complete (2-5 minutes)

### Step 2: Check Railway Logs

After deployment, check logs for:
- `Database engine created successfully`
- No database connection errors

### Step 3: Test Prediction Generation

**Option A: Wait for Cron Job**
- Cron job runs every 5 minutes
- Wait 5 minutes after deployment
- Check Railway logs for prediction generation messages

**Option B: Manually Trigger**
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5"
```

Expected response:
```json
{"status":"started","message":"Prediction generation started in background","limit":5}
```

### Step 4: Verify Predictions

1. **Check Railway Logs**:
   - Look for "Prediction generated" messages
   - Should see logs like:
     ```
     [INFO] Prediction generated
     [INFO] Prediction generation complete
     ```

2. **Check Database**:
   ```bash
   curl "https://web-production-c490dd.up.railway.app/predictions?limit=5"
   ```
   - Should return predictions with today's date (2026-01-11...)

3. **Check UI**:
   - Go to Railway dashboard
   - Check Predictions tab
   - Should see new predictions with today's date

---

## Expected Behavior

**Before Fix**:
- Prediction generation would start but fail silently
- No predictions saved to database
- No error messages in logs (or generic errors)

**After Fix**:
- Prediction generation starts correctly
- Database session created properly
- Predictions saved to database
- Logs show "Prediction generated" messages
- New predictions appear in UI

---

## Troubleshooting

### Still No Predictions?

1. **Check Railway Logs**:
   - Go to Railway Dashboard → Logs
   - Look for errors (especially FileNotFoundError for models)
   - Look for database connection errors

2. **Check Models**:
   - Verify `data/models/xgboost_model.pkl` exists in deployment
   - Verify `data/models/lightgbm_model.pkl` exists (optional)

3. **Check Database**:
   - Verify database connection in Railway
   - Check `DATABASE_URL` environment variable

4. **Manual Test**:
   ```bash
   curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=1"
   ```
   - Wait 2-3 minutes
   - Check logs for errors

---

## Summary

✅ **Status**: Fixed database session issue

✅ **Change**: Use `AsyncSessionLocal()` directly instead of `get_db()`

✅ **Result**: Background tasks can now create database sessions correctly

✅ **Next**: Wait for Railway deployment, then test prediction generation

---

*Fixed: 2026-01-11*
*Commit: 9d4a559*


