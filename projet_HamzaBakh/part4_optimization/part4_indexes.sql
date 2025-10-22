-- ============================================
--  File: part4_indexes.sql
-- Description: Database index optimization
-- ============================================

-- Indexes to improve joins and aggregations
CREATE INDEX IF NOT EXISTS idx_sellers_id ON sellers(seller_id);
CREATE INDEX IF NOT EXISTS idx_leads_seller_id ON leads(seller_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_credits_seller_id ON credits(seller_id);
CREATE INDEX IF NOT EXISTS idx_credits_status ON credits(status);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_seller_id ON wallet_transactions(seller_id);
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_created_at ON wallet_transactions(created_at);

--  How to apply (PowerShell):
-- Get-Content .\part4_optimization\part4_indexes.sql | sqlite3 ..\exam_database.db
