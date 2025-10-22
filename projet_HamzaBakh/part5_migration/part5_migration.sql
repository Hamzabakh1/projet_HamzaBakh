-- ============================================
-- File: part5_migration.sql
-- Description: Complete migration script with rollback capability
-- Version: 1.0.0
-- Date: 2025-10-21
-- ============================================

-- ============================================
-- MIGRATION TRANSACTION START
-- ============================================
BEGIN TRANSACTION;

-- ============================================
-- STEP 1: CREATE EXCHANGE_RATES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate REAL NOT NULL CHECK(rate > 0),
    effective_date TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(from_currency, to_currency, effective_date)
);

-- ============================================
-- STEP 2: CREATE BACKUP TABLES (for rollback)
-- ============================================
CREATE TABLE IF NOT EXISTS _backup_credits AS SELECT * FROM credits;
CREATE TABLE IF NOT EXISTS _backup_invoices AS SELECT * FROM invoices;
CREATE TABLE IF NOT EXISTS _backup_wallet_transactions AS SELECT * FROM wallet_transactions;
CREATE TABLE IF NOT EXISTS _backup_leads AS SELECT * FROM leads;
CREATE TABLE IF NOT EXISTS _backup_sellers AS SELECT * FROM sellers;

-- ============================================
-- STEP 3: ADD CURRENCY COLUMNS
-- ============================================
-- SQLite doesn't support ALTER TABLE ADD COLUMN with CHECK constraints directly
-- We need to recreate tables with new schema

-- 3.1: Migrate CREDITS table
CREATE TABLE credits_new (
    credit_id INTEGER PRIMARY KEY,
    seller_id INTEGER,
    amount REAL,
    issue_date TEXT,
    due_date TEXT,
    status TEXT,
    currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'))
);

INSERT INTO credits_new (credit_id, seller_id, amount, issue_date, due_date, status, currency)
SELECT credit_id, seller_id, amount, issue_date, due_date, status, 'USD' FROM credits;

DROP TABLE credits;
ALTER TABLE credits_new RENAME TO credits;

-- 3.2: Migrate INVOICES table
CREATE TABLE invoices_new (
    invoice_id TEXT PRIMARY KEY,
    seller_id INTEGER,
    period_start TEXT,
    period_end TEXT,
    sales_amount REAL,
    fees REAL,
    credits_due REAL,
    from_balance REAL,
    total REAL,
    currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'))
);

INSERT INTO invoices_new (invoice_id, seller_id, period_start, period_end, sales_amount, fees, credits_due, from_balance, total, currency)
SELECT invoice_id, seller_id, period_start, period_end, sales_amount, fees, credits_due, from_balance, total, 'USD' FROM invoices;

DROP TABLE invoices;
ALTER TABLE invoices_new RENAME TO invoices;

-- 3.3: Migrate WALLET_TRANSACTIONS table
CREATE TABLE wallet_transactions_new (
    transaction_id TEXT PRIMARY KEY,
    seller_id INTEGER,
    type TEXT,
    amount REAL,
    created_at TEXT,
    currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'))
);

INSERT INTO wallet_transactions_new (transaction_id, seller_id, type, amount, created_at, currency)
SELECT transaction_id, seller_id, type, amount, created_at, 'USD' FROM wallet_transactions;

DROP TABLE wallet_transactions;
ALTER TABLE wallet_transactions_new RENAME TO wallet_transactions;

-- 3.4: Migrate LEADS table
CREATE TABLE leads_new (
    lead_id INTEGER PRIMARY KEY,
    seller_id INTEGER,
    created_at TEXT,
    amount REAL,
    status TEXT,
    shipping_status TEXT,
    tracking_number TEXT,
    currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'))
);

INSERT INTO leads_new (lead_id, seller_id, created_at, amount, status, shipping_status, tracking_number, currency)
SELECT lead_id, seller_id, created_at, amount, status, shipping_status, tracking_number, 'USD' FROM leads;

