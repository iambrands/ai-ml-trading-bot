# How to Populate the Dashboard Tabs

## Why Some Tabs Are Empty

**Markets Tab** ✅ - Shows data because it loads **live data** directly from Polymarket API

**Predictions Tab** ❌ - Empty because predictions need to be **generated first**
- Predictions are created by running ML models on markets
- This must be done manually or via background service

**Signals Tab** ❌ - Empty because signals are generated **from predictions**
- Signals are automatically created when predictions have edge > threshold
- No predictions = No signals

**Trades Tab** ❌ - Empty because trades are created **from signals**
- Trades are automatically created when signals meet criteria
- No signals = No trades

**Portfolio Tab** ❌ - Empty because portfolio is built **from trades**
- Portfolio shows your account status based on trades
- No trades = Empty portfolio

---

## How Data Flows

```
Markets (Live from Polymarket)
    ↓
Generate Predictions (AI Analysis)
    ↓
Generate Signals (Trading Opportunities)
    ↓
Create Trades (Execute Trades)
    ↓
Update Portfolio (Track Performance)
```

**Each step depends on the previous one!**

---

## Step-by-Step: How to Populate Each Tab

### Step 1: Markets Tab ✅ (Already Working)

**Status**: Already showing data!

**Why**: Markets tab loads live data directly from Polymarket API

**What to do**: Nothing! Just browse the markets.

---

### Step 2: Predictions Tab (Generate Predictions)

**Status**: Empty - needs to be populated

**How to Populate**:

#### Option A: Use the API Endpoint (Easiest)

1. **Make sure API server is running** (port 8002):
   ```bash
   uvicorn src.api.app:app --host 0.0.0.0 --port 8002
   ```

2. **Call the prediction generation endpoint**:
   ```bash
   curl -X POST http://localhost:8002/predictions/generate
   ```

   Or if on Railway:
   ```bash
   curl -X POST https://your-railway-url.railway.app/predictions/generate
   ```

3. **Wait 1-2 minutes** for predictions to generate

4. **Refresh the Predictions tab** (auto-refreshes every 30 seconds)

#### Option B: Run the Python Script

1. **Run the script**:
   ```bash
   python scripts/generate_predictions.py --limit 20
   ```

2. **Wait for completion** (may take a few minutes)

3. **Check the Predictions tab**

#### Option C: Start Background Service (Recommended)

**For continuous operation**:

```bash
# Start background service (generates predictions every 5 minutes)
nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
echo $! > logs/background_service.pid

# Check if running
ps -p $(cat logs/background_service.pid)

# View logs
tail -f logs/background_service.log
```

**What this does**:
- Automatically generates predictions every 5 minutes
- Runs 24/7 in the background
- No manual intervention needed

**See**: `BACKGROUND_SERVICE_GUIDE.md` for details

---

### Step 3: Signals Tab (Automatic - After Predictions)

**Status**: Empty - will populate automatically after predictions exist

**How to Populate**: 

✅ **Automatic!** Signals are created automatically when:
- Predictions exist (from Step 2)
- Edge > your minimum threshold (default: 5%)
- Confidence > your minimum threshold (default: 60%)

**What to do**: 
- Generate predictions first (Step 2)
- Signals will appear automatically
- Check Settings tab to see your thresholds

**Note**: If predictions exist but no signals, it means no predictions met your criteria (edge too small, confidence too low, etc.)

---

### Step 4: Trades Tab (Automatic - After Signals)

**Status**: Empty - will populate automatically after signals exist

**How to Populate**:

✅ **Automatic!** Trades are created automatically when:
- Signals exist (from Step 3)
- Auto-trading is enabled (via API call with `auto_trades=true`)

**To enable auto-trades**:

```bash
# Generate predictions AND create trades automatically
curl -X POST "http://localhost:8002/predictions/generate?auto_trades=true"
```

Or:

```bash
python scripts/generate_predictions.py --auto-trades
```

