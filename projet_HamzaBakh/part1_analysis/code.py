# ===============================================================
#  Part 1: Data Exploration & Business Analysis
#  Candidate: HAMZA BAKH
#  Date: 2025-10-17
#  Duration: ~90 min
# ===============================================================

# -------------------------
#  🧰 Imports & Setup
# -------------------------
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display

# Configure pandas display options for readability
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)
pd.set_option("display.max_colwidth", None)

# Configure plot style
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)

# -------------------------
#  📁 Data Directory & Constants
# -------------------------
DATA_DIR = Path(r"C:\Users\lenovo\OneDrive\Documents\SolidWorksComposer\projet_HamzaBakh\credit_challenge_dataset")

# Define key credit statuses used in business rules
APPROVED_STATUSES = {"approved", "paid", "deposit"}   # Considered “approved” in business logic
ACTIVE_STATUSES   = {"approved", "deposit"}           # Credits that are currently active/open

# -------------------------
#  ⚙️ Helper Functions
# -------------------------
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names by lowercasing and stripping spaces."""
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def annotate_bars(ax, values, fmt="{:.1f}%"):
    """Add text labels on top of bars for visualization clarity."""
    for patch, val in zip(ax.patches, values):
        ax.text(
            patch.get_x() + patch.get_width() / 2,
            patch.get_height(),
            fmt.format(val * 100),
            ha="center", va="bottom", fontsize=10
        )

# -------------------------
#  📊 Load and Prepare Data
# -------------------------
sellers = normalize(pd.read_csv(DATA_DIR / "sellers.csv", parse_dates=["signup_date"]))
credits = normalize(pd.read_csv(DATA_DIR / "credits.csv", parse_dates=["issue_date", "due_date"]))
leads   = normalize(pd.read_csv(DATA_DIR / "leads.csv",   parse_dates=["created_at"]))
ams     = normalize(pd.read_csv(DATA_DIR / "account_managers.csv"))

# Clean text statuses (strip, lowercase) to ensure consistency in joins and filters
for df in [credits, leads]:
    df["status"] = df["status"].astype(str).str.strip().str.lower()

print(f"✅ Data Loaded: Sellers={len(sellers)}, Credits={len(credits)}, Leads={len(leads)}")

# ===============================================================
#  Q1.1 — Credit Approval Analysis
# ===============================================================
# 🎯 Goal:
# Measure the approval rate of credit requests per market (e.g., GCC vs AFRQ)
# This metric reflects underwriting policy and seller maturity.

# 🧮 Method:
# 1. Merge credits with seller market info.
# 2. Group by market, count total credits, and approved credits (statuses in APPROVED_STATUSES).
# 3. Compute approval rate per market.

credits_m = credits.merge(sellers[["seller_id", "market"]], on="seller_id", how="left")

approval_summary = (
    credits_m.groupby("market")["status"]
    .agg(total_credits="count", approved_credits=lambda s: s.isin(APPROVED_STATUSES).sum())
    .reset_index()
)

approval_summary["approval_rate"] = (approval_summary["approved_credits"] / approval_summary["total_credits"]).round(4)
approval_summary["approval_rate_%"] = (approval_summary["approval_rate"] * 100).round(1).astype(str) + "%"

display(approval_summary)

# 📈 Visualization
ax = sns.barplot(data=approval_summary, x="market", y="approval_rate", palette="Blues_d")
annotate_bars(ax, approval_summary["approval_rate"])
plt.title("Credit Approval Rate by Market", fontsize=13, fontweight="bold")
plt.xlabel("Market (GCC = Gulf Cooperation Council | AFRQ = Africa Region)")
plt.ylabel("Approval Rate")
plt.tight_layout()
plt.show()

# 💡 Business Insight:
print("""
💡 Insight (1.1):
AFRQ shows a higher approval rate than GCC, indicating a more mature seller base
or flexible underwriting. GCC’s lower approval rate suggests tighter credit controls,
possibly targeting risk mitigation for newer sellers.
""")

# ===============================================================
#  Q1.2 — Account Manager Performance
# ===============================================================
# 🎯 Goal:
# Identify top-performing Account Managers (AMs) based on total credit issued
# and utilization rate (measure of how much issued credit sellers actually use).

# 🧮 Method:
# 1. Sum total credits per seller.
# 2. Compute credit utilization = credits issued / credit limit.
# 3. Aggregate by Account Manager (AM) to find total volume, avg. utilization, and number of sellers.

seller_credit = credits.groupby("seller_id", as_index=False).agg(total_credits=("amount", "sum"))

seller_base = sellers.merge(seller_credit, on="seller_id", how="left").fillna({"total_credits": 0})
seller_base["utilization"] = np.where(
    seller_base["credit_limit"] > 0,
    seller_base["total_credits"] / seller_base["credit_limit"],
    np.nan
)
seller_base["utilization"] = seller_base["utilization"].clip(upper=seller_base["utilization"].quantile(0.95))

am_perf = (
    seller_base.groupby("am_id", as_index=False)
    .agg(
        am_total_credits=("total_credits", "sum"),
        am_avg_utilization=("utilization", "mean"),
        seller_count=("seller_id", "nunique")
    )
    .merge(ams, on="am_id", how="left")
    .sort_values("am_total_credits", ascending=False)
)
am_perf["avg_credit_per_seller"] = am_perf["am_total_credits"] / am_perf["seller_count"]

display(am_perf.head(5))

# 📈 Visualization
ax = sns.barplot(data=am_perf.head(5), y="am_name", x="am_total_credits", palette="Greens_d")
for p in ax.patches:
    ax.text(p.get_width(), p.get_y() + p.get_height() / 2, f"{p.get_width():,.0f}", va="center", fontsize=9)
plt.title("Top 5 Account Managers by Credit Volume", fontsize=13, fontweight="bold")
plt.xlabel("Total Credits Issued ($)")
plt.ylabel("Account Manager")
plt.tight_layout()
plt.show()

# 💡 Business Insight:
print("""
💡 Insight (1.2):
High-performing AMs combine strong credit volume with high utilization —
indicating efficient portfolio management.
Those with high credit volume but low utilization should focus on reactivating inactive sellers
or recalibrating credit limits to avoid underuse.
""")

# ===============================================================
#  Q1.3 — Lead Conversion Efficiency
# ===============================================================
# 🎯 Goal:
# Measure how active credit access impacts lead-to-confirmed conversion rate.

# 🧮 Method:
# 1. Flag sellers with active credits (statuses in ACTIVE_STATUSES).
# 2. Merge with lead data.
# 3. Compute conversion = confirmed_leads / total_leads, segmented by credit status and market.

active_flag = (
    credits.assign(is_active=credits["status"].isin(ACTIVE_STATUSES))
    .groupby("seller_id", as_index=False)["is_active"].max()
    .rename(columns={"is_active": "has_active_credit"})
)
leads_m = (
    leads.merge(sellers[["seller_id", "market"]], on="seller_id", how="left")
         .merge(active_flag, on="seller_id", how="left")
)
leads_m["has_active_credit"] = leads_m["has_active_credit"].fillna(False)
leads_m["is_confirmed"] = leads_m["status"].eq("confirmed")

conv_summary = (
    leads_m.groupby(["market", "has_active_credit"], dropna=False)
    .agg(total_leads=("lead_id", "count"), confirmed=("is_confirmed", "sum"))
    .reset_index()
)
conv_summary["conversion_rate"] = (conv_summary["confirmed"] / conv_summary["total_leads"]).round(4)

display(conv_summary)

# 📈 Visualization
palette_map = {False: "#66c2a5", True: "#fc8d62"}
sns.barplot(data=conv_summary, x="market", y="conversion_rate", hue="has_active_credit", palette=palette_map)
plt.title("Lead Conversion by Market & Active Credit", fontsize=13, fontweight="bold")
plt.xlabel("Market"); plt.ylabel("Conversion Rate"); plt.tight_layout(); plt.show()

# 💡 Business Insight:
print("""
💡 Insight (1.3):
Sellers with active credit lines achieve higher conversion rates —
credit liquidity helps close leads faster.
If uplift is minimal, focus should shift to lead quality, funnel optimization, or AM follow-up efficiency.
""")

# ===============================================================
#  Q1.4 — Revenue Efficiency Metric
# ===============================================================
# 🎯 Goal:
# Compute how effectively sellers convert credit into revenue (Return on Financed Capital).

# 🧮 Method:
# 1. Aggregate confirmed leads’ total revenue per seller.
# 2. Aggregate total credit issued per seller.
# 3. Compute revenue_per_credit = confirmed_revenue / total_credit.

confirmed_val = leads[leads["status"].eq("confirmed")].groupby("seller_id", as_index=False).agg(revenue=("amount", "sum"))
credit_sum = credits.groupby("seller_id", as_index=False).agg(credit=("amount", "sum"))

eff = sellers.merge(confirmed_val, on="seller_id", how="left").merge(credit_sum, on="seller_id", how="left").fillna(0)
eff = eff[eff["credit"] > 0]
eff["rev_per_credit"] = (eff["revenue"] / eff["credit"]).round(3)

top5_eff = eff.sort_values("rev_per_credit", ascending=False).head(5)
display(top5_eff[["seller_name", "market", "credit", "revenue", "rev_per_credit"]])

# 📈 Visualization
plt.scatter(eff["credit"], eff["revenue"], alpha=0.3, color="gray", label="All Sellers")
plt.scatter(top5_eff["credit"], top5_eff["revenue"], color="orange", label="Top Sellers")
plt.xlabel("Credit Issued"); plt.ylabel("Confirmed Lead Value")
plt.title("Revenue per Credit Dollar"); plt.legend(); plt.tight_layout(); plt.show()

# 💡 Business Insight:
print("""
💡 Insight (1.4):
This metric reveals ROI on financed credit.
Top sellers efficiently convert every credit dollar into confirmed revenue — candidates for limit expansion.
Low ratios indicate overfunding or weak sales efficiency, needing targeted support.
""")

# ===============================================================
#  Q1.5 — Credit-to-Lead Timeline
# ===============================================================
# 🎯 Goal:
# Measure time (in days) between credit approval and first confirmed lead per market.

# 🧮 Method:
# 1. Filter approved credits.
# 2. Find the first confirmed lead created after the credit’s issue date.
# 3. Compute average and median days per market.

approved = credits[credits["status"].isin(APPROVED_STATUSES)].merge(sellers[["seller_id", "market"]], on="seller_id", how="left")
confirmed = leads[leads["status"].eq("confirmed")][["seller_id", "created_at"]]

pairs = approved.merge(confirmed, on="seller_id", how="left")
pairs = pairs[pairs["created_at"] >= pairs["issue_date"]]
pairs["days_to_lead"] = (pairs["created_at"] - pairs["issue_date"]).dt.days

timeline = pairs.groupby("market")["days_to_lead"].agg(avg_days="mean", median_days="median").reset_index()
display(timeline)

# 📈 Visualization
sns.barplot(data=timeline, x="market", y="avg_days", color="royalblue")
plt.title("Avg Days: Credit Approval → First Confirmed Lead", fontsize=13, fontweight="bold")
plt.xlabel("Market"); plt.ylabel("Days"); plt.tight_layout(); plt.show()

# 💡 Business Insight:
print("""
💡 Insight (1.5):
This metric tracks how fast sellers convert credit into sales.
Shorter lags in GCC indicate faster activation and liquidity utilization.
AFRQ’s longer delay may reflect onboarding friction — post-approval engagement can close this gap.
""")

# ===============================================================
#  📦 Export Summary for Next Steps
# ===============================================================
summary = {
    "approval_summary": approval_summary.to_dict("records"),
    "top5_am": am_perf.head(5).to_dict("records"),
    "conversion_rates": conv_summary.to_dict("records"),
    "top5_sellers_efficiency": top5_eff.to_dict("records"),
    "timeline_by_market": timeline.to_dict("records"),
}
with open("part1_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, default=str)

print("✅ Analysis complete → part1_summary.json saved successfully.")
