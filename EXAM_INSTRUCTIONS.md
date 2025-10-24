# Mid-Level Data Engineer/Analyst Technical Assessment

**Duration:** 4-6 hours (can be split over 2 days)  
**Format:** Take-home coding challenge  
**Dataset:** Credit Management System (217K+ records)

---

## 📋 Overview

This assessment evaluates your ability to work with real-world financial data, build production-quality data pipelines, optimize database queries, and communicate technical decisions effectively.

You will work with a credit management system dataset containing:
- 300 sellers across two markets (GCC, AFRQ)
- 800 credit records with lifecycle tracking
- 27,600 invoices and 138,000 invoice items
- 20,000 sales leads
- Account manager hierarchies and wallet transactions

## 🎯 Assessment Structure

| Part | Focus Area | Time | Weight |
|------|------------|------|--------|
| 1 | Data Exploration & Business Analysis | 90 min | 25% |
| 2 | Data Quality & Validation | 90 min | 30% |
| 3 | ETL Pipeline Development | 90 min | 25% |
| 4 | Database & API Optimization | 60 min | 15% |
| 5 | Schema Migration & Documentation | 45 min | 5% |

**Total: 4-6 hours**

---

## Part 1: Data Exploration & Business Analysis (90 minutes)

### Objective
Demonstrate SQL/Python proficiency and business acumen by analyzing the credit management dataset.

### Tasks

Using SQL queries and/or Python (pandas), answer the following questions:

**1.1 Credit Approval Analysis**
Calculate the credit approval rate by market (GCC vs AFRQ). Approval rate = (Approved + Paid + Deposit credits) / Total credits requested.

**1.2 Account Manager Performance**
Identify the top 5 account managers by:
- Total credit volume issued to their sellers
- Average seller credit utilization rate (sum of credits issued / sum of credit limits)
- Include AM name, email, and calculated metrics

**1.3 Lead Conversion Efficiency**
Calculate the lead conversion rate (Confirmed leads / Total leads) by:
- Market (GCC vs AFRQ)
- Seller credit status (has active credit vs no active credit)

Determine if sellers with active credits have higher conversion rates.

**1.4 Revenue Efficiency Metric**
Identify the top 5 sellers by "revenue per credit dollar" metric:
- Formula: Total confirmed lead amount / Total credit amount issued
- Only include sellers who have received at least one credit
- Show seller name, market, total credits, total confirmed leads value, and efficiency ratio

**1.5 Credit-to-Lead Timeline**
Calculate the average time (in days) between:
- Credit approval date → First confirmed lead creation date

Group by market. What insights can you derive?

### Deliverables
- Jupyter notebook (`part1_analysis.ipynb`) with:
  - SQL queries OR pandas code for each question
  - Results displayed clearly (tables/charts)
  - 2-3 sentence business insight for each question
  - At least one data visualization

### Evaluation Criteria
- ✅ Query correctness (results are accurate)
- ✅ Efficient SQL (proper joins, no unnecessary subqueries)
- ✅ Clear presentation of results
- ✅ Quality of business insights
- ✅ Code readability and comments

---

## Part 2: Data Quality & Validation (90 minutes)

### Objective
Build a comprehensive data quality validation framework to detect integrity issues, logical inconsistencies, and anomalies.

### Tasks

**2.1 Referential Integrity Checks**
Validate all foreign key relationships:
- Sellers → Account Managers (am_id)
- Sellers → Senior Account Managers (sam_id)
- Credits → Sellers (seller_id)
- Invoices → Sellers (seller_id)
- Leads → Sellers (seller_id)
- Wallet Transactions → Sellers (seller_id)

Report any orphaned records.

**2.2 Business Logic Validation**
Detect the following inconsistencies:
1. **Credit limit violations**: Sellers with total issued credits > credit_limit
2. **Invoice arithmetic errors**: Invoice total ≠ sales_amount - fees - credits_due - abs(negative from_balance)
3. **Temporal violations**: 
   - Leads created before seller signup_date
   - Credits issued before seller signup_date
   - Due dates before issue dates
4. **Wallet inconsistencies**: Wallet transactions that don't correspond to invoice totals

**2.3 Statistical Outlier Detection**
Flag records that are statistical outliers:
- Credit amounts > 99th percentile or < 1st percentile
- Sellers with 0 leads but active credits
- Invoice fees > 40% or < 5% of sales_amount
- Sellers with extremely low (<0.1) or high (>0.9) lead conversion rates