**Note**: By default, trades are NOT created automatically for safety. You must explicitly enable `--auto-trades` flag.

---

### Step 5: Portfolio Tab (Automatic - After Trades)

**Status**: Empty - will populate automatically after trades exist

**How to Populate**:

✅ **Automatic!** Portfolio is updated automatically when:
- Trades exist (from Step 4)
- Portfolio snapshots are created (automatic)

**What to do**: 
- Create trades first (Step 4)
- Portfolio will update automatically
- Check Portfolio tab to see your account status

---

## Quick Start: Get Everything Working

### For New Users (Recommended)

**Step 1**: Generate Predictions
```bash
curl -X POST http://localhost:8002/predictions/generate
```

**Step 2**: Check Predictions Tab
- Wait 1-2 minutes
- Refresh browser
- Should see predictions with edges

**Step 3**: Check Signals Tab
- Signals should appear automatically
- If empty, check Settings → Min Edge Threshold

**Step 4**: Enable Auto-Trades (Optional)
```bash
curl -X POST "http://localhost:8002/predictions/generate?auto_trades=true"
```

**Step 5**: Check Trades and Portfolio Tabs
- Trades should appear in Trades tab
- Portfolio should show account status

---

## For Continuous Operation

**Start Background Service**:

```bash
# Start service (generates predictions every 5 minutes)
nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
echo $! > logs/background_service.pid

# Verify it's running
ps -p $(cat logs/background_service.pid)

# Monitor logs
tail -f logs/background_service.log
```

**What Happens**:
- Every 5 minutes: Generates predictions
- Automatically: Creates signals (if edge > threshold)
- Automatically: Creates trades (if auto_trades enabled)
- Automatically: Updates portfolio

**You don't need to do anything** - it runs itself!

---

## Troubleshooting

### Predictions Tab Still Empty After Running Command?

**Check**:
1. Is API server running? (port 8002)
2. Are models trained? (Check `data/models/` directory)
3. Check API logs for errors
4. Try running the Python script directly:
   ```bash
   python scripts/generate_predictions.py --limit 5
   ```

### Signals Tab Empty Even After Predictions Exist?

**Possible reasons**:
1. **No predictions met criteria**: Edge too small, confidence too low
2. **Check Settings**: Min Edge Threshold (default: 5%), Min Confidence (default: 60%)
3. **Lower thresholds**: Try reducing Min Edge to 1% to see more signals

### Trades Tab Empty Even After Signals Exist?

**Possible reasons**:
1. **Auto-trades not enabled**: Must use `--auto-trades` flag or `auto_trades=true` parameter
2. **Risk limits hit**: System may stop trading if limits exceeded
3. **Check Settings**: Trading mode, risk level, position limits

### Portfolio Tab Empty Even After Trades Exist?

**Possible reasons**:
1. **Trades not executed**: Check Trades tab status
2. **Portfolio snapshot not created**: Should be automatic
3. **Check database**: Verify trades exist in database

---

## Summary

**Quick Summary**:

1. ✅ **Markets**: Already working (live data)
2. ⚠️ **Predictions**: Must generate manually or via background service
3. ✅ **Signals**: Automatic (after predictions exist)
4. ⚠️ **Trades**: Automatic (after signals exist, but requires `--auto-trades` flag)
5. ✅ **Portfolio**: Automatic (after trades exist)

**To get everything working**:

```bash
# Generate predictions (this also creates signals automatically)
curl -X POST http://localhost:8002/predictions/generate

# Wait 1-2 minutes, then check Predictions and Signals tabs

# If you want trades too, enable auto-trades:
curl -X POST "http://localhost:8002/predictions/generate?auto_trades=true"

# Check all tabs - they should now have data!
```

**For continuous operation**:

```bash
# Start background service (runs automatically every 5 minutes)
nohup python scripts/background_prediction_service.py > logs/background_service.log 2>&1 &
```

---

*See `DATA_UPDATE_GUIDE.md` for more detailed information on data generation*

