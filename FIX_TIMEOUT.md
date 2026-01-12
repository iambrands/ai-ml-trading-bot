# Fix: Cron Job Timeout Issue

## Problem

**Error**: Cron job execution failed with timeout
**URL**: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true`
**Status**: Failed (timeout)

---

## Root Cause

The prediction generation endpoint was running **synchronously** (blocking), causing the HTTP request to wait 2-5 minutes for completion. Cron services (like cron-job.org) typically timeout after **30-60 seconds**, causing the job to fail.

**What was happening**:
1. Cron job calls API endpoint
2. Endpoint waits for prediction generation to complete (2-5 minutes)
3. Cron service times out after 30-60 seconds
4. Request fails with "timeout" error

---

## Solution

**Changed**: Endpoint to **always run in background**

**Before**:
- Had conditional logic: `if background_tasks:`
- Else branch ran synchronously: `await generate_predictions(...)`
- HTTP request waited for completion

**After**:
- Always uses `BackgroundTasks` (FastAPI always injects it)
- Removed synchronous fallback
- HTTP request returns immediately (< 1 second)
- Processing continues in background

---

## Code Changes

### File: `src/api/endpoints/predictions.py`

**Changed**:
```python
# Before:
background_tasks: BackgroundTasks = None,
# ... code ...
if background_tasks:
    background_tasks.add_task(...)
else:
    await generate_predictions(...)  # Synchronous - causes timeout!

# After:
background_tasks: BackgroundTasks,  # Required, always injected by FastAPI
# ... code ...
# Always run in background
background_tasks.add_task(...)
```

---

## Result

### Before Fix

- ❌ HTTP request waits 2-5 minutes
- ❌ Cron job times out after 30-60 seconds
- ❌ Request fails with "timeout" error
- ❌ Predictions may still be generating (but job marked as failed)

### After Fix

- ✅ HTTP request returns immediately (< 1 second)
- ✅ Cron job completes successfully
- ✅ Prediction generation continues in background
- ✅ Railway logs show completion messages
- ✅ Predictions still generated correctly

---

## Testing

### Immediate Test

1. **Deploy to Railway**
2. **Wait for deployment** (2-3 minutes)
3. **Trigger cron job manually** (or wait for next scheduled run)
4. **Expected**: Job completes successfully (no timeout)

### Verify Processing

1. **Check Railway logs** after cron job runs
2. **Look for**: "Starting prediction generation" message
3. **Wait 2-5 minutes** for completion
4. **Check logs** for "Prediction generated" messages
5. **Check Predictions tab** - should see new predictions

---

## Timeline

**Before Fix**:
```
Cron Job → API Call → Processing (2-5 min) → Timeout (30-60 sec) ❌
```

**After Fix**:
```
Cron Job → API Call → Return (< 1 sec) ✅
                    ↓
              Background Processing (2-5 min) ✅
```

---

## Important Notes

### Background Processing

- Processing continues in background after HTTP response
- Railway logs will show all processing messages
- Predictions are still generated correctly
- No impact on functionality - only response time

### Cron Job Configuration

**No changes needed** to cron job URL or settings:
- URL: `/predictions/generate?limit=20&auto_signals=true&auto_trades=true`
- Method: POST
- Schedule: Every 5 minutes
- Timeout: 30-60 seconds (now sufficient - response is < 1 second)

---

## Summary

**Problem**: Endpoint running synchronously, causing timeouts
**Solution**: Always run in background using BackgroundTasks
**Result**: Immediate response, no timeouts, processing continues in background

**Status**: ✅ Fixed - Ready to deploy

---

*Fixed: 2026-01-11*
*Deployment: After fix applied*


