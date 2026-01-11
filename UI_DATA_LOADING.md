# UI Data Loading Guide

## How the UI Loads Data

The UI has **two modes** for loading data:

### 1. **Database Mode** (Default)
- Loads data from your PostgreSQL database
- Shows markets, predictions, signals, trades, and portfolio snapshots that have been saved
- **Use this when:** You've trained models, executed trades, or saved data to the database

### 2. **Live API Mode** (New!)
- Fetches real-time data directly from Polymarket API
- Works **immediately** without any training or database setup
- **Use this when:** You want to see current markets right now

## How to Use

### Markets Tab

1. **"Load from DB"** button:
   - Fetches markets from your database
   - Shows empty state if database is empty (which is normal at first)

2. **"Load Live Data"** button (Green):
   - Fetches real-time markets from Polymarket API
   - Shows current active markets with live prices
   - **Works immediately - no training required!**

### Other Tabs

- **Predictions**: Shows ML model predictions (requires trained models)
- **Signals**: Shows trading signals (requires predictions)
- **Trades**: Shows executed trades (requires trading activity)
- **Portfolio**: Shows portfolio snapshots (requires trades)

## Current Status

✅ **Live Markets Endpoint**: Working!  
✅ **UI Updated**: "Load Live Data" button added  
✅ **Real-time Data**: Fetches from Polymarket API  

## Example Usage

1. **Start the server:**
   ```bash
   uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
   ```

2. **Open the UI:**
   - Go to http://localhost:8001/

3. **Click "Load Live Data"** in the Markets tab
   - You'll see real-time markets from Polymarket!
   - No database or training needed

4. **As you train models and execute trades:**
   - Use "Load from DB" to see your saved data
   - Use "Load Live Data" to see current market prices

## API Endpoints

### Live Data Endpoints (No Database Required)

- `GET /live/markets?limit=50` - Fetch active markets from Polymarket
- `GET /live/market/{market_id}` - Get detailed market data

### Database Endpoints (Requires Data)

- `GET /markets` - Markets from database
- `GET /predictions` - ML predictions from database
- `GET /signals` - Trading signals from database
- `GET /trades` - Executed trades from database
- `GET /portfolio/latest` - Portfolio snapshot from database

## Next Steps

1. **Test Live Data**: Click "Load Live Data" to see real markets
2. **Train Models**: Follow `TRAINING_GUIDE.md` to generate predictions
3. **Execute Trades**: Once you have signals, trades will appear
4. **View Portfolio**: Portfolio tab will show your trading performance

The UI is now fully functional for viewing live data! 🎉


