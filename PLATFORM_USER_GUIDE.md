# Platform User Guide

## 📖 Table of Contents

1. [What Is This Platform?](#what-is-this-platform)
2. [How Does It Work? (Simple Overview)](#how-does-it-work-simple-overview)
3. [The Complete Workflow](#the-complete-workflow)
4. [Understanding Each Component](#understanding-each-component)
5. [Page-by-Page Guide](#page-by-page-guide)
6. [Getting Started](#getting-started)
7. [Common Questions](#common-questions)

---

## What Is This Platform?

**Polymarket AI Trading Bot** is an automated system that:

1. **Analyzes prediction markets** on Polymarket (like betting on whether events will happen)
2. **Uses AI/ML models** to predict the true probability of events
3. **Finds opportunities** where the AI thinks the market price is wrong
4. **Generates trading signals** when there's a good opportunity
5. **Executes trades** automatically (if enabled)
6. **Tracks performance** in your portfolio

### Real-World Example

Imagine a market asking: **"Will it rain tomorrow?"**

- **Market says**: 30% chance (YES costs $0.30)
- **Your AI model says**: 60% chance (it thinks it's more likely to rain)
- **Opportunity**: The AI sees a 30% "edge" - the market is undervaluing rain
- **Action**: Buy YES shares (bet it will rain) because the AI thinks it's undervalued

That's the core concept - finding markets where your AI disagrees with the crowd.

---

## How Does It Work? (Simple Overview)

### The Big Picture

```
1. Markets (Polymarket) 
   ↓
2. AI Models Predict Probabilities
   ↓
3. Compare AI vs Market Price
   ↓
4. Find Opportunities (Edge)
   ↓
5. Generate Trading Signals
   ↓
6. Execute Trades (Optional)
   ↓
7. Track Performance
```

### Step-by-Step in Plain English

**Step 1: Get Markets** ✅
- The system fetches active prediction markets from Polymarket
- These are questions like "Will X happen?" with YES/NO betting
- **Automated**: Every 5 minutes via cron job

**Step 2: AI Makes Predictions** ✅
- Your trained ML models analyze each market
- They consider: news, social media, market data, historical patterns
- They output: "I think there's a 65% chance this happens"
- **Automated**: Runs automatically with prediction generation

**Step 3: Find the Edge** ✅
- Compare AI prediction (65%) vs Market price (40%)
- Edge = 65% - 40% = 25% opportunity
- If edge > 5%, there's a potential trade
- **Automated**: Calculated automatically for each prediction

**Step 4: Create Signals** ✅
- System automatically creates a "signal" when edge is significant
- Signal says: "Buy YES, edge is 25%, confidence is high"
- **Automated**: Signals created automatically when criteria met

**Step 5: Execute Trades** ✅
- **Automated**: Trades created automatically from signals (paper trading mode)
- All trades are paper trades by default (safe for demo)
- Real trading requires API keys and explicit enablement

**Step 6: Track Results** ✅
- Monitor open positions
- See profit/loss when markets resolve
- Portfolio shows overall performance
- **Automated**: Portfolio snapshots updated automatically

---

## The Complete Workflow

### Phase 1: Setup (One-Time)

**Production (Railway)**: ✅ Already set up! Models are trained and deployed. System is running automatically.

**Local Development**:

1. **Train Models** (if not already done)
   ```bash
   python scripts/train_models.py
   ```
   - This trains AI models on historical data
   - Models learn patterns from past markets
   - Takes time (hours), but only needed once or periodically

2. **Run Database Migration** (for new features)
   ```bash
   psql $DATABASE_URL -f src/database/migrations/add_alerts_and_paper_trading.sql
   ```
   - Adds alerts, paper trading, and analytics tables
   - Required for alerts, paper trading, and analytics features

2. **Start API Server**
   ```bash
   uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
   ```

3. **Open Browser**
   - Go to: http://localhost:8001/
   - You'll see the dashboard

### Phase 2: Generate Predictions (Fully Automated) ✅

**Production (Railway)**: ✅ **FULLY AUTOMATED** - No manual action needed!

**What**: System automatically analyzes markets and creates predictions

**How It Works**:
- ✅ Cron job runs every 5 minutes
- ✅ Calls: `POST /predictions/generate?limit=20&auto_signals=true&auto_trades=true`
- ✅ Runs in background (no timeouts)
- ✅ Fully automated - "set it and forget it"

**What Happens Automatically**:
1. ✅ Fetches 20 active markets from Polymarket
2. ✅ For each market:
   - Gathers news, social media data
   - Generates features (sentiment, market data, etc.)
   - Runs AI models to predict probability
   - Compares prediction vs market price
   - Calculates edge (opportunity)
3. ✅ Saves predictions to database
4. ✅ **Automatically** creates signals if edge > 5%
5. ✅ **Automatically** creates trades (paper trading mode)
6. ✅ **Automatically** updates portfolio snapshot
7. ✅ **Automatically** sends alerts if configured

**Frequency**: ✅ Every 5 minutes automatically - no manual intervention needed!

**Local Development** (if running locally):
```bash
python scripts/generate_predictions.py --limit 20 --auto-signals --auto-trades
```

### Phase 3: View Results (In Browser)

1. **Markets Tab**
   - Click "Load Live Data" to see current markets
   - Browse available prediction markets

2. **Predictions Tab**
   - Click "Load from DB" to see AI predictions
   - See: Model probability, Market price, Edge, Confidence
   - **Green edge** = AI thinks YES is undervalued
   - **Red edge** = AI thinks NO is undervalued

3. **Signals Tab**
   - Click "Load from DB" to see trading signals
   - Signals are automatically created from predictions
   - **STRONG** signals = best opportunities (>15% edge)
   - **MEDIUM** signals = good opportunities (10-15% edge)
   - **WEAK** signals = small opportunities (5-10% edge)

4. **Trades Tab**
   - Click "Load from DB" to see executed trades
   - **OPEN** = Active positions
   - **CLOSED** = Completed trades (with P&L)
   - Monitor your active positions here

5. **Portfolio Tab**
   - Click "Load from DB" to see overall performance
   - **Total Value** = Your entire portfolio worth
   - **Cash** = Available money for new trades
   - **P&L** = Profit/Loss (realized + unrealized)

6. **AI Analysis Tab**
   - Select any page → Click "Explain This Page"
   - Get detailed explanations of what you're seeing

### Phase 4: Monitor & Adjust (Ongoing)

- **Daily**: Run `generate_predictions.py` to find new opportunities
- **Regularly**: Check Signals tab for new trading opportunities
- **Monitor**: Watch Trades tab for open positions
- **Review**: Check Portfolio tab for performance
- **Adjust**: Modify thresholds, position sizes, etc. based on results

---

## Understanding Each Component

### 1. Markets
**What**: Prediction markets from Polymarket

**Example**: "Will Bitcoin reach $100k by end of 2024?"
- YES price: $0.45 (45% chance)
- NO price: $0.55 (55% chance)

**Purpose**: These are the opportunities you're analyzing

### 2. Predictions
**What**: AI model's estimate of true probability

**Example**: 
- Market says: 45% chance
- AI model says: 70% chance
- **Edge**: 25% (AI thinks it's undervalued)

**Purpose**: Identify where markets might be wrong

### 3. Signals
**What**: Trading recommendations based on predictions

**Example**:
- Prediction has 25% edge
- System creates signal: "Buy YES, STRONG signal"
- Signal strength based on edge size

**Purpose**: Convert predictions into actionable trades

### 4. Trades
**What**: Actual positions you've opened

**Example**:
- Opened: YES position at $0.45
- Size: $100
- Status: OPEN (waiting for resolution)

**Purpose**: Track your active positions

### 5. Portfolio
**What**: Overall trading performance

**Example**:
- Total Value: $10,500
- Cash: $9,000
- Positions: $1,500
- P&L: +$500

**Purpose**: Monitor overall strategy performance

---

## Page-by-Page Guide

### 📊 Markets Page

**What it shows**: All available prediction markets from Polymarket

**How to use**:
1. Click **"Load Live Data"** to fetch current markets
2. Browse markets to find interesting questions
3. Markets are saved when you generate predictions

**What to look for**:
- Markets with clear, specific questions
- Active markets (not closed)
- Markets with good liquidity

**Key fields**:
- **Question**: What the market is predicting
- **YES Price**: Cost to bet YES (0-100%)
- **NO Price**: Cost to bet NO (0-100%)
- **Outcome**: ACTIVE, RESOLVED, or CLOSED

---

### 🔮 Predictions Page

**What it shows**: AI model predictions for markets

**How to use**:
1. Click **"Load from DB"** to see saved predictions
2. Look for predictions with:
   - **High edge** (>10%) = model sees opportunity
   - **High confidence** (>60%) = model is sure

**Understanding the data**:
- **Model Probability**: What the AI thinks (0-100%)
- **Market Price**: Current market price
- **Edge**: Difference (positive = opportunity)
- **Confidence**: How sure the model is

**What happens next**:
- Predictions with edge >5% automatically generate signals

**Example**:
```
Question: "Will it rain tomorrow?"
Model Probability: 75%
Market Price: 45%
Edge: +30% ✅ (Big opportunity!)
Confidence: 85% ✅ (Model is very sure)
→ This will create a STRONG signal
```

---

### 📡 Signals Page

**What it shows**: Trading signals generated from predictions

**How to use**:
1. Click **"Load from DB"** to see signals
2. Focus on **STRONG signals** (best opportunities)
3. Signals are automatically created from predictions

**Understanding the data**:
- **Side**: YES (bet it happens) or NO (bet it doesn't)
- **Strength**: Based on edge size
  - **STRONG**: >15% edge (best opportunities)
  - **MEDIUM**: 10-15% edge (good opportunities)
  - **WEAK**: 5-10% edge (small opportunities)
- **Edge**: Opportunity percentage
- **Executed**: Whether a trade was opened

**What happens next**:
- Signals can be automatically converted to trades (if enabled)
- Or you can review and execute manually

**Example**:
```
Question: "Will it rain tomorrow?"
Side: YES
Strength: STRONG (30% edge)
Edge: 30%
Executed: No (not yet traded)
→ Consider opening a trade
```

---

### 💼 Trades Page

**What it shows**: All executed trades

**How to use**:
1. Click **"Load from DB"** to see trades
2. Monitor **OPEN trades** for active positions
3. Review **P&L** on closed trades

**Understanding the data**:
- **Side**: YES or NO position
- **Entry Price**: Price when trade opened
- **Size**: Position size in USD
- **Status**: OPEN, CLOSED, or CANCELLED
- **P&L**: Profit/Loss (shown when closed)

**What happens next**:
- Closed trades contribute to portfolio P&L
- Monitor open trades until markets resolve

**Example**:
```
Question: "Will it rain tomorrow?"
Side: YES
Entry Price: 45%
Size: $100
Status: OPEN
P&L: - (not resolved yet)
→ Waiting for market to resolve
```

---

### 💰 Portfolio Page

**What it shows**: Overall portfolio performance

**How to use**:
1. Click **"Load from DB"** to see portfolio
2. Monitor **Total Value** for overall performance
3. Track **P&L** to see if strategy is working

**Understanding the data**:
- **Total Value**: Entire portfolio (cash + positions + P&L)
- **Cash**: Money available for new trades
- **Positions Value**: Current value of open positions
- **Total Exposure**: Amount at risk
- **Daily P&L**: Profit/Loss today
- **Unrealized P&L**: Profit/Loss on open positions
- **Realized P&L**: Profit/Loss on closed trades

**Example**:
```
Total Value: $10,500
Cash: $9,000
Positions: $1,500
Exposure: $1,500
Daily P&L: +$50
Unrealized P&L: +$200 (open positions up)
Realized P&L: +$300 (closed trades profit)
→ Overall doing well!
```

---

### 🤖 AI Analysis Page

**What it shows**: Explanations of each page

**How to use**:
1. Select a page from the dropdown
2. Click **"Explain This Page"**
3. Read the explanation to understand the data

**Features**:
- Explains what you're seeing
- Interprets the metrics
- Provides usage tips
- Shows summary statistics

---

## Getting Started - Simple User Flow

### 🚀 Quick Start (5 Minutes)

**Step 1: Open the App**
- Navigate to the platform URL (provided by your administrator)
- You'll see the dashboard with 6 tabs

**Step 2: Connect Your Wallet**
- Click "Connect Wallet" button (top right)
- Choose your wallet provider (MetaMask, WalletConnect, etc.)
- Approve the connection
- ✅ Your wallet is now connected

**Step 3: Fund Your Account**
- Go to **Portfolio** tab
- Click "Deposit" or "Add Funds"
- Enter amount you want to trade with
- Confirm transaction
- ✅ Your account is funded

**Step 4: Set Your Preferences**
- Go to **Settings** (gear icon) or **Preferences** tab
- Configure:
  - **Trading Mode**: Auto-trade (recommended) or Manual review
  - **Risk Level**: Conservative, Moderate, or Aggressive
  - **Max Position Size**: Maximum $ per trade
  - **Min Edge Threshold**: Minimum edge to trade (default: 10%)
  - **Min Confidence**: Minimum confidence level (default: 60%)
- Click "Save Preferences"
- ✅ Your preferences are saved

**Step 5: Activate Auto-Trading**
- Toggle "Auto-Trading" to ON
- Confirm you understand the risks
- ✅ The system is now running automatically!

**That's it!** The app will now:
- ✅ Automatically analyze markets
- ✅ Generate predictions
- ✅ Create trading signals
- ✅ Execute trades (if auto-trading enabled)
- ✅ Update your portfolio

---

## Simple Step-by-Step User Flow

### First Time User Journey

#### 1️⃣ **Start Here: Markets Tab**

**What you see**: List of available prediction markets

**What to do**:
- Browse markets to see what's available
- Markets are automatically loaded
- No action needed - just explore!

**Example**: You see "Will Bitcoin reach $100k by end of 2024?"

---

#### 2️⃣ **Check: Predictions Tab**

**What you see**: AI model predictions for markets

**What to do**:
- Click "Load from DB" to see predictions
- The system automatically generates these
- Look for predictions with **green edge** (opportunities)

**What to look for**:
- ✅ **High Edge** (>10%) = Good opportunity
- ✅ **High Confidence** (>60%) = Model is sure
- ✅ **Green Edge** = AI thinks YES is undervalued

**Example**:
```
Question: "Will Bitcoin reach $100k?"
Model Probability: 75%
Market Price: 45%
Edge: +30% ✅ (Big opportunity!)
Confidence: 85% ✅
```

**No action needed** - Just review to understand what the AI is thinking!

---

#### 3️⃣ **Review: Signals Tab**

**What you see**: Trading signals (recommendations)

**What to do**:
- Click "Load from DB" to see signals
- Signals are automatically created from predictions
- Focus on **STRONG** signals (best opportunities)

**What you see**:
- **STRONG** signals = Best opportunities (>15% edge)
- **MEDIUM** signals = Good opportunities (10-15% edge)
- **WEAK** signals = Small opportunities (5-10% edge)

**If Auto-Trading is ON**: Signals automatically become trades
**If Auto-Trading is OFF**: Review signals and execute manually

**Example**:
```
Signal: "Buy YES on Bitcoin $100k market"
Strength: STRONG (30% edge)
Status: Executed ✅ (if auto-trading)
```

---

#### 4️⃣ **Monitor: Trades Tab**

**What you see**: Your active and completed trades

**What to do**:
- Click "Load from DB" to see your trades
- Monitor **OPEN** trades (active positions)
- Review **CLOSED** trades (completed with P&L)

**What you see**:
- **OPEN** = Active positions waiting for market resolution
- **CLOSED** = Completed trades showing profit/loss
- **P&L** = How much you made or lost

**No action needed** - Just monitor your positions!

**Example**:
```
Trade: "Bitcoin $100k - YES"
Entry Price: 45%
Size: $100
Status: OPEN
Current Value: $150
Unrealized P&L: +$50 ✅
```

---

#### 5️⃣ **Track: Portfolio Tab**

**What you see**: Your overall trading performance

**What to do**:
- Click "Load from DB" to see your portfolio
- Monitor **Total Value** (your net worth)
- Track **P&L** (profit/loss)

**Key Metrics**:
- **Total Value**: Your entire portfolio worth
- **Cash**: Available money for new trades
- **Positions**: Value of open positions
- **Daily P&L**: Profit/loss today
- **Total P&L**: Overall profit/loss

**No action needed** - Just review your performance!

**Example**:
```
Total Value: $10,500
Cash: $9,000
Positions: $1,500
Daily P&L: +$50 ✅
Total P&L: +$500 ✅
```

---

#### 6️⃣ **Get Help: AI Analysis Tab**

**What you see**: Explanations of each page

**What to do**:
- Select any page from dropdown
- Click "Explain This Page"
- Read the explanation

**Use this when**: You're confused about what something means!

---

## Set It and Forget It Workflow

### For Users Who Want Full Automation

**Initial Setup (One Time)**:

1. **Connect Wallet** → Approve connection
2. **Fund Account** → Deposit trading capital
3. **Set Preferences**:
   - Trading Mode: **Auto-trade**
   - Risk Level: Choose your comfort level
   - Max Position Size: Set your limit
   - Min Edge: 10% (default)
   - Min Confidence: 60% (default)
4. **Activate Auto-Trading** → Toggle ON

**That's it!** The system now runs automatically:

✅ **Every Hour/Day**: System analyzes new markets
✅ **Automatically**: Generates predictions
✅ **Automatically**: Creates trading signals
✅ **Automatically**: Executes trades (if edge > threshold)
✅ **Automatically**: Updates portfolio

**You just need to**:
- Check Portfolio tab occasionally
- Review Trades tab to see what's happening
- Adjust preferences if needed

**No daily tasks required!**

---

## Daily Check-In (Optional)

If you want to monitor actively:

**Morning (5 minutes)**:
1. Open **Portfolio** tab → See overnight performance
2. Open **Trades** tab → Check open positions
3. Open **Signals** tab → See new opportunities

**Evening (5 minutes)**:
1. Open **Portfolio** tab → Review daily P&L
2. Open **Trades** tab → See any closed trades
3. Open **Predictions** tab → Understand what AI is thinking

**That's it!** Everything else is automated.

---

## User Preferences Explained

### Trading Mode

**Auto-Trade** (Recommended):
- System automatically executes trades
- No manual intervention needed
- Best for "set it and forget it"

**Manual Review**:
- System generates signals
- You review and approve each trade
- More control, but requires daily check-ins

### Risk Level

**Conservative**:
- Smaller position sizes
- Only STRONG signals (>15% edge)
- Lower risk, lower returns

**Moderate** (Recommended):
- Medium position sizes
- STRONG and MEDIUM signals (>10% edge)
- Balanced risk/return

**Aggressive**:
- Larger position sizes
- All signals (>5% edge)
- Higher risk, higher potential returns

### Max Position Size

**What it means**: Maximum $ you'll bet on a single trade

**Examples**:
- $100 = Small positions, many trades
- $500 = Medium positions, moderate trades
- $1,000+ = Large positions, fewer trades

**Recommendation**: Start with 1-2% of your total capital per trade

### Min Edge Threshold

**What it means**: Minimum edge required to create a signal

**Examples**:
- 5% = More signals, smaller opportunities
- 10% = Balanced (recommended)
- 15% = Fewer signals, bigger opportunities

### Min Confidence

**What it means**: Minimum confidence level required

**Examples**:
- 50% = More trades, less certainty
- 60% = Balanced (recommended)
- 70% = Fewer trades, high certainty

---

## Common Questions

### Q: Why are some buttons unclickable?
**A**: All buttons are clickable! Try:
- "Load from DB" - loads saved data
- "Load Live Data" - fetches from API (Markets tab)
- "Refresh" - reloads current data

### Q: How do predictions get generated?
**A**: The system runs automatically! You don't need to do anything. The app:
- Analyzes markets every hour/day (automatically)
- Generates predictions (automatically)
- Creates signals (automatically)
- Executes trades (if auto-trading is ON)

### Q: Why don't I see data?
**A**: 
1. Make sure your wallet is connected
2. Make sure your account is funded
3. Make sure auto-trading is activated
4. Wait a few minutes for the system to analyze markets
5. Click "Load from DB" on each tab to refresh

### Q: What's the difference between predictions and signals?
**A**:
- **Predictions**: AI model's probability estimates
- **Signals**: Trading recommendations (created from predictions with edge >5%)

### Q: How do trades get created?
**A**: 
- **Automatically**: If auto-trading is ON, trades execute automatically when signals are created
- **Manually**: If auto-trading is OFF, review signals in Signals tab and execute manually

### Q: What is "edge"?
**A**: Edge is the difference between:
- What the AI thinks (model probability)
- What the market thinks (market price)
- **Positive edge** = AI thinks market is undervalued (opportunity)
- **Higher edge** = Better opportunity

### Q: What is "confidence"?
**A**: How sure the AI model is in its prediction:
- **High confidence** (>60%) = Model is very sure
- **Low confidence** (<40%) = Model is uncertain
- Use with edge: High edge + high confidence = best trades

### Q: How often does the system analyze markets?
**A**: 
- The system runs automatically in the background
- Typically analyzes markets every hour or daily (configurable)
- You don't need to do anything - it's automatic!

### Q: Do I need to train models?
**A**: 
- **No!** Models are pre-trained and ready to use
- The system uses trained models automatically
- You don't need to do anything with models

### Q: What if I don't see any data yet?
**A**: 
1. Make sure wallet is connected
2. Make sure account is funded
3. Make sure auto-trading is activated
4. Wait 5-10 minutes for first analysis cycle
5. Click "Load from DB" on each tab

### Q: How do I know if it's working?
**A**: Check:
1. **Predictions tab**: Should show predictions with edges
2. **Signals tab**: Should show signals (if edge >5%)
3. **Trades tab**: Should show trades (if auto-trading enabled)
4. **Portfolio tab**: Should show portfolio value

---

## Key Concepts Explained

### Edge (Opportunity)
- **What it is**: Difference between model prediction and market price
- **Positive edge**: Model thinks market is undervalued (opportunity)
- **Negative edge**: Model thinks market is overvalued
- **Higher edge = Better opportunity**

**Example**:
- Market: 40% chance
- AI Model: 70% chance
- Edge: +30% (big opportunity!)

### Signal Strength
- **STRONG**: >15% edge (best opportunities)
- **MEDIUM**: 10-15% edge (good opportunities)
- **WEAK**: 5-10% edge (small opportunities)

### Confidence
- **What it is**: How sure the model is
- **High confidence** (>60%): Model is very sure
- **Low confidence** (<40%): Model is uncertain
- **Use with edge**: High edge + high confidence = best trades

### Position Sizing
- **What it is**: How much money to bet on each trade
- **Based on**: Edge, confidence, portfolio size
- **Risk management**: Never bet more than you can afford to lose

---

## Typical User Journey Example

### Scenario: New User Sets Up and Trades

**Day 1 - Setup (10 minutes)**:

1. **User opens app** → Sees dashboard
2. **Connects wallet** → MetaMask approved
3. **Funds account** → Deposits $10,000
4. **Sets preferences**:
   - Trading Mode: Auto-trade ✅
   - Risk Level: Moderate
   - Max Position: $200
   - Min Edge: 10%
   - Min Confidence: 60%
5. **Activates auto-trading** → System is live!

**Day 1 - System Runs Automatically**:

- System analyzes 50 markets
- Finds 5 opportunities with edge >10%
- Creates 5 STRONG signals
- Executes 5 trades automatically
- User doesn't need to do anything!

**Day 2 - User Checks In (2 minutes)**:

1. **Opens Portfolio tab**:
   - Total Value: $10,150
   - Daily P&L: +$150 ✅
   - 5 open positions

2. **Opens Trades tab**:
   - Sees 5 OPEN trades
   - All showing positive unrealized P&L
   - No action needed

**Day 3 - Market Resolves**:

1. **User opens Trades tab**:
   - 1 trade closed: +$45 profit ✅
   - 4 trades still open
   - Portfolio updated automatically

2. **User opens Portfolio tab**:
   - Total Value: $10,195
   - Realized P&L: +$45
   - Unrealized P&L: +$120

**Week 1 - Review**:

- User checks Portfolio tab
- Total Value: $10,500
- Total P&L: +$500 (5% return)
- System continues running automatically
- User hasn't done anything since Day 1!

---

## What Happens Behind the Scenes (Fully Automated) ✅

**Every 5 Minutes** (fully automated via cron job - you don't need to do anything):

1. ✅ System fetches new markets from Polymarket
2. ✅ AI models analyze each market
3. ✅ System generates predictions automatically
4. ✅ System calculates edge (opportunity)
5. ✅ System creates signals for opportunities automatically
6. ✅ System creates trades automatically (paper trading mode)
7. ✅ System updates portfolio automatically
8. ✅ System tracks performance automatically
9. ✅ System sends alerts if configured

**Current Status**: ✅ **FULLY AUTOMATED** - Running on Railway with cron job every 5 minutes

**Cron Job URL**: 
```
https://web-production-c490dd.up.railway.app/predictions/generate?limit=20&auto_signals=true&auto_trades=true
```

**You just check the results!** The system runs completely automatically - perfect for "set it and forget it" operation.

---

## Tips for Success

1. **Start Small**: Test with small position sizes first
2. **Focus on Quality**: Look for STRONG signals with high confidence
3. **Monitor Performance**: Check Portfolio regularly
4. **Use AI Analysis**: Get explanations when confused
5. **Automate**: Let the system generate signals automatically
6. **Be Patient**: Markets take time to resolve
7. **Manage Risk**: Never bet more than you can afford

---

## Need More Help?

- **AI Analysis Tab**: Select any page → Click "Explain This Page"
- **This Guide**: Read through each section
- **API Documentation**: See `API_DOCUMENTATION.md`
- **Training Guide**: See `TRAINING_GUIDE.md`

---

**Happy Trading!** 🎉
