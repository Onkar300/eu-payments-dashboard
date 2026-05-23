"""
EU Payments KPI & Risk Reporting Dashboard
Script: eda_analysis.py
Purpose: Exploratory Data Analysis with 6 visualisations covering
         volume trends, risk distribution, country flows,
         merchant breakdown, segment comparison, and anomaly detection.
Author: Your Name
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

# ── Settings ──────────────────────────────────────────────────────────────────
CHART_OUTPUT = "../data/charts"
os.makedirs(CHART_OUTPUT, exist_ok=True)

# Clean professional style for all charts
sns.set_theme(style="whitegrid", palette="Blues_d")
plt.rcParams.update({
    "figure.dpi":      150,
    "figure.facecolor": "white",
    "axes.facecolor":  "white",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "font.family":     "sans-serif",
    "axes.titlesize":  13,
    "axes.titleweight": "bold",
    "axes.labelsize":  11,
})

BLUE       = "#1F4E79"
LIGHT_BLUE = "#2E75B6"
ORANGE     = "#C55A11"
GREY       = "#595959"
RED        = "#C00000"
GREEN      = "#375623"

# ── Load Data ─────────────────────────────────────────────────────────────────
print("Loading transactions data...")
df = pd.read_csv("../data/transactions_raw.csv", parse_dates=["transaction_date"])
print(f"  {len(df):,} rows loaded.\n")

# ── Helper: save chart ────────────────────────────────────────────────────────
def save_chart(fig, filename):
    path = os.path.join(CHART_OUTPUT, filename)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  ✓ Saved: {filename}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Monthly Transaction Volume Trend (2023 vs 2024)
# Business question: How is our payment volume trending over time?
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 1: Monthly Volume Trend...")

monthly = (
    df.groupby(["year", "month"])
    .agg(
        total_transactions=("transaction_id", "count"),
        total_volume_eur=("amount_eur", "sum"),
    )
    .reset_index()
)
monthly["period"] = monthly["month"].apply(
    lambda m: ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"][m-1]
)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Monthly Payment Activity — 2023 vs 2024", fontsize=14, fontweight="bold", y=1.01)

for i, (year, color) in enumerate([(2023, BLUE), (2024, LIGHT_BLUE)]):
    yd = monthly[monthly["year"] == year].sort_values("month")

    # Left: transaction count
    axes[0].plot(yd["period"], yd["total_transactions"],
                 marker="o", color=color, linewidth=2.2, label=str(year))
    # Right: volume in EUR millions
    axes[1].plot(yd["period"], yd["total_volume_eur"] / 1_000_000,
                 marker="o", color=color, linewidth=2.2, label=str(year))

axes[0].set_title("Transaction Count per Month")
axes[0].set_ylabel("Number of Transactions")
axes[0].legend()
axes[0].tick_params(axis="x", rotation=45)

axes[1].set_title("Total Volume per Month (€M)")
axes[1].set_ylabel("Volume (EUR Millions)")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:.1f}M"))
axes[1].legend()
axes[1].tick_params(axis="x", rotation=45)

plt.tight_layout()
save_chart(fig, "01_monthly_volume_trend.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Transaction Amount Distribution by Payment Type
# Business question: What does the value profile look like per payment type?
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 2: Amount Distribution by Payment Type...")

fig, ax = plt.subplots(figsize=(12, 5))

payment_types = df["payment_type"].unique()
colors = [BLUE, LIGHT_BLUE, ORANGE, GREY]

for pt, color in zip(payment_types, colors):
    subset = df[df["payment_type"] == pt]["amount_eur"]
    # Log scale because amounts span several orders of magnitude
    sns.kdeplot(np.log10(subset + 1), ax=ax, label=pt,
                fill=True, alpha=0.25, color=color, linewidth=2)

ax.set_title("Transaction Amount Distribution by Payment Type (Log Scale)")
ax.set_xlabel("Transaction Amount — log₁₀(EUR)")
ax.set_ylabel("Density")
ax.legend(title="Payment Type")

# Add readable x-axis labels
tick_vals = [1, 2, 3, 4, 5, 6]
ax.set_xticks(tick_vals)
ax.set_xticklabels([f"€{10**v:,.0f}" for v in tick_vals])

plt.tight_layout()
save_chart(fig, "02_amount_distribution_by_type.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Risk Score Distribution: Flagged vs Clean Transactions
# Business question: How does our risk scoring separate flagged transactions?
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 3: Risk Score Distribution...")

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Risk Score Analysis", fontsize=14, fontweight="bold")

# Left: distribution of risk scores flagged vs clean
sns.histplot(
    data=df, x="risk_score", hue="is_flagged",
    bins=40, ax=axes[0], palette={0: BLUE, 1: RED},
    alpha=0.7, edgecolor="white"
)
axes[0].set_title("Risk Score Distribution: Flagged vs Clean")
axes[0].set_xlabel("Risk Score (0–100)")
axes[0].set_ylabel("Number of Transactions")
axes[0].axvline(x=60, color=RED, linestyle="--", linewidth=1.5, label="Flag threshold (60)")
axes[0].legend(["Flag threshold (60)", "Clean", "Flagged"])

# Right: average risk score by payment type
avg_risk = df.groupby("payment_type")["risk_score"].mean().sort_values(ascending=False)
bars = axes[1].barh(avg_risk.index, avg_risk.values,
                    color=[RED if v >= 50 else LIGHT_BLUE for v in avg_risk.values],
                    edgecolor="white")
axes[1].set_title("Average Risk Score by Payment Type")
axes[1].set_xlabel("Average Risk Score")
axes[1].axvline(x=50, color=GREY, linestyle="--", linewidth=1, alpha=0.7)

for bar, val in zip(bars, avg_risk.values):
    axes[1].text(val + 0.5, bar.get_y() + bar.get_height()/2,
                 f"{val:.1f}", va="center", fontsize=10)

plt.tight_layout()
save_chart(fig, "03_risk_score_distribution.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Country Heatmap: Transaction Volume by Sender Country
# Business question: Which EU countries are driving the most payment activity?
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 4: Country Volume Heatmap...")

country_data = (
    df.groupby("sender_country")
    .agg(
        total_transactions=("transaction_id", "count"),
        total_volume_eur=("amount_eur", "sum"),
        avg_risk_score=("risk_score", "mean"),
        flagged_count=("is_flagged", "sum"),
    )
    .reset_index()
    .sort_values("total_volume_eur", ascending=False)
)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Transaction Activity by Sender Country", fontsize=14, fontweight="bold")

# Left: total volume bar chart
bars = axes[0].barh(
    country_data["sender_country"],
    country_data["total_volume_eur"] / 1_000_000,
    color=BLUE, edgecolor="white"
)
axes[0].set_title("Total Volume by Country (€M)")
axes[0].set_xlabel("Total Volume (EUR Millions)")
axes[0].invert_yaxis()
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:.0f}M"))

# Right: average risk score per country
color_list = [RED if v >= 50 else LIGHT_BLUE for v in country_data["avg_risk_score"]]
bars2 = axes[1].barh(
    country_data["sender_country"],
    country_data["avg_risk_score"],
    color=color_list, edgecolor="white"
)
axes[1].set_title("Average Risk Score by Country")
axes[1].set_xlabel("Average Risk Score")
axes[1].invert_yaxis()
axes[1].axvline(x=50, color=GREY, linestyle="--", linewidth=1, alpha=0.6)

for bar, val in zip(bars2, country_data["avg_risk_score"]):
    axes[1].text(val + 0.3, bar.get_y() + bar.get_height()/2,
                 f"{val:.1f}", va="center", fontsize=9)

plt.tight_layout()
save_chart(fig, "04_country_volume_heatmap.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Customer Segment Performance Comparison
# Business question: How do Retail, SME and Corporate segments compare?
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 5: Customer Segment Performance...")

seg = (
    df.groupby("customer_segment")
    .agg(
        total_transactions=("transaction_id", "count"),
        total_volume_eur=("amount_eur", "sum"),
        avg_amount=("amount_eur", "mean"),
        approval_rate=("processing_status", lambda x: (x == "Completed").mean() * 100),
        flag_rate=("is_flagged", "mean"),
        avg_risk=("risk_score", "mean"),
    )
    .reset_index()
)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("Customer Segment Performance Dashboard", fontsize=14, fontweight="bold")

colors_seg = [BLUE, LIGHT_BLUE, ORANGE]

# Left: Volume share (pie chart)
axes[0].pie(
    seg["total_volume_eur"],
    labels=seg["customer_segment"],
    autopct="%1.1f%%",
    colors=colors_seg,
    startangle=90,
    wedgeprops={"edgecolor": "white", "linewidth": 2}
)
axes[0].set_title("Volume Share by Segment")

# Middle: Approval rate comparison
bars = axes[1].bar(seg["customer_segment"], seg["approval_rate"],
                   color=colors_seg, edgecolor="white", width=0.5)
axes[1].set_title("Approval Rate by Segment (%)")
axes[1].set_ylabel("Approval Rate (%)")
axes[1].set_ylim(70, 100)
for bar, val in zip(bars, seg["approval_rate"]):
    axes[1].text(bar.get_x() + bar.get_width()/2, val + 0.3,
                 f"{val:.1f}%", ha="center", fontsize=11, fontweight="bold")

# Right: Average risk score comparison
bars2 = axes[2].bar(seg["customer_segment"], seg["avg_risk"],
                    color=colors_seg, edgecolor="white", width=0.5)
axes[2].set_title("Average Risk Score by Segment")
axes[2].set_ylabel("Average Risk Score")
for bar, val in zip(bars2, seg["avg_risk"]):
    axes[2].text(bar.get_x() + bar.get_width()/2, val + 0.3,
                 f"{val:.1f}", ha="center", fontsize=11, fontweight="bold")

plt.tight_layout()
save_chart(fig, "05_segment_performance.png")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Daily Anomaly Detection: Volume Spikes Over Time
# Business question: Which days had abnormal transaction activity?
# ══════════════════════════════════════════════════════════════════════════════
print("Chart 6: Daily Anomaly Detection...")

daily = (
    df.groupby(df["transaction_date"].dt.date)
    .agg(
        daily_count=("transaction_id", "count"),
        daily_volume=("amount_eur", "sum"),
        daily_flagged=("is_flagged", "sum"),
        daily_risk=("risk_score", "mean"),
    )
    .reset_index()
)
daily["transaction_date"] = pd.to_datetime(daily["transaction_date"])
daily = daily.sort_values("transaction_date")

# 30-day rolling average for comparison
daily["rolling_avg"] = daily["daily_count"].rolling(window=30, min_periods=1).mean()
daily["is_spike"] = daily["daily_count"] > daily["rolling_avg"] * 1.5

fig, axes = plt.subplots(2, 1, figsize=(15, 8), sharex=True)
fig.suptitle("Daily Transaction Volume — Anomaly Detection", fontsize=14, fontweight="bold")

# Top: daily count with rolling average and spikes highlighted
axes[0].fill_between(daily["transaction_date"], daily["daily_count"],
                     alpha=0.3, color=BLUE)
axes[0].plot(daily["transaction_date"], daily["daily_count"],
             color=BLUE, linewidth=1, alpha=0.8, label="Daily count")
axes[0].plot(daily["transaction_date"], daily["rolling_avg"],
             color=ORANGE, linewidth=2, linestyle="--", label="30-day rolling avg")

# Mark spike days
spikes = daily[daily["is_spike"]]
axes[0].scatter(spikes["transaction_date"], spikes["daily_count"],
                color=RED, zorder=5, s=40, label="Volume spike")

axes[0].set_title("Daily Transaction Count with Anomaly Spikes")
axes[0].set_ylabel("Transactions per Day")
axes[0].legend(loc="upper right")

# Bottom: daily flagged count
axes[1].fill_between(daily["transaction_date"], daily["daily_flagged"],
                     alpha=0.4, color=RED)
axes[1].plot(daily["transaction_date"], daily["daily_flagged"],
             color=RED, linewidth=1)
axes[1].set_title("Daily Flagged (High-Risk) Transactions")
axes[1].set_ylabel("Flagged Transactions")
axes[1].set_xlabel("Date")

# Add year divider line
axes[1].axvline(pd.Timestamp("2024-01-01"), color=GREY,
                linestyle=":", linewidth=1.5, alpha=0.7)
axes[0].axvline(pd.Timestamp("2024-01-01"), color=GREY,
                linestyle=":", linewidth=1.5, alpha=0.7, label="2024 start")

plt.tight_layout()
save_chart(fig, "06_daily_anomaly_detection.png")


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY PRINT
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*55)
print("  ALL 6 CHARTS GENERATED SUCCESSFULLY")
print("="*55)
print(f"  Charts saved to: {os.path.abspath(CHART_OUTPUT)}")
print()
print("  Chart index:")
print("  01 — Monthly Volume Trend (2023 vs 2024)")
print("  02 — Amount Distribution by Payment Type")
print("  03 — Risk Score Distribution")
print("  04 — Country Volume & Risk Heatmap")
print("  05 — Customer Segment Performance")
print("  06 — Daily Anomaly Detection")
print("="*55)
print("\nNext step: open the charts folder and review each chart.")
print("These are your Power BI dashboard screenshots for your CV.")