DROP TABLE leads;
ALTER TABLE leads_new RENAME TO leads;

-- 3.5: Migrate SELLERS table
CREATE TABLE sellers_new (
    seller_id INTEGER PRIMARY KEY,
    seller_name TEXT,
    market TEXT,
    signup_date TEXT,
    credit_limit REAL,
    avg_weekly_leads INTEGER,
    initial_wallet REAL,
    am_id INTEGER,
    sam_id INTEGER,
    preferred_currency TEXT DEFAULT 'USD' CHECK(preferred_currency IN ('USD', 'EUR', 'SAR', 'AED'))
);

INSERT INTO sellers_new (seller_id, seller_name, market, signup_date, credit_limit, avg_weekly_leads, initial_wallet, am_id, sam_id, preferred_currency)
SELECT seller_id, seller_name, market, signup_date, credit_limit, avg_weekly_leads, initial_wallet, am_id, sam_id, 'USD' FROM sellers;

DROP TABLE sellers;
ALTER TABLE sellers_new RENAME TO sellers;

-- ============================================
-- STEP 4: CREATE INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_exchange_rates_currencies_date 
ON exchange_rates(from_currency, to_currency, effective_date DESC);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_effective_date 
ON exchange_rates(effective_date DESC);

CREATE INDEX IF NOT EXISTS idx_credits_currency ON credits(currency);
CREATE INDEX IF NOT EXISTS idx_invoices_currency ON invoices(currency);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_currency ON wallet_transactions(currency);
CREATE INDEX IF NOT EXISTS idx_leads_currency ON leads(currency);
CREATE INDEX IF NOT EXISTS idx_sellers_market_currency ON sellers(market, preferred_currency);

