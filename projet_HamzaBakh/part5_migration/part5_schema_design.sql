-- ============================================
-- File: part5_schema_design.sql
-- Description: Schema design for multi-currency support
-- Business Requirement: Add multi-currency support to credit system
-- ============================================

-- ============================================
-- 1. EXCHANGE RATES TABLE
-- ============================================
-- Stores historical exchange rates for currency conversion
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate REAL NOT NULL CHECK(rate > 0),
    effective_date TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(from_currency, to_currency, effective_date)
);

-- Index for efficient rate lookups
CREATE INDEX IF NOT EXISTS idx_exchange_rates_currencies_date 
ON exchange_rates(from_currency, to_currency, effective_date DESC);

-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_exchange_rates_effective_date 
ON exchange_rates(effective_date DESC);

-- ============================================
-- 2. CURRENCY COLUMN ADDITIONS
-- ============================================

-- Add currency to credits table
-- Default: 'USD' for existing records (backward compatible)
ALTER TABLE credits ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- Add currency to invoices table
ALTER TABLE invoices ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- Add currency to wallet_transactions table
ALTER TABLE wallet_transactions ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- Add currency to leads table (for lead amount)
ALTER TABLE leads ADD COLUMN currency TEXT DEFAULT 'USD' CHECK(currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- Add preferred currency to sellers table
ALTER TABLE sellers ADD COLUMN preferred_currency TEXT DEFAULT 'USD' CHECK(preferred_currency IN ('USD', 'EUR', 'SAR', 'AED'));

-- ============================================
-- 3. INDEXES FOR PERFORMANCE
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
-- Insert initial exchange rates (as of October 2025)
-- Note: In production, these should be updated via automated feeds

INSERT INTO exchange_rates (from_currency, to_currency, rate, effective_date) VALUES
-- USD as base currency
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
