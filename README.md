# 💳 Credit Management Platform – Data Engineering Project

**Author:** Hamza Bakh  
**Date:** October 2025  
---

## 🧭 Overview

The **Credit Management Platform** is a full-stack data engineering project simulating how financial data is processed, validated, optimized, and exposed for analytics.  
It showcases an end-to-end workflow, covering:

- **Data ingestion**
- **Quality validation**
- **ETL orchestration**
- **Database optimization**
- **API design**
- **Schema migration**

All datasets are **synthetic** and rebuilt solely for educational and portfolio demonstration purposes.

---

## 🎯 Objectives

- Automate ingestion and validation across multiple datasets  
- Maintain >99.9% data quality through systematic checks  
- Achieve <50 ms query latency with optimized indexing  
- Serve analytical insights through REST APIs  
- Enable backward-compatible schema migration for multi-currency support  

---

## ⚙️ Architecture Overview

| Layer | Technology | Purpose |
|-------|-------------|----------|
| **Data Layer** | SQLite | Lightweight relational storage |
| **Processing Layer** | Python (pandas, sqlite3) | ETL, validation, transformation |
| **API Layer** | Node.js (Express.js) | REST endpoints for analytics |
| **Migration Layer** | SQL scripts | Schema evolution & rollback |
| **Visualization Layer** | CSV / JSON exports | BI integration (Power BI-ready) |

---

## 📂 Repository Structure

```plaintext
credit-management-platform/
│
├── credit_challenge_dataset/           # Synthetic dataset (CSV files)
│
├── part1_analysis/
│   └── credit_analysis.ipynb           # Business analysis & exploration
│
├── part2_data_quality/
│   ├── data_quality.py                 # Validation framework
│   ├── data_quality_report.csv         # Metrics summary
│   └── findings.md                     # Key insights & quality results
│
├── part3_etl/
│   ├── etl_pipeline.py                 # Incremental ETL with idempotency
│   ├── etl_execution.log               # Pipeline logs
│   └── etl_summary.json                # Load statistics
│
├── part4_optimization/
│   ├── indexes.sql                     # Index optimization scripts
│   ├── seller_health.js                # Analytics endpoint logic
│   ├── server.js                       # Express.js API server
│   ├── performance_report.md           # Benchmark & latency report
│   └── test_cases.md                   # API test documentation
│
└── part5_migration/
    ├── schema_design.sql               # Multi-currency schema design
    ├── migration.sql                   # Migration + rollback scripts
    ├── migration_runbook.md            # Step-by-step deployment guide
    └── api_impact_analysis.md          # API change analysis
```

## 🚀 Quick Start

### Prerequisites
- Python ≥ 3.10  
- Node.js ≥ 18  
- SQLite 3.x  
- Git  

### Run Components
# 1️⃣ Run data analysis
jupyter notebook part1_analysis/credit_analysis.ipynb

# 2️⃣ Validate data quality
python part2_data_quality/data_quality.py

# 3️⃣ Execute ETL pipeline
python part3_etl/etl_pipeline.py --db finance.db --run-all credit_challenge_dataset

# 4️⃣ Start the API server
cd part4_optimization && npm install && node server.js

# 5️⃣ Apply database migration
sqlite3 finance.db < part5_migration/migration.sql


## 📁 Repository Structure

