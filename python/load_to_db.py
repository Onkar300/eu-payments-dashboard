"""
EU Payments KPI & Risk Reporting Dashboard
Script: load_to_db.py
Purpose: Load the raw transactions CSV into a local SQLite database.
         This simulates a data warehouse layer for SQL-based reporting.
Author: Your Name
"""

import sqlite3
import pandas as pd
import os

# ── File Paths ────────────────────────────────────────────────────────────────
CSV_PATH = "../data/transactions_raw.csv"
DB_PATH  = "../data/payments.db"

# ── Load CSV ──────────────────────────────────────────────────────────────────
print("Loading CSV file...")

if not os.path.exists(CSV_PATH):
    print(f"ERROR: Could not find {CSV_PATH}")
    print("Make sure you have run generate_transactions.py first.")
    exit()

df = pd.read_csv(CSV_PATH, parse_dates=["transaction_date"])
print(f"  Loaded {len(df):,} rows and {len(df.columns)} columns.")

# ── Connect to SQLite ─────────────────────────────────────────────────────────
# SQLite creates the .db file automatically if it doesn't exist
print(f"\nConnecting to database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)

# ── Write to Database ─────────────────────────────────────────────────────────
# if_exists="replace" means it will overwrite the table if you run this again
print("Writing transactions table to database...")
df.to_sql(
    name="transactions",
    con=conn,
    if_exists="replace",
    index=False
)
print("  Table 'transactions' created successfully.")

# ── Create Useful Indexes ─────────────────────────────────────────────────────
# Indexes speed up queries on columns we'll filter/group by frequently
print("\nCreating indexes for faster queries...")
cursor = conn.cursor()

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_date       ON transactions(transaction_date);",
    "CREATE INDEX IF NOT EXISTS idx_status     ON transactions(processing_status);",
    "CREATE INDEX IF NOT EXISTS idx_type       ON transactions(payment_type);",
    "CREATE INDEX IF NOT EXISTS idx_country    ON transactions(sender_country);",
    "CREATE INDEX IF NOT EXISTS idx_segment    ON transactions(customer_segment);",
    "CREATE INDEX IF NOT EXISTS idx_flagged    ON transactions(is_flagged);",
    "CREATE INDEX IF NOT EXISTS idx_risk       ON transactions(risk_score);",
]

for idx_sql in indexes:
    cursor.execute(idx_sql)
    print(f"  ✓ {idx_sql.split('idx_')[1].split(' ')[0]} index created")

conn.commit()

# ── Verify: Run a Quick Check Query ──────────────────────────────────────────
print("\nVerification — quick check query:")
check = pd.read_sql_query("""
    SELECT
        COUNT(*)                                    AS total_transactions,
        ROUND(SUM(amount_eur), 2)                   AS total_volume_eur,
        ROUND(AVG(amount_eur), 2)                   AS avg_amount_eur,
        SUM(CASE WHEN is_flagged = 1 THEN 1 END)    AS flagged_count,
        SUM(CASE WHEN is_flagged = 0 THEN 1 END)    AS clean_count
    FROM transactions
""", conn)

print(check.to_string(index=False))

# ── Close Connection ──────────────────────────────────────────────────────────
conn.close()
print(f"\nDone! Database saved to: {DB_PATH}")
print("Next step: run the SQL reporting scripts in the /sql folder.")
