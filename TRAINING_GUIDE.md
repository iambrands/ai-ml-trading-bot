# Model Training Guide

## Prerequisites

Before training models, ensure you have:

1. **Polymarket API Access** - The training script needs to fetch resolved markets
2. **NewsAPI Key** (optional but recommended) - For sentiment features
3. **PostgreSQL Database** (optional) - For storing training data and results
4. **Sufficient Historical Data** - At least 100+ resolved markets for meaningful training

## Step-by-Step Training Process

### 1. Check Available Training Data

First, verify you can fetch resolved markets:

```bash
python -c "
import asyncio
from src.data.sources.polymarket import PolymarketDataSource
from datetime import datetime, timedelta, timezone

async def check():
    async with PolymarketDataSource() as pm:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=90)
        markets = await pm.fetch_resolved_markets(start_date, end_date, limit=100)
        print(f'Found {len(markets)} resolved markets in last 90 days')
        if markets:
            print(f'Sample: {markets[0].question[:60]}...')

asyncio.run(check())
"
```

### 2. Train Models

Run the training script with default settings (last 90 days):

```bash
python scripts/train_models.py
```

Or specify custom date range:

```bash
# Train on last 6 months
python scripts/train_models.py \
    --start-date 2024-07-01T00:00:00Z \
    --end-date 2024-12-31T23:59:59Z

# Train with custom time points (days before resolution to sample)
python scripts/train_models.py \
    --time-points 1 3 7 14 30
```

### 3. What the Training Script Does

1. **Collects Training Data**:
   - Fetches resolved markets from Polymarket
   - For each market, samples features at multiple time points (1, 3, 7, 14 days before resolution)
   - Generates features using the feature pipeline
   - Creates labels (1 for YES, 0 for NO)

2. **Trains Models**:
   - XGBoost model
   - LightGBM model
   - Uses time-series cross-validation to prevent data leakage
   - Saves trained models to `data/models/`

3. **Evaluates Performance**:
   - Calculates accuracy, Brier score, log loss, AUC-ROC
   - Logs metrics for monitoring

### 4. Expected Output

After training, you should see:

```
✅ Models saved to: data/models/
  - xgboost_model.pkl
  - lightgbm_model.pkl
  - ensemble_config.json
```

### 5. Verify Trained Models

Test that models can be loaded:

```bash
python -c "
import pickle
from pathlib import Path

models_dir = Path('data/models')
if (models_dir / 'xgboost_model.pkl').exists():
    print('✅ XGBoost model found')
    with open(models_dir / 'xgboost_model.pkl', 'rb') as f:
        model = pickle.load(f)
    print(f'Model type: {type(model)}')
else:
    print('❌ No trained models found. Run training first.')
"
```

## Troubleshooting

### Issue: "No training examples collected"

**Possible causes:**
1. No resolved markets in the date range
2. Polymarket API authentication issues
3. Markets don't have resolution dates

**Solutions:**
- Try a wider date range: `--start-date 2023-01-01T00:00:00Z`
- Check Polymarket API access
- Verify markets have `outcome` and `resolution_date` set

### Issue: "Model training failed"

**Possible causes:**
1. Insufficient training data (< 50 examples)
2. Feature extraction errors
3. Missing dependencies

**Solutions:**
- Collect more training data (wider date range)
- Check logs for feature extraction errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Issue: "Out of memory during training"

**Solutions:**
- Reduce number of time points: `--time-points 1 7`
- Use smaller date range
- Reduce feature dimensions in config

## Next Steps After Training

1. **Evaluate Model Performance**:
   - Check training logs for metrics
   - Models should achieve >55% accuracy on validation set

2. **Run Backtest**:
   ```bash
   python scripts/backtest.py --start-date 2024-01-01 --end-date 2024-06-30
   ```

3. **Load Models in Main Bot**:
   - The main bot (`src/main.py`) will automatically load models from `data/models/`
   - Ensure models are in the correct directory

4. **Monitor Performance**:
   - Use the API to track predictions and trades
   - Review model performance over time

## Training Configuration

Edit `config/model_params.yaml` to adjust:
- Model hyperparameters
- Training settings
- Cross-validation parameters

## Data Requirements

**Minimum for meaningful training:**
- 100+ resolved markets
- Markets with clear YES/NO outcomes
- Markets with resolution dates

**Recommended:**
- 500+ resolved markets
- 6+ months of historical data
- Diverse market categories


