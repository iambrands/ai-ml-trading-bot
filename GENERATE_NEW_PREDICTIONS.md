# Generate New Predictions on Railway

## Quick Start

**Generate New Predictions**:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

**Timeline**: 2-5 minutes for 20 markets

---

## What's Needed for Prediction Generation

### ✅ Already Available (Ready to Use)

1. **Trained ML Models**:
   - ✅ XGBoost model (`xgboost_model.pkl`)
   - ✅ LightGBM model (`lightgbm_model.pkl`)
   - ✅ Feature names (`feature_names.pkl`)
   - ✅ Models are in git, deployed to Railway

2. **Database Connection**:
   - ✅ `DATABASE_URL` is set
   - ✅ Database is connected and working
   - ✅ Can save predictions to database

3. **API Endpoint**:
   - ✅ `/predictions/generate` endpoint works
   - ✅ Can fetch markets from Polymarket
   - ✅ Can generate features and run models

4. **Data Sources**:
   - ✅ Polymarket API (for market data)
   - ✅ RSS News (for sentiment analysis)
   - ✅ Models trained on historical data

### ⏳ What Happens During Generation

1. **Fetches Active Markets** from Polymarket (live data)
2. **For Each Market**:
   - Fetches market data (prices, volume, etc.)
   - Fetches news articles (RSS feeds)
   - Generates features (sentiment, market data, temporal, etc.)
   - Runs ML models (XGBoost, LightGBM, Ensemble)
   - Calculates edge (AI prediction vs market price)
   - Saves prediction to database
   - Creates signals automatically (if edge > threshold)

---

## How to Generate New Predictions

### Option 1: API Endpoint (Recommended)

```bash
# Generate 20 predictions
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"

# Generate 50 predictions
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=50"

# Generate with auto-trades (creates trades automatically)
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_trades=true"
```

**Parameters**:
- `limit`: Number of markets to process (default: 10)
- `auto_trades`: Automatically create trades from signals (default: false)

### Option 2: Wait for Completion

After calling the API:
1. ⏱️ **Wait 2-5 minutes** for processing to complete
2. 🔄 **Refresh Railway dashboard**: `https://web-production-c490dd.up.railway.app/dashboard`
3. ✅ **Check Predictions tab** - should show NEW predictions (today's date)

---

## Understanding Market Counts

### Markets in Database vs Active Markets

**Markets in Database** (`/markets` endpoint):
- Markets that were previously fetched and saved
- Historical markets (from 1/9/26)
- May include resolved markets

**Active Markets** (`/live/markets` endpoint):
- Currently active markets on Polymarket (live)
- Markets that are accepting orders
- Updated in real-time from Polymarket API

**For New Predictions**:
- System fetches **active markets** from Polymarket (live)
- Processes them to generate predictions
- Saves predictions to database
- Doesn't need existing markets in database (fetches fresh from Polymarket)

### Why Only 5 Markets?

**Possible Reasons**:
1. **Database Query Limit**: API endpoint might be returning limited results
2. **Market Filtering**: Only showing active/unresolved markets
3. **Date Range**: Only showing recent markets

**To Check Total**:
```bash
# Check total markets in database
curl "https://web-production-c490dd.up.railway.app/markets?limit=1000" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Total: {len(data)}')"

# Check active markets on Polymarket
curl "https://web-production-c490dd.up.railway.app/live/markets?limit=100" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Active: {len(data)}')"
```

---

## How Prediction Generation Works

### Step 1: Fetch Active Markets

- Calls Polymarket API to get active markets
- Filters for markets accepting orders
- Limits to specified count (e.g., 20 markets)

### Step 2: Generate Features

For each market:
1. **Market Features**:
   - Current prices (YES/NO)
   - Volume, liquidity
   - Time to resolution
   - Market category

2. **Sentiment Features**:
   - Fetches news articles (RSS feeds)
   - Analyzes sentiment (FinBERT model)
   - Calculates sentiment scores

3. **Temporal Features**:
   - Time-based features
   - Market age, time remaining

4. **Text Embeddings**:
   - Generates embeddings from market question
   - Uses sentence-transformers

### Step 3: Run ML Models

1. **XGBoost Model**:
   - Input: Feature vector
   - Output: Probability prediction

2. **LightGBM Model**:
   - Input: Feature vector
   - Output: Probability prediction

3. **Ensemble Model**:
   - Combines XGBoost and LightGBM predictions
   - Weighted average
   - Calculates confidence

### Step 4: Calculate Edge

- **AI Prediction**: Ensemble model probability (e.g., 65%)
- **Market Price**: Current market price (e.g., 40%)
- **Edge**: Difference (e.g., +25% - AI thinks it's undervalued)

### Step 5: Save to Database

- Saves prediction with:
  - Market ID
  - Model probability
  - Market price
  - Edge
  - Confidence
  - Timestamp

### Step 6: Create Signals (Automatic)

If edge > threshold (default: 5%):
- Creates trading signal
- Determines signal strength (STRONG, MODERATE, WEAK)
- Saves signal to database

---

## Verification

### Check Predictions Were Generated

```bash
# Check latest predictions
curl "https://web-production-c490dd.up.railway.app/predictions?limit=10" | python3 -m json.tool

# Check prediction dates (should show today's date)
curl "https://web-production-c490dd.up.railway.app/predictions?limit=5" | python3 -c "
import sys, json
from datetime import datetime
data = json.load(sys.stdin)
for pred in data[:5]:
    if 'prediction_time' in pred:
        print(f\"{pred['prediction_time']}\")
"
```

### Check UI

1. **Open Dashboard**: `https://web-production-c490dd.up.railway.app/dashboard`
2. **Go to Predictions tab**
3. **Check prediction dates**: Should show today's date for new predictions
4. **Check signals**: Signals tab should show new signals (if edge > threshold)

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

### Predictions Not Generating

**Check Railway Logs**:
1. Go to Railway Dashboard
2. Click on web service
3. Go to "Logs" tab
4. Look for errors

**Common Issues**:
- Models not found: Check if model files are in Railway deployment
- Database errors: Check database connection
- API errors: Check Polymarket API access

### No New Predictions After 5 Minutes

**Check**:
1. Railway logs for errors
2. Prediction generation completed successfully
3. Predictions saved to database

**Solutions**:
- Check Railway logs for errors
- Try with smaller limit: `limit=5`
- Wait longer (may take 5+ minutes for 20 markets)

---

## Summary

**What's Needed**:
- ✅ Trained models (already deployed)
- ✅ Database connection (already working)
- ✅ API endpoint (already working)
- ✅ Active markets from Polymarket (fetched live)

**How to Generate**:
```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=20"
```

**Timeline**: 2-5 minutes for 20 markets

**Result**: New predictions saved to database, visible in UI

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*

