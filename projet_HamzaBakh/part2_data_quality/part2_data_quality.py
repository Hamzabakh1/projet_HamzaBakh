# PART 2 — DATA QUALITY & VALIDATION FRAMEWORK
#
# Candidate Name:  HAMZA BAKH
# Date:            20 Oct 2025
# Time Spent:      90 min
#------------------------------------------------
# This module implements a comprehensive Data Quality Validation Framework
# for the Credit Management System dataset.
#
# Objective:
# Detect and report integrity issues, logical inconsistencies,
# and statistical anomalies across all core entities
# (Sellers, Credits, Leads, Invoices, Wallets, Managers).
# --------------------------------------------------------------
# How to run:
#   python part2_data_quality.py --data-dir ../credit_challenge_dataset --out-dir .
#--------------------------------------------------------------



from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


# --------------------------------------------------
# Configuration 
# --------------------------------------------------
WALLET_INV_TOLERANCE = 0.01  
WALLET_INV_REL_TOL = 0.005  # 0.5% relative tolerance
MIN_LEADS_FOR_CONV_EXTREME = 10
LOW_CONV_THRESHOLD = 0.10
HIGH_CONV_THRESHOLD = 0.90


# --------------------------------------------------
# Logging
# --------------------------------------------------
def setup_logging(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Only log to stdout (no file logging)
    handlers = [
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=handlers,
    )
    logging.info("Logger initialized (console output only)")


# --------------------------------------------------
# Utilities
# --------------------------------------------------
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase & trim column names for resilient joins/selections."""
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def safe_load_csv(base: Path, filename: str, parse_dates: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Robust CSV loader that only parses dates that actually exist.
    Avoids errors when schemas slightly differ.
    """
    p = base / filename
    if not p.exists():
        logging.warning("File not found: %s", filename)
        return pd.DataFrame()

    # First pass to discover columns
    df = pd.read_csv(p)
    df = normalize(df)

    # Parse only existing date columns
    if parse_dates:
        existing_date_cols = [col for col in parse_dates if col in df.columns]
        if existing_date_cols:
            df = pd.read_csv(p, parse_dates=existing_date_cols)
            df = normalize(df)
        else:
            missing_cols = [col for col in parse_dates if col not in df.columns]
            if missing_cols:
                logging.info("In %s: requested date columns not found: %s", filename, missing_cols)

    return df


def pick_first_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return first column name present from candidates list."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def ensure_invoice_total(invoices: pd.DataFrame, invoice_items: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure invoices has 'invoice_total'.
    1) If a plausible total column exists, normalize to 'invoice_total'.
    2) Else, compute from invoice_items if invoice_id exists on both sides.
    3) Else, leave NaN and skip arithmetic checks.
    """
    invoices = invoices.copy()
    total_candidates = ["invoice_total", "total", "amount_total", "grand_total", "invoice_amount", "total_amount"]
    found_total = pick_first_col(invoices, total_candidates)

    if found_total:
        invoices["invoice_total"] = pd.to_numeric(invoices[found_total], errors="coerce").fillna(0.0)
        return invoices

    if invoice_items.empty:
        logging.info("invoice_total not found and invoice_items.csv missing; arithmetic checks will be skipped.")
        invoices["invoice_total"] = np.nan
        return invoices

    # Try to compute from items
    amount_candidates = ["line_total", "total", "amount", "net_amount", "subtotal", "price_total"]
    amt_col = pick_first_col(invoice_items, amount_candidates)
    if not amt_col:
        logging.info("invoice_items present, but no usable amount column; arithmetic checks will be skipped.")
        invoices["invoice_total"] = np.nan
        return invoices

    if "invoice_id" not in invoices.columns or "invoice_id" not in invoice_items.columns:
        logging.info("invoice_id not available on invoices or invoice_items; arithmetic checks will be skipped.")
        invoices["invoice_total"] = np.nan
        return invoices

    items_sum = (
        invoice_items.groupby("invoice_id", as_index=False)[amt_col]
        .sum()
        .rename(columns={amt_col: "invoice_total"})
    )
    invoices = invoices.merge(items_sum, on="invoice_id", how="left")
    invoices["invoice_total"] = pd.to_numeric(invoices["invoice_total"], errors="coerce").fillna(0.0)
    return invoices


# --------------------------------------------------
# Load data
# --------------------------------------------------
def load_data(data_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load all datasets required for validation.
    Raises if a critical dataset is missing.
    """
    data = {
        "sellers": safe_load_csv(data_dir, "sellers.csv", ["signup_date"]),
        "credits": safe_load_csv(data_dir, "credits.csv", ["issue_date", "due_date"]),
        "leads": safe_load_csv(data_dir, "leads.csv", ["created_at"]),
        "invoices": safe_load_csv(data_dir, "invoices.csv", ["period_start", "period_end"]),
        "invoice_items": safe_load_csv(data_dir, "invoice_items.csv"),
        "account_managers": safe_load_csv(data_dir, "account_managers.csv"),
        "senior_account_managers": safe_load_csv(data_dir, "senior_account_managers.csv"),
        "wallet": safe_load_csv(data_dir, "wallet_transactions.csv", ["created_at"]),
        "credit_histories": safe_load_csv(data_dir, "credit_histories.csv", ["created_at"]),
        "credit_chat": safe_load_csv(data_dir, "credit_chat.csv", ["created_at"]),
    }
    # Required tables for this exercise
    for req in ("sellers", "credits", "leads", "invoices"):
        if data[req].empty:
            raise FileNotFoundError(f"Missing critical dataset: {req}.csv")
    logging.info("Datasets loaded successfully from %s", data_dir.resolve())
    return data


