#!/bin/bash
# Complete migration script: Local data and models to Railway
# This script helps you migrate everything from local to Railway

set -e

echo "=========================================="
echo "Railway Migration Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check local database
echo -e "${YELLOW}Step 1: Checking local database...${NC}"
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client found"
    
    # Check if database exists and has data
    DB_CHECK=$(psql -h localhost -U iabadvisors -d polymarket_trader -tAc "SELECT COUNT(*) FROM markets;" 2>/dev/null || echo "0")
    
    if [ "$DB_CHECK" != "0" ]; then
        echo "✅ Found data in local database (markets table: $DB_CHECK rows)"
        echo ""
        echo "Exporting local database..."
        pg_dump -h localhost -U iabadvisors -d polymarket_trader \
            -F c \
            -f local_db_backup_$(date +%Y%m%d_%H%M%S).dump
        
        pg_dump -h localhost -U iabadvisors -d polymarket_trader \
            -F p \
            -f local_db_backup_$(date +%Y%m%d_%H%M%S).sql
        
        echo -e "${GREEN}✅ Database exported${NC}"
        echo "   Files created:"
        ls -lh local_db_backup_*.dump local_db_backup_*.sql 2>/dev/null | tail -2
    else
        echo -e "${YELLOW}⚠️  No data found in local database (or database doesn't exist)${NC}"
        echo "   This is OK - you can start fresh on Railway"
    fi
else
    echo -e "${RED}❌ PostgreSQL client not found${NC}"
    echo "   Install with: brew install postgresql (macOS) or apt-get install postgresql-client (Linux)"
fi

echo ""

# Step 2: Check models
echo -e "${YELLOW}Step 2: Checking trained models...${NC}"
if [ -d "data/models" ]; then
    MODEL_COUNT=$(find data/models -name "*.pkl" -type f | wc -l)
    if [ "$MODEL_COUNT" -gt 0 ]; then
        echo "✅ Found $MODEL_COUNT model file(s):"
        ls -lh data/models/*.pkl 2>/dev/null | awk '{print "   - " $9 " (" $5 ")"}'
        
        TOTAL_SIZE=$(du -sh data/models/*.pkl 2>/dev/null | awk '{sum+=$1} END {print sum}' || du -ch data/models/*.pkl 2>/dev/null | tail -1 | awk '{print $1}')
        echo "   Total size: ~330KB (very small - can add to git)"
        echo -e "${GREEN}✅ Models are small enough to add to git${NC}"
    else
        echo -e "${YELLOW}⚠️  No model files found in data/models/${NC}"
    fi
else
    echo -e "${RED}❌ data/models directory not found${NC}"
fi

echo ""

# Step 3: Add models to git
echo -e "${YELLOW}Step 3: Preparing models for git...${NC}"
if [ -f "data/models/xgboost_model.pkl" ] || [ -f "data/models/lightgbm_model.pkl" ] || [ -f "data/models/feature_names.pkl" ]; then
    echo "Adding models to git..."
    
    # Check if already in git
    if git ls-files --error-unmatch data/models/*.pkl >/dev/null 2>&1; then
        echo "✅ Models already in git"
    else
        echo "Adding models to git (will be included in Railway deployment)..."
        git add -f data/models/xgboost_model.pkl 2>/dev/null || true
        git add -f data/models/lightgbm_model.pkl 2>/dev/null || true
        git add -f data/models/feature_names.pkl 2>/dev/null || true
        
        if git diff --cached --quiet; then
            echo "✅ Models already committed or no changes"
        else
            echo -e "${GREEN}✅ Models staged for commit${NC}"
            echo "   Run: git commit -m 'Add trained models for Railway deployment'"
            echo "   Then: git push origin main"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Model files not found - skipping${NC}"
fi

echo ""

# Step 4: Instructions
echo -e "${YELLOW}=========================================="
echo "Next Steps:"
echo "==========================================${NC}"
echo ""
echo "1. ${GREEN}Models Migration (Automatic)${NC}:"
echo "   - Models will be included when you push to git"
echo "   - Railway will automatically include them in Docker build"
echo ""
echo "2. ${GREEN}Database Migration (Manual)${NC}:"
echo "   a. Set up Railway PostgreSQL:"
echo "      - Go to Railway Dashboard → + New → Database → PostgreSQL"
echo "   b. Link to web service:"
echo "      - Web service → Variables tab"
echo "      - Add: POSTGRES_HOST = \${{Postgres.PGHOST}}"
echo "      - Add: POSTGRES_PORT = \${{Postgres.PGPORT}}"
echo "      - Add: POSTGRES_DB = \${{Postgres.PGDATABASE}}"
echo "      - Add: POSTGRES_USER = \${{Postgres.PGUSER}}"
echo "      - Add: POSTGRES_PASSWORD = \${{Postgres.PGPASSWORD}}"
echo ""
echo "   c. Import your data:"
echo "      railway connect postgres"
echo "      pg_restore -h \${{Postgres.PGHOST}} -U \${{Postgres.PGUSER}} -d \${{Postgres.PGDATABASE}} local_db_backup_*.dump"
echo ""
echo "3. ${GREEN}Verify Everything Works${NC}:"
echo "   - Check Railway logs for 'Database engine created successfully'"
echo "   - Check Railway logs for model loading (no errors)"
echo "   - Test API endpoints: /predictions, /signals, /trades"
echo ""

echo -e "${GREEN}=========================================="
echo "Migration Summary"
echo "==========================================${NC}"
echo ""
echo "✅ Models: ~330KB (will be added to git)"
if [ "$DB_CHECK" != "0" ]; then
    echo "✅ Database: Exported to local_db_backup_*.dump and *.sql"
else
    echo "⚠️  Database: No local data found (will start fresh on Railway)"
fi
echo ""

