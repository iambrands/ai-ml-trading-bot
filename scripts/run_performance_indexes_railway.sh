#!/bin/bash
# Run performance indexes migration on Railway

echo "🚀 Running Performance Indexes Migration on Railway"
echo "===================================================="

# Method 1: Try Railway CLI
if command -v railway &> /dev/null; then
    echo "✅ Railway CLI found"
    echo ""
    echo "Connecting to Railway PostgreSQL..."
    echo "Once connected, run:"
    echo "  \\i src/database/migrations/002_performance_indexes.sql"
    echo ""
    echo "OR copy-paste the SQL file contents directly"
    echo ""
    railway connect postgres
    exit 0
fi

# Method 2: Use DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set and Railway CLI not found"
    echo ""
    echo "Option 1: Install Railway CLI and run:"
    echo "  railway connect postgres"
    echo "  Then: \\i src/database/migrations/002_performance_indexes.sql"
    echo ""
    echo "Option 2: Get DATABASE_URL from Railway dashboard:"
    echo "  1. Go to Railway dashboard"
    echo "  2. Select PostgreSQL service"
    echo "  3. Go to 'Variables' tab"
    echo "  4. Copy DATABASE_URL"
    echo "  5. Run: export DATABASE_URL='your-url'"
    echo "  6. Run this script again"
    exit 1
fi

echo "✅ Using DATABASE_URL"
echo "📝 Running migration..."
echo ""

psql "$DATABASE_URL" -f src/database/migrations/002_performance_indexes.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo "📊 Performance indexes have been added"
else
    echo ""
    echo "❌ Migration failed. Check the error above."
    exit 1
fi

