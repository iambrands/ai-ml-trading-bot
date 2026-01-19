# Running the Diagnostic Script

## Quick Start

The diagnostic script checks why whale tracker and calendar features aren't working.

### Option 1: Railway (Recommended)

**Select the "web" service** when prompted, or specify it directly:

```bash
railway run --service web python scripts/diagnose_issues.py
```

### Option 2: Railway with DATABASE_URL from Postgres service

If you need the database URL from the Postgres service:

```bash
railway run --service Postgres python scripts/diagnose_issues.py
```

**Note**: The web service has both `DATABASE_URL` and `API_BASE_URL` configured, so it's usually the better choice.

### Option 3: Local (if you have Railway CLI linked)

```bash
# Export variables from Railway
railway variables --service web

# Then set them locally
export DATABASE_URL="postgresql://..."
export API_BASE_URL="https://web-production-c490dd.up.railway.app"

# Run script
python scripts/diagnose_issues.py
```

## What the Script Checks

✅ **Database Connection** - Can we connect to PostgreSQL?  
✅ **Table Existence** - Do whale/calendar tables exist?  
✅ **Data Existence** - Is there data in the tables?  
✅ **API Endpoints** - Are `/whales/*` and `/calendar/*` endpoints working?  
✅ **Frontend Paths** - Are API calls using correct paths?  
✅ **Environment Variables** - Are required vars set?

## Expected Output

The script provides color-coded output:
- 🟢 **Green ✓** = Passing
- 🔴 **Red ✗** = Failing  
- 🟡 **Yellow ⚠** = Warnings/Recommendations

At the end, you'll get a **Diagnostic Summary** with priority actions to fix any issues.

## Common Issues Found

1. **Missing Tables** → Run migrations
2. **No Data** → Initialize whales/calendar data
3. **API Errors** → Check Railway logs
4. **Wrong Paths** → Frontend using incorrect API routes

## Next Steps After Diagnosis

After running the script, follow the priority actions it recommends:
- Run migrations if tables are missing
- Initialize data if tables are empty
- Check logs if API endpoints fail

