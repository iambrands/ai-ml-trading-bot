# AI Analysis Feature Guide

## Overview

The AI Analysis tab provides intelligent market insights and analysis powered by machine learning and market data analysis.

## Features

### 1. Individual Market Analysis

Analyze a specific market by entering its Market ID or question.

**What it shows:**
- **Current Prices**: YES/NO prices and spread
- **Market Characteristics**: Liquidity, volatility, sentiment
- **AI Insights**: Automated analysis of market conditions
- **Risk Assessment**: Risk level and trading recommendations

**How to use:**
1. Go to AI Analysis tab
2. Enter a Market ID or question in the input field
3. Click "Analyze Market"
4. Review the comprehensive analysis

### 2. Top Markets Analysis

Get AI analysis for the top active markets automatically.

**What it shows:**
- List of top markets with:
  - Current prices (YES/NO)
  - Spread
  - Market sentiment (Bullish/Bearish/Neutral)
  - Liquidity level (High/Medium/Low)
  - Opportunity score (higher = more trading opportunity)

**How to use:**
1. Go to AI Analysis tab
2. Click "Analyze Top Markets"
3. Review the sorted list (by opportunity score)

## Understanding the Analysis

### Market Characteristics

- **Liquidity**: 
  - High: >$10k volume (easy to enter/exit)
  - Medium: $1k-$10k volume
  - Low: <$1k volume (may have slippage)

- **Volatility**:
  - High: Spread >10% (more price movement)
  - Medium: Spread 5-10%
  - Low: Spread <5% (efficient pricing)

- **Sentiment**:
  - Bullish: YES price >60% (market favors YES)
  - Bearish: YES price <40% (market favors NO)
  - Neutral: YES price 40-60% (uncertain)

### AI Insights

The AI provides automated insights such as:
- Directional bias analysis
- Probability assessments
- Market efficiency indicators
- Trading volume implications

### Risk Assessment

- **Risk Level**: High/Medium/Low based on spread and volatility
- **Recommendation**: Trading advice based on market conditions

### Opportunity Score

Higher scores indicate:
- Strong directional bias (far from 50/50)
- Better trading opportunities
- More potential edge

## API Endpoints

### Individual Market Analysis
- `GET /ai/analyze/{market_id}` - Analyze specific market

### Top Markets Analysis
- `GET /ai/analyze-top?limit=10` - Analyze top markets

## Use Cases

1. **Market Research**: Quickly understand market conditions before trading
2. **Opportunity Discovery**: Find markets with high opportunity scores
3. **Risk Assessment**: Evaluate risk before entering positions
4. **Market Comparison**: Compare multiple markets side-by-side

## Next Steps

After analyzing markets:
1. Review AI insights and risk assessment
2. Check Predictions tab for ML model predictions
3. Generate Signals if conditions are favorable
4. Execute trades based on analysis

The AI Analysis feature helps you make informed trading decisions! 🤖📊

