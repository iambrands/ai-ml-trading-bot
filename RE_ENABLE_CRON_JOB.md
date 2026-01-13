# 🔄 Re-Enable Cron Job - Quick Guide

## Problem
Cron job was automatically disabled after repeated 500 errors (syntax error in code).

## Solution
Re-enable the cron job now that the syntax error is fixed.

---

## Step-by-Step Instructions

### Step 1: Go to cron-job.org Dashboard

1. **Log in** to your cron-job.org account
2. **Find your cron job** (the one calling Railway API)
3. **Check status** - it should show "Disabled" or "Inactive"

### Step 2: Re-Enable the Cron Job

1. **Click on the cron job** to open settings
2. **Look for "Enable" or "Activate" button**
3. **Click it** to re-enable the job

### Step 3: Verify Settings

Make sure these settings are correct:

**URL**:
```
https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true
```

**Method**: `POST`

**Schedule**: `*/5 * * * *` (every 5 minutes)

**Timeout**: `60` seconds (or higher)

**Status**: `Enabled` or `Active`

### Step 4: Test Run

1. **Click "Test Run"** or "Execute Now" button
2. **Wait for response**
3. **Should see**: `200 OK` (not 500 anymore!)

**Expected Response**:
```json
{
  "status": "started",
  "message": "Prediction generation started in background",
  "limit": 20,
  "auto_signals": true,
  "auto_trades": true
}
```

### Step 5: Save and Monitor

1. **Click "Save"** if you made any changes
2. **Check execution log** after 5 minutes
3. **Verify** it's running successfully

---

## Why It Was Disabled

Cron services (like cron-job.org) automatically disable jobs that:
- ❌ Return 500 errors repeatedly
- ❌ Timeout consistently
- ❌ Fail multiple times in a row

This is a **safety feature** to prevent:
- Wasting API quota
- Spamming your server
- Running broken jobs

---

## Verify It's Working

### Check cron-job.org Dashboard

**Look for**:
- ✅ Status: "Enabled" or "Active"
- ✅ Last execution: Recent timestamp
- ✅ Status code: 200 OK
- ✅ Next run: Shows next scheduled time

### Check Railway Logs

1. Go to Railway Dashboard
2. Select web service
3. Go to "Logs" tab
4. Look for:
   ```
   [INFO] Starting prediction generation
   [INFO] Found active markets
   [INFO] Prediction generated
   ```

### Check Dashboard

After 5-10 minutes:
- **Predictions Tab**: Should show new predictions
- **Signals Tab**: Should show new signals (if edge > threshold)
- **Trades Tab**: Should show new trades
- **Portfolio Tab**: Should show updated portfolio

---

## Troubleshooting

### Still Getting 500 Errors

**Check**:
1. Has Railway finished deploying? (wait 2-3 minutes)
2. Check Railway logs for errors
3. Test endpoint manually:
   ```bash
   curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true"
   ```

**Solution**:
- Wait for Railway deployment to complete
- Check Railway logs for specific errors
- Verify database connection is working

### Cron Job Keeps Getting Disabled

**Possible Causes**:
1. Endpoint still returning errors
2. Timeout too short
3. Network issues

**Solutions**:
1. Fix the underlying error (check Railway logs)
2. Increase timeout to 120 seconds
3. Check Railway service status

### No Predictions Generated

**Check**:
1. Railway logs for errors
2. Database connection
3. Model files exist
4. Polymarket API accessible

**Solutions**:
- Check Railway logs
- Verify database connection
- Check model files in deployment
- Test Polymarket API manually

---

## Manual Refresh (If Needed)

If cron job still has issues, you can manually refresh:

```bash
./scripts/refresh_all_data.sh
```

Or use curl:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true"
```

---

## Summary

1. ✅ **Go to cron-job.org**
2. ✅ **Re-enable the cron job**
3. ✅ **Verify settings** (URL, method, schedule)
4. ✅ **Test run** to verify it works
5. ✅ **Monitor** execution log

The syntax error is fixed, so the cron job should work now! 🚀