**2.4 Credit Lifecycle Reconciliation**
The credit status can be: New, InReview, Approved, Paid, Deposit, Cancelled

Reconstruct the *expected* final status for each credit based on:
- Invoice totals generated after credit issue_date
- Whether due_date has passed
- Credit history progression

Compare expected vs actual status. Generate a report showing:
- Number of mismatches
- Top 10 examples with explanation
- Possible root causes

**2.5 Data Quality Scorecard**
Generate a summary scorecard:
```
Entity          | Total Records | Clean Records | Issues | Quality Score (%)
----------------|---------------|---------------|--------|------------------
Sellers         | 300           | 298           | 2      | 99.3%
Credits         | 800           | 750           | 50     | 93.8%
...
```

### Deliverables
- Python script (`part2_data_quality.py`) with:
  - Validation functions for each check
  - Proper error handling and logging
  - CSV output: `data_quality_report.csv`
- Markdown report (`data_quality_findings.md`) with:
  - Summary of issues found
  - Severity classification (Critical/Warning/Info)
  - Recommendations for remediation

### Evaluation Criteria
- ✅ Completeness (all checks implemented)
- ✅ Code quality (modular, reusable functions)
- ✅ Accurate detection of issues
- ✅ Clear, actionable reporting
- ✅ Proper use of logging (not just print)

---

## Part 3: ETL Pipeline Development (90 minutes)

### Objective
Design and implement an incremental ETL pipeline that safely loads new data into the existing database.

### Scenario
Your company receives updated CSV files daily. The pipeline must handle:
- New records (new sellers, credits, leads)
- Updated records (credit status changes, invoice corrections)
- Duplicate records (same ID submitted multiple times)

### Requirements

**3.1 Pipeline Design**
Implement a Python class `IncrementalETL` with methods:
- `validate_schema(csv_file)` - Verify CSV has expected columns and data types
- `detect_changes(csv_file, table_name)` - Identify new vs updated vs duplicate records
- `load_data(csv_file, table_name)` - Load data with proper transaction handling
- `generate_load_report()` - Return summary of records added/updated/skipped/failed

**3.2 Data Validation**
Before loading, validate:
- Required fields are not null
- Foreign keys exist in parent tables
- Data types are correct
- Business rules (e.g., amount > 0, dates are valid)

**3.3 Idempotency**
The pipeline must be idempotent:
- Running twice with same data should not create duplicates
- Use upsert logic (INSERT or UPDATE based on primary key)

**3.4 Transaction Management**
- All changes for one file must be in a single transaction
- Rollback entirely if critical errors occur
- Continue with warnings for non-critical issues

**3.5 Logging & Monitoring**
- Use Python's `logging` module (not print statements)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Create structured logs: timestamp, operation, record_id, status, message
- Export log to `etl_execution.log`

**3.6 Error Handling**
Handle gracefully:
- Missing CSV files
- Schema mismatches
- Database connection failures
- Constraint violations

### Test Scenario
We've provided incremental CSV files in `exam_test_dataset/incremental/`:
- `incremental_sellers.csv` (3 new sellers, 2 updates to existing)
- `incremental_credits.csv` (10 new credits, 1 duplicate, 1 with invalid seller_id)

Your pipeline should handle these correctly.

### Deliverables
- Python module (`part3_etl_pipeline.py`) with:
  - `IncrementalETL` class
  - Comprehensive error handling
  - Unit tests for key functions (optional but highly valued)
- Execution log (`etl_execution.log`)
- Load summary report (`etl_load_summary.json`) in format:
```json
{
  "file": "incremental_sellers.csv",
  "timestamp": "2025-10-10T14:30:00",
  "records_processed": 5,
  "records_inserted": 3,
  "records_updated": 2,
  "records_skipped": 0,
  "errors": []
}
```

### Evaluation Criteria
- ✅ Idempotency implemented correctly
- ✅ Transaction handling (atomicity)
- ✅ Comprehensive error handling
- ✅ Proper logging (structured, appropriate levels)
- ✅ Code organization (class structure, modularity)
- ⭐ Bonus: Unit tests included

---

## Part 4: Database & API Optimization (60 minutes)

### Objective
Optimize slow database queries and implement a new analytics API endpoint.

