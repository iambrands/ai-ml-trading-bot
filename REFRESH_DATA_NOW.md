# 🔄 Refresh All Data - Quick Guide

## Problem
Data hasn't updated in 2+ days. Need to manually trigger prediction generation.

## Quick Solution

### Option 1: Use the Script (Easiest) ✅

```bash
./scripts/refresh_all_data.sh
```

This will:
- ✅ Trigger prediction generation for 20 markets
- ✅ Enable auto-signals
- ✅ Enable auto-trades (paper trading mode)
- ✅ Show you the response

### Option 2: Manual curl Command

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true"
```

### Option 3: Use Browser/Postman

**URL**: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true`

**Method**: POST

**Headers**: `Content-Type: application/json`

---

## What Happens

1. ✅ API receives request
2. ✅ Starts prediction generation in background (returns immediately)
3. ✅ Fetches 20 active markets from Polymarket
4. ✅ Generates predictions using ML models
5. ✅ Creates signals automatically (if edge > threshold)
6. ✅ Creates trades automatically (paper trading mode)
7. ✅ Updates portfolio snapshots

**Duration**: 2-5 minutes in background

---

## Verify It's Working

### 1. Check Response
You should see:
```json
{
  "status": "started",
  "message": "Prediction generation started in background",
  "limit": 20,
  "auto_signals": true,
  "auto_trades": true
}
```

### 2. Check Railway Logs
1. Go to Railway Dashboard
2. Select web service
3. Go to "Logs" tab
4. Look for:
   - `Starting prediction generation`
   - `Found active markets`
   - `Prediction generated`
   - `Prediction saved`

### 3. Check Dashboard
After 2-5 minutes:
- **Predictions Tab**: Should show new predictions
- **Signals Tab**: Should show new signals (if edge > threshold)
- **Trades Tab**: Should show new trades (paper trading)
- **Portfolio Tab**: Should show updated portfolio

---

## Why Data Might Not Be Updating

### 1. Cron Job Stopped
- **Check**: Go to cron-job.org dashboard
- **Solution**: Verify cron job is enabled and running
- **Fix**: Re-enable or recreate the cron job

### 2. Railway Service Down
- **Check**: Go to Railway dashboard, check service status
- **Solution**: Restart the service if needed

### 3. Database Connection Issues
- **Check**: Railway logs for database errors
- **Solution**: Verify DATABASE_URL is set correctly

### 4. Model Files Missing
- **Check**: Railway logs for "Model not found" errors
- **Solution**: Verify models are deployed (check .dockerignore)

### 5. API Rate Limiting
- **Check**: Railway logs for rate limit errors
- **Solution**: Wait a few minutes and try again

---

## Fix Cron Job (If Needed)

If the cron job stopped working:

1. **Go to cron-job.org**
2. **Check your cron job**:
   - Is it enabled?
   - Any errors in execution log?
   - When was last successful run?

3. **Update Cron Job URL**:
   ```
   https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true
   ```

4. **Settings**:
   - **Method**: POST
   - **Schedule**: Every 5 minutes (`*/5 * * * *`)
   - **Timeout**: 60 seconds (or higher)

5. **Test Run**: Click "Test Run" to verify it works

---

## Manual Refresh Schedule

If cron job is not working, you can manually refresh:

**Option 1: Run script periodically**
```bash
# Add to your crontab (runs every 5 minutes)
*/5 * * * * cd /path/to/ai-ml-trading-bot && ./scripts/refresh_all_data.sh
```

**Option 2: Use Railway's built-in cron** (if available)
- Some Railway plans support scheduled tasks
- Check Railway dashboard for "Cron Jobs" or "Scheduled Tasks"

**Option 3: Use external service**
- cron-job.org (free tier available)
- EasyCron
- GitHub Actions (if repo is on GitHub)

---

## Expected Results

After running refresh:

- ✅ **Predictions**: New predictions for 20 markets
- ✅ **Signals**: New signals (if predictions have edge > 5%)
- ✅ **Trades**: New trades (paper trading mode)
- ✅ **Portfolio**: Updated portfolio snapshots
- ✅ **Last Updated**: Timestamps should show current time

---

## Troubleshooting

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

### Predictions Generated But No Signals

**Check**:
1. Edge threshold in settings (default: 5%)
2. Confidence threshold (default: 55%)
3. Liquidity threshold (default: $500)

**Solutions**:
- Lower thresholds in settings
- Check prediction edges in database
- Verify signal generation logic

### Signals Generated But No Trades

**Check**:
1. `auto_trades` parameter (should be `true`)
2. Paper trading mode enabled
3. Risk limits not blocking trades

**Solutions**:
- Verify `auto_trades=true` in URL
- Check paper trading mode setting
- Review risk limit settings

---

## Summary

**Quick Fix**: Run `./scripts/refresh_all_data.sh` to manually trigger predictions.

**Long-term Fix**: Verify cron job is running and enabled.

**Monitor**: Check Railway logs and dashboard to verify data is updating.

