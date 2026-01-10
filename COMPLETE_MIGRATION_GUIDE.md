# Complete Migration Guide: Local Data & Models to Railway

This guide will help you migrate **everything** from your local environment to Railway:
1. ✅ **Database data** (markets, predictions, signals, trades, etc.)
2. ✅ **Trained models** (XGBoost, LightGBM model files)
3. ✅ **Feature names** (feature_names.pkl)

## Overview

You have:
- **Models**: `data/models/xgboost_model.pkl`, `data/models/lightgbm_model.pkl`, `data/models/feature_names.pkl`
- **Local Database**: PostgreSQL with historical data (if exists)

Railway needs:
- Models accessible in the deployment
- Database data imported to Railway PostgreSQL

## Step-by-Step Migration

### Part 1: Migrate Database Data

#### Step 1.1: Check What Data You Have Locally

```bash
# Connect to local database
psql -h localhost -U iabadvisors -d polymarket_trader

# Check what data exists
SELECT 
  'markets' as table_name, COUNT(*) as row_count FROM markets
UNION ALL
SELECT 'predictions', COUNT(*) FROM predictions
UNION ALL
SELECT 'signals', COUNT(*) FROM signals
UNION ALL
SELECT 'trades', COUNT(*) FROM trades
UNION ALL
SELECT 'portfolio_snapshots', COUNT(*) FROM portfolio_snapshots
UNION ALL
SELECT 'feature_snapshots', COUNT(*) FROM feature_snapshots
UNION ALL
SELECT 'model_performance', COUNT(*) FROM model_performance;

# Exit
\q
```

#### Step 1.2: Export Local Database

```bash
# Export entire database (all tables and data)
pg_dump -h localhost -U iabadvisors -d polymarket_trader \
  -F c \
  -f local_db_backup.dump

# Or export as SQL script (more portable)
pg_dump -h localhost -U iabadvisors -d polymarket_trader \
  -F p \
  -f local_db_backup.sql

# Check file size
ls -lh local_db_backup.*
```

#### Step 1.3: Set Up Railway PostgreSQL

