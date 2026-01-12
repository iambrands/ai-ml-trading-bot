# ✅ Loading Predictions from Database

## Status: **READY!**

Your models are trained and predictions are being saved to the database! 🎉

## Current Database Status

- ✅ **Markets**: Saved to database
- ✅ **Predictions**: Saved to database
- ✅ **Models**: XGBoost working, LightGBM using XGBoost fallback

## How to Generate More Predictions

### Option 1: Generate Predictions Script

```bash
# Generate predictions for 10 markets
python scripts/generate_predictions.py --limit 10

# Generate predictions for 50 markets
python scripts/generate_predictions.py --limit 50
```

This script will:
1. Load your trained models (XGBoost + LightGBM)
2. Fetch active markets from Polymarket
3. Generate features for each market
4. Make predictions using your models
5. Save predictions to the database

### Option 2: Run Full Trading Bot

```bash
# Start the full trading bot (includes prediction engine)
python src/main.py
```

This will continuously:
- Fetch active markets
- Generate predictions
- Save to database
- Generate trading signals
- Execute trades (if configured)

## Viewing Predictions in the UI

1. **Start the API Server**:
   ```bash
   uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
   ```

2. **Open the UI**: http://localhost:8001/

3. **View Predictions**:
   - Click the **"Predictions"** tab
   - Click **"Load from Database"** button
   - You'll see all predictions with:
     - Market question
     - Model probability
     - Market price
     - Edge (opportunity)
     - Confidence

4. **View Markets**:
   - Click the **"Markets"** tab
   - Click **"Load from Database"** button
   - See all markets saved in the database

## Checking Database Status

```bash
# Check database contents
python -c "
import asyncio
from src.database.connection import get_db
from src.database.models import Prediction, Market
from sqlalchemy import select, func

async def check():
    async for db in get_db():
        result = await db.execute(select(func.count(Market.id)))
        markets = result.scalar()
        result = await db.execute(select(func.count(Prediction.id)))
        predictions = result.scalar()
        print(f'Markets: {markets}')
        print(f'Predictions: {predictions}')
        break

asyncio.run(check())
"
```

## API Endpoints for Database Data

All these endpoints load from the database:

- `GET /markets` - Get all markets from database
- `GET /predictions` - Get all predictions from database
- `GET /signals` - Get all signals from database
- `GET /trades` - Get all trades from database
- `GET /portfolio/latest` - Get latest portfolio snapshot

## Example: Generate and View Predictions

```bash
# 1. Generate predictions
python scripts/generate_predictions.py --limit 20

# 2. Start API server
uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload

# 3. Open browser
# Go to http://localhost:8001/
# Click "Predictions" tab
# Click "Load from Database"
```

## Notes

- **XGBoost Model**: Working perfectly ✅
- **LightGBM Model**: Currently using XGBoost fallback (will be fixed on next training)
- **NewsAPI**: Rate limited (free tier), but predictions still work
- **Twitter/Reddit**: Not configured, but predictions still work

## Next Steps

1. ✅ Models trained
2. ✅ Predictions saving to database
3. ✅ UI can load from database
4. 🎯 **You're ready to use the system!**

Generate more predictions and view them in the UI! 🚀



