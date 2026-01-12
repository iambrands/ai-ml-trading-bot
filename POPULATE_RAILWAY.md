# Populate Railway with Data

## Problem

Railway has a **separate database** from your local database. Data generated locally won't appear on Railway.

## Solution: Generate Predictions on Railway

### Step 1: Verify Railway is Running

```bash
curl https://web-production-c490dd.up.railway.app/health
```

**Expected Response**:
```json
{"status":"healthy","timestamp":"..."}
```

### Step 2: Generate Predictions on Railway

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

**What This Does**:
1. ✅ Fetches active markets from Polymarket
2. ✅ Generates features (sentiment, market data, etc.)
3. ✅ Runs ML models to create predictions
4. ✅ Saves predictions to Railway database
5. ✅ Automatically creates signals (if edge > threshold)

**Timeline**:
- API call: Immediate
- Processing: 2-5 minutes (for 20 markets)
- Completion: Predictions saved to Railway database

### Step 3: Wait and Refresh

1. **Wait 2-5 minutes** for processing to complete
2. **Refresh Railway dashboard**: `https://web-production-c490dd.up.railway.app/dashboard`
3. **Check Predictions tab** - should show predictions!

### Step 4: Verify Data

```bash
# Check predictions
curl "https://web-production-c490dd.up.railway.app/predictions?limit=5"

# Check signals
curl "https://web-production-c490dd.up.railway.app/signals?limit=5"

# Check trades
curl "https://web-production-c490dd.up.railway.app/trades?limit=5"
```

---

## Troubleshooting

### API Returns Error

**Common errors**:
- `500 Internal Server Error`: Check Railway logs
- `503 Service Unavailable`: Database not connected
- `Timeout`: Processing taking too long (normal)

**Solutions**:
1. Check Railway logs in dashboard
2. Verify database is connected in Railway
3. Try with smaller limit: `limit=5`
4. Wait longer (may take 5+ minutes)

### Predictions Tab Still Empty

**Possible causes**:
1. **Still processing**: Wait 5 minutes
2. **Database issue**: Predictions not saved
3. **API error**: Check Railway logs

**Solutions**:
1. Wait 5 minutes, then refresh
2. Check Railway logs for errors
3. Try generating again with smaller limit
4. Verify database connection in Railway

### No Data After 10 Minutes

**Check**:
1. Railway logs for errors
2. Database connection in Railway
3. Models deployed (check `data/models/` in Railway)
4. API endpoint response

**Solution**:
- Check Railway logs
- Verify environment variables
- Try smaller limit: `limit=5`
- Check Railway deployment status

---

## Quick Commands

### Generate Predictions

```bash
# Generate 20 predictions
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"

# Generate 5 predictions (faster)
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5"

# Generate with auto-trades
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_trades=true"
```

### Check Data

```bash
# Check health
curl https://web-production-c490dd.up.railway.app/health

# Check predictions count
curl "https://web-production-c490dd.up.railway.app/predictions?limit=1" | python3 -m json.tool

# Check signals count
curl "https://web-production-c490dd.up.railway.app/signals?limit=1" | python3 -m json.tool
```

---

## Summary

**Problem**: Railway database is separate from local database

**Solution**: Generate predictions on Railway via API

**Steps**:
1. ✅ Call prediction generation endpoint
2. ⏱️ Wait 2-5 minutes for processing
3. 🔄 Refresh Railway dashboard
4. ✅ Check Predictions tab - should show data!

**Railway URL**: `https://web-production-c490dd.up.railway.app/`



