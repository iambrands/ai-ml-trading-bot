# Model Training - Quick Start Guide

## Prerequisites Check

Before starting training, let's verify everything is set up:

### 1. Check Polymarket API Access

```bash
python -c "
import asyncio
from src.data.sources.polymarket import PolymarketDataSource
from datetime import datetime, timedelta, timezone

async def check():
    async with PolymarketDataSource() as pm:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=90)
        markets = await pm.fetch_resolved_markets(start_date, end_date, limit=10)
        print(f'✅ Found {len(markets)} resolved markets in last 90 days')
        if markets:
            print(f'Sample: {markets[0].question[:60]}...')
        else:
            print('⚠️  No resolved markets found. This might be due to:')
            print('   - API authentication issues')
            print('   - No markets resolved in date range')
            print('   - API endpoint changes')

asyncio.run(check())
"
```

### 2. Verify Dependencies

```bash
python -c "
import xgboost
import lightgbm
import sklearn
import numpy as np
print('✅ All ML dependencies installed')
"
```

### 3. Check Data Directory

```bash
mkdir -p data/models
echo "✅ Data directory ready"
```

## Step 1: Quick Training (Recommended First Run)

Start with a small dataset to test everything works:

```bash
# Train on last 30 days (quick test)
python scripts/train_models.py \
    --start-date $(python -c "from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) - timedelta(days=30)).isoformat())") \
    --end-date $(python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat())") \
    --time-points 1 7
```

**Expected output:**
- Collecting training data...
- Found X resolved markets
- Training models...
- Model training complete!

## Step 2: Full Training (Production)

Once quick training works, train on more data:

```bash
# Train on last 90 days (default)
python scripts/train_models.py

# Or train on last 6 months
python scripts/train_models.py \
    --start-date 2024-07-01T00:00:00Z \
    --end-date 2024-12-31T23:59:59Z \
    --time-points 1 3 7 14 30
```

## Step 3: Verify Trained Models

After training completes, verify models were saved:

```bash
python -c "
from pathlib import Path
import pickle

models_dir = Path('data/models')
files = list(models_dir.glob('*.pkl'))
print(f'✅ Found {len(files)} model files:')
for f in files:
    print(f'   - {f.name}')
    try:
        with open(f, 'rb') as file:
            model = pickle.load(file)
        print(f'     Type: {type(model).__name__}')
    except Exception as e:
        print(f'     ⚠️  Error loading: {e}')
"
```

## What Happens During Training

1. **Data Collection** (5-15 minutes):
   - Fetches resolved markets from Polymarket
   - For each market, samples features at multiple time points
   - Creates training examples with labels (YES=1, NO=0)

2. **Feature Generation** (10-30 minutes):
   - Generates market features (price, volume, etc.)
   - Generates sentiment features (if NewsAPI is configured)
   - Creates feature vectors for each training example

3. **Model Training** (5-20 minutes):
   - Trains XGBoost model
   - Trains LightGBM model
   - Uses time-series cross-validation
   - Saves models to `data/models/`

## Expected Training Time

- **Quick test (30 days)**: 5-10 minutes
- **Standard (90 days)**: 15-30 minutes
- **Full (6 months)**: 30-60 minutes

## Troubleshooting

### Issue: "No training examples collected"

**Solution:**
```bash
# Try wider date range
python scripts/train_models.py \
    --start-date 2023-01-01T00:00:00Z \
    --end-date 2024-12-31T23:59:59Z
```

### Issue: "ModuleNotFoundError"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Out of memory"

**Solution:**
```bash
# Reduce time points
python scripts/train_models.py --time-points 1 7

# Or reduce date range
python scripts/train_models.py \
    --start-date $(python -c "from datetime import datetime, timedelta, timezone; print((datetime.now(timezone.utc) - timedelta(days=30)).isoformat())")
```

## Next Steps After Training

1. **Check Model Performance**:
   - Review training logs for accuracy metrics
   - Models should achieve >55% accuracy

2. **Test Models**:
   ```bash
   python scripts/test_components.py
   ```

3. **Start Trading Bot**:
   ```bash
   python src/main.py
   ```

4. **View Predictions in UI**:
   - Open http://localhost:8001/
   - Go to Predictions tab
   - Click "Load from DB" to see model predictions

## Training Configuration

Edit `config/model_params.yaml` to adjust:
- Model hyperparameters
- Training settings
- Cross-validation parameters

Ready to start? Run the quick training command above! 🚀

