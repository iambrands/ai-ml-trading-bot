# PostgreSQL Setup on Railway - Complete Guide

This guide will walk you through setting up PostgreSQL on Railway and connecting it to your web service so your models can store and retrieve data.

## Overview

Railway provides a managed PostgreSQL service that automatically creates connection variables. Once you add the PostgreSQL service and link it to your web service, Railway will automatically inject the database connection variables, and your application will be able to use them.

## Step-by-Step Setup

### Step 1: Add PostgreSQL Service to Railway

1. **Go to your Railway project dashboard**
   - Navigate to: https://railway.app/dashboard
   - Select your project (handsome-perception)

2. **Add PostgreSQL Service**
   - Click the **"+ New"** button (top right)
   - Select **"Database"** → **"Add PostgreSQL"**
   - Railway will create a new PostgreSQL service

3. **Wait for PostgreSQL to provision**
   - Railway will automatically provision a PostgreSQL database
   - This usually takes 1-2 minutes
   - You'll see a green checkmark when it's ready

### Step 2: Link PostgreSQL to Your Web Service

1. **Go to your Web Service**
   - Click on your `web` service

2. **Link the Database**
   - Railway should automatically detect the PostgreSQL service
   - If not, go to the **"Variables"** tab in your web service
   - You should see variables like:
     - `${{Postgres.PGHOST}}`
     - `${{Postgres.PGPORT}}`
     - `${{Postgres.PGDATABASE}}`
     - `${{Postgres.PGUSER}}`
     - `${{Postgres.PGPASSWORD}}`

3. **Add Database Variables to Web Service**
   - In your web service → **"Variables"** tab
   - Add the following variables:
   
   | Variable Name | Value |
   |--------------|-------|
   | `POSTGRES_HOST` | `${{Postgres.PGHOST}}` |
   | `POSTGRES_PORT` | `${{Postgres.PGPORT}}` |
   | `POSTGRES_DB` | `${{Postgres.PGDATABASE}}` |
   | `POSTGRES_USER` | `${{Postgres.PGUSER}}` |
   | `POSTGRES_PASSWORD` | `${{Postgres.PGPASSWORD}}` |

   **Note**: Railway's variable reference syntax `${{Postgres.PGHOST}}` automatically resolves to the actual database host at runtime.

### Step 3: Verify Database Connection

Once you've added the variables:

1. **Railway will automatically redeploy** your web service
2. **Check the deployment logs** - You should see:
   ```
   Database engine created successfully
   Initializing database...
   Database tables initialized successfully
   ```
   
   Instead of:
   ```
   Database initialization failed (this is OK if DB is not set up) error='[Errno 111] Connection refused'
   ```

3. **Test the API endpoints**:
   - Go to: `https://web-production-c490dd.up.railway.app/health`
   - Should return: `{"status": "healthy", "database": "connected"}`
   - Or similar health check response

### Step 4: Initialize Database Schema (Automatic)

**Good News**: Your application automatically initializes the database schema on startup!

The `src/api/app.py` already calls `init_db()` on startup (I can see it in your logs). This uses SQLAlchemy to automatically create all the tables defined in `src/database/models.py`.

The tables that will be created:
- `markets` - Market data
- `feature_snapshots` - Feature data for ML models
- `predictions` - Model predictions
- `signals` - Trading signals
- `trades` - Trade history
- `model_performance` - Model performance metrics
- `portfolio_snapshots` - Portfolio snapshots

**No manual SQL script execution needed!** The application handles this automatically.

## Alternative: Manual Database Initialization

If you prefer to initialize the database manually, you can use the provided script:

### Option A: Using Railway CLI

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Link your project**:
   ```bash
   railway link
   ```

4. **Run the initialization script**:
   ```bash
   railway run python scripts/init_db.py
   ```

### Option B: Using Railway's Console/Terminal

1. Go to your **web service** in Railway dashboard
2. Click on **"Deployments"** → **"Latest Deployment"**
3. Open **"View Terminal"** or **"Execute Command"**
4. Run:
   ```bash
   python scripts/init_db.py
   ```

## Verification Checklist

After setup, verify everything works:

- [ ] PostgreSQL service is running (green status)
- [ ] Database variables are added to web service
- [ ] Web service redeployed successfully
- [ ] Deployment logs show "Database engine created successfully"
- [ ] Deployment logs show "Database tables initialized successfully"
- [ ] API endpoints return data (no more "[Errno 111] Connection refused" errors)
- [ ] `/health` endpoint shows database as connected

## Troubleshooting

### Issue: Still seeing "Connection refused" errors

**Solution**: 
1. Verify PostgreSQL service is running (green checkmark)
2. Check that all 5 database variables are set in web service Variables tab
3. Ensure variable names match exactly (case-sensitive)
4. Verify variable values use Railway's reference syntax: `${{Postgres.PGHOST}}`

### Issue: "Database engine not available" in logs

**Solution**:
1. Check that `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` are all set
2. Verify the PostgreSQL service is linked to your web service
3. Check Railway's PostgreSQL service logs for any errors

### Issue: Tables not created

**Solution**:
1. The app should auto-create tables on startup
2. If not, manually run: `python scripts/init_db.py` via Railway CLI or terminal
3. Check deployment logs for any SQLAlchemy errors

### Issue: Cannot connect to database

**Solution**:
1. Verify PostgreSQL service is in the same Railway project
2. Check that variables are using Railway's reference syntax
3. Ensure web service has access to PostgreSQL service (they should be in the same project)

## Database Schema Overview

Your application uses the following tables:

1. **markets** - Stores market information (ID, question, category, resolution date)
2. **feature_snapshots** - Stores feature vectors at different time points (for training)
3. **predictions** - Stores model predictions with probabilities and edge calculations
4. **signals** - Stores trading signals generated from predictions
5. **trades** - Stores executed trades with entry/exit prices and PnL
6. **model_performance** - Tracks model accuracy, Brier score, log loss, etc.
7. **portfolio_snapshots** - Periodic snapshots of portfolio value and PnL

## Next Steps After Database Setup

Once PostgreSQL is connected:

1. **Test Data Storage**:
   - Visit `/dashboard` and check if predictions/signals/trades are being saved
   - The app should now persist data instead of returning empty lists

2. **Train Models**:
   - Models can now save training data to the database
   - Predictions will be stored and accessible via the API

3. **Monitor Performance**:
   - Check `model_performance` table for model metrics
   - View `portfolio_snapshots` for portfolio tracking

4. **Query Data**:
   - Use Railway's PostgreSQL service → "Data" tab to view tables
   - Or use your API endpoints to query data

## Cost Considerations

- Railway PostgreSQL pricing depends on your plan
- Check Railway's pricing page for current PostgreSQL costs
- You can use Railway's free tier for development/testing

## Additional Resources

- **Railway PostgreSQL Docs**: https://docs.railway.app/databases/postgresql
- **Railway Variables Docs**: https://docs.railway.app/develop/variables
- **Your Database Models**: `src/database/models.py`
- **Database Connection**: `src/database/connection.py`

---

**Quick Command Reference**:

```bash
# Check Railway services
railway status

# View database connection info
railway variables

# Run database initialization
railway run python scripts/init_db.py

# Connect to database (if you have psql)
railway connect postgres
```



