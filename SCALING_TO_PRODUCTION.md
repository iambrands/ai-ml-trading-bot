# Scaling to Production: 23 → 500+ Markets

## Overview

This guide explains how to scale from the current POC (23 markets) to production-ready training with 500+ resolved markets.

## Current Status (POC)

- ✅ **23 resolved markets** from last 2 years
- ✅ Training pipeline working
- ✅ Models training successfully
- ⚠️ Limited data for robust generalization

## Production Requirements

For production, you need:
- **500+ resolved markets** (minimum)
- **1000+ preferred** for robust models
- **Diverse market categories**
- **6+ months of historical data**
- **Balanced YES/NO outcomes**

## Strategy 1: Expand Date Range

### Current Approach
```bash
# POC: Last 2 years
--start-date 2024-01-01T00:00:00Z
--end-date 2026-01-08T23:59:59Z
```

### Production Approach
```bash
# Option A: Last 3-4 years
python scripts/train_models.py \
    --start-date 2020-01-01T00:00:00Z \
    --end-date 2026-01-08T23:59:59Z \
    --time-points 1 3 7 14

# Option B: Specific high-activity periods
python scripts/train_models.py \
    --start-date 2022-01-01T00:00:00Z \
    --end-date 2024-12-31T23:59:59Z \
    --time-points 1 3 7 14 30
```

**Expected Result**: 200-500+ markets depending on Polymarket activity

## Strategy 2: Multiple Time Points

### POC Configuration
```bash
--time-points 1 7  # 2 samples per market = 46 examples
```

### Production Configuration
```bash
--time-points 1 3 7 14 30  # 5 samples per market
# With 100 markets = 500 training examples
```

**Benefit**: More training examples from same markets

## Strategy 3: Data Collection Script

Create a dedicated script to collect and cache resolved markets:

```bash
# scripts/collect_training_data.py
python scripts/collect_training_data.py \
    --start-date 2020-01-01 \
    --end-date 2026-01-08 \
    --output data/training_markets.json
```

This allows you to:
- Collect data once
- Cache for multiple training runs
- Filter and clean data
- Add manual markets if needed

## Strategy 4: Incremental Training

Train on batches and combine:

```bash
# Batch 1: 2020-2022
python scripts/train_models.py \
    --start-date 2020-01-01T00:00:00Z \
    --end-date 2022-12-31T23:59:59Z \
    --data-dir data/batch1

# Batch 2: 2023-2024
python scripts/train_models.py \
    --start-date 2023-01-01T00:00:00Z \
    --end-date 2024-12-31T23:59:59Z \
    --data-dir data/batch2

# Combine and retrain on all data
python scripts/combine_training_data.py \
    --batches data/batch1 data/batch2 \
    --output data/combined
```

## Strategy 5: Alternative Data Sources

### Option A: Polymarket Historical Data
- Check if Polymarket provides historical data exports
- Use their API documentation for bulk downloads
- Consider paid API tiers for historical access

### Option B: Community Datasets
- Check Polymarket community forums
- Look for shared datasets
- Consider data partnerships

### Option C: Manual Collection
- Use Polymarket website to identify resolved markets
- Collect market IDs manually
- Create training dataset from known outcomes

## Strategy 6: Synthetic Data Augmentation

For markets with limited data, augment with synthetic examples:

```python
# Generate synthetic training examples
# Based on real market patterns
# Use data augmentation techniques
```

## Implementation: Production Training Script

### Step 1: Check Available Data

```bash
python -c "
import asyncio
from src.data.sources.polymarket import PolymarketDataSource
from datetime import datetime, timedelta, timezone

async def check():
    async with PolymarketDataSource() as pm:
        end_date = datetime.now(timezone.utc)
        ranges = [
            (365, '1 year'),
            (730, '2 years'),
            (1095, '3 years'),
            (1460, '4 years'),
        ]
        for days, label in ranges:
            start_date = end_date - timedelta(days=days)
            markets = await pm.fetch_resolved_markets(start_date, end_date, limit=10000)
            print(f'{label}: {len(markets)} markets')
            if len(markets) >= 500:
                print(f'✅ Found {len(markets)} markets - sufficient for production!')
                break

asyncio.run(check())
"
```

### Step 2: Production Training Command

```bash
# Full production training
python scripts/train_models.py \
    --start-date 2020-01-01T00:00:00Z \
    --end-date 2026-01-08T23:59:59Z \
    --time-points 1 3 7 14 30 \
    --data-dir data/production
```

### Step 3: Monitor Training

```bash
# Monitor in separate terminal
python scripts/monitor_training.py --interval 60
```

## Performance Optimization

### For Large Datasets (500+ markets)

1. **Reduce Time Points** (if needed):
   ```bash
   --time-points 1 7 14  # 3 instead of 5
   ```

2. **Use Sampling**:
   - Sample features instead of all time points
   - Use stratified sampling for balanced classes

3. **Parallel Processing**:
   - Process markets in parallel
   - Use multiprocessing for feature generation

4. **Caching**:
   - Cache feature vectors
   - Save intermediate results

## Expected Results

### POC (23 markets)
- Training examples: ~46 (23 × 2 time points)
- Accuracy: 50-60% (baseline)
- Training time: 20-45 minutes

### Production (500+ markets)
- Training examples: 2500+ (500 × 5 time points)
- Expected accuracy: 55-65%+
- Training time: 2-4 hours
- Better generalization
- More robust predictions

## Validation Strategy

### Cross-Validation
```python
# Use time-series cross-validation
# Train on 2020-2023, validate on 2024
# Ensures no data leakage
```

### Holdout Test Set
```python
# Reserve 20% of data for final testing
# Never use for training
# Final performance metric
```

## Monitoring Production Models

1. **Track Performance**:
   - Log predictions vs actual outcomes
   - Calculate accuracy over time
   - Monitor model drift

2. **Retrain Schedule**:
   - Monthly retraining with new resolved markets
   - Quarterly full retraining
   - Continuous learning pipeline

3. **A/B Testing**:
   - Compare model versions
   - Track which performs better
   - Gradual rollout

## Next Steps

1. **Run Data Check**:
   ```bash
   # Check how many markets available in wider range
   python -c "..." # Use script above
   ```

2. **Start Production Training**:
   ```bash
   # Use widest date range that gives 500+ markets
   python scripts/train_models.py --start-date ... --end-date ...
   ```

3. **Monitor Progress**:
   ```bash
   python scripts/monitor_training.py
   ```

4. **Validate Models**:
   - Check accuracy metrics
   - Test on holdout set
   - Compare to baseline

## Troubleshooting

### Issue: Still < 500 markets

**Solutions**:
- Use longer date range (3-4 years)
- Reduce time points to get more markets
- Consider data augmentation
- Use alternative data sources

### Issue: Training too slow

**Solutions**:
- Reduce time points
- Use sampling
- Enable parallel processing
- Cache intermediate results

### Issue: Memory errors

**Solutions**:
- Process in batches
- Reduce feature dimensions
- Use data streaming
- Increase system memory

## Production Checklist

- [ ] 500+ resolved markets collected
- [ ] Balanced YES/NO outcomes
- [ ] Diverse market categories
- [ ] Training script optimized
- [ ] Models trained and validated
- [ ] Performance metrics tracked
- [ ] Retraining schedule established
- [ ] Monitoring system in place

Ready to scale? Start with the data check script above! 🚀



