# Demo Data Guide

## Overview

All tabs (Markets, Predictions, Signals, Trades) now support **demo data** that you can view immediately without training models or executing trades!

## How It Works

### Markets Tab
- **"Load from DB"**: Shows markets saved in your database
- **"Load Live Data"** (Green button): Fetches real-time markets from Polymarket API
- **Works immediately** - no setup required!

### Predictions Tab
- **"Load from DB"**: Shows ML model predictions from your database
- **"Load Demo Data"** (Green button): Shows example predictions based on live markets
- Demo predictions show what real predictions would look like (model probability vs market price, edge, confidence)

### Signals Tab
- **"Load from DB"**: Shows trading signals from your database
- **"Load Demo Data"** (Green button): Shows example signals with edge > 5%
- Demo signals show what real signals would look like (side, strength, suggested size)

### Trades Tab
- **"Load from DB"**: Shows executed trades from your database
- **"Load Demo Data"** (Green button): Shows example trades (mix of OPEN and CLOSED)
- Demo trades show what real trades would look like (entry/exit prices, P&L, status)

## Demo Data Features

✅ **Based on Real Markets**: Demo data uses actual Polymarket markets  
✅ **Realistic Values**: Probabilities, prices, and sizes are realistic  
✅ **Visual Indicators**: Demo data shows a green "Demo" badge  
✅ **No Training Required**: Works immediately without any setup  

## API Endpoints

### Demo Endpoints
- `GET /demo/predictions?limit=10` - Example predictions
- `GET /demo/signals?limit=10` - Example trading signals
- `GET /demo/trades?limit=10` - Example trades

### Live Data Endpoints
- `GET /live/markets?limit=50` - Real-time markets from Polymarket

### Database Endpoints
- `GET /markets` - Markets from database
- `GET /predictions` - Predictions from database
- `GET /signals` - Signals from database
- `GET /trades` - Trades from database

## Usage

1. **Start the server:**
   ```bash
   uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
   ```

2. **Open the UI:**
   - Go to http://localhost:8001/

3. **Click the green "Load Demo Data" buttons** in any tab to see example data!

4. **As you train models and execute trades:**
   - Use "Load from DB" to see your real data
   - Use "Load Demo Data" to see examples for comparison

## Next Steps

1. **View Demo Data**: Click "Load Demo Data" in each tab to see what the UI will show
2. **Train Models**: Follow `TRAINING_GUIDE.md` to generate real predictions
3. **Execute Trades**: Once you have signals, trades will appear in the database
4. **Compare**: Use demo data to understand what real data will look like

The UI is now fully functional for exploring both demo and real data! 🎉


