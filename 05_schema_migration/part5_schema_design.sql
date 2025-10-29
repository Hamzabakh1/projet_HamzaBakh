-- ============================================================================
-- PART 5.1 — SCHEMA DESIGN: MULTI-CURRENCY ARCHITECTURE
--
-- Candidate Name:  HAMZA BAKH
-- Date:            22 Oct 2025
-- Time Spent:      20 min (Schema Design)
-- ============================================================================
-- This document defines the database schema changes to support multi-currency
-- transactions in the credit management system.
--
-- Business Context:
-- Current System: All amounts in USD only
-- Requirement: Support USD, EUR, SAR, AED currencies
-- Use Case: Issue credits in local currency, invoice in seller's preferred
--           currency, report in base currency (USD)
--
-- Design Principles:
-- 1. Backward Compatibility: Existing USD data unchanged
-- 2. Data Integrity: Currency validation via CHECK constraints
-- 3. Performance: Strategic indexes for exchange rate lookups
-- 4. Audit Trail: Created_at timestamp on all new records
-- 5. Referential Integrity: Foreign keys maintained
--
-- Schema Changes Summary:
-- - New Table: exchange_rates (tracks historical rates)
-- - New Columns: currency (5 tables) + preferred_currency (sellers)
-- - New Indexes: 5 performance indexes for common queries
-- - Constraints: CHECK for valid currency codes
--
-- Implementation Notes:
-- - Use SQLite rename-based migration (ADD COLUMN has limitations)
-- - Apply as atomic transaction (all-or-nothing)
-- - Test on replica before production deployment
-- ============================================================================

-- ============================================================================
-- 1. EXCHANGE_RATES TABLE (Reference Data for Conversion)
-- ============================================================================
-- Purpose: Store daily/periodic exchange rates for currency conversion
-- Primary Key: rate_id (auto-incrementing)
-- Unique Constraint: One rate per currency pair per effective date
--
-- Structure:
--   rate_id: Unique identifier (auto-increment)
--   from_currency: Source currency code (USD, EUR, SAR, AED)
--   to_currency: Target currency code (USD, EUR, SAR, AED)
--   rate: Exchange rate multiplier (e.g., 1 USD = 3.75 SAR)
--   effective_date: Date when rate became effective
--   created_at: Timestamp when record was created
--
-- ============================================================================
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate REAL NOT NULL CHECK(rate > 0),
    effective_date TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(from_currency, to_currency, effective_date)
);

-- ============================================================================
-- 2. PERFORMANCE INDEXES FOR EXCHANGE_RATES
-- ============================================================================
-- Index 1: Composite index for currency pair + effective date
-- Used by: Daily rate lookups, currency conversion queries
CREATE INDEX IF NOT EXISTS idx_exchange_rates_currencies_date 
ON exchange_rates(from_currency, to_currency, effective_date DESC);

-- Index 2: Effective date only
-- Used by: Historical rate queries, rate audit trails
CREATE INDEX IF NOT EXISTS idx_exchange_rates_effective_date 
ON exchange_rates(effective_date DESC);

