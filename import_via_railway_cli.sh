#!/bin/bash
# Import database using Railway CLI (which has access to resolved environment variables)
# This script uses 'railway run' to execute psql with the correct DATABASE_URL

set -e

SQL_FILE="local_db_backup_railway.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ Error: $SQL_FILE not found"
    exit 1
fi

echo "📦 Importing database to Railway using Railway CLI..."
echo "📁 SQL file: $SQL_FILE"
echo ""

# Check if Railway is linked
if ! railway status > /dev/null 2>&1; then
    echo "❌ Error: Not linked to Railway project"
    echo "Run: railway link"
    exit 1
fi

echo "ℹ️  Note: Railway CLI will use the resolved DATABASE_URL from your PostgreSQL service"
echo "   Make sure you have a PostgreSQL service in your Railway project"
echo ""

# Try to import using railway run
# This will execute psql with the resolved DATABASE_URL from Railway
echo "🔄 Executing import via Railway CLI..."
railway run psql < "$SQL_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Database import completed!"
    echo ""
    echo "🔍 Verifying import..."
    railway run psql -c "
    SELECT 
        'markets' as table_name, COUNT(*) as rows FROM markets
    UNION ALL
    SELECT 'predictions', COUNT(*) FROM predictions
    UNION ALL
    SELECT 'signals', COUNT(*) FROM signals
    UNION ALL
    SELECT 'trades', COUNT(*) FROM trades
    UNION ALL
    SELECT 'portfolio_snapshots', COUNT(*) FROM portfolio_snapshots;
    " 2>&1
    
    echo ""
    echo "✅ Done! Your database has been imported to Railway."
    echo "   Your web service should now connect automatically using DATABASE_URL."
else
    echo ""
    echo "❌ Import failed (exit code: $EXIT_CODE)"
    echo ""
    echo "💡 Alternative method: Use Railway Dashboard"
    echo "   1. Go to Railway dashboard"
    echo "   2. Select your PostgreSQL service"
    echo "   3. Click 'Connect' or 'Query' tab"
    echo "   4. Paste the SQL file contents"
    echo ""
    echo "   Or get the actual DATABASE_URL from Railway dashboard:"
    echo "   - Go to PostgreSQL service → Variables tab"
    echo "   - Copy the resolved DATABASE_URL (it should have actual values)"
    echo "   - Run: psql \"YOUR_RESOLVED_DATABASE_URL\" < $SQL_FILE"
    exit 1
fi


