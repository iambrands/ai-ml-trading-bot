# Fix Railway Database Connection

## Current Issue

**Error**: `[Errno -2] Name or service not known`

**Problem**: Railway web service can't connect to PostgreSQL database

**Impact**:
- ❌ Database queries fail (return empty arrays)
- ❌ Can't save predictions to database
- ❌ UI tabs show empty (except live markets)
- ✅ Live endpoints work (fetch from Polymarket API directly)

---

## Solution: Link PostgreSQL Service

### Step 1: Check PostgreSQL Service Exists

1. **Go to Railway Dashboard**: https://railway.app/
2. **Navigate to your project**
3. **Look for PostgreSQL service**:
   - Should show "Running" status
   - If not present, add it: "New" → "Database" → "Add PostgreSQL"

### Step 2: Link PostgreSQL to Web Service

1. **Click on web service** (web-production-c490dd)
2. **Go to "Variables" tab**
3. **Click "Reference Variable"** button
4. **Select PostgreSQL service** from dropdown
5. **Select `DATABASE_URL` variable** from PostgreSQL service
6. **Save** the reference

**What This Does**:
- Railway automatically sets `DATABASE_URL` in web service
- Points to the correct PostgreSQL hostname
- Handles connection string formatting

### Step 3: Verify DATABASE_URL is Set

1. **In web service Variables tab**
2. **Check for `DATABASE_URL`**:
   - Should show value (or "Reference" indicator)
   - Should start with `postgresql://` or `postgresql+asyncpg://`
   - Should include hostname, port, database, user, password

### Step 4: Redeploy Web Service

**Railway should auto-redeploy** after linking database.

**Or manually redeploy**:
1. Go to web service
2. Click "Deployments" tab
3. Click "Redeploy" or trigger new deployment
4. Wait for deployment to complete

### Step 5: Verify Connection in Logs

**After redeploy, check logs** for:

✅ **Success Indicators**:
- `Database engine created successfully`
- `Database initialized successfully`
- No `[Errno -2] Name or service not known` errors

❌ **Still Failing**:
- `[Errno -2] Name or service not known`
- `Database initialization failed`
- Database connection errors

---

## Troubleshooting

### Error: "Name or service not known"

**Causes**:
1. PostgreSQL service not linked
2. `DATABASE_URL` not set
3. Database hostname wrong or inaccessible
4. Service not running

**Solutions**:
1. ✅ Verify PostgreSQL service exists and is running
2. ✅ Link PostgreSQL to web service (Reference Variable)
3. ✅ Check `DATABASE_URL` is set in Variables
4. ✅ Redeploy web service after linking
5. ✅ Check Railway logs for connection errors

### DATABASE_URL Shows "Reference"

**This is Normal**:
- Railway shows "Reference" for linked variables
- Actual value is resolved at runtime
- Connection should still work

### Database Connection Still Failing After Linking

**Check**:
1. PostgreSQL service is running (status: "Running")
2. `DATABASE_URL` is actually set (not empty)
3. Web service redeployed after linking
4. Railway logs show new deployment

**Try**:
1. Unlink and relink database
2. Check PostgreSQL service logs for issues
3. Verify database is accessible
4. Check Railway status page for issues

---

## Verification

### Test Database Connection

**After fixing, check logs** for:

✅ **Connection Success**:
```
Database engine created successfully
Database initialized successfully
```

❌ **Connection Failure**:
```
[Errno -2] Name or service not known
Database initialization failed
```

### Test API Endpoints

**Database endpoints should return data**:

```bash
# Should return markets (not empty array)
curl "https://web-production-c490dd.up.railway.app/markets?limit=5"

# Should return predictions (not empty array)
curl "https://web-production-c490dd.up.railway.app/predictions?limit=5"

# Should return signals (not empty array)
curl "https://web-production-c490dd.up.railway.app/signals?limit=5"
```

### Test Prediction Generation

```bash
# Should successfully save predictions to database
curl -X POST "https://web-production-c490dd.up.railway.app/predictions/generate?limit=5"

# Check logs - should NOT show database errors
# Check database - should have new predictions
```

---

## Summary

**Problem**: Database connection failing - `[Errno -2] Name or service not known`

**Solution**: Link PostgreSQL service to web service via Reference Variable

**Steps**:
1. ✅ Check PostgreSQL service exists
2. ✅ Link PostgreSQL to web service (Reference Variable → DATABASE_URL)
3. ✅ Verify DATABASE_URL is set
4. ✅ Redeploy web service
5. ✅ Verify connection in logs

**Result**: Database connection works, queries return data, predictions can be saved

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*

