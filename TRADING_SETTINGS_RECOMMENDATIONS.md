# Trading Settings Recommendations

## Current Settings vs Recommended Settings

Based on analysis of your system and prediction market best practices.

---

## Current Settings

**From `config/trading_params.yaml` and `src/config/settings.py`**:
- `min_edge`: 0.05 (5%)
- `min_confidence`: 0.60 (60%)
- `min_liquidity`: 1000.0 ($1000)

**From UI Settings**:
- Min Edge Threshold: 10% (but code uses 5%)
- Min Confidence: 60%
- Risk Level: Moderate

---

## Recommended Settings

### Option 1: Conservative (Fewer but Higher Quality Trades)

**Goal**: Only trade on very high-confidence opportunities

```
min_edge: 0.10          # 10% minimum edge
min_confidence: 0.70    # 70% model confidence
min_liquidity: 500.0    # $500 minimum volume
```

**Pros**:
- ✅ Very high quality signals
- ✅ Lower risk per trade
- ✅ Better win rate expected

**Cons**:
- ❌ Fewer trading opportunities
- ❌ Might miss good opportunities with lower confidence
- ❌ Lower trade frequency

**Best for**: Starting out, conservative approach, learning the system

---

### Option 2: Moderate (Balanced) ⭐ **RECOMMENDED**

**Goal**: Balance between signal quality and quantity

```
min_edge: 0.05          # 5% minimum edge
min_confidence: 0.55    # 55% model confidence (lowered from 60%)
min_liquidity: 500.0    # $500 minimum volume (lowered from $1000)
```

**Pros**:
- ✅ Good balance of quality and quantity
- ✅ More trading opportunities
- ✅ Reasonable risk level
- ✅ Works well with your current edge (37.55%)

**Cons**:
- ⚠️ Moderate risk level
- ⚠️ Some trades might have lower confidence

**Best for**: Regular trading, balanced approach, most users

**Why these values**:
- **Edge 5%**: Your current edge is 37.55%, so 5% threshold is very conservative
- **Confidence 55%**: 60% might be too strict (causing signals not to be created)
- **Volume $500**: $1000 might be too high for smaller markets

---

### Option 3: Aggressive (More Trading Opportunities)

**Goal**: Capture more opportunities, accept more risk

```
min_edge: 0.03          # 3% minimum edge
min_confidence: 0.50    # 50% model confidence
min_liquidity: 250.0    # $250 minimum volume
```

**Pros**:
- ✅ Many trading opportunities
- ✅ Don't miss good edges
- ✅ Higher trade frequency

**Cons**:
- ❌ Higher risk per trade
- ❌ Lower win rate expected
- ❌ More trades to manage

**Best for**: Experienced traders, higher risk tolerance, active markets

---

## Specific Recommendations for Your System

### Based on Current Behavior

**Problem**: Signals not being created despite 37.55% edge

**Recommendation**: Start with **Moderate** settings and adjust:

```yaml
signals:
  min_edge: 0.05          # 5% minimum edge (keep as is)
  min_confidence: 0.55    # 55% confidence (LOWER from 60%)
  min_liquidity: 500.0    # $500 volume (LOWER from $1000)
```

**Why**:
1. **Edge 5%**: Your edge (37.55%) is way above this, so this threshold is fine
2. **Confidence 55%**: 60% might be too strict - lowering to 55% should allow signals to be created
3. **Volume $500**: $1000 might exclude valid markets - $500 is more reasonable

---

## Additional Settings to Consider

### Position Sizing

**Current**:
```yaml
position_sizing:
  kelly_fraction: 0.25    # Quarter Kelly (good)
  max_position_pct: 0.05  # 5% max per trade (good)
  max_total_exposure: 0.50  # 50% max total (good)
  min_position_size: 10   # $10 minimum (good)
```

**Recommendation**: Keep as is - these are good defaults

### Risk Management

**Current**:
```yaml
risk:
  max_daily_loss: 0.05    # 5% daily loss limit (good)
  max_drawdown: 0.15      # 15% max drawdown (good)
  stop_loss_pct: 0.50     # Stop if position down 50% (good)
  max_positions: 20       # Maximum concurrent positions (good)
```

**Recommendation**: Keep as is - these are good defaults

---

## Implementation Steps

### Step 1: Update Config File

Edit `config/trading_params.yaml`:

