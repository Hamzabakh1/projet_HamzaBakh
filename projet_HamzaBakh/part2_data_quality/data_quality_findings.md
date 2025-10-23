# Data Quality Findings

_Run at: 2025-10-23T15:50:06.471026+00:00Z_

This report summarizes the checks executed by the validation framework.

## Overview

- Total issues detected: 35144

- By severity: Critical=24804, Warning=10324, Info=16

- Entities analyzed: Sellers, Credits, Leads, Invoices, InvoiceItems, AccountManagers, SeniorAccountManagers, Wallet, CreditHistories, CreditChat


## Data Quality Scorecard

| Entity                |   Total Records |   Clean Records |   Issues |   Quality Score (%) |
|:----------------------|----------------:|----------------:|---------:|--------------------:|
| Sellers               |             300 |             190 |      110 |               63.33 |
| Credits               |             800 |               0 |     1104 |                0    |
| Leads                 |           20000 |           10970 |     9030 |               54.85 |
| Invoices              |           27600 |            2906 |    24694 |               10.53 |
| InvoiceItems          |          138000 |          138000 |        0 |              100    |
| AccountManagers       |              20 |              20 |        0 |              100    |
| SeniorAccountManagers |               5 |               5 |        0 |              100    |
| Wallet                |           27600 |           27394 |      206 |               99.25 |
| CreditHistories       |            3137 |            3137 |        0 |              100    |
| CreditChat            |            1600 |            1600 |        0 |              100    |



## Issue Summary by Type

| entity   | issue                   | severity   |   count |
|:---------|:------------------------|:-----------|--------:|
| credits  | amount_outlier          | Info       |      16 |
| credits  | credit_before_signup    | Warning    |     376 |
| credits  | status_mismatch         | Warning    |     712 |
| invoices | arithmetic_error        | Critical   |   24694 |
| leads    | lead_before_signup      | Warning    |    9030 |
| sellers  | credit_limit_exceeded   | Critical   |     110 |
| wallet   | wallet_invoice_mismatch | Warning    |     206 |



## Top 10 Credit Status Mismatches

| entity   |   id | issue           | severity   | desc                                                                         |
|:---------|-----:|:----------------|:-----------|:-----------------------------------------------------------------------------|
| credits  |    1 | status_mismatch | Warning    | actual=cancelled, expected=approved, inv_sum=479.59, issued=583.37           |
| credits  |    2 | status_mismatch | Warning    | actual=deposit, expected=inreview, inv_sum=-41.800250000000005, issued=608.3 |
| credits  |    3 | status_mismatch | Warning    | actual=deposit, expected=approved, inv_sum=96.32039999999995, issued=519.35  |
| credits  |    5 | status_mismatch | Warning    | actual=deposit, expected=approved, inv_sum=71.83010000000002, issued=264.77  |
| credits  |    6 | status_mismatch | Warning    | actual=paid, expected=inreview, inv_sum=-20175.21, issued=322.93             |
| credits  |    7 | status_mismatch | Warning    | actual=cancelled, expected=inreview, inv_sum=-169.4001, issued=468.48        |
| credits  |    8 | status_mismatch | Warning    | actual=paid, expected=approved, inv_sum=145.37, issued=782.92                |
| credits  |    9 | status_mismatch | Warning    | actual=paid, expected=approved, inv_sum=153.7, issued=669.92                 |
| credits  |   10 | status_mismatch | Warning    | actual=paid, expected=approved, inv_sum=403.6296, issued=668.38              |
| credits  |   11 | status_mismatch | Warning    | actual=paid, expected=inreview, inv_sum=-18321.2503, issued=599.88           |



## Severity Guidance

| Severity | Definition | Examples |
|---------|------------|----------|
| Critical | Breaks financial or contractual logic | credit_limit_exceeded, arithmetic_error |
| Warning  | Likely to skew reporting or KPIs | lead_before_signup, due_before_issue, status_mismatch |
| Info     | Anomalies worth review | amount_outlier, fee_ratio_outlier, conversion_extreme |


## Recommendations

- Credits: review status_mismatch and enforce pre-issuance checks against seller credit_limit.

- Invoices: standardize columns (sales_amount, fees, credits_due, from_balance) and reconcile totals.

- Wallet: reconcile with invoices weekly and investigate persistent gaps beyond tolerance.

- Leads: monitor temporal violations and extreme conversion cohorts; tune lead routing.
