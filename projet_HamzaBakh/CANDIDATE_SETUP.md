# Candidate Setup Guide

Welcome! This guide will help you set up your environment for the Data Engineer technical assessment.

---

## 📋 Prerequisites

### Required Software
- **Python 3.9+** (recommended: Python 3.11)
- **Node.js 18+** (for Part 4 only)
- **Git** (for version control)
- **SQLite3** (usually pre-installed on macOS/Linux)
- **Text Editor/IDE** (VS Code, PyCharm, or your preference)

### Recommended Tools
- **Jupyter Notebook** (for Part 1)
- **SQLite Browser** (for exploring the database)
- **Postman or curl** (for testing APIs in Part 4)

---

## 🚀 Quick Start (5 minutes)

### Step 1: Clone the Repository

```bash
# Clone the exam repository
git clone <provided-repo-url>
cd dataeng_exam

# Verify you have all files
ls -la
```

You should see:
```
credit_challenge_dataset/    # Dataset CSVs (217K records)
exam_starter_kit/            # Your starter templates
exam_test_dataset/           # Test data for validation
EXAM_INSTRUCTIONS.md         # Main exam document
CANDIDATE_SETUP.md          # This file
requirements.txt             # Python dependencies
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Setup

```bash
# Test Python environment
python -c "import pandas, sqlite3, jupyter; print('✅ Python environment ready!')"

# Check dataset
ls -lh credit_challenge_dataset/
# Should see: sellers.csv, credits.csv, invoices.csv, etc.

# Test database connection
python -c "import sqlite3; conn = sqlite3.connect(':memory:'); print('✅ SQLite working!')"
```

If all commands succeed, you're ready to start! 🎉

---

## 📦 Python Dependencies

The `requirements.txt` includes:

```
# Core data processing
pandas>=2.0.0
numpy>=1.24.0

# Database
sqlite3  # (built-in, but listed for reference)
sqlalchemy>=2.0.0

# Jupyter for analysis
jupyter>=1.0.0
notebook>=7.0.0
ipykernel>=6.25.0

# Data visualization
matplotlib>=3.7.0
seaborn>=0.12.0

# Code quality
pylint>=2.17.0
flake8>=6.0.0
black>=23.0.0

# Testing (optional but recommended)
pytest>=7.4.0
pytest-cov>=4.1.0

# Utilities
python-dateutil>=2.8.0
tabulate>=0.9.0
```

---

## 💾 Understanding the Dataset

### Dataset Overview
The `credit_challenge_dataset/` folder contains 10 CSV files:

| File | Records | Description |
|------|---------|-------------|
| `sellers.csv` | 300 | Seller information with AM assignments |
| `account_managers.csv` | 20 | Account managers |
| `senior_account_managers.csv` | 5 | Senior account managers |
| `credits.csv` | 800 | Credit records |
| `credit_histories.csv` | 3,140 | Credit status change history |
| `credit_chat.csv` | 1,600 | Chat messages for credit requests |
| `leads.csv` | 20,000 | Sales leads |
| `invoices.csv` | 27,600 | Weekly invoices |
| `invoice_items.csv` | 138,000 | Invoice line items |
| `wallet_transactions.csv` | 27,600 | Wallet deposit/withdrawal transactions |

**Total: 217,465 records**

### Quick Data Exploration

```python
import pandas as pd

# Load a dataset
sellers = pd.read_csv('credit_challenge_dataset/sellers.csv')
print(sellers.head())
print(sellers.info())

# Check relationships
credits = pd.read_csv('credit_challenge_dataset/credits.csv')
print(f"Total credits: {len(credits)}")
print(f"Unique sellers with credits: {credits['seller_id'].nunique()}")
```

### Schema Reference

**sellers.csv**
```
seller_id, seller_name, market, signup_date, credit_limit, 
avg_weekly_leads, initial_wallet, am_id, sam_id
```

**credits.csv**
```
credit_id, seller_id, amount, issue_date, due_date, status
```

**invoices.csv**
```
invoice_id, seller_id, period_start, period_end, 
sales_amount, fees, credits_due, from_balance, total
```

*See EXAM_INSTRUCTIONS.md for complete schema details*

---

## 🔧 Development Environment Setup

### Option 1: Jupyter Notebook (Recommended for Part 1)

```bash
# Activate your virtual environment first
source venv/bin/activate