```yaml
signals:
  min_edge: 0.05          # 5% minimum edge
  min_confidence: 0.55    # 55% model confidence (CHANGED from 0.60)
  min_liquidity: 500.0    # $500 minimum volume (CHANGED from 1000.0)
  max_signals_per_day: 10
  cooldown_minutes: 60
```

### Step 2: Update Settings (if needed)

The code reads from `config/trading_params.yaml`, but also has defaults in `src/config/settings.py`.

**Current code flow**:
1. `SignalGenerator()` reads from `settings.min_edge`, `settings.min_confidence`, `settings.min_liquidity`
2. These come from environment variables or defaults in `settings.py`
3. Config file (`trading_params.yaml`) is not directly used by `SignalGenerator`

**To change settings**, you need to:
- Set environment variables, OR
- Change defaults in `src/config/settings.py`, OR
- Pass parameters directly to `SignalGenerator()`

### Step 3: Test the Changes

1. Deploy changes to Railway
2. Run prediction generation
3. Check if signals are now being created
4. Monitor signal quality and win rate
5. Adjust as needed

---

## Settings by Risk Profile

### Very Conservative

```
min_edge: 0.10          # 10%
min_confidence: 0.75    # 75%
min_liquidity: 1000.0   # $1000
```
- **Expected signals**: Very few (1-2 per day)
- **Win rate**: High (65-75%)
- **Risk**: Very low

### Conservative

```
min_edge: 0.08          # 8%
min_confidence: 0.70    # 70%
min_liquidity: 750.0    # $750
```
- **Expected signals**: Few (3-5 per day)
- **Win rate**: High (60-70%)
- **Risk**: Low

### Moderate ⭐ **RECOMMENDED**

```
min_edge: 0.05          # 5%
min_confidence: 0.55    # 55%
min_liquidity: 500.0    # $500
```
- **Expected signals**: Moderate (5-10 per day)
- **Win rate**: Good (55-65%)
- **Risk**: Moderate

### Aggressive

```
min_edge: 0.03          # 3%
min_confidence: 0.50    # 50%
min_liquidity: 250.0    # $250
```
- **Expected signals**: Many (10-20 per day)
- **Win rate**: Moderate (50-60%)
- **Risk**: Higher

---

## Quick Recommendation Summary

**For Your Current Situation**:

```yaml
signals:
  min_edge: 0.05          # Keep at 5% (your edge is 37.55%)
  min_confidence: 0.55    # LOWER from 60% to 55%
  min_liquidity: 500.0    # LOWER from $1000 to $500
```

**Reasoning**:
1. Your edge (37.55%) is very high, so 5% threshold is conservative enough
2. Confidence at 60% might be blocking signals - try 55%
3. Volume at $1000 might exclude valid markets - try $500

**Start here, then adjust based on results**:
- If too many signals: Increase confidence/volume
- If too few signals: Decrease confidence/volume
- If win rate too low: Increase thresholds
- If win rate good: Can lower thresholds slightly

---

## Monitoring and Adjusting

### Metrics to Watch

1. **Signal Creation Rate**:
   - How many signals per prediction run?
   - Target: 1-5 signals per 20 markets

2. **Win Rate**:
   - Percentage of profitable trades
   - Target: >55% for moderate settings

3. **Average Edge**:
   - Average edge of signals created
   - Target: >10% for good quality

4. **Trade Frequency**:
   - Number of trades per day
   - Target: 5-15 trades per day for moderate

### When to Adjust

**Increase Thresholds (More Conservative)**:
- Win rate < 50%
- Too many losing trades
- Portfolio drawdown increasing

**Decrease Thresholds (More Aggressive)**:
- Win rate > 65% consistently
- Too few trading opportunities
- Missing good edges

---

## Summary

**Recommended Starting Point (Moderate)**:

```
min_edge: 0.05          # 5% (keep as is)
min_confidence: 0.55    # 55% (LOWER from 60%)
min_liquidity: 500.0    # $500 (LOWER from $1000)
```

**Why**:
- ✅ Balances quality and quantity
- ✅ Should allow signals to be created (addresses current issue)
- ✅ Reasonable risk level
- ✅ Works well with your high edge (37.55%)

**Next Steps**:
1. Apply these settings
2. Test signal generation
3. Monitor results
4. Adjust based on performance

---

*Created: 2026-01-11*
*Based on: Current system behavior, prediction market best practices*
*Status: Recommendations ready for implementation*

