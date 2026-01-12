# Debug: Why Signals Aren't Being Created

## Problem

Recent prediction generation runs show:
- ✅ `predictions_saved=5` (predictions are being generated)
- ❌ `signals_created=0` (signals are NOT being created)
- Edge: 37.55% (well above 5% threshold)

---

## Signal Generation Logic

### Code Flow

1. `generate_predictions()` function (scripts/generate_predictions.py)
2. Calls `save_prediction_to_db()` for each prediction
3. `save_prediction_to_db()` checks:
   ```python
   if signal_generator and abs(edge) > 0.05:
       signal = signal_generator.generate_signal(market, prediction)
   ```

4. `SignalGenerator.generate_signal()` checks:
   - ✅ Edge threshold: `abs_edge >= min_edge` (0.05 = 5%)
   - ❓ Confidence threshold: `prediction.confidence >= min_confidence` (0.60 = 60%)
   - ❓ Volume threshold: `market.volume_24h >= min_liquidity` (1000.0 = $1000)

---

## What We Know

### ✅ Confirmed

From recent logs:
- **Edge**: 37.55% ✅ (passes 5% threshold: `abs(0.3755) = 0.3755 >= 0.05`)
- **Market Price**: 0.5
- **Model Probability**: 0.8755 (0.5 + 0.3755)
- **Predictions being saved**: ✅ (5 saved)

### ❓ Unknown

We don't know from logs:
- **Confidence**: What is `prediction.confidence`? (might be < 60%)
- **Volume**: What is `market.volume_24h`? (might be < $1000 or None)
- **Signal Generator**: Is `signal_generator` being passed correctly?
- **Errors**: Are exceptions being caught silently?

---

## SignalGenerator.generate_signal() Conditions

From `src/trading/signal_generator.py` lines 77-98:

```python
def generate_signal(self, market: Market, prediction: EnsemblePrediction) -> Optional[TradingSignal]:
    # Check thresholds
    if abs_edge < self.min_edge:  # 0.05 = 5%
        logger.debug("Edge too small", ...)
        return None  # ❌ Edge too small
    
    if prediction.confidence < self.min_confidence:  # 0.60 = 60%
        logger.debug("Confidence too low", ...)
        return None  # ❌ Confidence too low
    
    if market.volume_24h < self.min_liquidity:  # 1000.0 = $1000
        logger.debug("Liquidity too low", ...)
        return None  # ❌ Volume too low
    
    # All checks passed - create signal
    return TradingSignal(...)
```

**Possible reasons signals aren't created**:
1. ✅ Edge: PASSES (37.55% > 5%)
2. ❓ Confidence: UNKNOWN (likely < 60%)
3. ❓ Volume: UNKNOWN (likely < $1000 or None)
4. ❓ Exception: UNKNOWN (error in signal generation)

---

## Debug Steps

### Step 1: Check Railway Logs for Debug Messages

Look for these debug messages in Railway logs:
- `"Edge too small"` - Edge threshold not met
- `"Confidence too low"` - Confidence threshold not met
- `"Liquidity too low"` - Volume threshold not met
- `"Failed to auto-generate signal"` - Exception in signal generation

**Action**: Check Railway logs for recent prediction generation runs

### Step 2: Add Logging to Check Values

Add logging to see actual values:
- `prediction.confidence`
- `market.volume_24h`
- Whether `signal_generator.generate_signal()` is being called
- Whether it returns `None` or raises an exception

### Step 3: Check Signal Generator Creation

Verify that `signal_generator` is created and passed correctly:
- Is `SignalGenerator()` created?
- Is it passed to `save_prediction_to_db()`?
- Is `auto_generate_signals=True`?

---

## Code Analysis

### How signal_generator is Created

From `scripts/generate_predictions.py`:

```python
# Check if signal generator is created
signal_generator = None
if auto_generate_signals:
    from src.trading.signal_generator import SignalGenerator
    signal_generator = SignalGenerator()
```

**Note**: `auto_generate_signals=True` by default in the endpoint

### How signal_generator is Used

From `scripts/generate_predictions.py` line 131:

```python
if signal_generator and abs(edge) > 0.05:  # 5% minimum edge
    try:
        signal = signal_generator.generate_signal(market, prediction)
        if signal:
            # Save signal to database
            ...
    except Exception as e:
        logger.warning("Failed to auto-generate signal", ...)
```

**Note**: Edge check passes (37.55% > 5%), so `signal_generator.generate_signal()` should be called

---

## Most Likely Causes

### 1. Confidence Too Low (Most Likely)

**Hypothesis**: `prediction.confidence < 0.60` (60%)

**Why**: Model confidence might be below 60% threshold

**Check**: Look for "Confidence too low" in Railway logs

**Fix**: Lower confidence threshold or check why confidence is low

### 2. Volume Too Low (Likely)

**Hypothesis**: `market.volume_24h < 1000.0` ($1000) or `market.volume_24h` is None

**Why**: Markets might not have enough volume, or volume attribute missing

**Check**: Look for "Liquidity too low" in Railway logs

**Fix**: Lower volume threshold or check market data structure

### 3. Exception in Signal Generation (Possible)

**Hypothesis**: Exception raised but caught silently

**Why**: Error in signal generation logic (e.g., missing attribute)

**Check**: Look for "Failed to auto-generate signal" in Railway logs

**Fix**: Check exception message and fix the bug

### 4. Signal Generator Not Called (Unlikely)

**Hypothesis**: `signal_generator` is None or edge check fails

**Why**: `auto_generate_signals=False` or edge calculation wrong

**Check**: Verify `auto_generate_signals=True` in endpoint call

**Fix**: Ensure `auto_generate_signals=True` is passed

---

## Recommended Actions

### 1. ✅ Check Railway Logs (Quickest)

Look for debug messages in Railway logs:
- "Edge too small"
- "Confidence too low"
- "Liquidity too low"
- "Failed to auto-generate signal"

### 2. ✅ Add Enhanced Logging (Recommended)

Add logging to see actual values:
```python
logger.info("Signal generation attempt",
    edge=abs_edge,
    confidence=prediction.confidence,
    volume=market.volume_24h,
    min_edge=self.min_edge,
    min_confidence=self.min_confidence,
    min_liquidity=self.min_liquidity,
)
```

### 3. ✅ Test Signal Generation Directly

Create a test script to generate signals with known values:
- Edge: 37.55% (passes)
- Confidence: Test with different values (50%, 60%, 70%)
- Volume: Test with different values ($500, $1000, $2000)

---

## Summary

**Known**:
- ✅ Edge passes threshold (37.55% > 5%)
- ✅ Predictions are being generated
- ✅ Signal generation logic exists and worked before (2026-01-09)

**Unknown**:
- ❓ Confidence value (likely < 60%)
- ❓ Volume value (likely < $1000 or None)
- ❓ Whether exceptions are being raised

**Next Steps**:
1. Check Railway logs for debug messages
2. Add enhanced logging to see actual values
3. Test signal generation with known values

---

*Created: 2026-01-11*
*Issue: signals_created=0 despite predictions being generated*
*Status: Debugging in progress*


