# Railway Background Service Setup (External Cron)

## Quick Setup: cron-job.org

Since Railway runs containers (not background scripts), the simplest way to replicate your local background service is to use an external cron service.

---

## Step-by-Step Setup

### Step 1: Sign Up for cron-job.org

1. **Go to**: https://cron-job.org/
2. **Sign up** (free tier available)
3. **Verify email** if required

### Step 2: Create New Cron Job

1. **Click "Create cronjob"**
2. **Fill in the form**:

   **Title**: `Railway Prediction Generation`
   
   **Address (URL)**: 
   ```
   https://web-production-c490dd.up.railway.app/predictions/generate?limit=20
   ```
   
   **Schedule**: 
   - **Every 5 minutes**: Select "Every X minutes" → Enter `5`
   - Or use cron syntax: `*/5 * * * *`
   
   **⚠️ IMPORTANT - Request method**: **`POST`** (must be POST, not GET!)
   
   **Notification email** (optional): Your email
   
   **Status**: `Enabled`

3. **Click "Create cronjob"**

**Note**: Some cron services show "405 Method Not Allowed" in test runs if they test with GET first. This is normal - make sure **Request method is set to POST** in the cron job settings. The actual scheduled runs will use POST and work correctly.

### Step 3: Test

1. **Wait 5 minutes**
2. **Check Railway dashboard** for new predictions
3. **Verify** predictions are being generated every 5 minutes

---

## Alternative: EasyCron

If you prefer EasyCron:

1. **Go to**: https://www.easycron.com/
2. **Sign up** (free tier available)
3. **Create new cron job**:
   - **URL**: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20`
   - **Method**: `POST`
   - **Schedule**: Every 5 minutes (`*/5 * * * *`)
   - **Save**

---

## What This Does

**Every 5 minutes**:
1. ✅ External cron service calls Railway API
2. ✅ API endpoint generates predictions for 20 markets
3. ✅ Predictions saved to Railway database
4. ✅ Signals created automatically (if edge > threshold)
5. ✅ UI auto-refreshes every 30 seconds to show new data

**Result**: Same as local background service - "set it and forget it"!

---

## Monitoring

### Check Railway Logs

1. Go to Railway Dashboard
2. Click on web service (web-production-c490dd)
3. Go to "Logs" tab
4. Look for prediction generation messages every 5 minutes

### Check Railway Dashboard

1. Open: `https://web-production-c490dd.up.railway.app/dashboard`
2. Check Predictions tab
3. Should see new predictions every 5 minutes

### Check cron-job.org Dashboard

1. Go to cron-job.org dashboard
2. Check "Execution log" for your cron job
3. Should show successful executions every 5 minutes

---

## Troubleshooting

### Cron Job Not Running

**Check**:
1. cron-job.org dashboard - is job enabled?
2. Execution log - any errors?
3. Railway logs - is API receiving requests?

**Solutions**:
- Verify URL is correct
- Check Railway API is accessible
- Verify cron job is enabled

### Predictions Not Generating

**Check**:
1. Railway logs for errors
2. API endpoint response
3. Database connection

**Solutions**:
- Check Railway logs for errors
- Test API endpoint manually
- Verify database connection

---

## Summary

**Problem**: Railway doesn't run background scripts like local environment

**Solution**: External cron service (cron-job.org) calls Railway API every 5 minutes

**Setup**:
1. ✅ Sign up for cron-job.org (free)
2. ✅ Create cron job
3. ✅ URL: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20`
4. ✅ Schedule: Every 5 minutes
5. ✅ Method: POST
6. ✅ Done!

**Result**: Predictions generated automatically every 5 minutes - same as local!

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*