# --------------------------------------------------
# 2.1 Referential Integrity Checks
# --------------------------------------------------
def referential_integrity_checks(d: Dict[str, pd.DataFrame]) -> List[Dict]:
    issues: List[Dict] = []
    s, c, l, i = d["sellers"], d["credits"], d["leads"], d["invoices"]
    am, sam = d["account_managers"], d["senior_account_managers"]
    w = d["wallet"]

    # Sellers → Account Managers (am_id)
    if "am_id" in s.columns and not am.empty and "am_id" in am.columns:
        bad = s[~s["am_id"].isin(am["am_id"])]
        for _, r in bad.iterrows():
            issues.append({"entity": "sellers", "issue": "invalid_am_id", "id": r["seller_id"], "severity": "Warning", "desc": f"am_id {r['am_id']} not found"})

    # Sellers → Senior Account Managers (sam_id)
    if "sam_id" in s.columns and not sam.empty and "sam_id" in sam.columns:
        bad = s[~s["sam_id"].isin(sam["sam_id"])]
        for _, r in bad.iterrows():
            issues.append({"entity": "sellers", "issue": "invalid_sam_id", "id": r["seller_id"], "severity": "Warning", "desc": f"sam_id {r['sam_id']} not found"})

    # Credits → Sellers
    if "seller_id" in c.columns:
        bad = c[~c["seller_id"].isin(s["seller_id"])]
        for _, r in bad.iterrows():
            issues.append({"entity": "credits", "issue": "invalid_seller_id", "id": r["credit_id"], "severity": "Critical", "desc": f"seller_id {r['seller_id']} not found"})

    # Invoices → Sellers
    if "seller_id" in i.columns:
        bad = i[~i["seller_id"].isin(s["seller_id"])]
        for _, r in bad.iterrows():
            issues.append({"entity": "invoices", "issue": "invalid_seller_id", "id": r.get("invoice_id", np.nan), "severity": "Critical", "desc": f"seller_id {r['seller_id']} not found"})

    # Leads → Sellers
    if "seller_id" in l.columns:
        bad = l[~l["seller_id"].isin(s["seller_id"])]
        for _, r in bad.iterrows():
            issues.append({"entity": "leads", "issue": "invalid_seller_id", "id": r["lead_id"], "severity": "Critical", "desc": f"seller_id {r['seller_id']} not found"})

    # Wallet → Sellers
    if not w.empty and "seller_id" in w.columns:
        bad = w[~w["seller_id"].isin(s["seller_id"])]
        for _, r in bad.iterrows():
            issues.append({"entity": "wallet", "issue": "invalid_seller_id", "id": r.get("wallet_id", np.nan), "severity": "Warning", "desc": f"seller_id {r['seller_id']} not found"})

    logging.info("Referential integrity issues found: %d", len(issues))
    return issues


