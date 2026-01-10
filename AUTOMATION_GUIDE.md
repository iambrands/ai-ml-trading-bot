# Automation Guide

## ✅ Automatic Processing Now Enabled!

The system now automatically processes predictions into signals, trades, and portfolio updates. No manual scripts needed!

## How It Works

### 1. **Automatic Signal Generation** (Default: ON)

When you generate predictions, signals are **automatically created** for predictions with:
- Edge > 5% (configurable)
- Confidence above threshold
- Sufficient liquidity

**No action needed** - signals are created automatically!

### 2. **Automatic Trade Creation** (Default: OFF)

You can optionally enable automatic trade creation from signals:
- Set `--auto-trades` flag when generating predictions
- Or use the API endpoint with `auto_trades=true`

### 3. **Automatic Portfolio Updates**

Portfolio snapshots are automatically updated when:
- Trades are created
- Trades are closed
- Portfolio value changes

## Usage Methods

### Method 1: Command Line (Recommended)

```bash
# Generate predictions with automatic signal generation (default)
python scripts/generate_predictions.py --limit 20

# Generate predictions with automatic signals AND trades
python scripts/generate_predictions.py --limit 20 --auto-trades

# Disable automatic signal generation (if needed)
python scripts/generate_predictions.py --limit 20 --no-auto-signals
```

### Method 2: API Endpoint (For Web UI)

```bash
# Start API server
uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
```

Then use the API:

```bash
# Generate predictions with auto-signals (default)
curl -X POST "http://localhost:8001/predictions/generate?limit=20&auto_signals=true"

# Generate predictions with auto-signals AND auto-trades
curl -X POST "http://localhost:8001/predictions/generate?limit=20&auto_signals=true&auto_trades=true"
```

### Method 3: Main Trading Bot

The main trading bot (`src/main.py`) automatically:
- Generates predictions
- Creates signals
- Executes trades
- Updates portfolio

Run it with:
```bash
python src/main.py
```

## Configuration

### Signal Generation Thresholds

Edit `config/trading_params.yaml`:

```yaml
signal_generation:
  min_edge: 0.05  # 5% minimum edge
  min_confidence: 0.4  # 40% minimum confidence
  min_liquidity: 1000.0  # Minimum liquidity
```

### Auto-Processing Settings

You can configure defaults in `src/config/settings.py` or pass flags:

- `--auto-signals` / `--no-auto-signals`: Enable/disable signal generation
- `--auto-trades`: Enable automatic trade creation

## What Gets Created Automatically

### When You Generate Predictions:

1. ✅ **Predictions** → Always created
2. ✅ **Signals** → Created automatically (if edge > 5%)
3. ⚙️ **Trades** → Created if `--auto-trades` enabled
4. ✅ **Portfolio** → Updated automatically when trades change

## Example Workflow

```bash
# 1. Generate predictions (signals auto-created)
python scripts/generate_predictions.py --limit 10

# Output:
# - 10 predictions created
# - 8 signals auto-generated (for predictions with >5% edge)
# - Portfolio snapshot updated

# 2. View in UI
# - Refresh browser
# - Click "Predictions" tab → See 10 predictions
# - Click "Signals" tab → See 8 signals (auto-created!)
# - Click "Portfolio" tab → See updated portfolio
```

## Background Processing

The API supports background processing:

```bash
# Start prediction generation in background
curl -X POST "http://localhost:8001/predictions/generate?limit=50"

# Returns immediately, processes in background
```

## Processing Existing Predictions

If you have existing predictions without signals:

```bash
# Process a specific prediction
curl -X POST "http://localhost:8001/predictions/process/1?auto_signals=true&auto_trades=false"
```

Or use the script:
```bash
python scripts/generate_signals_from_predictions.py
```

## Benefits

✅ **No Manual Steps**: Everything happens automatically
✅ **Consistent**: All predictions get processed the same way
✅ **Real-time**: Signals created immediately after predictions
✅ **Configurable**: Adjust thresholds and settings
✅ **Scalable**: Works with any number of predictions

## Troubleshooting

### Signals Not Being Created

1. Check edge threshold: `config/trading_params.yaml`
2. Verify prediction has sufficient edge (>5% default)
3. Check logs for signal generation errors

### Trades Not Being Created

1. Enable `--auto-trades` flag
2. Verify signals exist first
3. Check trade creation logs

### Portfolio Not Updating

1. Portfolio updates when trades are created/closed
2. Check database for portfolio snapshots
3. Verify trades are being created

## Next Steps

1. ✅ **Generate predictions** - Signals auto-created!
2. ✅ **View in UI** - All tabs populated automatically
3. 🎯 **Configure thresholds** - Adjust in `config/trading_params.yaml`
4. 🚀 **Scale up** - Process hundreds of markets automatically!

No more manual scripts needed! 🎉