### Task 4.1: Query Performance Optimization (30 min)

**Problem Statement:**
The dashboard endpoint `/api/dashboard/stats` is slow with 217K+ records. You can find the current implementation in `web-app/backend/routes/dashboard.js`.

**Your Task:**
1. Analyze the current implementation and identify performance bottlenecks
2. Propose optimizations:
   - Add database indexes where needed
   - Optimize SQL queries (use CTEs, eliminate N+1 queries)
   - Consider aggregation strategies
3. Implement your optimizations
4. Measure performance improvement

**Deliverables:**
- SQL script (`part4_indexes.sql`) with index creation statements
- Optimized route handler (`part4_dashboard_optimized.js`)
- Performance report (`performance_report.md`) showing:
  - Before: Query time and explain plan
  - After: Query time and explain plan
  - % improvement

### Task 4.2: New Analytics Endpoint (30 min)

**Requirement:**
Create a new API endpoint: `GET /api/analytics/seller-health/:seller_id`

**Response Format:**
```json
{
  "seller_id": 123,
  "seller_name": "Acme Corp",
  "health_score": 85,
  "metrics": {
    "credit_utilization_rate": 0.65,
    "payment_reliability_score": 0.92,
    "lead_conversion_rate": 0.78,
    "wallet_health": {
      "current_balance": 450.50,
      "avg_weekly_change": 120.30,
      "trend": "improving"
    }
  },
  "risk_level": "low",
  "last_updated": "2025-10-10T14:30:00Z"
}
```

**Metric Definitions:**
- `credit_utilization_rate`: Sum of issued credits / credit_limit
- `payment_reliability_score`: Paid credits / Total credits (exclude Cancelled)
- `lead_conversion_rate`: Confirmed leads / Total leads
- `wallet_health.trend`: "improving" if avg is positive, else "declining"
- `risk_level`: 
  - High: credit_utilization > 0.9 OR payment_reliability < 0.5
  - Medium: credit_utilization > 0.7 OR payment_reliability < 0.7
  - Low: otherwise
- `health_score`: Weighted average (0-100):
  - payment_reliability_score × 40
  - lead_conversion_rate × 30
  - (1 - credit_utilization_rate) × 20
  - wallet_trend_bonus × 10

**Technical Requirements:**
- Single SQL query (no N+1)
- Proper error handling (404 if seller not found)
- Input validation (seller_id must be integer)
- Return 400 for invalid input

**Deliverables:**
- Express route file (`part4_seller_health.js`)
- Test cases document (`part4_test_cases.md`) with at least 3 example curl commands

### Evaluation Criteria
- ✅ Correct SQL optimization approach
- ✅ Measurable performance improvement
- ✅ API implements all required metrics correctly
- ✅ Proper error handling and validation
- ✅ Single optimized query (no N+1)
- ⭐ Bonus: Comprehensive test cases

---

## Part 5: Schema Migration & Documentation (45 minutes)

### Objective
Design a backward-compatible schema change and document the migration process.

### Scenario
**Business Requirement:** Add multi-currency support to the credit system.

Currently, all amounts are in USD. The system needs to support:
- Credits issued in different currencies (USD, EUR, SAR, AED)
- Invoices and transactions in seller's local currency
- Exchange rate tracking for reporting

### Tasks

**5.1 Schema Design (20 min)**
Design the necessary schema changes:
1. Add `currency` column to relevant tables
2. Create `exchange_rates` table with structure:
   - from_currency, to_currency, rate, effective_date
3. Consider indexes needed for performance

**5.2 Migration Script (15 min)**
Write a migration SQL script (`part5_migration.sql`) that:
- Adds new columns with defaults (all existing records → 'USD')
- Creates new tables
- Maintains referential integrity
- Can be rolled back if needed

**5.3 Migration Runbook (10 min)**
Document the migration process (`migration_runbook.md`):
- Pre-migration checklist (backups, testing steps)
- Step-by-step execution instructions
- Rollback procedure
- Validation queries to confirm success
- Breaking changes and API impact

### Deliverables
- `part5_schema_design.sql` - DDL for schema changes
- `part5_migration.sql` - Complete migration script with rollback
- `migration_runbook.md` - Detailed migration guide
- `api_impact_analysis.md` - Document which API endpoints need updates

