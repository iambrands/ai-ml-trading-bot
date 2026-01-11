# Simple User Guide - How the Platform Works

## 🎯 What This Guide Is

This is a **simple, step-by-step guide** for new users who want to understand how to use the Polymarket AI Trading Bot. No technical jargon - just clear instructions on what to do.

---

## 📋 Table of Contents

1. [What Is This?](#what-is-this)
2. [How It Works (Simple Explanation)](#how-it-works-simple-explanation)
3. [Step-by-Step: What You Need to Do](#step-by-step-what-you-need-to-do)
4. [Understanding the Dashboard](#understanding-the-dashboard)
5. [Common Questions](#common-questions)

---

## What Is This?

**In simple terms**: This is an automated system that:

1. **Looks at betting markets** (like "Will it rain tomorrow?")
2. **Uses AI to guess** what the real probability is
3. **Compares** the AI's guess to what the market thinks
4. **Finds opportunities** where the AI thinks the market is wrong
5. **Places bets automatically** (if you enable it)
6. **Tracks your results**

**Real Example**:
- Market says: 30% chance it will rain (costs $0.30 to bet YES)
- AI says: 60% chance it will rain
- Opportunity: AI thinks rain is more likely than the market says
- Action: Buy YES (bet it will rain) because the AI thinks it's a good deal

---

## How It Works (Simple Explanation)

### The Big Picture Flow

```
1. Markets (Polymarket has betting markets)
   ↓
2. AI Makes Predictions (your system analyzes each market)
   ↓
3. Compare AI vs Market (find differences)
   ↓
4. Find Opportunities (where AI disagrees with market)
   ↓
5. Create Signals (trading recommendations)
   ↓
6. Execute Trades (buy/sell automatically - optional)
   ↓
7. Track Results (see your wins and losses)
```

### What Happens Automatically

Once set up, the system runs by itself:

1. **Every 5 minutes**: Checks for new markets and creates predictions
2. **When it finds opportunities**: Creates trading signals
3. **If auto-trading is on**: Places trades automatically
4. **Always**: Updates your portfolio and tracks performance

**You don't need to do anything daily** - it runs itself!

---

## Step-by-Step: What You Need to Do

### Step 1: Open the Dashboard

1. Start the API server (if running locally):
   ```bash
   uvicorn src.api.app:app --host 0.0.0.0 --port 8002
   ```

2. Open your web browser and go to:
   - Local: `http://localhost:8002/dashboard`
   - Railway (production): Your Railway URL + `/dashboard`

3. You'll see the main dashboard with tabs at the top

---

### Step 2: Explore the Markets Tab

**What you'll see**:
- A list of prediction markets from Polymarket
- Each market is a question like "Will X happen?"
- Shows market prices and details
- ✅ **This tab shows data immediately** (loads live from Polymarket)

**What to do**:
- Browse the markets to see what's available
- Click on markets to see more details (if available)
- Understand what questions are being bet on

**This shows you**: What markets the system can analyze

**Note**: This is the only tab that shows data right away because it loads live data from Polymarket. Other tabs need predictions to be generated first (see Step 3).

---

### Step 3: Check the Predictions Tab

**⚠️ IMPORTANT: This tab will be empty until you generate predictions!**

**Why it's empty**: Predictions need to be generated first by running the AI models on markets.

**How to populate it**:

#### Option 1: Use the API (Easiest)

1. Make sure your API server is running (port 8002)
2. Run this command:
   ```bash
   curl -X POST http://localhost:8002/predictions/generate
   ```
3. Wait 1-2 minutes for predictions to generate
4. Refresh the Predictions tab (or wait for auto-refresh after 30 seconds)

#### Option 2: Run Python Script

```bash
python scripts/generate_predictions.py --limit 20
```

**What you'll see after generating**:
- AI predictions for markets
- Shows:
  - **Market Question**: What's being predicted
  - **AI Prediction**: What the AI thinks (e.g., "65% chance")
  - **Market Price**: What the market thinks (e.g., "40% chance")
  - **Edge**: The difference (e.g., "+25%" means AI thinks it's undervalued)
  - **Confidence**: How confident the AI is in its prediction

**What the colors mean**:
- **Green Edge**: AI thinks YES is undervalued (good time to buy YES)
- **Red Edge**: AI thinks NO is undervalued (good time to buy NO)
- **Small Edge**: Market and AI mostly agree (not a good trade)

**This shows you**: Where the AI sees opportunities

**See**: `HOW_TO_POPULATE_TABS.md` for detailed instructions

---

### Step 4: Review the Signals Tab

**⚠️ IMPORTANT: This tab will be empty until predictions exist AND meet your criteria!**

**Why it might be empty**:
- No predictions generated yet (see Step 3)
- Predictions exist but don't meet your threshold (edge too small, confidence too low)

**How to populate it**:
1. **First**: Generate predictions (see Step 3)
2. **Then**: Signals appear automatically if predictions have edge > your threshold
3. **Check Settings**: Min Edge Threshold (default: 5%), Min Confidence (default: 60%)

**What you'll see after predictions exist**:
- Trading signals automatically generated from predictions
- Only shows signals where the edge is significant (above your threshold)
- Shows:
  - **Market**: Which market
  - **Action**: Buy YES or Buy NO
  - **Edge**: How much the AI disagrees with market
  - **Strength**: STRONG, MODERATE, or WEAK signal
  - **Suggested Size**: How much to bet (if trading)

**What to do**:
- Review signals to see opportunities
- STRONG signals are the best opportunities
- MODERATE signals are okay
- WEAK signals are less reliable

**This shows you**: Specific trading recommendations

**Note**: If predictions exist but no signals, lower your Min Edge Threshold in Settings (try 1% instead of 5%)

---

### Step 5: Monitor the Trades Tab

**⚠️ IMPORTANT: This tab will be empty until trades are created!**

**Why it's empty**:
- No signals exist yet (see Step 4)
- Signals exist but auto-trading not enabled
- Trades only created when you use `--auto-trades` flag

**How to populate it**:

Trades are created automatically from signals, but you must enable auto-trading:

```bash
# Generate predictions AND create trades automatically
curl -X POST "http://localhost:8002/predictions/generate?auto_trades=true"
```

Or:

```bash
python scripts/generate_predictions.py --auto-trades
```

**What you'll see after trades are created**:
- All trades that have been executed
- Shows:
  - **Market**: What you bet on
  - **Side**: YES or NO (what you bet)
  - **Entry Price**: Price when you entered
  - **Size**: How much you bet
  - **Status**: OPEN (still active) or CLOSED (resolved)
  - **P&L**: Profit or Loss (if closed)

**What to do**:
- Check your active trades
- See which trades are winning or losing
- Wait for markets to resolve to see final results

**This shows you**: Your actual trading activity

**Note**: By default, trades are NOT created automatically (for safety). You must explicitly enable `--auto-trades`.

---

### Step 6: Check the Portfolio Tab

**⚠️ IMPORTANT: This tab will be empty until trades exist!**

**Why it's empty**:
- No trades exist yet (see Step 5)
- Portfolio is built from trades

**How to populate it**:
1. **First**: Create trades (see Step 5)
2. **Then**: Portfolio updates automatically

**What you'll see after trades exist**:
- Overall account performance
- Shows:
  - **Total Value**: Your current account value
  - **Cash**: Money not invested
  - **Positions Value**: Money in active bets
  - **Total P&L**: Total profit or loss
  - **Daily P&L**: Today's profit or loss

**What to do**:
- Monitor your overall performance
- See if you're making or losing money
- Check daily performance trends

**This shows you**: Your account summary and performance

---

### Step 7: Configure Settings (Important!)

Click on the **Settings** tab:

#### A. Trading Mode
- **Test Mode**: Practice with simulated money (default - recommended to start)
- **Live Mode**: Trade with real money (only when ready)

**Start with Test Mode** until you understand how it works!

#### B. Connect Wallet (for Live Mode only)
- Click "Connect Wallet" button
- Connect MetaMask (or other wallet)
- Only needed if you want to trade with real money

#### C. Fund Account
- In **Test Mode**: Enter amount (simulated)
- In **Live Mode**: Deposit real funds via MetaMask
- Start small! $100-500 is good for testing

#### D. Trading Preferences
- **Risk Level**: 
  - Conservative (safer, fewer trades)
  - Moderate (balanced)
  - Aggressive (more trades, higher risk)
- **Max Position Size**: Maximum % of portfolio per bet (default: 5%)
- **Min Edge Threshold**: Only trade if edge exceeds this (default: 5%)
- **Min Confidence**: Only trade if confidence exceeds this (default: 60%)

**Recommendation for beginners**: Use Conservative risk, 5% max position, 5% min edge

#### E. Save Preferences
- Click "Save Preferences" button
- Your settings are now active

---

## Understanding the Dashboard

### The Tabs (Left to Right)

1. **Markets**: See what markets are available
2. **Predictions**: See what the AI predicts
3. **Signals**: See trading opportunities
4. **Trades**: See your actual trades
5. **Portfolio**: See your account status
6. **Settings**: Configure the system
7. **Help & FAQ**: Get help and answers

### Data Refresh

- **Auto-refresh**: Data updates automatically every 30 seconds
- **Manual refresh**: Click "Refresh Now" button if needed
- **Last updated**: See timestamp at bottom of each tab

### Display Limits

- Each tab shows up to 50 items by default
- You can change the limit (10-100)
- Tooltip shows the range when you hover over the limit input

---

## Common Questions

### Q: Do I need to do anything daily?

**A**: No! Once set up, the system runs automatically:
- Generates predictions every 5 minutes
- Creates signals when opportunities are found
- Executes trades if auto-trading is enabled
- Updates portfolio automatically

**You only need to**:
- Check your portfolio weekly/monthly
- Review settings occasionally
- Adjust preferences if needed

### Q: How do I start trading?

**A**: Step-by-step:

1. Start in **Test Mode** (Settings tab)
2. Set your preferences (risk level, limits)
3. Review Predictions and Signals tabs to understand what the system does
4. Monitor Trades and Portfolio to see results
5. Once comfortable, switch to **Live Mode**
6. Connect wallet and deposit funds
7. Enable auto-trading (if you want automatic trades)

**Important**: Start with Test Mode and small amounts!

### Q: What's the difference between Test Mode and Live Mode?

**A**:

**Test Mode**:
- Simulated trading (no real money)
- Practice without risk
- Learn how the system works
- See how trades would perform
- **Recommended for beginners**

**Live Mode**:
- Real trading with real money
- Requires wallet connection (MetaMask)
- Requires real funds deposit
- Actual profits and losses
- **Only use when you're ready**

### Q: How does the system decide when to trade?

**A**: The system trades when:

1. **Edge > Minimum Threshold**: AI disagrees with market by at least your minimum (default: 5%)
2. **Confidence > Minimum**: AI is confident in its prediction (default: 60%)
3. **Risk Checks Pass**: All risk limits are within bounds
4. **Liquidity Available**: Market has enough volume to trade

If all conditions are met, it creates a signal and (if auto-trading is on) executes a trade.

### Q: How do I know if it's working?

**A**: Check these signs:

1. **Predictions Tab**: Shows predictions with edges
2. **Signals Tab**: Shows trading signals (if opportunities exist)
3. **Trades Tab**: Shows executed trades (if auto-trading is on)
4. **Portfolio Tab**: Shows account value and P&L
5. **Last Updated**: Timestamp shows recent activity

If you see new predictions every 5 minutes, it's working!

### Q: What if I see no data?

**A**: This is normal! Here's why each tab might be empty:

1. **Markets Tab**: Should show data (loads live from Polymarket)
   - If empty: Check API server is running

2. **Predictions Tab**: Empty until you generate predictions
   - **Solution**: Run `curl -X POST http://localhost:8002/predictions/generate`
   - See `HOW_TO_POPULATE_TABS.md` for details

3. **Signals Tab**: Empty until predictions exist AND meet criteria
   - **Solution**: Generate predictions first
   - If still empty: Lower Min Edge Threshold in Settings

4. **Trades Tab**: Empty until trades are created
   - **Solution**: Use `--auto-trades` flag: `curl -X POST "http://localhost:8002/predictions/generate?auto_trades=true"`

5. **Portfolio Tab**: Empty until trades exist
   - **Solution**: Create trades first (see Trades Tab)

**Check**: Look at "Last updated" timestamp - if it's old, predictions haven't been generated

### Q: How much should I start with?

**A**: Recommendations:

- **Test Mode**: Any amount (simulated) - try $1,000 to $10,000
- **Live Mode**: Start small
  - Beginners: $100 - $500
  - Experienced: $1,000 - $5,000
  - **Never trade more than you can afford to lose!**

### Q: How do I stop trading?

**A**: To pause trading:

1. Go to **Settings** tab
2. Change **Trading Mode** to **Test Mode** (even if you were in Live Mode)
3. Or change **Risk Level** to most conservative settings
4. Or reduce **Max Position Size** to 0%

The system will stop creating new trades but will continue tracking existing positions.

### Q: What if a trade is losing?

**A**: This is normal! Here's what to know:

- **Not all trades win** - even the best systems lose sometimes
- **Markets resolve over time** - wait for resolution before judging
- **Diversification helps** - multiple trades reduce risk
- **Check your risk limits** - system stops trading if losses get too high

**Remember**: Past performance doesn't guarantee future results. Losses are part of trading.

---

## Quick Start Checklist

For new users, here's the order to do things:

### Phase 1: Learn (Day 1-3)
- [ ] Open dashboard and explore Markets tab
- [ ] Review Predictions tab to see AI predictions
- [ ] Check Signals tab to see trading opportunities
- [ ] Read Help & FAQ tab for detailed explanations
- [ ] Keep Trading Mode on **Test Mode**

### Phase 2: Configure (Day 4-5)
- [ ] Go to Settings tab
- [ ] Set Risk Level to **Conservative**
- [ ] Set Max Position Size to **5%**
- [ ] Set Min Edge to **5%**
- [ ] Set Min Confidence to **60%**
- [ ] Save preferences

### Phase 3: Test (Week 1-2)
- [ ] Monitor Predictions tab daily
- [ ] Review Signals tab to see opportunities
- [ ] Check Trades tab (may be empty if no auto-trading)
- [ ] Review Portfolio tab weekly
- [ ] Understand how the system behaves

### Phase 4: Go Live (Week 3+, when ready)
- [ ] Switch to **Live Mode** in Settings
- [ ] Connect MetaMask wallet
- [ ] Deposit small amount ($100-500)
- [ ] Monitor closely for first week
- [ ] Gradually increase if comfortable

---

## Important Reminders

### ⚠️ Before Going Live

1. **Understand the risks** - Trading involves risk of loss
2. **Start small** - Never trade more than you can afford to lose
3. **Test first** - Use Test Mode until you're comfortable
4. **Read documentation** - Understand how the system works
5. **Monitor regularly** - Check your portfolio frequently

### ✅ Best Practices

1. **Start conservative** - Use low risk settings initially
2. **Diversify** - Don't bet everything on one market
3. **Be patient** - Markets take time to resolve
4. **Track performance** - Review what's working and what's not
5. **Adjust gradually** - Change settings slowly, not all at once

### 🎯 Success Tips

1. **Let it run** - Don't overthink, let the system do its job
2. **Focus on edges** - Bigger edges = better opportunities
3. **Trust the system** - It's designed to be objective
4. **Review weekly** - Check performance, not daily
5. **Learn continuously** - Read signals and predictions to understand patterns

---

## Need More Help?

- **Help & FAQ Tab**: Detailed explanations of each feature
- **Platform Overview**: High-level explanation of the system
- **Technical Architecture**: For advanced users wanting technical details
- **User Guide**: Comprehensive guide with all details

---

## Summary

**In the simplest terms**:

1. **Open the dashboard** → See what's happening
2. **Check Predictions** → See what the AI thinks
3. **Review Signals** → See trading opportunities
4. **Monitor Trades** → See what you've bet on
5. **Track Portfolio** → See your performance
6. **Adjust Settings** → Configure your preferences

**The system runs automatically** - you just need to:
- Set it up once
- Configure your preferences
- Monitor weekly/monthly
- Adjust settings as needed

**Start with Test Mode, learn how it works, then go Live when ready!**

---

*Remember: This is a tool to help you trade. It's not a guarantee of profits. Always trade responsibly and within your means.*

