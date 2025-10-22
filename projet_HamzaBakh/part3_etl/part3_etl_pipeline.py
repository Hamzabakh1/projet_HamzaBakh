#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
part3_etl_pipeline.py
Author: Hamza Bakh
Date: 2025-10-19

✅ Final Version with --run-all
Loads all CSVs automatically in dependency-safe order.
"""

from __future__ import annotations
import argparse, json, logging, sqlite3, sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("etl_execution.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ETL")

# --------------------------------------------------
# Schema Definitions
# --------------------------------------------------
SCHEMAS = {
    "sellers": {
        "pk": "seller_id",
        "required": ["seller_id", "seller_name", "market"],
        "numeric": ["credit_limit", "avg_weekly_leads", "initial_wallet"],
        "dates": ["signup_date"],
        "fks": [],
        "all": ["seller_id", "seller_name", "market", "signup_date", "credit_limit", "avg_weekly_leads", "initial_wallet", "am_id", "sam_id"],
    },
    "credits": {
        "pk": "credit_id",
        "required": ["credit_id", "seller_id", "amount"],
        "numeric": ["amount"],
        "dates": ["issue_date", "due_date"],
        "fks": [("seller_id", "sellers", "seller_id")],
        "all": ["credit_id", "seller_id", "amount", "issue_date", "due_date", "status"],
    },
    "leads": {
        "pk": "lead_id",
        "required": ["lead_id", "seller_id"],
        "numeric": ["amount"],
        "dates": ["created_at"],
        "fks": [("seller_id", "sellers", "seller_id")],
        "all": ["lead_id", "seller_id", "created_at", "amount", "status", "shipping_status", "tracking_number"],
    },
    "invoices": {
        "pk": "invoice_id",
        "required": ["invoice_id", "seller_id"],
        "numeric": ["sales_amount", "fees", "credits_due", "from_balance", "total"],
        "dates": ["period_start", "period_end"],
        "fks": [("seller_id", "sellers", "seller_id")],
        "all": ["invoice_id", "seller_id", "period_start", "period_end", "sales_amount", "fees", "credits_due", "from_balance", "total"],
    },
    "invoice_items": {
        "pk": "invoice_id",  
        "required": ["invoice_id", "item_type", "amount"],
        "numeric": ["amount"],
        "dates": [],
        "fks": [("invoice_id", "invoices", "invoice_id")],
        "all": ["invoice_id", "item_type", "amount"],
    },
    "account_managers": {
        "pk": "am_id",
        "required": ["am_id"],
        "numeric": [],
        "dates": [],
        "fks": [],
        "all": ["am_id", "am_name", "am_email", "sam_id"],
    },
    "senior_account_managers": {
        "pk": "sam_id",
        "required": ["sam_id"],
        "numeric": [],
        "dates": [],
        "fks": [],
        "all": ["sam_id", "sam_name", "sam_email"],
    },
    "wallet_transactions": {
        "pk": "transaction_id",
        "required": ["transaction_id", "seller_id", "amount"],
        "numeric": ["amount"],
        "dates": ["created_at"],
        "fks": [("seller_id", "sellers", "seller_id")],
        "all": ["transaction_id", "seller_id", "type", "amount", "created_at"],
    },
    "credit_histories": {
        "pk": "credit_id", 
        "required": ["credit_id", "status", "changed_at"],
        "numeric": [],
        "dates": ["changed_at"],
        "fks": [("credit_id", "credits", "credit_id")],
        "all": ["credit_id", "status", "changed_at"],
    },
    "credit_chat": {
        "pk": "credit_id",  
        "required": ["credit_id", "user_id", "role", "message_time", "message"],
        "numeric": [],
        "dates": ["message_time"],
        "fks": [("credit_id", "credits", "credit_id")],
        "all": ["credit_id", "user_id", "role", "message_time", "message"],
    },
}


# --------------------------------------------------
# ETL Class
# --------------------------------------------------
class IncrementalETL:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.summary = {}

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _log(self, level, op, msg, rid=None):
        getattr(log, level.lower())(f"[{op}] id={rid} | {msg}")

    def validate_schema(self, csv_file: Path, table: str):
        df = pd.read_csv(csv_file, dtype=str).fillna("")
        df.columns = [c.strip().lower() for c in df.columns]
        schema = SCHEMAS[table]

        id_map = {
            "invoice_items": "invoice_item_id",
            "wallet_transactions": "wallet_id",
            "credit_histories": "credit_history_id",
            "credit_chat": "chat_id"
        }
        if table in id_map:
            expected_id = id_map[table]
            if "id" in df.columns and expected_id not in df.columns:
                df.rename(columns={"id": expected_id}, inplace=True)
                log.info(f"[auto_fix] Renamed id → {expected_id} for {table}")
            if expected_id not in df.columns:
                df.insert(0, expected_id, range(1, len(df)+1))
                log.warning(f"[auto_fix] Generated missing PK column {expected_id} for {table}")

        missing = [c for c in schema["required"] if c not in df.columns]
        if missing:
            raise ValueError(f"{table}: missing required columns {missing}")
        return df[[c for c in df.columns if c in schema["all"]]].copy()

    def detect_changes(self, csv_file, table):
        df = self.validate_schema(csv_file, table)
        schema = SCHEMAS[table]
        pk = schema["pk"]

        # Always ensure PK is string to avoid merge dtype mismatches
        df[pk] = df[pk].astype(str)

        with self._conn() as conn:
            try:
                existing = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                # Force existing PK to string type too
                existing[pk] = existing[pk].astype(str)
                existing = existing.astype(str).fillna("")
            except Exception:
                existing = pd.DataFrame(columns=df.columns).astype(str)

        if existing.empty:
            return df, pd.DataFrame(), pd.DataFrame()

        merged = df.merge(existing, on=pk, how="left", suffixes=("", "_db"), indicator=True)

        new_df = merged[merged["_merge"] == "left_only"][df.columns]
        diff = pd.concat(
            [(merged[c] != merged.get(f"{c}_db", merged[c])) for c in df.columns if c != pk],
            axis=1
        ).any(axis=1)
        upd_df = merged[(merged["_merge"] == "both") & diff][df.columns]
        dup_df = merged[(merged["_merge"] == "both") & (~diff)][df.columns]
        return new_df, upd_df, dup_df


    def load_data(self, csv_file, table):
        log.info(f"🚀 Loading {table} from {csv_file}")
        if not Path(csv_file).exists():
            log.warning(f"❌ Missing file {csv_file}")
            return None
        new_df, upd_df, dup_df = self.detect_changes(csv_file, table)
        conn = self._conn()
        conn.execute("BEGIN")
        try:
            if not new_df.empty:
                new_df.to_sql(table, conn, if_exists="append", index=False)
            if not upd_df.empty:
                pk = SCHEMAS[table]["pk"]
                cols = [c for c in upd_df.columns if c != pk]
                sql = f"UPDATE {table} SET " + ", ".join([f"{c}=?" for c in cols]) + f" WHERE {pk}=?"
                conn.executemany(sql, [tuple([*(r[c] for c in cols), r[pk]]) for _, r in upd_df.iterrows()])
            conn.commit()
            log.info(f"✅ COMMIT | table={table} | +{len(new_df)} | updated={len(upd_df)} | skipped={len(dup_df)}")
            return {
                "table": table,
                "inserted": len(new_df),
                "updated": len(upd_df),
                "skipped": len(dup_df),
                "records": len(new_df)+len(upd_df)+len(dup_df)
            }
        except Exception as e:
            conn.rollback()
            log.error(f"❌ Rollback {table}: {e}")
            return {"table": table, "error": str(e)}
        finally:
            conn.close()

# --------------------------------------------------
# CLI Runner
# --------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Part 3 — Incremental ETL Pipeline")
    p.add_argument("--db", required=True, type=Path)
    p.add_argument("--input", type=Path)
    p.add_argument("--table", type=str)
    p.add_argument("--run-all", type=Path, help="Run all tables from a dataset directory")
    args = p.parse_args()

    etl = IncrementalETL(args.db)

    if args.run_all:
        order = [
            "senior_account_managers",
            "account_managers",
            "sellers",
            "credits",
            "leads",
            "invoices",
            "invoice_items",
            "wallet_transactions",
            "credit_histories",
            "credit_chat"
        ]
        results = []
        for table in order:
            file = args.run_all / f"{table}.csv"
            if file.exists():
                result = etl.load_data(file, table)
                results.append(result)
            else:
                log.warning(f"⚠️ Skipping missing {file}")
        Path("etl_load_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        log.info("✅ Run-all complete → etl_load_summary.json")
        print(json.dumps(results, indent=2))
        return

    if not args.input or not args.table:
        p.error("Provide --input and --table or use --run-all")

    etl.load_data(args.input, args.table)

if __name__ == "__main__":
    main()
