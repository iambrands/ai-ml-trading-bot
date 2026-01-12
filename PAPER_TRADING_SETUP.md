# Paper Trading Setup for Demo/Sharing

## Current Configuration

Your system is now configured for **Paper Trading Mode** by default, which is perfect for:
- ✅ Sharing the link with users to see performance
- ✅ Demo purposes without real money risk
- ✅ Testing strategies safely

## How It Works

### Default Setting
- `paper_trading_mode: True` (in `src/config/settings.py`)
- All trades created via cron job will be **paper trades**
- No real money is at risk
- Performance tracking works the same way

### Your Cron Job
Your current cron job URL is correct:
```
https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true
```

This will:
1. ✅ Generate predictions
2. ✅ Create signals automatically
3. ✅ Create trades automatically (as **paper trades**)

## What Users Will See

When users visit your dashboard, they'll see:
- **Markets** - Live market data from Polymarket
- **Predictions** - AI/ML model predictions
- **Signals** - Trading signals generated from predictions
- **Trades** - Paper trades (simulated, not real money)
- **Portfolio** - Performance tracking of paper trades

All trades are marked as `paper_trading=True` in the database, so:
- They're clearly identified as demo/simulated
- No real exchange connection needed
- Safe to share publicly

## Switching to Real Trading

If you want to enable real trading later:

### Option 1: Environment Variable
Set in Railway environment variables:
```
PAPER_TRADING_MODE=false
```

### Option 2: Update Settings
Change in `src/config/settings.py`:
```python
paper_trading_mode: bool = Field(default=False)  # Real trading
```

⚠️ **Warning**: Only enable real trading if you:
- Have Polymarket API keys configured
- Have sufficient capital
- Understand the risks
- Have proper risk management in place

## Verification

To verify trades are paper trading:
```sql
SELECT COUNT(*) FROM trades WHERE paper_trading = true;
SELECT COUNT(*) FROM trades WHERE paper_trading = false;
```

All new trades should have `paper_trading = true`.

## Performance Tracking

Paper trades track performance the same way as real trades:
- Entry/exit prices
- P&L calculations
- Portfolio snapshots
- All analytics work identically

The only difference is no real money is at risk.

## Sharing Your Dashboard

Your dashboard URL is safe to share:
```
https://web-production-c490dd.up.railway.app/
```

Users can:
- View live predictions
- See trading signals
- Track paper trade performance
- Monitor portfolio metrics

All without any real money being involved!

