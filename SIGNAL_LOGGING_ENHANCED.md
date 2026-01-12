# Enhanced Logging for Signal Generation

## Issue

Predictions are being generated with high edge (37.5%) and confidence (87.55%), but `signals_created=0`.

## Problem

The signal generator checks three conditions:
1. ✅ Edge >= 5% (37.5% passes)
2. ✅ Confidence >= 55% (87.55% passes)
3. ❓ Volume >= $500 (unknown - likely failing)

## Solution

**Added enhanced logging** to see exactly why signals aren't being created:

### Changes Made

1. **Changed log level**: `logger.debug()` → `logger.info()` for visibility
2. **Added detailed logging**:
   - Shows actual edge/confidence/volume values
   - Shows percentages for easier reading
   - Logs when signals are skipped and why
   - Logs when signals are successfully generated

### What You'll See in Logs

**If signal skipped due to liquidity:**
```
[info] Signal skipped - Liquidity too low market_id=0x7c97080dfbbe71bfa5 volume=0.0 min_liquidity=500.0 volume_usd=$0.00
```

**If signal generated successfully:**
```
[info] Signal generated successfully market_id=0x7c97080dfbbe71bfa5 side=YES strength=STRONG edge=0.3755 edge_pct=37.55 confidence=0.8755 confidence_pct=87.55 volume=1000.0 volume_usd=$1000.00
```

## Next Steps

1. ✅ **Deploy** - Changes pushed to GitHub
2. ⏳ **Wait for deployment** - Railway will auto-deploy
3. ⏳ **Check logs** - After next prediction run (cron job)
4. ⏳ **Diagnose** - See actual volume values in logs
5. ⏳ **Fix** - Adjust liquidity threshold or volume fetching if needed

## Expected Diagnosis

Most likely scenarios:

1. **Volume = 0 or NULL**:
   - Polymarket API not returning volume data
   - Need to fix volume fetching

2. **Volume < $500**:
   - Markets have low volume
   - Can lower liquidity threshold to $100 or $50

3. **Volume data missing**:
   - Need to make liquidity check optional
   - Or use a different metric (e.g., liquidity instead of volume)

---

*Created: 2026-01-11*  
*Status: Enhanced logging deployed - Awaiting next prediction run*


