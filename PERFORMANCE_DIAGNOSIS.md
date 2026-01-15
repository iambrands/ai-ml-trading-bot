# Performance Diagnosis & Fix Guide

## Current Issue
System running very slow, cron job may have failed.

## Quick Diagnostic Steps

### Step 1: Check Health Endpoint
```bash
curl -s "https://web-production-c490dd.up.railway.app/health" | python3 -m json.tool
```

**Look for**:
- `"status": "degraded"` - What component is failing?
- `"pool_usage"` - Is database pool exhausted (>95%)?
- `"recent_predictions"` - How old are predictions?

### Step 2: Check Cron Job Status
1. Go to cron-job.org dashboard
2. Check if cron job is **enabled**
3. Check last execution time
4. Check for errors in execution log

### Step 3: Check Railway Logs
1. Go to Railway Dashboard
2. Select web service
3. Check "Logs" tab for:
   - Errors
   - Timeouts
   - Slow queries
   - Connection pool exhaustion

### Step 4: Test Prediction Endpoint
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5&auto_signals=false&auto_trades=false"
```

**Expected**: `{"status": "started", "message": "Prediction generation started in background"}`

---

## Common Causes of Slowness

### 1. Database Connection Pool Exhaustion

**Symptoms**:
- Health check shows `pool_usage > 95%`
- Slow or timeout on all endpoints
- Database errors in logs

**Current Settings**:
- `pool_size=20`
- `max_overflow=30`
- Total: 50 connections

**Fix**: Check if connections are being properly closed

### 2. Long-Running Queries

**Symptoms**:
- Specific endpoints slow (e.g., `/predictions`, `/trades`)
- Database queries taking >30 seconds

**Fix**: Check for missing indexes or inefficient queries

### 3. API Rate Limiting

**Symptoms**:
- Polymarket API calls failing
- 429 Too Many Requests errors
- Slow market fetching

**Fix**: Check rate limiter configuration

### 4. Background Tasks Hanging

**Symptoms**:
- Prediction generation never completes
- Background tasks accumulating
- Server becomes unresponsive

**Fix**: Check for blocking operations in background tasks

### 5. Cron Job Timeout

**Symptoms**:
- Cron job shows "timeout" or "failed"
- Predictions not generating
- No new data

**Fix**: Ensure background tasks are used (already implemented)

---

## Immediate Fixes

### Fix 1: Manually Trigger Predictions
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=10&auto_signals=true&auto_trades=true"
```

### Fix 2: Check and Re-enable Cron Job
1. Go to cron-job.org
2. Check if disabled
3. Re-enable if needed
4. Increase timeout to 120 seconds

### Fix 3: Restart Railway Service
1. Go to Railway Dashboard
2. Select web service
3. Click "Restart" or "Redeploy"

### Fix 4: Check Database Pool
```bash
# Check health endpoint for pool stats
curl -s "https://web-production-c490dd.up.railway.app/health" | grep -A 5 "database"
```

If pool usage > 95%, connections may not be closing properly.

---

## Performance Optimization Checklist

- [ ] Database pool size appropriate (20 base + 30 overflow = 50 total)
- [ ] Database indexes applied (see RUN_PERFORMANCE_INDEXES.md)
- [ ] Database statistics refreshed (ANALYZE commands)
- [ ] Background tasks used for long operations
- [ ] Rate limiting configured for external APIs
- [ ] Connection timeouts set appropriately
- [ ] Query timeouts set (30 seconds)

---

## Next Steps

1. Run diagnostic script: `./scripts/diagnose_performance.sh`
2. Check Railway logs for specific errors
3. Verify cron job is enabled
4. Manually trigger predictions if needed
5. Monitor health endpoint for improvements

---

*See TROUBLESHOOTING_DATA_NOT_UPDATING.md for more detailed troubleshooting steps.*