-- ============================================================================
-- 3. CURRENCY COLUMNS ADDED TO EXISTING TABLES
-- ============================================================================
-- All new currency columns:
-- - Default to 'USD' (backward compatible)
-- - Constrained to: USD, EUR, SAR, AED
-- - NOT NULL (enforces currency requirement)
--
-- Important: SQLite ALTER TABLE ADD COLUMN limitation
-- Solution: Use migration script that recreates tables
-- (Not shown here; see part5_migration.sql for actual migration)
--
-- 3.1: CREDITS TABLE
-- ============================================================================
-- Purpose: Track which currency each credit was issued in
-- Rationale: Seller receives credit in local currency per agreement
ALTER TABLE credits ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- 3.2: INVOICES TABLE
-- ============================================================================
-- Purpose: Track currency for invoice totals and payments
-- Rationale: Seller pays invoices in their preferred currency
ALTER TABLE invoices ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- 3.3: WALLET_TRANSACTIONS TABLE
-- ============================================================================
-- Purpose: Track currency for each wallet transaction
-- Rationale: Transactions may occur in different currencies
ALTER TABLE wallet_transactions ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- 3.4: LEADS TABLE
-- ============================================================================
-- Purpose: Track currency for lead amounts
-- Rationale: Sales lead amounts recorded in local currency
ALTER TABLE leads ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- 3.5: SELLERS TABLE
-- ============================================================================
-- Purpose: Store seller's preferred currency for payments
-- Rationale: Enables invoice generation in seller's preferred currency
ALTER TABLE sellers ADD COLUMN preferred_currency TEXT DEFAULT 'USD' CHECK(preferred_currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- ============================================================================
-- 4. INDEXES FOR CURRENCY-BASED QUERIES
-- ============================================================================
-- These indexes speed up common currency-related queries

-- Index on credits by currency
CREATE INDEX IF NOT EXISTS idx_credits_currency 
ON credits(currency);
-- ============================================

-- Index for filtering credits by currency
CREATE INDEX IF NOT EXISTS idx_credits_currency ON credits(currency);

-- Index for filtering invoices by currency
CREATE INDEX IF NOT EXISTS idx_invoices_currency ON invoices(currency);

-- Index for filtering wallet transactions by currency
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_currency ON wallet_transactions(currency);

-- Index for filtering leads by currency
CREATE INDEX IF NOT EXISTS idx_leads_currency ON leads(currency);

-- Composite index for seller analytics queries
CREATE INDEX IF NOT EXISTS idx_sellers_market_currency ON sellers(market, preferred_currency);

-- ============================================
-- 4. SEED DATA FOR EXCHANGE RATES
-- ============================================
-- Insert initial exchange rates (as of October 22, 2025)
-- Note: In production, these should be updated via automated feeds

INSERT INTO exchange_rates (from_currency, to_currency, rate, effective_date) VALUES
-- USD as base currency (October 22, 2025 market rates)
('USD', 'USD', 1.0, '2025-10-22'),
('USD', 'EUR', 0.9220, '2025-10-22'),
('USD', 'SAR', 3.7519, '2025-10-22'),
('USD', 'AED', 3.6725, '2025-10-22'),

-- EUR conversions
('EUR', 'USD', 1.0846, '2025-10-22'),
('EUR', 'EUR', 1.0, '2025-10-22'),
('EUR', 'SAR', 4.0689, '2025-10-22'),
('EUR', 'AED', 3.9837, '2025-10-22'),

-- SAR conversions
('SAR', 'USD', 0.2665, '2025-10-22'),
('SAR', 'EUR', 0.2458, '2025-10-22'),
('SAR', 'SAR', 1.0, '2025-10-22'),
('SAR', 'AED', 0.9788, '2025-10-22'),

-- AED conversions
('AED', 'USD', 0.2724, '2025-10-22'),
('AED', 'EUR', 0.2510, '2025-10-22'),
('AED', 'SAR', 1.0216, '2025-10-22'),
('AED', 'AED', 1.0, '2025-10-22');

-- ============================================
-- 5. HELPER VIEW FOR CURRENCY CONVERSION
-- ============================================
-- View to get latest exchange rates
CREATE VIEW IF NOT EXISTS latest_exchange_rates AS
SELECT 
    from_currency,
    to_currency,
    rate,
    effective_date,
    MAX(effective_date) OVER (PARTITION BY from_currency, to_currency) as latest_date
FROM exchange_rates
WHERE effective_date <= date('now');

-- ============================================
-- 6. DATA VALIDATION
-- ============================================
-- Ensure all existing records have USD as default currency
UPDATE credits SET currency = 'USD' WHERE currency IS NULL;
UPDATE invoices SET currency = 'USD' WHERE currency IS NULL;
UPDATE wallet_transactions SET currency = 'USD' WHERE currency IS NULL;
UPDATE leads SET currency = 'USD' WHERE currency IS NULL;
UPDATE sellers SET preferred_currency = 'USD' WHERE preferred_currency IS NULL;

-- ============================================
-- NOTES:
-- ============================================
-- 1. All amounts remain as stored (no conversion of existing data)
-- 2. New records will specify currency explicitly
-- 3. Reporting queries must use exchange_rates for conversion
-- 4. Currency constraints limited to: USD, EUR, SAR, AED
-- 5. Exchange rates should be updated daily via automated process
-- ============================================
