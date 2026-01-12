# Fix 405 Method Not Allowed Error

## Problem

**Error**: `405 Method Not Allowed` when setting up cron job

**Cause**: cron-job.org test run used `GET` method, but the endpoint requires `POST` method

---

## Solution

### Fix in cron-job.org Settings

1. **Go to cron-job.org dashboard**
2. **Edit your cron job** (or create new one)
3. **Check "Request method" setting**:
   - **Must be**: `POST` (not GET)
   - If it shows GET, change it to POST
4. **Save** the cron job

### Verify Settings

**Correct Settings**:
- **URL**: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20`
- **Method**: `POST` ✅ (must be POST!)
- **Schedule**: Every 5 minutes
- **Status**: Enabled

---

## Why This Happens

**Some cron services**:
- Test with `GET` method first (to verify URL is reachable)
- Show `405 Method Not Allowed` in test run (normal)
- Use `POST` method for actual scheduled runs (if configured correctly)

**The endpoint**:
- Requires `POST` method
- Returns `405 Method Not Allowed` for `GET` requests
- Works correctly with `POST` requests

---

## Verification

### Test with POST (Should Work)

```bash
# This should work (returns 200 OK)
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5"

# Expected response:
# {"status":"started","message":"Prediction generation started in background",...}
```

### Test with GET (Will Fail)

```bash
# This will fail (returns 405 Method Not Allowed)
curl -X GET "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5"

# Expected response:
# 405 Method Not Allowed
```

---

## Step-by-Step Fix

### In cron-job.org Dashboard

1. **Go to your cron job** (create new or edit existing)
2. **Find "Request method" field**
3. **Set to**: `POST` (not GET)
4. **Save**
5. **Test again** (should work now)

### Alternative: Use cron-job.org API Format

Some cron services use different field names:

- **Method**: `POST`
- **HTTP Method**: `POST`
- **Request Type**: `POST`

Look for any field that specifies the HTTP method and set it to `POST`.

---

## If Test Still Shows 405

**This is Normal**:
- Some cron services always test with GET first
- Test run may show 405 even if method is set to POST
- **Actual scheduled runs** will use POST and work correctly

**To Verify**:
1. **Save cron job** with POST method
2. **Wait 5 minutes** for first scheduled run
3. **Check Railway logs** for prediction generation
4. **Check Railway dashboard** for new predictions

If predictions are generated after 5 minutes, the cron job is working correctly (even if test showed 405).

---

## Summary

**Problem**: 405 Method Not Allowed in cron job test

**Cause**: Test run used GET, endpoint requires POST

**Solution**: Set "Request method" to `POST` in cron job settings

**Note**: Test run showing 405 is normal - actual scheduled runs will use POST and work correctly

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*



