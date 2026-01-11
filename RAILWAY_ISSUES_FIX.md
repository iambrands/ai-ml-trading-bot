# Railway Issues - Database Connection & Missing Models

## Issues Found

From Railway logs, two critical issues:

### Issue 1: Database Connection Failing

**Error**: `[Errno -2] Name or service not known`

**Problem**: Railway can't connect to PostgreSQL database

**Symptoms**:
- All database queries fail
- Returns empty lists
- Prediction generation can't save to database

**Causes**:
1. PostgreSQL service not added/linked
2. `DATABASE_URL` environment variable not set
3. Database hostname can't be resolved

### Issue 2: Missing Model Files

**Error**: `FileNotFoundError: data/models/xgboost_model.pkl`

**Problem**: Model files not found in Railway deployment

**Symptoms**:
- Prediction generation fails
- Can't load ML models
- Models directory missing or empty

---

## Solutions

### Fix 1: Database Connection

#### Step 1: Check PostgreSQL Service in Railway

1. Go to Railway Dashboard: https://railway.app/
2. Navigate to your project
3. Check if PostgreSQL service exists:
   - Look for a PostgreSQL service in your project
   - If not, add one: "New" → "Database" → "Add PostgreSQL"

#### Step 2: Link PostgreSQL to Web Service

1. Click on your web service (web-production-c490dd)
2. Go to "Variables" tab
3. Click "Reference Variable"
4. Select PostgreSQL service
5. Select `DATABASE_URL` variable
6. Railway should auto-link it

#### Step 3: Verify Database Variables

Check that these variables are set (automatically if linked):
- `DATABASE_URL` (from PostgreSQL service)
- OR individual `POSTGRES_*` variables

**Verify in Railway Dashboard**:
1. Go to your web service
2. Click "Variables" tab
3. Check for `DATABASE_URL` or `POSTGRES_HOST`, `POSTGRES_PORT`, etc.

#### Step 4: Redeploy After Linking

After linking database:
1. Railway should auto-redeploy
2. OR manually trigger redeploy
3. Check logs - database connection should work

---

### Fix 2: Missing Model Files

#### Step 1: Verify Models in Git

Check if models are committed to git:

```bash
git ls-files data/models/*.pkl
```

**Expected**: Should list `.pkl` files

#### Step 2: If Models Not in Git

**Option A: Commit Models** (if small enough):

```bash
# Check model file sizes
ls -lh data/models/*.pkl

# If under 100MB each, commit them
git add data/models/*.pkl
git commit -m "Add trained models"
git push origin main
```

**Option B: Upload Models to Railway** (if too large for git):

1. Use Railway's file system or volume
2. Or deploy models separately
3. Or train models on Railway

#### Step 3: Verify Models in Railway Deployment

After committing/pushing:

1. Check Railway build logs
2. Verify `data/models/` directory exists
3. Verify `.pkl` files are present

**If models are in git**:
- Should be deployed automatically on next deploy
- Check Railway build logs to confirm

**If models not in git**:
- Need to add them to git first
- Or use alternative deployment method

---

## Quick Checklist

### Database Connection

- [ ] PostgreSQL service exists in Railway
- [ ] PostgreSQL service is linked to web service
- [ ] `DATABASE_URL` variable is set (automatically if linked)
- [ ] Web service redeployed after linking
- [ ] Database connection errors gone from logs

### Model Files

- [ ] Model files exist locally: `ls data/models/*.pkl`
- [ ] Model files are in git: `git ls-files data/models/*.pkl`
- [ ] Models are pushed to GitHub
- [ ] Railway deployment includes models
- [ ] No `FileNotFoundError` for models in logs

---

## Verification

### Test Database Connection

After fixing database connection:

```bash
curl https://web-production-c490dd.up.railway.app/health
```

Should return `{"status":"healthy"}` without database errors.

### Test Model Loading

After fixing models:

```bash
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5"
```

Should not show `FileNotFoundError` for models.

---

## Common Issues

### Database: "Name or service not known"

**Cause**: Database hostname not resolvable

**Solutions**:
1. Verify PostgreSQL service is linked
2. Check `DATABASE_URL` is set correctly
3. Use Railway's internal hostname (not external URL)
4. Verify service is running

### Models: "No such file or directory"

**Cause**: Model files not deployed

**Solutions**:
1. Commit models to git (if small enough)
2. Push to GitHub
3. Redeploy on Railway
4. Or train models on Railway

---

## Next Steps

1. ✅ **Fix Database Connection**:
   - Add/link PostgreSQL service in Railway
   - Verify `DATABASE_URL` is set
   - Redeploy web service

2. ✅ **Fix Model Files**:
   - Verify models are in git
   - Push to GitHub if needed
   - Redeploy on Railway

3. ✅ **Test**:
   - Generate predictions: `curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5"`
   - Check logs for errors
   - Verify data appears in dashboard

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*


