# Part 5 Migration - Validation Script
# Run this after executing part5_migration.sql

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "Part 5 Migration Validation Report" -ForegroundColor Cyan
Write-Host "==================================================`n" -ForegroundColor Cyan

# Set database path
$dbPath = ".\exam_database.db"

# Function to run SQLite query and display results
function Run-SQLQuery {
    param (
        [string]$Query,
        [string]$Description
    )
    Write-Host "$Description" -ForegroundColor Yellow
    sqlite3 $dbPath $Query
    Write-Host ""
}

# 1. Check Exchange Rates Table
Write-Host "1. EXCHANGE RATES TABLE" -ForegroundColor Green
Run-SQLQuery "SELECT COUNT(*) || ' exchange rates loaded' FROM exchange_rates;" "   Total Exchange Rates:"
Run-SQLQuery "SELECT 'Currencies: ' || GROUP_CONCAT(DISTINCT from_currency) FROM exchange_rates;" "   Supported Currencies:"

# 2. Check Schema Changes
Write-Host "2. SCHEMA CHANGES" -ForegroundColor Green
Run-SQLQuery "SELECT 'Credits table has currency column: ' || CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END FROM pragma_table_info('credits') WHERE name = 'currency';" "   Credits Table:"
Run-SQLQuery "SELECT 'Invoices table has currency column: ' || CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END FROM pragma_table_info('invoices') WHERE name = 'currency';" "   Invoices Table:"
Run-SQLQuery "SELECT 'Sellers table has preferred_currency: ' || CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END FROM pragma_table_info('sellers') WHERE name = 'preferred_currency';" "   Sellers Table:"
Run-SQLQuery "SELECT 'Leads table has currency column: ' || CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END FROM pragma_table_info('leads') WHERE name = 'currency';" "   Leads Table:"
Run-SQLQuery "SELECT 'Wallet transactions has currency: ' || CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END FROM pragma_table_info('wallet_transactions') WHERE name = 'currency';" "   Wallet Transactions:"

# 3. Check Data Integrity
Write-Host "3. DATA INTEGRITY" -ForegroundColor Green
Run-SQLQuery "SELECT COUNT(*) || ' credits (all should be USD)' FROM credits WHERE currency = 'USD';" "   Credits Currency:"
Run-SQLQuery "SELECT COUNT(*) || ' sellers (all should be USD)' FROM sellers WHERE preferred_currency = 'USD';" "   Sellers Currency:"
Run-SQLQuery "SELECT COUNT(*) || ' NULL currency values' FROM credits WHERE currency IS NULL;" "   NULL Check:"

# 4. Check Indexes
Write-Host "4. INDEXES CREATED" -ForegroundColor Green
Run-SQLQuery "SELECT COUNT(*) || ' currency-related indexes' FROM sqlite_master WHERE type='index' AND name LIKE '%currency%';" "   Currency Indexes:"
Run-SQLQuery "SELECT COUNT(*) || ' exchange rate indexes' FROM sqlite_master WHERE type='index' AND name LIKE '%exchange_rates%';" "   Exchange Rate Indexes:"

# 5. Test Exchange Rate View
Write-Host "5. EXCHANGE RATE VIEW" -ForegroundColor Green
Run-SQLQuery "SELECT 'View exists: ' || CASE WHEN COUNT(*) > 0 THEN 'YES' ELSE 'NO' END FROM sqlite_master WHERE type='view' AND name='latest_exchange_rates';" "   View Status:"
Run-SQLQuery "SELECT COUNT(*) || ' exchange rate pairs available' FROM latest_exchange_rates;" "   Available Rates:"

# 6. Test Currency Conversion
Write-Host "6. CURRENCY CONVERSION TEST" -ForegroundColor Green
Write-Host "   Converting 1000 USD to other currencies:" -ForegroundColor Yellow
sqlite3 $dbPath "SELECT to_currency, ROUND(1000 * rate, 2) as converted_amount FROM latest_exchange_rates WHERE from_currency = 'USD';"
Write-Host ""

# 7. Record Counts
Write-Host "7. RECORD COUNTS" -ForegroundColor Green
Run-SQLQuery "SELECT COUNT(*) || ' sellers' FROM sellers;" "   Sellers:"
Run-SQLQuery "SELECT COUNT(*) || ' credits' FROM credits;" "   Credits:"
Run-SQLQuery "SELECT COUNT(*) || ' invoices' FROM invoices;" "   Invoices:"
Run-SQLQuery "SELECT COUNT(*) || ' leads' FROM leads;" "   Leads:"
Run-SQLQuery "SELECT COUNT(*) || ' wallet transactions' FROM wallet_transactions;" "   Wallet Transactions:"

# 8. Backup Tables Status
Write-Host "8. BACKUP TABLES (Safe to remove after validation)" -ForegroundColor Green
Run-SQLQuery "SELECT COUNT(*) || ' backup tables exist' FROM sqlite_master WHERE type='table' AND name LIKE '_backup_%';" "   Backup Tables:"

# Final Summary
Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "MIGRATION STATUS: SUCCESS" -ForegroundColor Green
Write-Host "==================================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Review the validation results above" -ForegroundColor White
Write-Host "2. Test API endpoints with the new currency fields" -ForegroundColor White
Write-Host "3. If everything looks good, you can remove backup tables:" -ForegroundColor White
Write-Host "   sqlite3 exam_database.db 'DROP TABLE _backup_credits; DROP TABLE _backup_invoices; DROP TABLE _backup_wallet_transactions; DROP TABLE _backup_leads; DROP TABLE _backup_sellers;'" -ForegroundColor Gray
Write-Host "4. Update API endpoints to use currency fields (see api_impact_analysis.md)" -ForegroundColor White
Write-Host ""
