# 🔧 Fix Degraded Status - Action Plan

## Current Status

**Health Check Results**:
- ✅ Database: Healthy
- ❌ Recent Predictions: **STALE** (37.7 hours old!)
- ✅ Paper Trading: Healthy
- ⚠️ Model Loaded: Unavailable (path issue)

**Overall Status**: **DEGRADED**

---

## Root Cause

**Predictions are 37+ hours old** (last: 2026-01-12T03:35:23)
- Health check fails if predictions > 60 minutes old
- This is why status is "degraded"

---

## Solution Steps

### Step 1: Wait for Prediction Generation ✅

**Already triggered!** Prediction generation started at:
```
Status: 200 OK
Message: "Prediction generation started in background"
```

**Wait 5-10 minutes** for it to complete.

### Step 2: Check Railway Logs

1. Go to Railway Dashboard
2. Select web service
3. Go to "Logs" tab
4. Look for:
   ```
   [INFO] Starting prediction generation
   [INFO] Found active markets
   [INFO] Prediction saved
   [INFO] Prediction generation complete
   ```

### Step 3: Verify Predictions Generated

**After 5-10 minutes**, check:

```bash
curl "https://web-production-c490dd.up.railway.app/health"
```

**Look for**:
- `recent_predictions.age_minutes` should be < 30
- `recent_predictions.status` should be "healthy"
- Overall `status` should be "healthy"

### Step 4: Check Dashboard

- Go to: `https://web-production-c490dd.up.railway.app/`
- Check **Predictions tab**
- Should see new predictions with today's date

---

## If Predictions Still Not Generating

### Check Cron Job

1. **Go to cron-job.org**
2. **Verify cron job is enabled**
3. **Check execution log**:
   - Last successful run?
   - Any errors?
   - Status code (should be 200)

### Manually Trigger Again

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true"
```

### Check Railway Logs for Errors

**Common errors**:
- Database connection issues
- Model file not found
- API rate limiting
- Timeout errors

---

## Model Path Issue (Secondary)

**Status**: Model file not found at expected path

**Fixed**: Health check now checks multiple paths:
- `/app/data/models/xgboost_model.pkl` (Railway/Docker)
- `data/models/xgboost_model.pkl` (relative)
- Other possible paths

**Note**: This doesn't prevent predictions from generating if models are deployed correctly.

---

## Expected Timeline

**After triggering predictions**:
- 0-2 min: Background task starts
- 2-5 min: Predictions generated
- 5-10 min: Signals created (if edge > threshold)
- 10-15 min: Health status improves to "healthy"

---

## Verification Checklist

- [ ] Wait 5-10 minutes after triggering
- [ ] Check Railway logs for completion
- [ ] Re-check health endpoint
- [ ] Verify `age_minutes < 30`
- [ ] Check dashboard for new predictions
- [ ] Verify status is "healthy"

---

## If Still Degraded After 15 Minutes

1. **Check Railway logs** for specific errors
2. **Verify cron job** is running
3. **Check database** has recent predictions:
   ```sql
   SELECT created_at FROM predictions ORDER BY created_at DESC LIMIT 5;
   ```
4. **Manually trigger** predictions again
5. **Check for errors** in prediction generation

---

## Summary

**Main Issue**: Predictions are 37+ hours old
**Solution**: Wait for current prediction generation to complete
**Timeline**: 5-10 minutes
**Expected Result**: Status changes to "healthy"

**Secondary Issue**: Model path (fixed in health check, doesn't block predictions)