1. **Go to Railway Dashboard** → Your project
2. **Click "+ New"** → **"Database"** → **"Add PostgreSQL"**
3. **Wait for provisioning** (1-2 minutes)
4. **Note the PostgreSQL service** (you'll link it to web service)

#### Step 1.4: Link PostgreSQL to Web Service

1. **Go to your `web` service** in Railway
2. **Click "Variables" tab**
3. **Add these variables** (using Railway's reference syntax):

   | Variable Name | Value |
   |--------------|-------|
   | `POSTGRES_HOST` | `${{Postgres.PGHOST}}` |
   | `POSTGRES_PORT` | `${{Postgres.PGPORT}}` |
   | `POSTGRES_DB` | `${{Postgres.PGDATABASE}}` |
   | `POSTGRES_USER` | `${{Postgres.PGUSER}}` |
   | `POSTGRES_PASSWORD` | `${{Postgres.PGPASSWORD}}` |

   **Important**: Use `${{Postgres.XXX}}` syntax - Railway resolves these automatically.

#### Step 1.5: Import Database Data to Railway

**Option A: Using Railway CLI (Recommended)**

```bash
# Install Railway CLI if needed
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Connect to Railway PostgreSQL
railway connect postgres

# In PostgreSQL shell:
# First, the app will auto-create tables on startup (or you can run init_db.py)
# Then import your data:
\i local_db_backup.sql

# Or restore from dump file:
# (Exit PostgreSQL shell first: \q)
pg_restore -h ${{Postgres.PGHOST}} -U ${{Postgres.PGUSER}} -d ${{Postgres.PGDATABASE}} local_db_backup.dump
```

**Option B: Using psql with Railway Connection String**

1. **Get connection string from Railway**:
   - Go to PostgreSQL service → "Variables" tab
   - Copy the connection details

2. **Import using psql**:
   ```bash
   # Get connection string from Railway dashboard
   # Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE
   
   # Import SQL file
   psql "postgresql://postgres:PASSWORD@HOST:PORT/railway" -f local_db_backup.sql
   
   # Or restore from dump
   pg_restore -h HOST -U postgres -d railway -f local_db_backup.dump
   ```

---

### Part 2: Migrate Trained Models

Models need to be included in the Railway deployment. Here are your options:

#### Option A: Add Models to Git (Recommended for Small Models)

**Check model sizes first**:
```bash
ls -lh data/models/*.pkl
```

If models are < 50MB total, we can add them to git:

1. **Temporarily allow models in git**:
   ```bash
   # Edit .gitignore - comment out or remove the data/models line
   # Or use git add -f to force add
   ```

2. **Add models to git**:
   ```bash
   git add -f data/models/*.pkl
   git commit -m "Add trained models for Railway deployment"
   git push origin main
   ```

3. **Railway will automatically include them** in the Docker build (they're in the repo)

4. **Update .gitignore after** (if you want to exclude future models):
   ```bash
   # Add back to .gitignore if needed
   echo "data/models/*.pkl" >> .gitignore
   # But keep the ones we just added:
   git add -f data/models/xgboost_model.pkl
   git add -f data/models/lightgbm_model.pkl
   git add -f data/models/feature_names.pkl
   ```

#### Option B: Use Railway Volume/Storage (For Large Models)

If models are too large for git:

1. **Railway Volumes** (if available on your plan):
   - Create a Railway volume
   - Upload models to the volume
   - Mount volume in your service

2. **External Storage** (S3, etc.):
   - Upload models to S3 or similar
   - Download in Dockerfile or startup script

#### Option C: Upload Models via Railway CLI

```bash
# Upload models after deployment
railway run --service web -- bash

# Then inside Railway container:
# Upload files (this requires setup)
```

**For now, let's use Option A** (add to git) since it's simplest.

---

### Part 3: Verify Models Are Loaded Correctly

#### Check Model Loading Path

The app needs to find models at runtime. Let's verify the path:

```python
# The models are expected at: data/models/*.pkl
# In Railway, the working directory is /app, so models should be at: /app/data/models/*.pkl
```

Let's create a script to verify models are accessible:

```python
# scripts/verify_models.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

models_dir = Path("data/models")

print(f"Models directory: {models_dir.absolute()}")
print(f"Directory exists: {models_dir.exists()}")

for model_file in models_dir.glob("*.pkl"):
    print(f"  ✅ {model_file.name} ({model_file.stat().st_size / 1024 / 1024:.2f} MB)")
```

---

## Complete Migration Checklist

### Database Migration

- [ ] Check local database for existing data
- [ ] Export local database using `pg_dump`
- [ ] Set up Railway PostgreSQL service
- [ ] Link PostgreSQL to web service (add 5 variables)
- [ ] Import exported data to Railway PostgreSQL
- [ ] Verify data imported correctly
- [ ] Check Railway logs for "Database engine created successfully"
- [ ] Test API endpoints return data (not empty lists)

### Models Migration

- [ ] Check model file sizes (`ls -lh data/models/*.pkl`)
- [ ] If < 50MB total: Add models to git
- [ ] If > 50MB: Use external storage (S3, Railway volume)
- [ ] Verify models are in git (check with `git ls-files data/models/`)
- [ ] Push to Railway (Railway will include in Docker build)
- [ ] Verify models are accessible in Railway deployment
- [ ] Test model loading (check Railway logs)

### Verification

- [ ] Database connection works (no "[Errno 111] Connection refused")
- [ ] Models can be loaded (test prediction generation)
- [ ] Historical data is accessible (check /predictions, /signals endpoints)
- [ ] New predictions can be generated and saved
- [ ] Everything works end-to-end

---

## Quick Commands Summary

```bash
# 1. Export local database
pg_dump -h localhost -U iabadvisors -d polymarket_trader -F c -f local_db_backup.dump

# 2. Check model sizes
ls -lh data/models/*.pkl

# 3. Add models to git (if small enough)
git add -f data/models/*.pkl
git commit -m "Add trained models for Railway deployment"
git push origin main

# 4. After Railway PostgreSQL is set up, import data:
railway connect postgres
pg_restore -h ${{Postgres.PGHOST}} -U ${{Postgres.PGUSER}} -d ${{Postgres.PGDATABASE}} local_db_backup.dump

# 5. Verify everything works:
railway logs --service web
# Check for: "Database engine created successfully" and no model loading errors
```

---

## Troubleshooting

### Models Too Large for Git

If models exceed GitHub's file size limits:

1. **Use Git LFS** (Large File Storage):
   ```bash
   git lfs install
   git lfs track "*.pkl"
   git add .gitattributes
   git add data/models/*.pkl
   git commit -m "Add models with Git LFS"
   git push origin main
   ```

2. **Or use external storage**:
   - Upload to S3, Google Cloud Storage, etc.
   - Modify app to download models on startup
   - Store download URL in environment variable

### Database Import Errors

If you get "table already exists" errors:

```sql
-- Drop tables first (in Railway PostgreSQL)
DROP TABLE IF EXISTS portfolio_snapshots CASCADE;
DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS feature_snapshots CASCADE;
DROP TABLE IF EXISTS model_performance CASCADE;
DROP TABLE IF EXISTS markets CASCADE;

-- Then let app recreate them (or run init_db.py)
-- Then import your data
```

### Models Not Found in Railway

If models aren't accessible:

1. **Check if models are in git**:
   ```bash
   git ls-files data/models/
   ```

2. **Check Railway build logs** - models should be copied during Docker build

3. **Check model paths in code** - ensure paths are relative or use environment variables

---

## Next Steps After Migration

1. **Test Predictions**: Generate predictions and verify models work
2. **Monitor Logs**: Check Railway logs for any errors
3. **Verify Data**: Check API endpoints return your historical data
4. **Test End-to-End**: Generate new predictions, signals, trades with migrated models

---

## Important Notes

1. **Models are NOT in database** - They're `.pkl` files that need to be included in the deployment
2. **Database schema auto-creates** - Your app automatically creates tables on startup
3. **Models load from disk** - The app looks for models in `data/models/` directory
4. **Both are needed** - Database for data persistence, models for predictions

---

Let me know when you're ready to proceed with the migration, and I can help with each step!

