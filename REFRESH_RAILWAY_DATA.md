# Refresh Data on Railway

## Current Status

✅ **Database Connection**: Working  
✅ **Data Exists**: Tables have data from 1/9/26 (imported from local)  
✅ **API**: Should be serving data to UI  
⏳ **New Predictions**: Need to generate to refresh data  

---

## Viewing Current Data

The data from 1/9/26 should be visible in the UI now:

1. **Open Railway Dashboard**:
   ```
   https://web-production-c490dd.up.railway.app/dashboard
   ```

2. **Check Each Tab**:
   - **Markets Tab**: Should show markets from database
   - **Predictions Tab**: Should show predictions from 1/9/26
   - **Signals Tab**: Should show signals from database
   - **Trades Tab**: Should show trades from database
   - **Portfolio Tab**: Should show portfolio from database

3. **If Data Not Showing**:
   - Refresh the browser
   - Check browser console for errors
   - Verify API endpoints return data (see below)

---

## Generating New Predictions

To refresh and add new predictions:

### Step 1: Generate New Predictions

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

**What This Does**:
- Fetches active markets from Polymarket
- Generates features (sentiment, market data, etc.)
- Runs ML models to create predictions
- Saves NEW predictions to database
- Automatically creates signals (if edge > threshold)

**Timeline**: 2-5 minutes for 20 markets

### Step 2: Wait for Processing

⏱️ **Wait 2-5 minutes** for processing to complete

### Step 3: Refresh Dashboard

1. **Refresh browser**: `https://web-production-c490dd.up.railway.app/dashboard`
2. **Check Predictions tab**: Should show NEW predictions (with today's date)
3. **Check Signals tab**: Should show NEW signals (if edge > threshold)

---

## Verifying Data via API

### Check Current Data

```bash
# Check markets
curl "https://web-production-c490dd.up.railway.app/markets?limit=5" | python3 -m json.tool

# Check predictions
curl "https://web-production-c490dd.up.railway.app/predictions?limit=5" | python3 -m json.tool

# Check signals
curl "https://web-production-c490dd.up.railway.app/signals?limit=5" | python3 -m json.tool

# Check trades
curl "https://web-production-c490dd.up.railway.app/trades?limit=5" | python3 -m json.tool
```

### Check Latest Predictions

```bash
# Get latest predictions (should show newest first)
curl "https://web-production-c490dd.up.railway.app/predictions?limit=10" | python3 -m json.tool | grep -A 5 "prediction_time"
```

---

## Regular Refresh Schedule

To keep data fresh, you can:

### Option 1: Manual Refresh

Generate predictions manually when needed:

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

### Option 2: Automated Background Service (Future)

Set up a background service on Railway to generate predictions automatically every 5 minutes (similar to local setup).

### Option 3: Scheduled Jobs (Future)

Use Railway's scheduled jobs or cron to trigger prediction generation periodically.

---

## Troubleshooting

### Data Not Showing in UI

**Check**:
1. Is API returning data? (use curl commands above)
2. Browser console errors?
3. Network tab shows API calls?

**Solutions**:
- Check API endpoints return data
- Verify browser can reach Railway
- Clear browser cache and refresh

### Predictions Not Generating

**Check**:
1. Railway logs for errors
2. Models are deployed (should be in git)
3. Database connection working

**Solutions**:
- Check Railway logs for errors
- Verify models exist in deployment
- Check database connection status

### Old Data Showing

**This is Expected**:
- Data from 1/9/26 should show in UI
- New predictions add to existing data
- Both old and new data will show
- Latest predictions appear first (sorted by date)

**To See Only New Data**:
- Check prediction timestamps
- Look for predictions with today's date
- Sort by prediction_time in UI

---

## Summary

**Current State**:
- ✅ Database connected and has data (1/9/26)
- ✅ UI should show existing data
- ⏳ New predictions being generated to refresh

**Next Steps**:
1. ✅ View current data in UI (should work now)
2. ⏱️ Wait 2-5 minutes for new predictions
3. 🔄 Refresh dashboard to see new predictions
4. ✅ Both old and new data will be visible

**To Generate New Predictions**:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*