-- Recreate original indexes
CREATE INDEX IF NOT EXISTS idx_sellers_id ON sellers(seller_id);
CREATE INDEX IF NOT EXISTS idx_leads_seller_id ON leads(seller_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_credits_seller_id ON credits(seller_id);
CREATE INDEX IF NOT EXISTS idx_credits_status ON credits(status);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_seller_id ON wallet_transactions(seller_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_created_at ON wallet_transactions(created_at);

-- ============================================
-- STEP 5: INSERT SEED EXCHANGE RATES
-- ============================================
INSERT INTO exchange_rates (from_currency, to_currency, rate, effective_date) VALUES
-- USD as base
('USD', 'USD', 1.0, '2025-01-01'),
('USD', 'EUR', 0.92, '2025-01-01'),
('USD', 'SAR', 3.75, '2025-01-01'),
('USD', 'AED', 3.67, '2025-01-01'),
-- EUR conversions
('EUR', 'USD', 1.09, '2025-01-01'),
('EUR', 'EUR', 1.0, '2025-01-01'),
('EUR', 'SAR', 4.08, '2025-01-01'),
('EUR', 'AED', 4.00, '2025-01-01'),
-- SAR conversions
('SAR', 'USD', 0.27, '2025-01-01'),
('SAR', 'EUR', 0.25, '2025-01-01'),
('SAR', 'SAR', 1.0, '2025-01-01'),
('SAR', 'AED', 0.98, '2025-01-01'),
-- AED conversions
('AED', 'USD', 0.27, '2025-01-01'),
('AED', 'EUR', 0.25, '2025-01-01'),
('AED', 'SAR', 1.02, '2025-01-01'),
('AED', 'AED', 1.0, '2025-01-01');

-- ============================================
-- STEP 6: CREATE HELPER VIEW
-- ============================================
CREATE VIEW IF NOT EXISTS latest_exchange_rates AS
SELECT 
    from_currency,
    to_currency,
    rate,
    effective_date
FROM exchange_rates e1
WHERE effective_date = (
    SELECT MAX(effective_date)
    FROM exchange_rates e2
    WHERE e1.from_currency = e2.from_currency
    AND e1.to_currency = e2.to_currency
    AND e2.effective_date <= date('now')
);

-- ============================================
-- STEP 7: VALIDATION CHECKS
-- ============================================
-- Verify record counts match
SELECT 'Credits count check: ' || 
    CASE WHEN (SELECT COUNT(*) FROM credits) = (SELECT COUNT(*) FROM _backup_credits)
    THEN 'PASS' ELSE 'FAIL' END;

SELECT 'Invoices count check: ' || 
    CASE WHEN (SELECT COUNT(*) FROM invoices) = (SELECT COUNT(*) FROM _backup_invoices)
    THEN 'PASS' ELSE 'FAIL' END;

SELECT 'Wallet transactions count check: ' || 
    CASE WHEN (SELECT COUNT(*) FROM wallet_transactions) = (SELECT COUNT(*) FROM _backup_wallet_transactions)
    THEN 'PASS' ELSE 'FAIL' END;

SELECT 'Leads count check: ' || 
    CASE WHEN (SELECT COUNT(*) FROM leads) = (SELECT COUNT(*) FROM _backup_leads)
    THEN 'PASS' ELSE 'FAIL' END;

SELECT 'Sellers count check: ' || 
    CASE WHEN (SELECT COUNT(*) FROM sellers) = (SELECT COUNT(*) FROM _backup_sellers)
    THEN 'PASS' ELSE 'FAIL' END;

-- Verify all currencies are USD
SELECT 'Credits currency check: ' || 
    CASE WHEN (SELECT COUNT(DISTINCT currency) FROM credits) = 1 
    AND (SELECT currency FROM credits LIMIT 1) = 'USD'
    THEN 'PASS' ELSE 'FAIL' END;

-- ============================================
-- COMMIT TRANSACTION
-- ============================================
COMMIT;

-- ============================================
-- CLEANUP (Optional - run after validation)
-- ============================================
-- DROP TABLE IF EXISTS _backup_credits;
-- DROP TABLE IF EXISTS _backup_invoices;
-- DROP TABLE IF EXISTS _backup_wallet_transactions;
-- DROP TABLE IF EXISTS _backup_leads;
-- DROP TABLE IF EXISTS _backup_sellers;

-- ============================================
-- ROLLBACK SCRIPT (Run if migration fails)
-- ============================================
-- ROLLBACK;
-- 
-- -- Restore from backups
-- DROP TABLE IF EXISTS credits;
-- DROP TABLE IF EXISTS invoices;
-- DROP TABLE IF EXISTS wallet_transactions;
-- DROP TABLE IF EXISTS leads;
-- DROP TABLE IF EXISTS sellers;
-- DROP TABLE IF EXISTS exchange_rates;
-- DROP VIEW IF EXISTS latest_exchange_rates;
-- 
-- ALTER TABLE _backup_credits RENAME TO credits;
-- ALTER TABLE _backup_invoices RENAME TO invoices;
-- ALTER TABLE _backup_wallet_transactions RENAME TO wallet_transactions;
-- ALTER TABLE _backup_leads RENAME TO leads;
-- ALTER TABLE _backup_sellers RENAME TO sellers;
--
-- -- Recreate original indexes
-- CREATE INDEX IF NOT EXISTS idx_sellers_id ON sellers(seller_id);
-- CREATE INDEX IF NOT EXISTS idx_leads_seller_id ON leads(seller_id);
-- CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
-- CREATE INDEX IF NOT EXISTS idx_credits_seller_id ON credits(seller_id);
-- CREATE INDEX IF NOT EXISTS idx_credits_status ON credits(status);
-- CREATE INDEX IF NOT EXISTS idx_wallet_transactions_seller_id ON wallet_transactions(seller_id);
-- CREATE INDEX IF NOT EXISTS idx_wallet_transactions_created_at ON wallet_transactions(created_at);