### Evaluation Criteria
- ✅ Schema design supports requirements
- ✅ Migration is backward-compatible
- ✅ Rollback plan is included
- ✅ Documentation is clear and complete
- ⭐ Bonus: Considers performance implications

---

## 📤 Submission Guidelines

### What to Submit
1. **Git Repository** containing:
   - All code files organized in folders by part
   - Documentation in markdown
   - Test data/logs generated
   - README.md explaining your approach

2. **Repository Structure:**
```
candidate-submission/
├── README.md                          # Your overview and approach
├── part1_analysis/
│   └── part1_analysis.ipynb
├── part2_data_quality/
│   ├── part2_data_quality.py
│   ├── data_quality_report.csv
│   └── data_quality_findings.md
├── part3_etl/
│   ├── part3_etl_pipeline.py
│   ├── etl_execution.log
│   └── etl_load_summary.json
├── part4_optimization/
│   ├── part4_indexes.sql
│   ├── part4_dashboard_optimized.js
│   ├── part4_seller_health.js
│   ├── performance_report.md
│   └── part4_test_cases.md
└── part5_migration/
    ├── part5_schema_design.sql
    ├── part5_migration.sql
    ├── migration_runbook.md
    └── api_impact_analysis.md
```

### Git Best Practices
- Use meaningful commit messages
- Commit incrementally (not all at once at the end)
- Include a .gitignore for virtual environments, cache files

### Submission Method
- Push to a private GitHub/GitLab repository
- Add our review account as collaborator
- Send repository URL via email

---

## 🎯 Evaluation Criteria Summary

### Overall Scoring (100 points)

| Criterion | Weight | What We Look For |
|-----------|--------|------------------|
| **Correctness** | 35% | Accurate results, working code, meets requirements |
| **Code Quality** | 20% | Clean, modular, maintainable, follows best practices |
| **Performance** | 15% | Efficient queries, proper indexing, scalable solutions |
| **Error Handling** | 10% | Robust error handling, validation, edge cases |
| **Documentation** | 10% | Clear comments, README, assumptions documented |
| **Business Understanding** | 10% | Demonstrates understanding of domain and context |

### Excellence Indicators (Bonus Points)
- ✨ Automated tests (unit/integration)
- ✨ Type hints in Python
- ✨ Structured logging with proper levels
- ✨ Reusable, modular code
- ✨ Data visualization in analysis
- ✨ Security considerations (parameterized queries, input validation)
- ✨ Multiple solution approaches with tradeoffs discussed

### Red Flags (Automatic Deductions)
- ❌ No error handling (silent failures)
- ❌ SQL injection vulnerabilities
- ❌ Hardcoded credentials or secrets
- ❌ No data validation
- ❌ Poor variable naming
- ❌ No comments on complex logic

---

## 🔍 Post-Submission Interview (30 minutes)

After reviewing your submission, we'll schedule a 30-minute session to:

1. **Code Walkthrough (10 min)**
   - Explain your approach for 1-2 parts
   - Discuss design decisions

2. **What-If Scenarios (10 min)**
   - How would you scale to 10M records?
   - What if we needed real-time updates?
   - How would you monitor this in production?

3. **Live Debugging (10 min)**
   - Debug a planted issue together
   - Demonstrate problem-solving approach

---

## ⚙️ Setup Instructions

See `CANDIDATE_SETUP.md` for detailed environment setup.

**Quick Start:**
```bash
# Clone the exam repository
git clone <provided-repo-url>
cd dataeng_exam

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Verify dataset access
ls -lh credit_challenge_dataset/

# Start coding!
```

---

## ❓ FAQ

**Q: Can I use external libraries?**
A: Yes, common data science libraries (pandas, numpy, sqlalchemy, pytest) are fine. Document any additions.

**Q: What if I don't finish all parts?**
A: Submit what you complete. Partial completion with high quality is better than rushed completion.

**Q: Can I ask questions?**
A: You may ask clarifying questions about requirements. We won't provide coding hints.

**Q: What Python version?**
A: Python 3.9+ is recommended.

**Q: What database?**
A: The dataset uses SQLite. You can use any ORM or raw SQL.

---

## 📞 Support

If you encounter technical issues (corrupt files, setup problems), contact:
- Email: recruitment@company.com
- Response time: Within 4 hours on business days

---

**Good luck! We look forward to reviewing your work.**

*Remember: We value quality over quantity. Clear, well-documented solutions are better than rushed completions.*