# --------------------------------------------------
# 2.2 Business Logic Validation
# --------------------------------------------------
def business_logic_validation(d: Dict[str, pd.DataFrame]) -> List[Dict]:
    issues: List[Dict] = []
    s, c, l, inv, inv_items, w = d["sellers"], d["credits"], d["leads"], d["invoices"], d["invoice_items"], d["wallet"]

    # 1) Credit limit violations
    issued = c.groupby("seller_id", as_index=False)["amount"].sum().rename(columns={"amount": "total_issued"})
    s1 = s.merge(issued, on="seller_id", how="left").fillna({"total_issued": 0})
    if "credit_limit" in s1.columns:
        viol = s1[s1["total_issued"] > s1["credit_limit"]]
        for _, r in viol.iterrows():
            issues.append({"entity": "sellers", "issue": "credit_limit_exceeded", "id": r["seller_id"], "severity": "Critical", "desc": f"{r['total_issued']} > {r['credit_limit']}"})
    else:
        logging.info("Skipping credit limit validation (credit_limit column missing).")

    # 2) Invoice arithmetic errors
    inv = ensure_invoice_total(inv, inv_items)
    sales_col = pick_first_col(inv, ["sales_amount", "amount_sales", "sales"])
    fees_col = pick_first_col(inv, ["fees", "fee", "total_fees"])
    credits_due_col = pick_first_col(inv, ["credits_due", "credit_due", "credits"])
    from_balance_col = pick_first_col(inv, ["from_balance", "prev_balance", "carryover"])

    if all(col is not None for col in [sales_col, fees_col, credits_due_col, from_balance_col]) and "invoice_total" in inv.columns:
        inv["calc_total"] = (
            pd.to_numeric(inv[sales_col], errors="coerce")
            - pd.to_numeric(inv[fees_col], errors="coerce")
            - pd.to_numeric(inv[credits_due_col], errors="coerce")
            - pd.to_numeric(inv[from_balance_col], errors="coerce").abs()
        ).fillna(0.0)
        mismatch = inv[np.round(inv["invoice_total"] - inv["calc_total"], 2) != 0]
        for _, r in mismatch.iterrows():
            issues.append({"entity": "invoices", "issue": "arithmetic_error", "id": r.get("invoice_id", np.nan), "severity": "Critical", "desc": f"expected {r['calc_total']}, got {r['invoice_total']}"})
    else:
        logging.info("Skipping invoice arithmetic check (missing columns).")

    # 3) Temporal violations
    if "signup_date" in s.columns and "created_at" in l.columns:
        l2 = l.merge(s[["seller_id", "signup_date"]], on="seller_id", how="left")
        early = l2[l2["created_at"] < l2["signup_date"]]
        for _, r in early.iterrows():
            issues.append({"entity": "leads", "issue": "lead_before_signup", "id": r["lead_id"], "severity": "Warning", "desc": "lead created before signup"})

    if "signup_date" in s.columns:
        c2 = c.merge(s[["seller_id", "signup_date"]], on="seller_id", how="left")
        early_credits = c2[pd.notna(c2["issue_date"]) & (c2["issue_date"] < c2["signup_date"])]
        for _, r in early_credits.iterrows():
            issues.append({"entity": "credits", "issue": "credit_before_signup", "id": r["credit_id"], "severity": "Warning", "desc": "issued before signup"})
        bad_due = c2[pd.notna(c2["due_date"]) & pd.notna(c2["issue_date"]) & (c2["due_date"] < c2["issue_date"])]
        for _, r in bad_due.iterrows():
            issues.append({"entity": "credits", "issue": "due_before_issue", "id": r["credit_id"], "severity": "Warning", "desc": "due date before issue date"})

    # 4) Wallet inconsistencies vs invoices
    if not w.empty and "seller_id" in w.columns:
        inv = ensure_invoice_total(inv, inv_items)
        wallet_amount_col = pick_first_col(w, ["amount", "value", "delta", "transaction_amount"])
        if wallet_amount_col and "invoice_total" in inv.columns and "seller_id" in inv.columns:
            w_sum = w.groupby("seller_id", as_index=False)[wallet_amount_col].sum().rename(columns={wallet_amount_col: "wallet_sum"})
            inv_sum = inv.groupby("seller_id", as_index=False)["invoice_total"].sum().rename(columns={"invoice_total": "invoices_sum"})
            chk = w_sum.merge(inv_sum, on="seller_id", how="outer").fillna(0)
            diff = np.round(chk["wallet_sum"] - chk["invoices_sum"], 2)
            # Check both absolute and relative tolerance
            abs_tolerance_exceeded = np.abs(diff) > WALLET_INV_TOLERANCE
            rel_tolerance_exceeded = (np.abs(diff) / chk["invoices_sum"].replace(0, np.nan)) > WALLET_INV_REL_TOL
            bad = chk[abs_tolerance_exceeded & rel_tolerance_exceeded.fillna(False)]
            for _, r in bad.iterrows():
                issues.append({"entity": "wallet", "issue": "wallet_invoice_mismatch", "id": r["seller_id"], "severity": "Warning", "desc": f"wallet_sum={r['wallet_sum']} vs invoices_sum={r['invoices_sum']}"})
        else:
            logging.info("Skipping wallet check (no usable wallet amount column or invoices missing totals).")

    logging.info("Business logic validation issues found: %d", len(issues))
    return issues


