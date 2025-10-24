# Migration Runbook: Multi-Currency Support

## Overview
**Migration Version:** 1.0.0  
**Date:** October 22, 2025  
**Estimated Duration:** 15-20 minutes  
**Downtime Required:** Yes (5-10 minutes)  
**Database:** SQLite  

### Changes Summary
- Add `currency` column to: credits, invoices, wallet_transactions, leads, sellers
- Create `exchange_rates` table for currency conversion
- Create `latest_exchange_rates` view
- Add indexes for currency-based queries
- Default all existing records to 'USD'

---

## Pre-Migration Checklist

### 1. Backup (CRITICAL)
- [ ] Create full database backup
  ```bash
  cp exam_database.db exam_database.db.backup_$(date +%Y%m%d_%H%M%S)
  ```
- [ ] Verify backup file size matches original
- [ ] Test backup can be opened
  ```bash
  sqlite3 exam_database.db.backup_* "SELECT COUNT(*) FROM sellers;"
  ```

### 2. Environment Verification
- [ ] Confirm SQLite version >= 3.24.0
  ```bash
  sqlite3 --version
  ```
- [ ] Stop all API servers and background jobs
- [ ] Verify no active database connections
  ```bash
  lsof exam_database.db  # Unix/Linux
  ```
- [ ] Ensure sufficient disk space (3x database size)
  ```bash
  df -h .
  ```

### 3. Testing
- [ ] Migration tested on development database
- [ ] Rollback tested on development database
- [ ] Validation queries prepared
- [ ] Team notified of maintenance window

---

## Migration Execution Steps

### Step 1: Stop Services (T-0 min)
```bash
# Stop Node.js API servers
pkill -f "node server.js"

# Stop any ETL jobs
# systemctl stop etl-cron  # if applicable

# Verify no connections
lsof exam_database.db
```

**Expected Result:** No active connections to database

### Step 2: Create Backup (T+1 min)
```bash
cd /path/to/projet_HamzaBakh

# Create timestamped backup
cp exam_database.db exam_database.db.backup_$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -lh exam_database.db*
```

**Expected Result:** Backup file created with same size as original

### Step 3: Run Migration Script (T+2 min)
```bash
# Execute migration
sqlite3 exam_database.db < part5_migration/part5_migration.sql

# Check exit code
echo $?  # Should be 0
```

**Expected Result:** 
- Exit code 0 (success)
- Validation checks all show 'PASS'
- No SQL errors in output

### Step 4: Post-Migration Validation (T+7 min)

#### 4.1 Verify Schema Changes
```sql
-- Check new columns exist
PRAGMA table_info(credits);
PRAGMA table_info(invoices);
PRAGMA table_info(wallet_transactions);
PRAGMA table_info(leads);
PRAGMA table_info(sellers);

-- Expected: Each should have 'currency' column
```

#### 4.2 Verify Exchange Rates Table
```sql
SELECT COUNT(*) FROM exchange_rates;
-- Expected: 16 rows (4 currencies x 4 conversions)

SELECT * FROM exchange_rates WHERE from_currency = 'USD';
-- Expected: 4 rows with rates for EUR, SAR, AED
```

#### 4.3 Verify Data Integrity
```sql
-- Check all records have USD currency
SELECT COUNT(*) FROM credits WHERE currency = 'USD';
SELECT COUNT(*) FROM invoices WHERE currency = 'USD';
SELECT COUNT(*) FROM wallet_transactions WHERE currency = 'USD';
SELECT COUNT(*) FROM leads WHERE currency = 'USD';
SELECT COUNT(*) FROM sellers WHERE preferred_currency = 'USD';

-- Should match original counts from backup tables
```

#### 4.4 Verify Indexes Created
```sql
SELECT name FROM sqlite_master 
WHERE type = 'index' 
AND name LIKE '%currency%';

-- Expected: 5 currency-related indexes
```

#### 4.5 Test Latest Exchange Rates View
```sql
SELECT * FROM latest_exchange_rates WHERE from_currency = 'USD';
-- Expected: 4 rows with current rates
```

### Step 5: Cleanup Backup Tables (T+10 min)
```sql
-- Only after successful validation
DROP TABLE IF EXISTS _backup_credits;
DROP TABLE IF EXISTS _backup_invoices;
DROP TABLE IF EXISTS _backup_wallet_transactions;
DROP TABLE IF EXISTS _backup_leads;
DROP TABLE IF EXISTS _backup_sellers;
```

### Step 6: Restart Services (T+12 min)
```bash
# Start API servers
cd part4_optimization
node server.js &

# Start ETL jobs (if applicable)
# systemctl start etl-cron

# Verify services started
ps aux | grep node
```

### Step 7: Smoke Tests (T+15 min)
```bash
# Test API endpoints still work
curl http://localhost:3000/api/analytics/seller-health/101

# Expected: 200 OK with valid JSON
```

---

## Rollback Procedure

### When to Rollback
Execute rollback if:
- Migration script fails with errors
- Validation checks fail
- Data integrity compromised
- Critical functionality broken

### Rollback Steps (10 minutes)

#### 1. Stop All Services
```bash
pkill -f "node server.js"
```

#### 2. Restore from Backup
```bash
# Identify latest backup
ls -lt exam_database.db.backup_* | head -1

# Restore (replace TIMESTAMP with actual value)
cp exam_database.db exam_database.db.failed_migration
cp exam_database.db.backup_TIMESTAMP exam_database.db
```

#### 3. Verify Restoration
```sql
sqlite3 exam_database.db "PRAGMA table_info(credits);"
-- Expected: NO currency column

sqlite3 exam_database.db "SELECT COUNT(*) FROM sellers;"
-- Expected: Original count (e.g., 300)
```

