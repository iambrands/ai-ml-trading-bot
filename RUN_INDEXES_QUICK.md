# Quick Guide: Run Database Indexes

## If You're Already in a psql Session

### Easiest Method: Use `\i` command

```sql
\i /Users/iabadvisors/ai-ml-trading-bot/scripts/add_performance_indexes.sql
```

This will execute the entire SQL file automatically.

---

## If You Need to Connect First

```bash
# 1. Connect to Railway database
railway connect postgres

# 2. Once connected, run:
\i /Users/iabadvisors/ai-ml-trading-bot/scripts/add_performance_indexes.sql

# 3. Exit when done:
\q
```

---

## Alternative: Copy-Paste Method

1. Open `scripts/add_performance_indexes.sql` in your editor
2. Copy lines 4-42 (the CREATE INDEX statements)
3. Paste into your psql session
4. Press Enter

---

## Verify Indexes Were Created

After running the SQL, verify:

```sql
SELECT 
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
    AND (indexname LIKE 'idx_%_created_at%'
         OR indexname LIKE 'idx_%_entry_time%'
         OR indexname LIKE 'idx_%_snapshot_time%'
         OR indexname LIKE 'idx_%_prediction_time%')
ORDER BY tablename, indexname;
```

You should see ~10 indexes.

---

## Expected Result

- **Before**: 60+ seconds page load
- **After**: <2 seconds page load ✅

---

*Quick Reference: scripts/add_performance_indexes.sql*


