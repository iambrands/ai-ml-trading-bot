# How Portfolio Page Works

## Overview

The Portfolio page displays portfolio snapshots that are stored in the `portfolio_snapshots` database table. These snapshots are **only created when trades are executed**.

---

## How It Works

### 1. Portfolio Endpoint

The Portfolio page uses the `/portfolio/latest` endpoint, which:
- Queries the `portfolio_snapshots` table
- Returns the **most recent** snapshot (ORDER BY snapshot_time DESC LIMIT 1)
- If no snapshot exists, returns 404

**Code**: `src/api/app.py` lines 392-410

```python
@app.get("/portfolio/latest", response_model=PortfolioSnapshotResponse)
async def get_latest_portfolio_snapshot(db: AsyncSession = Depends(get_db)):
    """Get latest portfolio snapshot."""
    query = select(PortfolioSnapshot).order_by(desc(PortfolioSnapshot.snapshot_time)).limit(1)
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No portfolio snapshot found")
    return PortfolioSnapshotResponse.model_validate(snapshot)
```

---

### 2. Portfolio Snapshot Creation

Portfolio snapshots are **only created when trades are executed**.

**Code**: `scripts/generate_predictions.py` lines 301-342

```python
async def update_portfolio_snapshot(db):
    """Update or create portfolio snapshot based on current trades."""
    # Get current OPEN trades
    open_trades = select(Trade).where(Trade.status == "OPEN")
    
    # Calculate portfolio metrics from trades
    total_exposure = sum(float(trade.size) for trade in open_trades)
    # ... calculate other metrics ...
    
    # Create or update snapshot
    snapshot = PortfolioSnapshot(...)
    db.add(snapshot)
    await db.commit()
```

**When is it called?**
- Only when `auto_create_trades=True` is enabled
- Only **after trades are created** (line 283-286 in generate_predictions.py)
- Currently, trades are **not being created** (`trades_created=0`)

---

### 3. Why Portfolio Values Don't Change

**The problem**: Portfolio snapshots are **not being created** because:

1. **Trades are not being created** (`trades_created=0`)
   - Signals are not being created (`signals_created=0`)
   - Therefore, trades cannot be created (trades require signals)
   - Therefore, portfolio snapshots cannot be created

2. **Even if trades existed**, portfolio snapshots would only update when:
   - New trades are executed
   - The `update_portfolio_snapshot()` function is called
   - Currently, this function is **only called when trades are created**

---

## Data Flow

```
Predictions → Signals → Trades → Portfolio Snapshots
     ✅          ❌        ❌           ❌
```

**Current Status**:
- ✅ Predictions: Being created (5 saved)
- ❌ Signals: Not being created (`signals_created=0`)
- ❌ Trades: Not being created (`trades_created=0`)
- ❌ Portfolio Snapshots: Cannot be created (no trades to base on)

---

## Portfolio Snapshot Data

A portfolio snapshot contains:
- `snapshot_time`: When the snapshot was taken
- `total_value`: Total portfolio value (cash + positions + unrealized P&L)
- `cash`: Available cash
- `positions_value`: Value of open positions
- `total_exposure`: Total exposure across all positions
- `daily_pnl`: Daily profit/loss
- `unrealized_pnl`: Unrealized profit/loss from open positions
- `realized_pnl`: Realized profit/loss from closed trades

---

## Why Values Haven't Changed

### Primary Reason: No Trades = No Portfolio Updates

1. **Portfolio snapshots are only created when trades exist**
   - No trades = No portfolio snapshots
   - No new trades = No new portfolio snapshots

2. **Even if a snapshot exists**, it won't update unless:
   - New trades are executed
   - `update_portfolio_snapshot()` is called
   - Currently, this only happens when trades are created

3. **The Portfolio page shows the latest snapshot**
   - If no new snapshots are created, the same snapshot is shown
   - Values appear "stuck" because they're the same snapshot

---

## Solutions

### Option 1: Fix Signal Generation (Recommended)

Fix the root cause - signals not being created:
- Check confidence thresholds
- Check volume thresholds
- Debug why signals aren't being generated

Once signals are created → Trades can be created → Portfolio snapshots will update

### Option 2: Create Manual Portfolio Snapshot

If you want to see portfolio data without trades:
1. Create a script to manually generate portfolio snapshots
2. Or modify the code to create snapshots even without trades
3. But this won't reflect real trading activity

### Option 3: Periodic Portfolio Updates

Modify the code to periodically update portfolio snapshots:
- Even if no new trades are created
- Calculate portfolio value from existing trades
- Update unrealized P&L based on current market prices

---

## Summary

**How Portfolio Works**:
1. Portfolio page shows the latest snapshot from `portfolio_snapshots` table
2. Snapshots are only created when trades are executed
3. Currently, no trades are being created
4. Therefore, no new portfolio snapshots are being created
5. The page shows the same snapshot (stale data)

**Why Values Don't Change**:
- No trades = No portfolio updates
- Even if trades existed, snapshots only update when new trades are created
- The latest snapshot is always shown (even if it's old)

**Solution**:
- Fix signal generation (so trades can be created)
- Then portfolio snapshots will update automatically

---

*Created: 2026-01-11*
*Issue: Portfolio values not changing*
*Root Cause: No trades being created (signals not being created)*