#### 4. Restart Services
```bash
cd part4_optimization
node server.js &
```

#### 5. Verify Services
```bash
curl http://localhost:3000/api/analytics/seller-health/101
# Expected: 200 OK
```

---

## Validation Queries

### Record Count Verification
```sql
-- Compare counts
SELECT 'credits' AS table_name, COUNT(*) AS count FROM credits
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'wallet_transactions', COUNT(*) FROM wallet_transactions
UNION ALL
SELECT 'leads', COUNT(*) FROM leads
UNION ALL
SELECT 'sellers', COUNT(*) FROM sellers;
```

### Currency Distribution Check
```sql
-- All should show 100% USD after migration
SELECT 
    'credits' AS table_name,
    currency,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM credits), 2) AS percentage
FROM credits
GROUP BY currency;
```

### Exchange Rates Validation
```sql
-- Verify rate consistency (USD->EUR->USD should equal 1.0)
SELECT 
    e1.from_currency,
    e1.to_currency,
    e1.rate AS forward_rate,
    e2.rate AS reverse_rate,
    ROUND(e1.rate * e2.rate, 4) AS round_trip
FROM exchange_rates e1
JOIN exchange_rates e2 
    ON e1.from_currency = e2.to_currency 
    AND e1.to_currency = e2.from_currency
WHERE e1.effective_date = '2025-01-01';

-- Expected: round_trip values close to 1.0
```

### Index Performance Test
```sql
-- Should use currency index
EXPLAIN QUERY PLAN
SELECT * FROM credits WHERE currency = 'USD';

-- Expected: "USING INDEX idx_credits_currency"
```

---

## Breaking Changes & API Impact

### 1. Database Schema Changes
**Impact:** Low (backward compatible)
- New columns have DEFAULT values
- Existing queries continue to work
- No columns removed or renamed

### 2. API Response Changes
**Impact:** None immediately
- APIs return same data structure
- Currency field available but not populated in responses yet

### 3. Required API Updates (Phase 2)
The following endpoints need updates to expose currency:

#### High Priority:
- `GET /api/analytics/seller-health/:seller_id`
  - Add `currency` to metrics
  - Add `converted_amounts` object with USD equivalents
  
#### Medium Priority:
- `POST /api/credits` - Accept currency in request body
- `GET /api/credits/:credit_id` - Include currency in response
- `GET /api/invoices/:invoice_id` - Include currency in response

#### Low Priority:
- Dashboard aggregations - Show multi-currency totals
- Reporting endpoints - Add currency conversion

---

## Monitoring & Post-Migration

### Key Metrics to Watch (First 24 hours)
1. **API Response Times**
   - Baseline: 50-200ms
   - Alert if: >500ms

2. **Database Query Performance**
   ```sql
   -- Monitor slow queries
   EXPLAIN QUERY PLAN SELECT * FROM credits WHERE currency = 'EUR';
   ```

3. **Error Rates**
   - Check application logs for currency-related errors
   - Monitor 500 errors on currency endpoints

### Health Check Queries
```sql
-- Run every hour for first 24 hours
SELECT 
    'Health Check' AS status,
    (SELECT COUNT(*) FROM exchange_rates) AS exchange_rates_count,
    (SELECT COUNT(DISTINCT currency) FROM credits) AS credit_currencies,
    datetime('now') AS checked_at;
```

---

## Troubleshooting

### Issue: Migration script fails mid-execution
**Solution:** Transaction will auto-rollback. Restore from backup.

### Issue: Currency column shows NULL values
**Solution:**
```sql
UPDATE credits SET currency = 'USD' WHERE currency IS NULL;
-- Repeat for other tables
```

### Issue: Exchange rates not showing in view
**Solution:**
```sql
DROP VIEW IF EXISTS latest_exchange_rates;
-- Re-run view creation from migration script
```

### Issue: Indexes not being used
**Solution:**
```sql
ANALYZE;  -- Update SQLite query planner statistics
```

---

## Communication Template

### Pre-Migration Announcement (24 hours before)
```
Subject: Scheduled Database Maintenance - Multi-Currency Support

The credit management system will undergo a schema migration to support 
multi-currency transactions.

Maintenance Window: [DATE] [TIME] (15-20 minutes)
Impact: API downtime during migration
Action Required: None

Details: Adding currency support to credits, invoices, and transactions.
All existing data will default to USD.

Contact: [YOUR EMAIL] for questions
```

### Post-Migration Announcement
```
Subject: Migration Complete - Multi-Currency Support Enabled

The database migration completed successfully.

Start Time: [TIME]
End Time: [TIME]
Duration: [X] minutes
Status: ✅ Success

Validation Results:
- All records migrated: ✅
- Data integrity verified: ✅
- Indexes created: ✅
- APIs operational: ✅

Next Steps: Phase 2 API updates will be deployed next sprint.
```

---

## Appendix

### A. File Locations
- Migration Script: `part5_migration/part5_migration.sql`
- Schema Design: `part5_migration/part5_schema_design.sql`
- Database: `exam_database.db`
- Backups: `exam_database.db.backup_*`

### B. Team Contacts
- Database Lead: [NAME]
- API Team: [NAME]
- DevOps: [NAME]
- On-call: [PHONE]

### C. Useful Commands
```bash
# Database size
du -h exam_database.db

# Record counts
sqlite3 exam_database.db "SELECT COUNT(*) FROM credits;"

# Table schema
sqlite3 exam_database.db ".schema credits"

# Compact database (after migration)
sqlite3 exam_database.db "VACUUM;"
```

---

**Migration prepared by:** Data Engineering Team  
**Approved by:** Technical Lead  
**Date:** October 21, 2025