# --------------------------------------------------
# 2.3 Statistical Outlier Detection
# --------------------------------------------------
def statistical_outliers(d: Dict[str, pd.DataFrame]) -> List[Dict]:
    issues: List[Dict] = []
    c, i, l, s = d["credits"], d["invoices"], d["leads"], d["sellers"]

    # Credit amount outliers
    if not c.empty and "amount" in c.columns:
        q01, q99 = c["amount"].quantile(0.01), c["amount"].quantile(0.99)
        outliers = c[(c["amount"] < q01) | (c["amount"] > q99)]
        for _, r in outliers.iterrows():
            issues.append({"entity": "credits", "issue": "amount_outlier", "id": r["credit_id"], "severity": "Info", "desc": f"{r['amount']} outside [{q01},{q99}]"})
    else:
        logging.info("Skipping credit amount outlier check (amount column missing).")

    # Sellers with 0 leads but active credits (Approved/Deposit)
    if "status" in c.columns and "seller_id" in c.columns and "seller_id" in s.columns:
        active_status = {"approved", "deposit"}
        has_active = c.assign(active=c["status"].astype(str).str.lower().isin(active_status)).groupby("seller_id", as_index=False)["active"].max()
        leads_cnt = l.groupby("seller_id", as_index=False)["lead_id"].count().rename(columns={"lead_id": "lead_count"})
        m = s[["seller_id"]].merge(has_active, on="seller_id", how="left").merge(leads_cnt, on="seller_id", how="left").fillna({"active": False, "lead_count": 0}).infer_objects(copy=False)
        flag = m[(m["active"] == True) & (m["lead_count"] == 0)]
        for _, r in flag.iterrows():
            issues.append({"entity": "sellers", "issue": "active_credit_no_leads", "id": r["seller_id"], "severity": "Warning", "desc": "active credit but no leads"})
    else:
        logging.info("Skipping active credit/no leads check (missing columns).")

    # Invoice fee ratio outliers
    sales_col = pick_first_col(i, ["sales_amount", "amount_sales", "sales"])
    fees_col = pick_first_col(i, ["fees", "fee", "total_fees"])
    if sales_col and fees_col:
        tmp = i.copy()
        tmp["fee_ratio"] = pd.to_numeric(tmp[fees_col], errors="coerce") / pd.to_numeric(tmp[sales_col], errors="coerce").replace(0, np.nan)
        bad = tmp[(tmp["fee_ratio"] < 0.05) | (tmp["fee_ratio"] > 0.40)]
        for _, r in bad.iterrows():
            issues.append({"entity": "invoices", "issue": "fee_ratio_outlier", "id": r.get("invoice_id", np.nan), "severity": "Info", "desc": f"fee_ratio={r['fee_ratio']:.3f}"})
    else:
        logging.info("Skipping invoice fee ratio outlier check (missing columns).")

    # Seller conversion extremes
    if "status" in l.columns:
        ll = l.assign(confirmed=l["status"].astype(str).str.lower().eq("confirmed"))
        agg = ll.groupby("seller_id", as_index=False).agg(leads=("lead_id", "count"), conf=("confirmed", "sum"))
        agg["conv"] = agg["conf"] / agg["leads"].replace(0, np.nan)
        ext = agg[(agg["leads"] >= MIN_LEADS_FOR_CONV_EXTREME) & ((agg["conv"] < LOW_CONV_THRESHOLD) | (agg["conv"] > HIGH_CONV_THRESHOLD))]
        for _, r in ext.iterrows():
            issues.append({"entity": "sellers", "issue": "conversion_extreme", "id": r["seller_id"], "severity": "Info", "desc": f"conv={r['conv']:.2f} over {int(r['leads'])} leads"})
    else:
        logging.info("Skipping conversion extremes check (status column missing on leads).")

    logging.info("Outlier detection issues found: %d", len(issues))
    return issues


