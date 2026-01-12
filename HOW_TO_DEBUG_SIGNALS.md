# How to Debug Why Signals Aren't Being Created

## Problem

Recent prediction generation runs show:
- ✅ Predictions: 5 saved
- ❌ Signals: 0 created (`signals_created=0`)
- Edge: 37.55% (well above 5% threshold)

---

## Signal Generation Logic

The `SignalGenerator.generate_signal()` method checks **3 conditions**:

1. ✅ **Edge Threshold**: `abs_edge >= 0.05` (5%)
   - Status: ✅ **PASSING** (37.55% > 5%)

2. ❓ **Confidence Threshold**: `prediction.confidence >= 0.60` (60%)
   - Status: ❓ **UNKNOWN** (likely failing)

3. ❓ **Volume Threshold**: `market.volume_24h >= 1000.0` ($1000)
   - Status: ❓ **UNKNOWN** (likely failing)

---

## Debug Steps

### Step 1: Check Railway Logs for Debug Messages

**Go to Railway Dashboard**:
1. Navigate to: https://railway.app/
2. Click on your project
3. Click on your web service
4. Click on "Logs" tab

**Look for recent prediction generation runs**:
- Search for: "Starting prediction generation"
- Look between "Prediction saved" and "Prediction generation complete"

**Search for these debug messages**:
- `"Confidence too low"` → Confidence < 60%
  - Should show: `confidence=X, min_confidence=0.6`
- `"Liquidity too low"` → Volume < $1000
  - Should show: `volume=X, min_liquidity=1000.0`
- `"Edge too small"` → Edge < 5% (unlikely)
  - Should show: `edge=X, min_edge=0.05`
- `"Failed to auto-generate signal"` → Exception in signal generation
  - Should show: `error=...`

**Note**: Debug messages use `logger.debug()`, which might not appear if log level is INFO or higher. If you don't see debug messages, we need to add enhanced logging.

---

### Step 2: Add Enhanced Logging (Recommended)

Add logging to see actual values. Modify `scripts/generate_predictions.py`:

**In `save_prediction_to_db()` function, around line 131**:

```python
# Automatically generate signal if generator provided and edge is significant
if signal_generator and abs(edge) > 0.05:  # 5% minimum edge
    try:
        # ADD THIS: Log signal generation attempt
        logger.info(
            "Signal generation attempt",
            market_id=market.id[:20],
            edge=abs(edge),
            confidence=prediction.confidence,
            volume=market.volume_24h if hasattr(market, 'volume_24h') else None,
            min_edge=signal_generator.min_edge,
            min_confidence=signal_generator.min_confidence,
            min_liquidity=signal_generator.min_liquidity,
        )
        
        signal = signal_generator.generate_signal(market, prediction)
        if signal:
            # ... existing code ...
        else:
            # ADD THIS: Log when signal is None
            logger.info("Signal generation returned None", market_id=market.id[:20])
    except Exception as e:
        logger.warning("Failed to auto-generate signal", market_id=market.id, error=str(e))
```

**Also, modify `src/trading/signal_generator.py` to use `logger.info()` instead of `logger.debug()`**:

Change lines 79, 83-88, 92-97 from `logger.debug()` to `logger.info()` so messages appear in production logs.

---

### Step 3: Check Prediction Confidence Values

Query the database to see actual confidence values:

```sql
-- Check recent predictions and their confidence values
SELECT 
    id,
    market_id,
    model_probability,
    market_price,
    edge,
    confidence,
    prediction_time
FROM predictions
ORDER BY prediction_time DESC
LIMIT 10;
```

**Look for**:
- Are confidence values < 0.60 (60%)?
- What's the average confidence?
- Are confidence values reasonable?

---

### Step 4: Check Market Volume Values

Check if markets have volume data:

```sql
-- Check if markets have volume (if stored)
SELECT 
    market_id,
    question
FROM markets
LIMIT 10;
```

**Note**: `market.volume_24h` comes from the Polymarket API, not the database. We need to check the actual market objects returned by the API.

---

## Most Likely Causes

### 1. Confidence Too Low (Most Likely)

**Hypothesis**: `prediction.confidence < 0.60` (60%)

**Why**: Ensemble model confidence might be below threshold

**Check**: 
- Railway logs for "Confidence too low" message
- Database query for confidence values
- If confidence is 0.5-0.6, it might be borderline

**Fix**: 
- Lower confidence threshold (e.g., 0.55 = 55%)
- Or improve model confidence calculation

### 2. Volume Too Low or Missing (Likely)

**Hypothesis**: `market.volume_24h < 1000.0` or `market.volume_24h` is None

**Why**: Markets might not have enough volume, or volume attribute is missing

**Check**: 
- Railway logs for "Liquidity too low" message
- Check if `market.volume_24h` exists
- Check actual volume values from Polymarket API

**Fix**: 
- Lower volume threshold (e.g., $500)
- Or handle None/missing volume values
- Or check if volume attribute name is correct

### 3. Exception in Signal Generation (Possible)

**Hypothesis**: Exception raised but caught silently

**Why**: Error in signal generation (e.g., missing attribute, type error)

**Check**: 
- Railway logs for "Failed to auto-generate signal" message
- Check exception error message

**Fix**: 
- Fix the bug causing the exception
- Add better error handling

---

## Quick Test

Create a test script to verify signal generation with known values:

```python
from src.trading.signal_generator import SignalGenerator
from src.models.ensemble import EnsemblePrediction
from src.data.models import Market

# Create signal generator
signal_generator = SignalGenerator()

# Test with known values
# Edge: 37.55% (should pass)
# Confidence: 0.65 (65% - should pass)
# Volume: 1500.0 ($1500 - should pass)

# If this works, the issue is with actual prediction/market values
# If this fails, there's a bug in the signal generator logic
```

---

## Summary

**Known**:
- ✅ Edge passes threshold (37.55% > 5%)
- ✅ Signal generation code exists and is correct
- ✅ Signal generator was created and passed correctly

**Unknown**:
- ❓ Confidence value (likely < 60%)
- ❓ Volume value (likely < $1000 or None)
- ❓ Whether debug messages appear in logs

**Next Steps**:
1. ✅ Check Railway logs for debug messages
2. ✅ Add enhanced logging (change debug to info)
3. ✅ Query database for confidence values
4. ✅ Test signal generation with known values

---

*Created: 2026-01-11*
*Issue: signals_created=0 despite predictions being generated*
*Status: Debugging guide created*


