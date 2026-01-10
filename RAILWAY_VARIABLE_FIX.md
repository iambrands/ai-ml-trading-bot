# Fix Railway POSTGRES_PORT Variable Error

## Problem

Railway was setting `POSTGRES_PORT` to a malformed value:
```
POSTGRES_PORT = " (usually 5432)"
```

This caused a Pydantic validation error:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
postgres_port
  Input should be a valid integer, unable to parse string as an integer 
  [type=int_parsing, input_value=' (usually 5432)', input_type=str]
```

## Solution

I've fixed the code to handle malformed port values. The application now:
- ✅ Automatically extracts numbers from strings like `" (usually 5432)"` → `5432`
- ✅ Uses default port `5432` if no number is found
- ✅ Handles both string and integer values

## Railway Variable Fix

However, you should **still fix the Railway variable** to prevent future issues:

### Step 1: Fix POSTGRES_PORT in Railway

1. **Go to Railway Dashboard** → **handsome-perception** project
2. **Select your Web Service** (not PostgreSQL service)
3. **Go to "Variables" tab**
4. **Find `POSTGRES_PORT`**
5. **Change value from:** ` (usually 5432)`
   **To:** `5432` (just the number, no text)

### Step 2: Fix Other Railway Variables

While you're there, check and fix these variables if they have similar issues:

- `POSTGRES_HOST` should be: `postgres.railway.internal` (or the actual host)
  - ❌ NOT: `${{Postgres.PGHOST}} (internal host)`
  - ✅ YES: `postgres.railway.internal` or use `${{Postgres.PGHOST}}` if Railway supports templates

- `POSTGRES_PORT` should be: `5432`
  - ❌ NOT: ` (usually 5432)`
  - ✅ YES: `5432`

- `POSTGRES_USER` should be: `postgres`
  - ❌ NOT: ` (default: postgres)`
  - ✅ YES: `postgres`

- `POSTGRES_PASSWORD` should be: actual password value
  - ❌ NOT: ` (auto-generated)`
  - ✅ YES: actual password string

- `POSTGRES_DB` should be: `railway` or your database name
  - ❌ NOT: ` (default: railway)`
  - ✅ YES: `railway` or `polymarket_trader`

### Step 3: Use Railway Template Variables Correctly

If Railway supports template variables (which it does), use them like this:

Instead of manual values, link variables from PostgreSQL service:

1. **In Web Service → Variables tab**
2. **For each variable, use Railway's template syntax:**
   - `POSTGRES_HOST` = `${{Postgres.PGHOST}}`
   - `POSTGRES_PORT` = `${{Postgres.PGPORT}}`
   - `POSTGRES_USER` = `${{Postgres.PGUSER}}`
   - `POSTGRES_PASSWORD` = `${{Postgres.PGPASSWORD}}`
   - `POSTGRES_DB` = `${{Postgres.PGDATABASE}}`

3. **Railway will automatically resolve these** to actual values at runtime

### Step 4: Verify Variables

After fixing, verify in Railway:

1. **Variables should show:**
   - `POSTGRES_PORT` = `5432` (or `${{Postgres.PGPORT}}`)
   - No extra text, comments, or parentheses
   - Just the actual value or template variable

2. **If using template variables:**
   - Make sure PostgreSQL service variables exist
   - Railway will resolve them automatically when the service runs

## Code Fix Applied

The code now handles malformed values gracefully using a Pydantic field validator:

```python
@field_validator('postgres_port', mode='before')
@classmethod
def parse_postgres_port(cls, v: any) -> int:
    """Parse port value, handling malformed strings from Railway."""
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        v = v.strip()
        # Extract first number from string
        match = re.search(r'\d+', v)
        if match:
            return int(match.group())
        return 5432
    return 5432
```

This means your app will work even with malformed values, but **you should still fix Railway variables** for clarity and to avoid future issues.

## Next Steps

1. ✅ Code fix applied - app now handles malformed port values
2. ⚠️ **Fix Railway variables** - remove extra text from `POSTGRES_PORT` and other variables
3. ✅ Redeploy web service
4. ✅ Check logs - should start successfully now

## Verification

After fixing variables and redeploying, check Railway logs:

✅ Should see: `Database engine created successfully`  
❌ Should NOT see: `ValidationError` or `int_parsing` errors

