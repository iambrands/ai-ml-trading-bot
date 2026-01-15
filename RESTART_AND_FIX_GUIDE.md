# Railway Restart & Stale Data Fix Guide

## PART 1: Restart Railway Service

### Step 1: Manual Restart (via Railway Dashboard)
1. Go to **Railway Dashboard**: https://railway.app
2. Select your **project**: "polymarket ai-ml bot"
3. Select **web** service
4. Click **"Restart"** or **"Redeploy"**
5. Wait 2-3 minutes for service to restart

### Step 2: Check Railway Logs
```bash
# Via Railway CLI (if available)
railway logs --tail 50

# Or check Railway Dashboard → Logs tab
```

**Look for**:
- ✅ "Application startup complete"
- ✅ "Database initialized successfully"
- ✅ "Uvicorn running on http://0.0.0.0:8001"
- ❌ Any errors or crashes

---

## PART 2: Verify Endpoints After Restart

### Step 3: Test Critical Endpoints
```bash
BASE_URL="https://web-production-c490dd.up.railway.app"

# Health check
echo "=== Health Check ==="
curl -s "$BASE_URL/health" | python3 -m json.tool | head -30

# Markets
echo "=== Markets ==="
curl -s "$BASE_URL/markets?limit=3" | python3 -m json.tool | head -20

# Live markets
echo "=== Live Markets ==="
curl -s "$BASE_URL/live/markets?limit=3" | python3 -m json.tool | head -20

# Predictions
echo "=== Predictions ==="
curl -s "$BASE_URL/predictions?limit=3" | python3 -m json.tool | head -20
```

---

## PART 3: Fix Stale Market Data ✅

### Issue Identified
**Location**: `src/data/sources/polymarket.py:277-305`

**Problem**: 
- Current filtering only excludes `archived=True` markets
- Does NOT filter by `end_date_iso` to exclude expired markets
- Result: Old markets from 2022-2023 are included

### Fix Applied ✅

**File**: `src/data/sources/polymarket.py`

**Change**: Added date filtering to exclude markets that ended more than 1 day ago:

```python
# 2. Filter out markets that have already ended (stale data)
end_date_str = item.get("end_date_iso") or item.get("end_date")
if end_date_str:
    try:
        # Parse ISO date string
        if end_date_str.endswith('Z'):
            end_date_str = end_date_str.replace('Z', '+00:00')
        end_date = datetime.fromisoformat(end_date_str)
        # Use UTC if timezone-naive
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        # Filter out markets that ended more than 1 day ago
        now = datetime.now(timezone.utc)
        if end_date < (now - timedelta(days=1)):
            strict_filtered += 1
            continue
    except (ValueError, TypeError) as e:
        logger.debug("Could not parse end_date", ...)
```

**Result**: 
- ✅ Markets ending >1 day ago are filtered out
- ✅ Only active/future markets are included
- ✅ Recently resolved markets (<1 day) still included (for analysis)

---

## PART 4: Deploy Fix and Test

### Step 4: Commit and Deploy
```bash
cd ~/ai-ml-trading-bot

git add src/data/sources/polymarket.py
git commit -m "Fix stale market data: filter out expired markets by end_date

- Added date filtering to exclude markets that ended >1 day ago
- Prevents 2022-2023 markets from appearing in active markets
- Keeps recently resolved markets (<1 day) for analysis
- Fixes issue where old markets were showing in dashboard"

git push
```

**Railway will auto-deploy** (if GitHub integration is enabled)

### Step 5: Wait for Deployment
- Check Railway Dashboard for deployment status
- Wait 2-3 minutes for deployment to complete
- Check logs for successful startup

### Step 6: Test Market Filtering
```bash
BASE_URL="https://web-production-c490dd.up.railway.app"

# Check markets - should only show future/active markets
echo "=== Checking Market Dates ==="
curl -s "$BASE_URL/markets?limit=10" | python3 -m json.tool | grep -A 2 "end_date\|resolution_date" | head -30

# Trigger prediction generation (will fetch fresh markets)
echo "=== Triggering Prediction Generation ==="
curl -X POST "$BASE_URL/predictions/generate?limit=20&auto_signals=true&auto_trades=true" | python3 -m json.tool
```

**Expected**:
- ✅ Markets have `end_date` in the future (or recent past <1 day)
- ✅ No markets from 2022-2023
- ✅ Prediction generation starts successfully

---

## PART 5: Verify Predictions and Signals

### Step 7: Check Predictions
```bash
# Wait 2-5 minutes for predictions to generate
sleep 120

# Check predictions
curl -s "$BASE_URL/predictions?limit=5" | python3 -m json.tool | head -40

# Check signals
curl -s "$BASE_URL/signals?limit=5" | python3 -m json.tool | head -40
```

**Expected**:
- ✅ New predictions with today's date
- ✅ Predictions for active markets only
- ✅ Signals created if edge > threshold

---

## PART 6: Verify Cron Job

### Step 8: Check Cron Job Configuration
**External Cron Job** (cron-job.org):
- **URL**: `https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true`
- **Method**: POST
- **Schedule**: Every 5-15 minutes
- **Timeout**: 120 seconds

**Check**:
1. Go to cron-job.org dashboard
2. Verify cron job is **enabled**
3. Check last execution time
4. Verify it's hitting the correct URL

---

## Summary of Changes

### ✅ Fix Applied
1. **Date Filtering**: Added `end_date_iso` filtering to exclude expired markets
2. **Buffer Period**: Keeps markets resolved <1 day ago (for analysis)
3. **Error Handling**: Gracefully handles date parsing errors

### ✅ Expected Results
1. **No More Stale Markets**: 2022-2023 markets filtered out
2. **Active Markets Only**: Only future/recent markets shown
3. **Better Predictions**: Predictions generated for relevant markets only

---

## Troubleshooting

### If Markets Still Show Old Data
1. **Clear Database Cache**:
   ```bash
   # Archive old markets in database
   railway run psql -c "
   UPDATE markets 
   SET archived = true 
   WHERE resolution_date < NOW() - INTERVAL '1 day';
   "
   ```

2. **Manually Trigger Refresh**:
   ```bash
   curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=30&auto_signals=true"
   ```

### If Server Still Not Responding
1. **Check Railway Dashboard** for service status
2. **Check Logs** for errors
3. **Restart Service** again if needed
4. **Check Database Connection** in Railway variables

---

*Fix committed and ready to deploy! 🚀*