# --------------------------------------------------
# 2.4 Credit Lifecycle Reconciliation
# --------------------------------------------------
def credit_lifecycle_reconciliation(d: Dict[str, pd.DataFrame]) -> List[Dict]:
    """
    Reconstruct expected credit status with simple heuristic:
      - If total invoices after issue_date >= amount => expected 'paid'
      - Else if invoices after issue_date > 0 => expected 'approved'
      - Else if due_date passed and no invoices => expected 'cancelled'
      - Else => expected 'inreview'
    
    Credit invoices are scoped per credit window: [issue_date, next_credit_issue_date)
    for the same seller to prevent cross-credit leakage.
    
    Credit histories override to 'paid'/'cancelled' when present as final event.
    """
    issues: List[Dict] = []
    c, inv, ch = d["credits"], d["invoices"], d["credit_histories"]

    inv = ensure_invoice_total(inv, d["invoice_items"])
    date_col = "period_start" if "period_start" in inv.columns else None
    now = pd.Timestamp.now().normalize()

    # Precompute next credit issue date per seller for windowing
    c_sorted = c.sort_values(["seller_id", "issue_date"]).copy()
    c_sorted["next_issue_date"] = c_sorted.groupby("seller_id")["issue_date"].shift(-1)

    for idx, r in c.iterrows():
        sid = r.get("seller_id")
        issued_amt = pd.to_numeric(r.get("amount"), errors="coerce")
        if pd.isna(issued_amt) or pd.isna(sid):
            continue

        # Sum invoices for this credit within windowed time range
        mask = inv["seller_id"] == sid
        
        # Window start: credit issue_date
        if date_col and pd.notna(r.get("issue_date")):
            mask &= inv[date_col] >= r["issue_date"]
        
        # Window end: min(next_credit_issue_date, due_date) for the same seller
        window_end_candidates = []
        if idx in c_sorted.index:
            next_issue = c_sorted.loc[idx, "next_issue_date"]
            if pd.notna(next_issue):
                window_end_candidates.append(pd.to_datetime(next_issue))
        
        due_date = r.get("due_date")
        if pd.notna(due_date):
            window_end_candidates.append(pd.to_datetime(due_date))
        
        if window_end_candidates and date_col:
            window_end = min(window_end_candidates)
            mask &= inv[date_col] < window_end
        
        inv_sum = pd.to_numeric(inv.loc[mask, "invoice_total"], errors="coerce").fillna(0).sum()

        # Baseline expectation
        expected = "paid" if inv_sum >= issued_amt else ("approved" if inv_sum > 0 else "inreview")

        # due_date handling
        if pd.notna(due_date):
            due_dt = pd.to_datetime(due_date)
            # If tz-aware, convert to naive for consistent comparison
            if getattr(due_dt, "tzinfo", None) is not None:
                due_dt = due_dt.tz_convert(None) if hasattr(due_dt, "tz_convert") else due_dt.tz_localize(None)
            if due_dt < now and inv_sum == 0:
                expected = "cancelled"

        # History override if last known final state is paid/cancelled
        if not ch.empty and "credit_id" in ch.columns and "status" in ch.columns:
            hist = ch[ch["credit_id"] == r.get("credit_id")]
            if not hist.empty:
                order_col = pick_first_col(hist, ["created_at", "event_time", "timestamp"]) or "created_at"
                if order_col in hist.columns:
                    last_status = str(hist.sort_values(order_col)["status"].iloc[-1]).lower()
                    if last_status in {"paid", "cancelled"}:
                        expected = last_status

        actual = str(r.get("status")).lower()
        if actual != expected:
            issues.append({
                "entity": "credits",
                "issue": "status_mismatch",
                "id": r.get("credit_id", np.nan),
                "severity": "Warning",
                "desc": f"actual={actual}, expected={expected}, inv_sum={inv_sum}, issued={issued_amt}"
            })

    logging.info("Credit lifecycle mismatches found: %d", len(issues))
    return issues


