# Portfolio Page Guide

## Overview

The Portfolio page displays a comprehensive snapshot of your trading bot's financial status, including cash, positions, exposure, and P&L metrics.

## What's Displayed

### Key Metrics

1. **Total Value** (Highlighted)
   - Your complete portfolio value
   - Formula: `Cash + Positions Value + Unrealized P&L`
   - This is your net worth in the trading system

2. **Cash**
   - Available cash balance
   - Money not currently invested in positions
   - Used for new trades

3. **Positions Value**
   - Total value of all open positions
   - Money currently invested in active trades
   - Updates as market prices change

4. **Total Exposure**
   - Total amount at risk across all positions
   - Helps track risk management limits
   - Should stay within configured limits

5. **Daily P&L**
   - Profit/Loss for the current day
   - Can be positive (green) or negative (red)
   - Resets daily

6. **Unrealized P&L**
   - Profit/Loss from open positions
   - Changes as market prices move
   - Becomes realized when positions are closed
   - Green if positive, red if negative

7. **Realized P&L**
   - Profit/Loss from closed trades
   - Locked in after positions are closed
   - Cumulative total of all completed trades
   - Green if positive, red if negative

### Portfolio Breakdown

The page also shows a detailed breakdown:
- How Total Value is calculated
- Total P&L (Realized + Unrealized)
- Last update timestamp

## Data Sources

### Database Mode (Default)
- **"Load from DB"**: Shows portfolio snapshots from your database
- Requires portfolio snapshots to be saved (happens automatically when trades are executed)
- Empty until you start trading

### Demo Mode
- **"Load Demo Data"** (Green button): Shows example portfolio data
- Based on realistic trading scenarios
- Shows what a portfolio would look like with active trading
- **Works immediately - no setup required!**

## How Portfolio Snapshots Work

Portfolio snapshots are automatically created when:
1. Trades are executed
2. Positions are opened or closed
3. The trading bot updates portfolio state

Each snapshot captures:
- Current cash balance
- All open positions and their values
- P&L metrics (daily, unrealized, realized)
- Total exposure

## Understanding the Metrics

### Total Value
Your complete portfolio worth. This is what you'd have if you closed all positions right now.

### Cash vs Positions
- **Cash**: Money available for new trades
- **Positions**: Money currently invested
- Together they make up your portfolio

### P&L Types
- **Realized P&L**: Locked in from closed trades
- **Unrealized P&L**: Potential profit/loss from open positions
- **Daily P&L**: Today's performance

### Exposure
- Total amount at risk
- Should be monitored to stay within risk limits
- Helps prevent over-leveraging

## Example Portfolio

A typical portfolio might show:
- **Total Value**: $10,500.00 (started with $10,000)
- **Cash**: $6,000.00 (60% in cash)
- **Positions Value**: $4,200.00 (40% invested)
- **Total Exposure**: $4,200.00
- **Daily P&L**: +$50.00 (up today)
- **Unrealized P&L**: +$150.00 (open positions are profitable)
- **Realized P&L**: +$350.00 (from closed trades)

## Next Steps

1. **View Demo Portfolio**: Click "Load Demo Data" to see example portfolio
2. **Start Trading**: Execute trades to generate real portfolio snapshots
3. **Monitor Performance**: Track your Total Value and P&L over time
4. **Risk Management**: Keep an eye on Total Exposure to stay within limits

The Portfolio page gives you a complete view of your trading bot's financial health! 📊💰