# Start Jupyter
jupyter notebook

# This will open a browser window
# Navigate to exam_starter_kit/part1_analysis_template.ipynb
```

### Option 2: VS Code Setup

1. Install VS Code Python extension
2. Open the `dataeng_exam` folder
3. Select Python interpreter (Command Palette → "Python: Select Interpreter" → choose `venv`)
4. Install Jupyter extension for notebook support

### Option 3: PyCharm Setup

1. Open project folder
2. Configure interpreter: Settings → Project → Python Interpreter → Add → Existing environment
3. Select `venv/bin/python`
4. Enable Jupyter support in Settings → Tools → Python Scientific

---

## 🗄️ Database Setup

### Option A: Use SQLite Directly

```python
import sqlite3
import pandas as pd

# Create in-memory database
conn = sqlite3.connect('exam_database.db')

# Load CSVs into database
sellers = pd.read_csv('credit_challenge_dataset/sellers.csv')
sellers.to_sql('sellers', conn, if_exists='replace', index=False)

credits = pd.read_csv('credit_challenge_dataset/credits.csv')
credits.to_sql('credits', conn, if_exists='replace', index=False)

# Query the database
result = pd.read_sql("SELECT * FROM sellers LIMIT 5", conn)
print(result)

conn.close()
```

### Option B: Use the Web App Database

If you want to use the existing web app's database:

```python
import sqlite3

# Connect to the web app's database
conn = sqlite3.connect('../web-app/database.sqlite')

# All tables are already set up with relationships
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Available tables:", cursor.fetchall())
```

### Useful SQLite Commands

```bash
# Open SQLite browser (if installed)
sqlite3 exam_database.db

# List tables
.tables

# Show schema
.schema sellers

# Run a query
SELECT COUNT(*) FROM sellers;

# Exit
.exit
```

---

## 🧪 Testing Your Code

### Part 1: Test Your Analysis

```python
# In your Jupyter notebook, verify results
import pandas as pd

# Your query result
result = your_query_function()

# Basic validation
assert len(result) > 0, "Query returned no results"
assert 'expected_column' in result.columns, "Missing expected column"
print("✅ Query works!")
```

### Part 2: Test Data Quality Script

```bash
# Run your validation script
python exam_starter_kit/part2_data_quality.py

# Check output
ls -l data_quality_report.csv
cat data_quality_findings.md
```

### Part 3: Test ETL Pipeline

```bash
# Run with test data
python exam_starter_kit/part3_etl_pipeline.py \
    --input exam_test_dataset/incremental/incremental_sellers.csv \
    --table sellers

# Check logs
tail -f etl_execution.log
```

### Part 4: Test API Endpoint

```bash
# Start the backend server (from web-app/backend/)
cd ../web-app/backend
npm install
npm start

# In another terminal, test your endpoint
curl http://localhost:3001/api/analytics/seller-health/1

# Should return JSON with health metrics
```

---

## 📂 Organizing Your Work

### Recommended Structure

Create your submission folder:

```bash
mkdir candidate-submission
cd candidate-submission

# Create folders for each part
mkdir part1_analysis part2_data_quality part3_etl part4_optimization part5_migration

# Copy starter templates
cp ../exam_starter_kit/part1_analysis_template.ipynb part1_analysis/
cp ../exam_starter_kit/part2_data_quality_template.py part2_data_quality/
# ... etc
```

### Git Setup

```bash
cd candidate-submission

# Initialize git
git init

# Create .gitignore
cat > .gitignore << EOF
venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
.DS_Store
*.db
node_modules/
.env
EOF

