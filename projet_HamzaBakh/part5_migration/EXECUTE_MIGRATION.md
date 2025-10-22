# Part 5 - How to Execute Migration

## Quick Start Guide

### Step 1: Execute the Migration

```powershell
# Navigate to project directory
cd C:\Users\Lenovo\Desktop\CODPartner\projet_HamzaBakh\projet_HamzaBakh

# Run the migration script
Get-Content .\part5_migration\part5_migration.sql | sqlite3 exam_database.db
```

**Expected Output:**
```
Credits count check: PASS
Invoices count check: PASS
Wallet transactions count check: PASS
Leads count check: PASS
Sellers count check: PASS
Credits currency check: PASS
```

---

### Step 2: Validate the Migration

```powershell
# Run validation script
.\part5_migration\validate_migration.ps1
```

**Expected Output:**
- All checks should show "YES"
- No NULL currency values
- 16 exchange rates loaded
- All backup tables created

---

### Step 3: Verify Schema Changes

```powershell
# Check credits table structure
sqlite3 exam_database.db "PRAGMA table_info(credits);"

# View exchange rates
sqlite3 exam_database.db "SELECT * FROM exchange_rates WHERE from_currency = 'USD';"

# Test the view
sqlite3 exam_database.db "SELECT * FROM latest_exchange_rates LIMIT 5;"
```

---

### Step 4: Test Currency Conversion

```powershell
# Test converting 5000 SAR to USD
sqlite3 exam_database.db "SELECT 5000 * rate as usd_equivalent FROM latest_exchange_rates WHERE from_currency = 'SAR' AND to_currency = 'USD';"

# Should output: 1350.0
```

---

### Step 5: Update a Seller's Currency (Example)

```powershell
# Update a GCC seller to use SAR
sqlite3 exam_database.db "UPDATE sellers SET preferred_currency = 'SAR' WHERE market = 'GCC' AND seller_id = 4;"

# Verify the change
sqlite3 exam_database.db "SELECT seller_id, seller_name, market, preferred_currency FROM sellers WHERE seller_id = 4;"
```

---

### Step 6: Create a Credit in Different Currency (Example)

```powershell
# Insert a new credit in SAR
sqlite3 exam_database.db "INSERT INTO credits (seller_id, amount, currency, issue_date, due_date, status) VALUES (4, 10000, 'SAR', date('now'), date('now', '+30 days'), 'New');"

# Verify with conversion
sqlite3 exam_database.db "SELECT c.credit_id, c.amount, c.currency, c.amount * er.rate as usd_equivalent FROM credits c LEFT JOIN latest_exchange_rates er ON c.currency = er.from_currency AND er.to_currency = 'USD' WHERE c.credit_id = (SELECT MAX(credit_id) FROM credits);"
```

---

### Step 7: Clean Up Backup Tables (Optional)

**⚠️ Only do this after confirming everything works!**

```powershell
sqlite3 exam_database.db "DROP TABLE _backup_credits; DROP TABLE _backup_invoices; DROP TABLE _backup_wallet_transactions; DROP TABLE _backup_leads; DROP TABLE _backup_sellers;"
```

---

## Rollback (If Needed)

If something goes wrong, restore from backup:

```powershell
# The migration script has automatic rollback
# To manually rollback:

sqlite3 exam_database.db "ROLLBACK;"

# Restore tables
sqlite3 exam_database.db "
DROP TABLE IF EXISTS credits;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS wallet_transactions;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS exchange_rates;
DROP VIEW IF EXISTS latest_exchange_rates;

ALTER TABLE _backup_credits RENAME TO credits;
ALTER TABLE _backup_invoices RENAME TO invoices;
ALTER TABLE _backup_wallet_transactions RENAME TO wallet_transactions;
ALTER TABLE _backup_leads RENAME TO leads;
ALTER TABLE _backup_sellers RENAME TO sellers;
"
```

---

## Common Queries After Migration

### 1. View Currency Distribution
```sql
SELECT currency, COUNT(*) as count 
FROM credits 
GROUP BY currency;
```

### 2. Calculate Multi-Currency Totals
```sql
SELECT 
  c.currency,
  SUM(c.amount) as total_in_currency,
  SUM(c.amount * COALESCE(er.rate, 1)) as total_in_usd
FROM credits c
LEFT JOIN latest_exchange_rates er 
  ON c.currency = er.from_currency 
  AND er.to_currency = 'USD'
GROUP BY c.currency;
```

### 3. Seller Health with Currency Conversion
```sql
SELECT 
  s.seller_id,
  s.seller_name,
  s.preferred_currency,
  SUM(c.amount * COALESCE(er.rate, 1)) as total_credits_in_seller_currency
FROM sellers s
LEFT JOIN credits c ON s.seller_id = c.seller_id
LEFT JOIN latest_exchange_rates er 
  ON c.currency = er.from_currency 
  AND s.preferred_currency = er.to_currency
WHERE s.seller_id = 101
GROUP BY s.seller_id, s.seller_name, s.preferred_currency;
```

---

## Files Reference

- **`part5_schema_design.sql`** - Schema design documentation
- **`part5_migration.sql`** - Executable migration script
- **`migration_runbook.md`** - Detailed operations guide
- **`api_impact_analysis.md`** - API changes documentation
- **`validate_migration.ps1`** - Validation script
- **`EXECUTE_MIGRATION.md`** - This file

---

## Troubleshooting

### Issue: "database is locked"
**Solution:** Close all SQLite connections and try again
```powershell
# Kill any sqlite3 processes
Get-Process sqlite3 -ErrorAction SilentlyContinue | Stop-Process
```

### Issue: "no such table: exchange_rates"
**Solution:** The migration didn't complete. Re-run the migration script.

### Issue: "NULL currency values found"
**Solution:** Run the update commands:
```sql
UPDATE credits SET currency = 'USD' WHERE currency IS NULL;
UPDATE sellers SET preferred_currency = 'USD' WHERE preferred_currency IS NULL;
```

---

## Success Criteria

✅ All validation checks pass  
✅ 16 exchange rates loaded  
✅ All tables have currency columns  
✅ No NULL currency values  
✅ Currency indexes created  
✅ latest_exchange_rates view works  
✅ All record counts match original  

---

**Migration Completed:** October 21, 2025  
**Status:** ✅ SUCCESS
