# Railway Variables Checklist - Complete Fix Guide

## Overview

This guide will help you fix all Railway variables to ensure your application connects properly to PostgreSQL.

## Step-by-Step Variable Fix

### Step 1: Access Railway Dashboard

1. Go to: https://railway.app
2. Select project: **handsome-perception**
3. Click on your **Web Service** (the one running your FastAPI app)

### Step 2: Go to Variables Tab

Click on **"Variables"** tab in your Web Service.

### Step 3: Fix PostgreSQL Variables

Check and fix each of these variables:

#### ✅ POSTGRES_HOST

**Current Value (likely wrong):**
- ❌ `${{Postgres.PGHOST}} (internal host)`
- ❌ ` (usually postgres.railway.internal)`
- ❌ Empty or template with extra text

**Correct Value:**
- ✅ `${{Postgres.PGHOST}}` (Railway template - recommended)
- OR: `postgres.railway.internal` (actual value if template doesn't work)

**Action:**
1. Find `POSTGRES_HOST` variable
2. Edit it
3. Set to: `${{Postgres.PGHOST}}`
4. Save

---

#### ✅ POSTGRES_PORT

**Current Value (WRONG - causing errors):**
- ❌ ` (usually 5432)` ← **THIS IS CAUSING THE ERROR**
- ❌ `5432 (default)`
- ❌ Any value with extra text

**Correct Value:**
- ✅ `5432` (just the number)
- OR: `${{Postgres.PGPORT}}` (Railway template)

**Action:**
1. Find `POSTGRES_PORT` variable
2. Edit it
3. **Delete all text, keep only:** `5432`
4. OR set to: `${{Postgres.PGPORT}}`
5. Save

---

#### ✅ POSTGRES_USER

**Current Value (likely wrong):**
- ❌ Empty string `""`
- ❌ ` (default: postgres)`
- ❌ Template with extra text

**Correct Value:**
- ✅ `postgres` (default PostgreSQL user)
- OR: `${{Postgres.PGUSER}}` (Railway template)

**Action:**
1. Find `POSTGRES_USER` variable (if it exists)
2. If missing, click **"+ New Variable"**
3. Variable name: `POSTGRES_USER`
4. Value: `postgres` or `${{Postgres.PGUSER}}`
5. Save

---

#### ✅ POSTGRES_PASSWORD

**Current Value (likely wrong):**
- ❌ Empty string `""`
- ❌ ` (auto-generated)`
- ❌ Template with extra text

**Correct Value:**
- ✅ `${{Postgres.PGPASSWORD}}` (Railway template - **RECOMMENDED**)
- OR: Actual password value from PostgreSQL service

**Action:**
1. Find `POSTGRES_PASSWORD` variable (if it exists)
2. If missing, click **"+ New Variable"**
3. Variable name: `POSTGRES_PASSWORD`
4. Value: `${{Postgres.PGPASSWORD}}`
   - This links to your PostgreSQL service's password
   - Railway will automatically resolve it
5. Save

**Note:** If `${{Postgres.PGPASSWORD}}` doesn't resolve, you need to:
1. Go to your **PostgreSQL service** in Railway
2. Go to **Variables** tab
3. Find `POSTGRES_PASSWORD` or `PGPASSWORD`
4. If missing, add it with a secure password
5. Then reference it from Web Service: `${{Postgres.PGPASSWORD}}`

---

#### ✅ POSTGRES_DB

**Current Value (likely wrong):**
- ❌ Empty string
- ❌ ` (default: railway)`
- ❌ Template with extra text

**Correct Value:**
- ✅ `railway` (Railway's default database)
- OR: `polymarket_trader` (if you want your own database name)
- OR: `${{Postgres.PGDATABASE}}` (Railway template)

**Action:**
1. Find `POSTGRES_DB` variable (if it exists)
2. If missing, click **"+ New Variable"**
3. Variable name: `POSTGRES_DB`
4. Value: `railway` or `${{Postgres.PGDATABASE}}`
5. Save

---

#### ✅ DATABASE_URL (Optional but Recommended)

**Current Value (likely wrong):**
- ❌ `postgresql://:@postgres.railway.internal:5432/` (empty credentials)
- ❌ Template with unresolved variables

**Correct Value:**
- ✅ `postgresql://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}`
- This constructs the full connection string from template variables

**Action:**
1. Find `DATABASE_URL` variable (if it exists)
2. Edit or create it
3. Value: `postgresql://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}`
4. Save

**Note:** Your app will use this if set, otherwise it constructs from individual variables.

---

### Step 4: Verify PostgreSQL Service Variables

Before the Web Service can use template variables, **PostgreSQL service must have these variables**:

1. Go to your **PostgreSQL service** (not Web Service)
2. Go to **Variables** tab
3. Check these variables exist:

#### PostgreSQL Service Variables:

- ✅ `PGUSER` or `POSTGRES_USER` = `postgres`
- ✅ `PGPASSWORD` or `POSTGRES_PASSWORD` = [actual password - Railway auto-generates this]
- ✅ `PGDATABASE` or `POSTGRES_DB` = `railway` (or your database name)
- ✅ `PGHOST` or `POSTGRES_HOST` = `postgres.railway.internal`
- ✅ `PGPORT` or `POSTGRES_PORT` = `5432`

**If any are missing:**
1. Click **"+ New Variable"**
2. Add the missing variable
3. Use the correct name (Railway might use `PG*` or `POSTGRES_*` format)
4. Set appropriate value

**Important:** Railway auto-generates `POSTGRES_PASSWORD` when PostgreSQL service is created. If it's missing, Railway might need to regenerate it. Check Railway documentation.

---

### Step 5: Link Variables from PostgreSQL to Web Service

Railway template variables (`${{Postgres.PGVAR}}`) automatically link variables from PostgreSQL service to Web Service, but you need to:

1. **Ensure PostgreSQL service variables exist** (Step 4)
2. **Use correct template syntax** in Web Service:
   - `${{Postgres.PGUSER}}` → Links `PGUSER` from PostgreSQL service
   - `${{Postgres.PGPASSWORD}}` → Links `PGPASSWORD` from PostgreSQL service
   - `${{Postgres.PGDATABASE}}` → Links `PGDATABASE` from PostgreSQL service
   - `${{Postgres.PGHOST}}` → Links `PGHOST` from PostgreSQL service
   - `${{Postgres.PGPORT}}` → Links `PGPORT` from PostgreSQL service

**Template Variable Format:**
```
${{ServiceName.VariableName}}
```

- `ServiceName` = Name of your PostgreSQL service (might be "Postgres", "PostgreSQL", or similar)
- `VariableName` = Variable name in that service (without `POSTGRES_` or `PG` prefix)

**To find correct service name:**
1. Check your PostgreSQL service name in Railway dashboard
2. Use that exact name in template: `${{YourServiceName.PGVAR}}`

**Example:**
If your PostgreSQL service is named "Postgres":
- `${{Postgres.PGUSER}}`
- `${{Postgres.PGPASSWORD}}`

If your PostgreSQL service is named "PostgreSQL":
- `${{PostgreSQL.PGUSER}}`
- `${{PostgreSQL.PGPASSWORD}}`

---

### Step 6: Other Required Variables

Check these non-PostgreSQL variables are also set:

#### ✅ PORT
- Should be: `8001` (or whatever port Railway assigns)
- Railway usually auto-sets this, but verify it exists

#### ✅ NEWSAPI_KEY (if using news data)
- Should be: Your actual NewsAPI key
- Value: `46ba59f50bcf4d2398fecba3f8776c84` (if that's your key)

#### ✅ Other API Keys (optional)
- `POLYMARKET_API_KEY` (if needed)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` (if using Reddit)
- `TWITTER_API_KEY`, etc. (if using Twitter)

---

## Step 7: Verify and Test

After fixing all variables:

1. **Save all changes** in Railway dashboard
2. **Wait for auto-redeploy** (or manually trigger redeploy)
3. **Check Railway logs** for your Web Service:
   - Should see: `Database engine created successfully`
   - Should NOT see: `ValidationError` or connection errors
   - Should see: Server starting on port 8001

4. **Test API endpoint:**
   ```bash
   curl https://your-railway-app.railway.app/api/health
   ```
   Should return success status.

---

## Quick Reference: Variable Values

### Web Service Variables (Minimum Required):

```
POSTGRES_HOST = ${{Postgres.PGHOST}}
POSTGRES_PORT = 5432
POSTGRES_USER = postgres
POSTGRES_PASSWORD = ${{Postgres.PGPASSWORD}}
POSTGRES_DB = railway
```

OR use DATABASE_URL:
```
DATABASE_URL = postgresql://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
```

### PostgreSQL Service Variables (Must Exist):

```
PGUSER = postgres
PGPASSWORD = [Railway auto-generated]
PGDATABASE = railway
PGHOST = postgres.railway.internal
PGPORT = 5432
```

---

## Troubleshooting

### Template Variables Not Resolving

If `${{Postgres.PGVAR}}` doesn't work:

1. **Check service name:** Make sure PostgreSQL service name matches
2. **Use actual values:** Instead of templates, use actual values from PostgreSQL service
3. **Check Railway documentation:** Template syntax might vary

### Still Getting Connection Errors

1. **Check PostgreSQL service is running:** Green status in Railway
2. **Verify password:** Make sure `POSTGRES_PASSWORD` is actually set in PostgreSQL service
3. **Check host:** For internal connections, use `postgres.railway.internal`
4. **Check database exists:** Railway creates `railway` database by default
5. **Review Railway logs:** Check both Web Service and PostgreSQL service logs

### Variables Keep Getting Corrupted

Railway might auto-update variables. If this happens:
- Lock variables to prevent auto-updates
- Use actual values instead of templates
- Document your variable values

---

## Next Steps After Fixing Variables

1. ✅ Variables fixed
2. ✅ Service redeployed
3. ✅ Database connection working
4. 🔄 **Import your database** (see `RAILWAY_DATABASE_IMPORT.md`)
5. 🔄 **Test API endpoints**
6. 🔄 **Verify data is accessible**

---

## Summary Checklist

- [ ] `POSTGRES_HOST` = `${{Postgres.PGHOST}}` or `postgres.railway.internal`
- [ ] `POSTGRES_PORT` = `5432` (NO extra text)
- [ ] `POSTGRES_USER` = `postgres` or `${{Postgres.PGUSER}}`
- [ ] `POSTGRES_PASSWORD` = `${{Postgres.PGPASSWORD}}` or actual password
- [ ] `POSTGRES_DB` = `railway` or `${{Postgres.PGDATABASE}}`
- [ ] `DATABASE_URL` = constructed template or leave unset
- [ ] PostgreSQL service has all required variables
- [ ] Variables saved and service redeployed
- [ ] Checked logs - no errors
- [ ] Tested API endpoint - works