# --------------------------------------------------
# 2.5 Scorecard + Reporting
# --------------------------------------------------
def build_scorecard(d: Dict[str, pd.DataFrame], issues: List[Dict]) -> pd.DataFrame:
    df_issues = pd.DataFrame(issues)
    rows = []
    label_map = {
        "sellers": "Sellers",
        "credits": "Credits",
        "invoices": "Invoices",
        "invoice_items": "InvoiceItems",
        "leads": "Leads",
        "wallet": "Wallet",
        "account_managers": "AccountManagers",
        "senior_account_managers": "SeniorAccountManagers",
        "credit_histories": "CreditHistories",
        "credit_chat": "CreditChat",
    }
    for name, df in d.items():
        total = len(df)
        errors = len(df_issues[df_issues["entity"] == name]) if not df_issues.empty else 0
        clean = max(total - errors, 0)
        score = 0.0 if total == 0 else round((clean / total) * 100.0, 2)
        rows.append({
            "Entity": label_map.get(name, name),
            "Total Records": total,
            "Clean Records": clean,
            "Issues": errors,
            "Quality Score (%)": score
        })
    return pd.DataFrame(rows)


def safe_to_markdown(df: pd.DataFrame) -> str:
    """Prefer markdown; fall back to CSV string if tabulate not available."""
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_csv(index=False)


