# Fix Slow Performance & Cron Job Issues

## Current Problem
- System running very slow
- Health endpoint not responding
- Cron job may have failed

## Immediate Actions

### Step 1: Check Server Status
```bash
# Test if server is responding
curl -v --max-time 10 "https://web-production-c490dd.up.railway.app/health"
```

**If no response**:
- Server may have crashed
- Go to Railway Dashboard → Restart service

### Step 2: Check Cron Job
1. Go to **cron-job.org** dashboard
2. Check if cron job is **enabled**
3. Check **last execution** time
4. Check for **errors** in execution log

**If disabled**: Re-enable it (see RE_ENABLE_CRON_JOB.md)

### Step 3: Check Railway Logs
1. Go to Railway Dashboard
2. Select **web** service
3. Go to **Logs** tab
4. Look for:
   - Errors
   - Timeouts
   - "Connection pool exhausted"
   - "502 Bad Gateway"
   - "503 Service Unavailable"

### Step 4: Manually Trigger Predictions
```bash
# Test with small limit first
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5&auto_signals=false&auto_trades=false"
```

**Expected**: `{"status": "started", "message": "Prediction generation started in background"}`

---

## Root Causes & Fixes

### Cause 1: Database Connection Pool Exhausted

**Symptoms**:
- Health check shows `pool_usage > 95%`
- All endpoints slow or timing out
- Database errors in logs

**Current Settings**:
- `pool_size=20`
- `max_overflow=30`
- Total: 50 connections

**Fix**: Check if connections are being properly closed

**Check**:
```bash
curl -s "https://web-production-c490dd.up.railway.app/health" | grep -A 5 "database"
```

**If pool usage > 95%**:
1. Check for unclosed database sessions
2. Restart Railway service to reset pool
3. Check for long-running queries

### Cause 2: Sequential API Calls (Not Parallelized)

**Problem**: Prediction generation may be making sequential API calls instead of parallel

**Current Code**: `scripts/generate_predictions.py` processes markets sequentially

**Potential Fix**: Process markets in batches with asyncio.gather

### Cause 3: Long-Running Background Tasks

**Problem**: Background tasks may be accumulating and blocking

**Check**: Railway logs for multiple "Starting prediction generation" messages

**Fix**: Ensure background tasks complete properly

### Cause 4: External API Timeouts

**Problem**: Polymarket API or Gamma API calls timing out

**Current Timeout**: 30 seconds per request

**Fix**: Check for API rate limiting or network issues

### Cause 5: Model Loading Issues

**Problem**: Models may be loading slowly or failing

**Check**: Railway logs for "Loading models..." messages

**Fix**: Ensure model files exist and are accessible

---

## Quick Fixes

### Fix 1: Restart Railway Service
1. Go to Railway Dashboard
2. Select web service
3. Click **Restart** or **Redeploy**

### Fix 2: Reduce Prediction Limit
If cron job is timing out, reduce the limit:
```bash
# Change cron job URL to use limit=5 instead of limit=20
https://web-production-c490dd.up.railway.app/predictions/generate?limit=5&auto_signals=true&auto_trades=true
```

### Fix 3: Increase Cron Job Timeout
1. Go to cron-job.org
2. Edit cron job
3. Increase **Timeout** to 120 seconds (or higher)

### Fix 4: Check Database Indexes
Ensure performance indexes are applied:
```bash
# See RUN_PERFORMANCE_INDEXES.md
```

### Fix 5: Refresh Database Statistics
```bash
# See REFRESH_STATS_NOW.md
```

---

## Performance Optimization

### 1. Parallelize Market Processing

**Current**: Markets processed sequentially
**Optimization**: Process in batches with asyncio.gather

### 2. Reduce API Calls

**Current**: Fetches data for each market individually
**Optimization**: Batch fetch where possible

### 3. Optimize Database Queries

**Current**: Multiple queries per market
**Optimization**: Use joins and batch inserts

### 4. Add Request Timeouts

**Current**: Some operations may hang indefinitely
**Optimization**: Add timeouts to all async operations

---

## Monitoring

### Check Health Regularly
```bash
curl -s "https://web-production-c490dd.up.railway.app/health" | python3 -m json.tool
```

### Monitor Pool Usage
```bash
curl -s "https://web-production-c490dd.up.railway.app/health" | grep "pool_usage"
```

### Check Recent Predictions
```bash
curl -s "https://web-production-c490dd.up.railway.app/predictions?limit=5" | python3 -m json.tool
```

---

## Next Steps

1. ✅ Check Railway logs for specific errors
2. ✅ Verify cron job is enabled
3. ✅ Restart Railway service if needed
4. ✅ Manually trigger predictions with small limit
5. ✅ Monitor health endpoint for improvements
6. ✅ Check database pool usage
7. ✅ Verify indexes are applied

---

*See TROUBLESHOOTING_DATA_NOT_UPDATING.md for more detailed troubleshooting.*

