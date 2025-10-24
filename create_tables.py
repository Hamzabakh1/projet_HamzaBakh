import sqlite3
import os

# Dynamically resolve path to create DB in current directory
db_filename = "exam_database.db"
db_path = os.path.join(os.getcwd(), db_filename)

# Define schema creation SQL statements
schema_statements = {
    "sellers": """
    CREATE TABLE IF NOT EXISTS sellers (
        seller_id INTEGER PRIMARY KEY,
        seller_name TEXT,
        market TEXT,
        signup_date TEXT,
        credit_limit REAL,
        avg_weekly_leads INTEGER,
        initial_wallet REAL,
        am_id INTEGER,
        sam_id INTEGER
    );
    """,
    "credits": """
    CREATE TABLE IF NOT EXISTS credits (
        credit_id INTEGER PRIMARY KEY,
        seller_id INTEGER,
        amount REAL,
        issue_date TEXT,
        due_date TEXT,
        status TEXT
    );
    """,
    "credit_histories": """
    CREATE TABLE IF NOT EXISTS credit_histories (
        credit_id INTEGER,
        status TEXT,
        changed_at TEXT
    );
    """,
    "credit_chat": """
    CREATE TABLE IF NOT EXISTS credit_chat (
        credit_id INTEGER,
        user_id INTEGER,
        role TEXT,
        message_time TEXT,
        message TEXT
    );
    """,
    "leads": """
    CREATE TABLE IF NOT EXISTS leads (
        lead_id INTEGER PRIMARY KEY,
        seller_id INTEGER,
        created_at TEXT,
        amount REAL,
        status TEXT,
        shipping_status TEXT,
        tracking_number TEXT
    );
    """,
    "account_managers": """
    CREATE TABLE IF NOT EXISTS account_managers (
        am_id INTEGER PRIMARY KEY,
        am_name TEXT,
        am_email TEXT,
        sam_id INTEGER
    );
    """,
    "senior_account_managers": """
    CREATE TABLE IF NOT EXISTS senior_account_managers (
        sam_id INTEGER PRIMARY KEY,
        sam_name TEXT,
        sam_email TEXT
    );
    """,
    "wallet_transactions": """
    CREATE TABLE IF NOT EXISTS wallet_transactions (
        transaction_id TEXT PRIMARY KEY,
        seller_id INTEGER,
        type TEXT,
        amount REAL,
        created_at TEXT
    );
    """,
    "invoices": """
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY,
        seller_id INTEGER,
        period_start TEXT,
        period_end TEXT,
        sales_amount REAL,
        fees REAL,
        credits_due REAL,
        from_balance REAL,
        total REAL
    );
    """,
    "invoice_items": """
    CREATE TABLE IF NOT EXISTS invoice_items (
        invoice_id TEXT,
        item_type TEXT,
        amount REAL
    );
    """
}

# Connect to SQLite DB and execute schema
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for table_name, ddl in schema_statements.items():
    print(f"Creating table: {table_name}")
    cursor.execute(ddl)

conn.commit()
conn.close()

print(f"\n✅ Database created at: {db_path}")
