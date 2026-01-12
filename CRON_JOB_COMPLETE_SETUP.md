# Complete Cron Job Setup for Railway

## Settings Summary

Based on your screenshot, here are the correct settings:

### COMMON Tab Settings

**Title**: `Railway Prediction Generation`

**URL**: 
```
https://web-production-c490dd.up.railway.app/predictions/generate?limit=20
```

**Schedule**: 
- **Every 5 minutes**: Select "Every X minutes" → Enter `5`
- Or cron format: `*/5 * * * *`

**Status**: `Enabled`

### ADVANCED Tab Settings (What You Have)

✅ **Request method**: `POST` (must be POST, not GET)  
✅ **Request body**: `Empty` (correct - endpoint uses query parameters, not body)  
✅ **Timeout**: `30 seconds` (should be fine)  
✅ **Time zone**: `America/Chicago` (matches your local timezone)  
✅ **HTTP Authentication**: `Off` (not needed)  
✅ **Custom Headers**: None (not needed)  
✅ **Treat redirects as success**: `Off` (default)

---

## Why Request Body is Empty

**The endpoint uses query parameters**, not request body:

- **Query parameters**: `?limit=20` (in URL)
- **Request body**: Not used (should be empty)

**Example**:
```
POST https://web-production-c490dd.up.railway.app/predictions/generate?limit=20
```

**Not**:
```
POST https://web-production-c490dd.up.railway.app/predictions/generate
Body: {"limit": 20}
```

---

## Complete Setup Steps

1. **COMMON Tab**:
   - Set Title: `Railway Prediction Generation`
   - Set URL: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20`
   - Set Schedule: Every 5 minutes

2. **ADVANCED Tab** (already configured):
   - ✅ Request method: POST
   - ✅ Request body: Empty
   - ✅ Other settings: Default (fine as-is)

3. **Click "CREATE" button**

4. **Wait for first run** (5 minutes)

5. **Verify**:
   - Check Railway logs for prediction generation
   - Check Railway dashboard for new predictions

---

## After Setup

### First Run

The cron job will:
1. Run every 5 minutes automatically
2. Call Railway API with POST method
3. Generate predictions for 20 markets
4. Save predictions to Railway database
5. Create signals automatically (if edge > threshold)

### Monitoring

**Check cron-job.org dashboard**:
- View execution log
- Check if runs are successful
- Monitor any errors

**Check Railway logs**:
- Go to Railway Dashboard
- Click on web service (web-production-c490dd)
- Go to "Logs" tab
- Look for prediction generation messages every 5 minutes

**Check Railway dashboard**:
- Open: `https://web-production-c490dd.up.railway.app/dashboard`
- Check Predictions tab
- Should see new predictions every 5 minutes

---

## Troubleshooting

### Cron Job Not Running

**Check**:
1. Is cron job enabled in cron-job.org?
2. Execution log - any errors?
3. Railway logs - receiving requests?

**Solutions**:
- Verify cron job is enabled
- Check execution log for errors
- Verify Railway API is accessible

### Predictions Not Generating

**Check**:
1. Railway logs for errors
2. API endpoint response
3. Database connection

**Solutions**:
- Check Railway logs for errors
- Test API endpoint manually
- Verify database connection

### Still Getting 405 Error

**If scheduled runs still show 405**:
1. Verify Request method is POST (not GET)
2. Check cron-job.org settings
3. Verify URL is correct

**If test run shows 405**:
- This is normal (some services test with GET)
- Make sure Request method is POST in settings
- Actual scheduled runs will use POST

---

## Summary

**Settings**:
- ✅ Request method: POST (you have this!)
- ✅ Request body: Empty (correct!)
- ✅ URL: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20`
- ✅ Schedule: Every 5 minutes

**Next Steps**:
1. ✅ Set COMMON tab settings (URL, schedule)
2. ✅ Click "CREATE" button
3. ✅ Wait 5 minutes for first run
4. ✅ Verify predictions are generated

**Result**: Predictions generated automatically every 5 minutes - same as local background service!

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*