# First commit
git add .
git commit -m "Initial setup"
```

---

## 🐛 Troubleshooting

### Issue: Python packages won't install

```bash
# Try upgrading pip first
pip install --upgrade pip setuptools wheel

# Install packages one by one to identify the problem
pip install pandas
pip install numpy
# etc.
```

### Issue: Jupyter kernel not found

```bash
# Install ipykernel
pip install ipykernel

# Add your virtual environment as a Jupyter kernel
python -m ipykernel install --user --name=dataeng_exam
```

### Issue: SQLite database locked

```python
# Use timeout parameter
import sqlite3
conn = sqlite3.connect('database.db', timeout=10)
```

### Issue: CSV encoding errors

```python
# Try different encodings
df = pd.read_csv('file.csv', encoding='utf-8')
# or
df = pd.read_csv('file.csv', encoding='latin-1')
```

### Issue: Module not found errors

```bash
# Verify you're in the virtual environment
which python
# Should show: /path/to/dataeng_exam/venv/bin/python

# If not, activate it
source venv/bin/activate
```

### Issue: Can't access web app database

```bash
# Check if database file exists
ls -l ../web-app/database.sqlite

# If missing, recreate it
cd ../web-app/backend
npm run import
```

---

## 💡 Productivity Tips

### 1. Start with Quick Wins
Begin with Part 1 (analysis) to get familiar with the data before tackling harder parts.

### 2. Use Jupyter for Exploration
Even for parts 2-3, use Jupyter notebooks to explore and prototype, then convert to .py scripts.

### 3. Commit Often
```bash
git add .
git commit -m "Completed Q1 in Part 1 - credit approval rate"
```

### 4. Test Incrementally
Don't write all code then test. Test each function/query as you build.

### 5. Document As You Go
Add comments and docstrings while coding, not at the end.

---

## 🎯 Ready to Start?

### Pre-Flight Checklist

- [ ] Virtual environment activated
- [ ] All Python packages installed
- [ ] Dataset accessible and loadable
- [ ] SQLite working
- [ ] Jupyter notebook opens
- [ ] Git initialized
- [ ] Read EXAM_INSTRUCTIONS.md thoroughly

### Next Steps

1. **Read** `EXAM_INSTRUCTIONS.md` completely
2. **Plan** your approach for each part
3. **Start** with Part 1 (Data Analysis)
4. **Commit** your progress regularly
5. **Test** your code thoroughly
6. **Document** your assumptions and decisions

---

## 📞 Getting Help

### For Technical Issues
- **Dataset corruption**: Re-download from provided link
- **Setup problems**: Email recruitment@company.com
- **Missing files**: Check repository URL

### For Clarification Questions
- Email your questions to: recruitment@company.com
- Expected response time: 4 hours (business days)
- We can clarify requirements but won't provide coding help

---

## ⏱️ Time Management Suggestions

| Part | Suggested Time | Buffer |
|------|---------------|--------|
| Setup & Familiarization | 30 min | - |
| Part 1: Analysis | 90 min | +15 min |
| Part 2: Data Quality | 90 min | +15 min |
| Part 3: ETL | 90 min | +20 min |
| Part 4: Optimization | 60 min | +15 min |
| Part 5: Migration | 45 min | +10 min |
| **Total** | **6.5 hours** | **+1.5 hours** |

**Recommendation**: Block out 2 days:
- Day 1: Setup + Parts 1-2 (3 hours)
- Day 2: Parts 3-5 + review (3-4 hours)

---

## 🎓 Additional Resources

### Learning SQLite
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [SQL Tutorial](https://www.sqlitetutorial.net/)

### Pandas Reference
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [10 Minutes to Pandas](https://pandas.pydata.org/docs/user_guide/10min.html)

### Python Best Practices
- [PEP 8 Style Guide](https://pep8.org/)
- [Type Hints](https://docs.python.org/3/library/typing.html)

---

**You're all set! Good luck with your assessment! 🚀**

*Remember: Quality over quantity. We'd rather see 3 parts done excellently than all 5 done poorly.*

