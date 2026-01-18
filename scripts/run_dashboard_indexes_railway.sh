#!/bin/bash

# Script to apply dashboard timeout fix indexes to Railway database

echo "=========================================="
echo "  DASHBOARD TIMEOUT FIX - ADD INDEXES"
echo "=========================================="
echo ""

# Check if Railway CLI is available
if command -v railway &> /dev/null; then
    echo "✅ Railway CLI found"
    
    # Try to connect and run migration
    echo ""
    echo "Running migration via Railway CLI..."
    railway connect postgres --command "\\i src/database/migrations/003_fix_dashboard_timeout.sql"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Migration applied successfully!"
    else
        echo ""
        echo "⚠️  Railway CLI command failed. Try manual method below."
    fi
else
    echo "⚠️  Railway CLI not found"
fi

echo ""
echo "=========================================="
echo "  ALTERNATIVE: Manual Method"
echo "=========================================="
echo ""
echo "1. Go to Railway Dashboard: https://railway.app"
echo "2. Select your PostgreSQL service"
echo "3. Click 'Query' tab"
echo "4. Copy and paste the SQL from:"
echo "   src/database/migrations/003_fix_dashboard_timeout.sql"
echo "5. Click 'Execute'"
echo ""
echo "OR use psql with DATABASE_URL:"
echo "   psql \$DATABASE_URL -f src/database/migrations/003_fix_dashboard_timeout.sql"
echo ""

