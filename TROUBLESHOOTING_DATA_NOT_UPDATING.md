# 🔧 Troubleshooting: Data Not Updating & Degraded Status

## Current Issues

1. ❌ Data shows no updates
2. ❌ Status says "degraded"

## Step-by-Step Troubleshooting

### Step 1: Check Health Endpoint

```bash
curl "https://web-production-c490dd.up.railway.app/health"
```

**Check the response for**:
- `"status": "degraded"` - What component is failing?
- `"recent_predictions"` - How old are predictions?
- `"database"` - Is database healthy?

### Step 2: Check Cron Job Status

**Go to cron-job.org dashboard**:
1. Check if cron job is **enabled**
2. Check **execution log** - last successful run?
3. Check for **errors** in recent runs

**If cron job is disabled**:
- Re-enable it (we fixed the syntax error)
- Test run to verify it works

### Step 3: Manually Trigger Predictions

**Option A: Use the script**:
```bash
./scripts/refresh_all_data.sh
```

**Option B: Use curl**:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true"
```

**Expected response**:
```json
{
  "status": "started",
  "message": "Prediction generation started in background"
}
```

### Step 4: Check Railway Logs

1. Go to Railway Dashboard
2. Select web service
3. Go to "Logs" tab
4. Look for:
   - `Starting prediction generation`
   - `Prediction saved`
   - Any errors

### Step 5: Verify Database Connection

```bash
# Check if database is accessible
curl "https://web-production-c490dd.up.railway.app/health" | grep -i database
```

---

## Common Causes & Solutions

### Cause 1: Cron Job Disabled

**Symptoms**:
- No new predictions for 2+ days
- Cron job shows "disabled" in dashboard

**Solution**:
1. Go to cron-job.org
2. Re-enable the cron job
3. Verify it's running every 5 minutes

---

### Cause 2: Predictions Too Old (>60 minutes)

**Symptoms**:
- Health check shows "degraded"
- `recent_predictions.age_minutes > 60`

**Solution**:
1. Manually trigger predictions (see Step 3)
2. Wait 2-5 minutes for completion
3. Check health endpoint again

---

### Cause 3: Database Connection Issues

**Symptoms**:
- Health check shows database as "unhealthy"
- 502 errors on endpoints

**Solution**:
1. Check Railway dashboard for database service
2. Verify DATABASE_URL is set correctly
3. Check database service logs

---

### Cause 4: Server Crashed

**Symptoms**:
- 502 errors on all endpoints
- Health endpoint not responding

**Solution**:
1. Check Railway logs for errors
2. Restart the service if needed
3. Check for syntax errors in recent commits

---

## Quick Fix Checklist

- [ ] Check health endpoint status
- [ ] Verify cron job is enabled
- [ ] Manually trigger predictions
- [ ] Check Railway logs for errors
- [ ] Verify database connection
- [ ] Wait 5 minutes after triggering
- [ ] Check dashboard for new data

---

## Expected Timeline

**After triggering predictions**:
- 0-2 min: Background task starts
- 2-5 min: Predictions generated
- 5-10 min: Signals created (if edge > threshold)
- 10-15 min: Trades created (if auto_trades=true)
- 15+ min: Portfolio updated

---

## Verify It's Working

**Check Predictions Tab**:
- Should show new predictions with today's date
- Predictions sorted by date (newest first)

**Check Signals Tab**:
- Should show new signals (if edge > 5%)
- Signals created from predictions

**Check Trades Tab**:
- Should show new trades (if auto_trades=true)
- Trades in paper trading mode

**Check Portfolio Tab**:
- Should show updated portfolio values
- Recent activity

---

## Still Not Working?

1. **Check Railway Logs** for specific errors
2. **Test endpoints manually**:
   ```bash
   curl "https://web-production-c490dd.up.railway.app/health"
   curl "https://web-production-c490dd.up.railway.app/predictions?limit=5"
   ```
3. **Verify cron job URL** is correct
4. **Check database** has recent predictions

---

## Next Steps After Fixing

1. ✅ Re-enable cron job
2. ✅ Manually trigger predictions
3. ✅ Monitor for 10 minutes
4. ✅ Verify data is updating
5. ✅ Check health status improves