def generate_findings_report(df_issues: pd.DataFrame, df_score: pd.DataFrame, out_path: Path) -> None:
    lines: List[str] = []
    lines.append("# Data Quality Findings\n")
    lines.append(f"_Run at: {pd.Timestamp.utcnow().isoformat()}Z_\n")
    lines.append("This report summarizes the checks executed by the validation framework.\n")

    # Quick overview
    lines.append("## Overview\n")
    sev_counts = {} if df_issues.empty else df_issues["severity"].value_counts().to_dict()
    lines.append(f"- Total issues detected: {len(df_issues)}\n")
    if sev_counts:
        parts = [f"{k}={v}" for k, v in sev_counts.items()]
        lines.append(f"- By severity: {', '.join(parts)}\n")
    lines.append(f"- Entities analyzed: {', '.join(df_score['Entity'].tolist())}\n")

    # Scorecard
    lines.append("\n## Data Quality Scorecard\n")
    lines.append(safe_to_markdown(df_score))
    lines.append("\n")

    if not df_issues.empty:
        lines.append("\n## Issue Summary by Type\n")
        summary = df_issues.groupby(["entity", "issue", "severity"]).size().reset_index(name="count")
        lines.append(safe_to_markdown(summary))
        lines.append("\n")

        # Top 10 mismatches (where applicable)
        top = df_issues[df_issues["issue"].eq("status_mismatch")].head(10)
        if not top.empty:
            lines.append("\n## Top 10 Credit Status Mismatches\n")
            lines.append(safe_to_markdown(top[["entity", "id", "issue", "severity", "desc"]]))
            lines.append("\n")
    else:
        lines.append("\nNo issues found.\n")

    lines.append("\n## Severity Guidance\n")
    lines.append(
        "| Severity | Definition | Examples |\n"
        "|---------|------------|----------|\n"
        "| Critical | Breaks financial or contractual logic | credit_limit_exceeded, arithmetic_error |\n"
        "| Warning  | Likely to skew reporting or KPIs | lead_before_signup, due_before_issue, status_mismatch |\n"
        "| Info     | Anomalies worth review | amount_outlier, fee_ratio_outlier, conversion_extreme |\n"
    )

    lines.append("\n## Recommendations\n")
    lines.append("- Credits: review status_mismatch and enforce pre-issuance checks against seller credit_limit.\n")
    lines.append("- Invoices: standardize columns (sales_amount, fees, credits_due, from_balance) and reconcile totals.\n")
    lines.append("- Wallet: reconcile with invoices weekly and investigate persistent gaps beyond tolerance.\n")
    lines.append("- Leads: monitor temporal violations and extreme conversion cohorts; tune lead routing.\n")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    logging.info("Markdown report written: %s", out_path)


# --------------------------------------------------
# Orchestrate
# --------------------------------------------------
def run_validation(data_dir: Path, out_dir: Path, min_severity: str = "Info") -> None:
    t0 = time.time()
    setup_logging(out_dir)

    logging.info("Starting validation with data_dir=%s out_dir=%s min_severity=%s", data_dir, out_dir, min_severity)

    data = load_data(data_dir)

    # Execute checks
    sections = [
        ("Referential Integrity", referential_integrity_checks),
        ("Business Logic", business_logic_validation),
        ("Outliers", statistical_outliers),
        ("Credit Lifecycle", credit_lifecycle_reconciliation),
    ]
    issues: List[Dict] = []
    for name, fn in sections:
        s0 = time.time()
        result = fn(data)
        issues.extend(result)
        logging.info("%s check completed in %.2fs (%d new issues)", name, time.time() - s0, len(result))

    df_issues = pd.DataFrame(issues, columns=["entity", "issue", "id", "severity", "desc"])
    
    # Apply severity filter
    severity_rank = {"Info": 0, "Warning": 1, "Critical": 2}
    min_rank = severity_rank[min_severity]
    df_issues_filtered = df_issues[df_issues["severity"].map(severity_rank) >= min_rank]
    
    df_score = build_scorecard(data, issues)  # Use unfiltered issues for scorecard to show full picture

    # Persist outputs (only report.csv and findings.md)
    out_dir.mkdir(parents=True, exist_ok=True)
    df_issues_filtered.to_csv(out_dir / "data_quality_report.csv", index=False, encoding="utf-8")
    generate_findings_report(df_issues_filtered, df_score, out_dir / "data_quality_findings.md")

    # Final log summary
    total_time = time.time() - t0
    sev_counts = {} if df_issues_filtered.empty else df_issues_filtered["severity"].value_counts().to_dict()
    logging.info("Validation completed in %.2fs | Issues by severity (filtered): %s", total_time, sev_counts)
    logging.info("\n%s", df_score.to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Part 2 — Data Quality & Validation Framework")
    parser.add_argument("--data-dir", type=Path, default=Path("./credit_challenge_dataset"), help="Path to dataset CSV folder")
    parser.add_argument("--out-dir", type=Path, default=Path("."), help="Directory to write outputs")
    parser.add_argument("--min-severity", choices=["Info", "Warning", "Critical"], default="Info", help="Minimum severity level to report")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_validation(args.data_dir, args.out_dir, args.min_severity)


if __name__ == "__main__":
    main()