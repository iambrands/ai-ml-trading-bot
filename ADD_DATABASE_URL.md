# Add DATABASE_URL to Railway Service Variables

## Current Status

**Problem**: `DATABASE_URL` is in "Suggested Variables" but NOT in "Service Variables"

**Impact**: Database connection fails with `[Errno -2] Name or service not known`

**Solution**: Add `DATABASE_URL` from Suggested Variables to Service Variables

---

## How to Add DATABASE_URL

### Method 1: Add from Suggested Variables (Recommended)

1. **Scroll down** to the "Suggested Variables" section in Railway Dashboard
2. **Find** `DATABASE_URL: ${{Postgres.DATABASE_URL}}` in the list
3. **Make sure it's selected** (should already be in the list)
4. **Scroll to bottom** of the suggested variables section
5. **Click the purple "Add" button** at the bottom
6. **Railway will auto-redeploy** after adding the variable

**Result**: `DATABASE_URL` will be added to Service Variables with the correct reference

### Method 2: Use Reference Variable

1. **Click "+ New Variable"** button (top right of Service Variables section)
2. **Click "Reference Variable"**
3. **Select "Postgres" service** from dropdown
4. **Select "DATABASE_URL"** variable
5. **Save**

**Result**: `DATABASE_URL` will be added as a referenced variable

---

## After Adding DATABASE_URL

### Railway Will Auto-Redeploy

After adding `DATABASE_URL`, Railway should automatically:
1. ✅ Detect the new variable
2. ✅ Trigger a new deployment
3. ✅ Use the new `DATABASE_URL` connection string

### Verify in Logs

After deployment, check Railway logs for:

✅ **Success Indicators**:
- `Database engine created successfully`
- `Database initialized successfully`
- No `[Errno -2] Name or service not known` errors

❌ **Still Failing**:
- `[Errno -2] Name or service not known`
- `Database initialization failed`
- Database connection errors

### Test Database Connection

After deployment, test API endpoints:

```bash
# Should return data (not empty array)
curl "https://web-production-c490dd.up.railway.app/markets?limit=5"

# Should return data (not empty array)
curl "https://web-production-c490dd.up.railway.app/predictions?limit=5"
```

---

## Why This Fixes the Issue

**Current Problem**:
- Individual `POSTGRES_*` variables exist but may not be configured correctly
- `DATABASE_URL` is missing, which is the primary connection string Railway uses
- Application can't resolve database hostname without `DATABASE_URL`

**After Adding DATABASE_URL**:
- Railway uses `DATABASE_URL` as the primary connection string
- References `${{Postgres.DATABASE_URL}}` from PostgreSQL service
- Contains all connection info in one string (host, port, database, user, password)
- Application can connect successfully

---

## Summary

**Problem**: `DATABASE_URL` not in Service Variables

**Solution**: Add `DATABASE_URL` from Suggested Variables

**Steps**:
1. ✅ Scroll to Suggested Variables section
2. ✅ Find `DATABASE_URL: ${{Postgres.DATABASE_URL}}`
3. ✅ Click purple "Add" button at bottom
4. ✅ Wait for Railway to redeploy
5. ✅ Verify connection in logs

**Result**: Database connection works, queries return data, UI shows data!

---

*Railway URL: `https://web-production-c490dd.up.railway.app/`*

