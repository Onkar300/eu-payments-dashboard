"""
EU Payments KPI & Risk Reporting Dashboard
Script: run_sql_reports.py
Purpose: Run all SQL reporting scripts against the payments database
         and save results as CSVs for Power BI and review.
Author: Your Name
"""

import sqlite3
import pandas as pd
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
DB_PATH      = "../data/payments.db"
SQL_FOLDER   = "../sql"
OUTPUT_FOLDER = "../data/reports"

# Create reports output folder if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Connect to Database ───────────────────────────────────────────────────────
print("Connecting to payments database...")
conn = sqlite3.connect(DB_PATH)

# ── SQL Scripts to Run ────────────────────────────────────────────────────────
# Each entry: (sql_filename, output_csv_name, description)
scripts = [
    ("01_kpi_monthly_volume.sql",        "report_monthly_volume.csv",      "Monthly Volume KPI"),
    ("02_kpi_approval_rate.sql",         "report_approval_rate.csv",       "Approval Rate KPI"),
    ("03_risk_flagged_transactions.sql", "report_risk_flags.csv",          "Risk Flagged Transactions"),
    ("04_high_value_swift_review.sql",   "report_review_queue.csv",        "High Value Review Queue"),
    ("05_country_pair_risk_matrix.sql",  "report_country_risk.csv",        "Country Pair Risk Matrix"),
    ("06_merchant_category_breakdown.sql","report_merchant_breakdown.csv", "Merchant Category Breakdown"),
    ("07_customer_segment_performance.sql","report_segment_performance.csv","Customer Segment Performance"),
    ("08_anomaly_detection_daily.sql",   "report_anomaly_daily.csv",       "Daily Anomaly Detection"),
]

# ── Run Each Script ───────────────────────────────────────────────────────────
print(f"\nRunning {len(scripts)} SQL reports...\n")

for sql_file, csv_file, description in scripts:
    sql_path = os.path.join(SQL_FOLDER, sql_file)
    csv_path = os.path.join(OUTPUT_FOLDER, csv_file)

    if not os.path.exists(sql_path):
        print(f"  ⚠  SKIPPED: {sql_file} not found yet")
        continue

    try:
        # Read the SQL file
        with open(sql_path, "r") as f:
            sql = f.read()

        # For scripts with multiple SELECT statements, run only the first one
        # (SQLite doesn't support multiple result sets)
        first_query = sql.split(";")[0].strip()

        # Run query and load into dataframe
        df = pd.read_sql_query(first_query, conn)

        # Save to CSV
        df.to_csv(csv_path, index=False)

        print(f"  ✓  {description}")
        print(f"     → {len(df):,} rows saved to {csv_file}")

    except Exception as e:
        print(f"  ✗  ERROR in {sql_file}: {e}")

# ── Close Connection ──────────────────────────────────────────────────────────
conn.close()
print(f"\nAll reports saved to: {OUTPUT_FOLDER}")
print("These CSV files are ready to connect to Power BI.")
