# Performance & Settings Analysis - 2026-01-11

## 🔍 Settings Analysis

### Settings Mismatch Found!

**UI Settings (from your page)**:
- Min Edge Threshold: **10%** (0.10)
- Min Confidence: **60%** (0.60)

**Code Settings (actual)**:
- `min_edge`: **5%** (0.05) - Default from `settings.py`
- `min_confidence`: **60%** (0.60)
- `min_liquidity`: **$1000** (1000.0)

**Config File** (`config/trading_params.yaml`):
- `min_edge`: **5%** (0.05)
- `min_confidence`: **60%** (0.60)
- `min_liquidity`: **$1000** (1000.0)

⚠️ **The UI shows 10% but the code uses 5%!**

---

## 📊 Performance Test Results

### Before Database Indexes:

| Endpoint | Response Time | Status |
|----------|---------------|--------|
| Health Check | **73.5 seconds** | ❌ VERY SLOW |
| Markets | 1.7 seconds | ✅ GOOD |
| Predictions | **43.0 seconds** | ❌ VERY SLOW |
| Signals | 1.5 seconds | ✅ GOOD |
| Trades | **11.7 seconds** | ❌ SLOW |
| Portfolio Latest | 4.0 seconds | ⚠️ ACCEPTABLE |

### Performance Categories:
- ✅ **Good**: < 2 seconds
- ⚠️ **Acceptable**: 2-5 seconds
- ❌ **Slow**: 5-10 seconds
- ❌ **Very Slow**: > 10 seconds

### Issues Identified:
1. **Health Check**: 73.5 seconds - Extremely slow
2. **Predictions**: 43.0 seconds - Very slow
3. **Trades**: 11.7 seconds - Slow

### Database Indexes NOT Applied Yet

The indexes we prepared have **not been run** yet. Once applied, performance should improve significantly:
- Predictions: 43 seconds → **<2 seconds** (expected)
- Trades: 11.7 seconds → **<2 seconds** (expected)
- Health Check: 73.5 seconds → **<1 second** (expected)

---

## 🔍 Why Signals Aren't Being Created

From logs:
- Edge: **37.55%** ✅ (well above 5% threshold)
- `signals_created=0` ❌

### Signal Generation Checks (in code):

1. **Edge Threshold**: ✅ **PASSING**
   - Required: `abs(edge) >= 0.05` (5%)
   - Actual: `abs(0.3755) = 37.55%` ✅

2. **Confidence Threshold**: ❓ **UNKNOWN**
   - Required: `prediction.confidence >= 0.60` (60%)
   - Actual: **Not shown in logs** - Need to check
   - **Most likely issue!**

3. **Liquidity Threshold**: ❓ **UNKNOWN**
   - Required: `market.volume_24h >= 1000.0` ($1000)
   - Actual: **Not shown in logs** - Need to check

### Likely Causes:

1. **Confidence too low** (< 60%)
   - Model confidence might be below 60%
   - Need to check actual confidence values

2. **Volume too low** (< $1000)
   - Markets might not have enough volume
   - Need to check `market.volume_24h` values

3. **Market data missing**
   - `market.volume_24h` might be None or missing
   - Need to check market data structure

---

## 📋 Action Items

### 1. ✅ Run Database Indexes (URGENT - Performance)

**Status**: SQL script ready, **NOT RUN YET**

**Command to run**:
```bash
railway connect postgres
```

Then in psql:
```sql
\i /Users/iabadvisors/ai-ml-trading-bot/scripts/add_performance_indexes.sql
```

**Expected improvement**:
- Predictions: 43s → <2s
- Trades: 11.7s → <2s
- Health: 73.5s → <1s

### 2. ❌ Fix Settings Mismatch

**Issue**: UI shows 10% edge threshold, but code uses 5%

**Options**:
1. Update code to match UI (change default to 10%)
2. Update UI to match code (show 5%)
3. Make UI settings actually work (store in database/env)

**Recommendation**: The UI settings don't seem to be connected to the backend. The backend uses hardcoded defaults or config files.

### 3. ❌ Debug Signal Generation

**Need to check**:
- Actual `prediction.confidence` values in logs
- Actual `market.volume_24h` values
- Whether `market.volume_24h` exists and is populated

**Check Railway logs for**:
- "Confidence too low" debug messages
- "Liquidity too low" debug messages
- Actual confidence/volume values

---

## 🎯 Summary

### Performance (Before Indexes):
- ❌ Health: 73.5s (very slow)
- ✅ Markets: 1.7s (good)
- ❌ Predictions: 43.0s (very slow)
- ✅ Signals: 1.5s (good)
- ❌ Trades: 11.7s (slow)
- ⚠️ Portfolio: 4.0s (acceptable)

### Settings:
- ⚠️ UI shows 10% edge, code uses 5% (mismatch)
- ⚠️ UI settings might not be connected to backend

### Signals:
- ✅ Edge threshold: PASSING (37.55% > 5%)
- ❓ Confidence: UNKNOWN (likely issue)
- ❓ Volume: UNKNOWN (possible issue)

### Next Steps:
1. **URGENT**: Run database indexes (will fix performance)
2. Check Railway logs for confidence/volume values
3. Consider fixing settings mismatch

---

*Created: 2026-01-11*
*Performance tests run at: [current time]*


