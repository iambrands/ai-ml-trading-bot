#!/bin/bash
# Script to add database indexes using Railway CLI
# This script will attempt to use Railway CLI to connect and run the SQL

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SQL_FILE="$SCRIPT_DIR/add_performance_indexes.sql"

echo "=========================================="
echo "Adding Database Indexes via Railway CLI"
echo "=========================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed"
    echo ""
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
    
    if ! command -v railway &> /dev/null; then
        echo "❌ Failed to install Railway CLI"
        echo "Please install manually: npm install -g @railway/cli"
        exit 1
    fi
    echo "✅ Railway CLI installed"
fi

echo "✅ Railway CLI found: $(which railway)"
echo ""

# Check if logged in
echo "Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "⚠️  Not logged in to Railway"
    echo "Please run: railway login"
    exit 1
fi

echo "✅ Authenticated with Railway"
echo ""

# Check if project is linked
echo "Checking project link..."
if [ ! -f "$PROJECT_ROOT/.railway" ] && ! railway status &> /dev/null; then
    echo "⚠️  Project not linked"
    echo "Please run: railway link"
    exit 1
fi

echo "✅ Project linked"
echo ""

# Check if SQL file exists
if [ ! -f "$SQL_FILE" ]; then
    echo "❌ SQL file not found: $SQL_FILE"
    exit 1
fi

echo "✅ SQL file found: $SQL_FILE"
echo ""

echo "=========================================="
echo "Attempting to connect to PostgreSQL..."
echo "=========================================="
echo ""
echo "⚠️  Note: Railway CLI's 'connect postgres' opens an interactive session."
echo "    We'll provide instructions for manual execution, or you can use"
echo "    the DATABASE_URL method instead."
echo ""

# Try to get DATABASE_URL using Railway CLI
echo "Trying to get DATABASE_URL..."
if DATABASE_URL=$(railway variables get DATABASE_URL --service postgres 2>/dev/null); then
    echo "✅ Got DATABASE_URL"
    echo ""
    echo "Attempting to run SQL directly using psql..."
    
    if command -v psql &> /dev/null; then
        # Try to use the DATABASE_URL directly
        # Note: This might fail if using internal network URL
        if psql "$DATABASE_URL" -f "$SQL_FILE" 2>/dev/null; then
            echo ""
            echo "✅ SUCCESS! Indexes have been added."
            exit 0
        else
            echo "⚠️  Direct psql connection failed (may need Railway tunnel)"
        fi
    else
        echo "⚠️  psql not found - cannot use direct connection"
    fi
else
    echo "⚠️  Could not get DATABASE_URL from Railway CLI"
fi

echo ""
echo "=========================================="
echo "Manual Instructions"
echo "=========================================="
echo ""
echo "Since automated execution isn't possible, please run manually:"
echo ""
echo "1. Connect to Railway database:"
echo "   railway connect postgres"
echo ""
echo "2. Once connected, copy and paste this SQL:"
echo ""
cat "$SQL_FILE"
echo ""
echo "3. Press Enter to execute"
echo ""
echo "OR use the alternative method with DATABASE_URL:"
echo ""
echo "1. Get DATABASE_URL:"
echo "   railway variables get DATABASE_URL --service postgres"
echo ""
echo "2. Use Railway TCP Proxy (from Railway dashboard)"
echo "   or use: psql \"\$DATABASE_URL\" -f $SQL_FILE"
echo ""

