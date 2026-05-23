"""
EU Payments KPI & Risk Reporting Dashboard
Script: generate_transactions.py
Purpose: Generate 12,000 synthetic EU payment transactions with realistic
         patterns, risk signals, and anomalies for analysis.
Author: Your Name
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta

# ── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker("de_DE")           # German locale for realistic EU names/BICs
Faker.seed(SEED)

# ── Configuration ─────────────────────────────────────────────────────────────
NUM_TRANSACTIONS = 12_000
START_DATE = datetime(2023, 1, 1)
END_DATE   = datetime(2024, 12, 31)

# ── Reference Data ────────────────────────────────────────────────────────────

EU_COUNTRIES = ["DE", "FR", "NL", "IT", "ES", "PL", "BE", "AT", "SE", "DK",
                "FI", "PT", "CZ", "HU", "RO"]

NON_EU_COUNTRIES = ["GB", "CH", "US", "AE", "SG", "HK"]   # higher risk weight

PAYMENT_TYPES = {
    "SEPA Credit Transfer": 0.45,
    "SEPA Direct Debit":    0.25,
    "SWIFT":                0.15,
    "Card Payment":         0.15,
}

PROCESSING_STATUS = {
    "Completed": 0.78,
    "Pending":   0.10,
    "Failed":    0.08,
    "Reversed":  0.04,
}

MERCHANT_CATEGORIES = {
    "Retail":          0.25,
    "SaaS / Software": 0.15,
    "Travel":          0.12,
    "Healthcare":      0.10,
    "Real Estate":     0.08,
    "Financial Svcs":  0.10,
    "Manufacturing":   0.08,
    "Logistics":       0.07,
    "Gambling":        0.03,   # higher risk
    "Crypto Exchange": 0.02,   # higher risk
}

CUSTOMER_SEGMENTS = {
    "Retail":    0.50,
    "SME":       0.35,
    "Corporate": 0.15,
}

CURRENCIES = {
    "EUR": 0.65,
    "GBP": 0.10,
    "CHF": 0.10,
    "PLN": 0.08,
    "SEK": 0.07,
}

# Approximate FX rates to EUR (as of mid-2024)
FX_TO_EUR = {
    "EUR": 1.00,
    "GBP": 1.17,
    "CHF": 1.10,
    "PLN": 0.23,
    "SEK": 0.09,
}

# BIC prefixes by country (simplified but realistic)
BIC_PREFIXES = {
    "DE": ["DEUTDEDB", "COBADEFF", "SSKMDEMMXXX", "BYLADEM1"],
    "FR": ["BNPAFRPP", "SOGEFRPP", "CMCIFRPP"],
    "NL": ["INGBNL2A", "ABNANL2A", "RABONL2U"],
    "IT": ["UNCRITMM", "BCITITMM", "BNLIITRR"],
    "ES": ["BBVAESBB", "CAIXESBB", "SANESSS"],
    "GB": ["BARCGB22", "HBUKGB4B", "NWBKGB2L"],
    "CH": ["UBSWCHZH", "CRESCHZZ"],
    "US": ["CHASUS33", "BOFAUS3N"],
    "PL": ["PKOPPLPW", "BREXPLPW"],
    "SE": ["SWEDSESS", "HANDSESS"],
    "OTHER": ["XXXXXXXX"],
}


# ── Helper Functions ──────────────────────────────────────────────────────────

def weighted_choice(options: dict) -> str:
    """Pick a key from a dict using values as weights."""
    keys   = list(options.keys())
    weights = list(options.values())
    return random.choices(keys, weights=weights, k=1)[0]


def random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between start and end."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def generate_amount(segment: str, payment_type: str) -> float:
    """
    Generate a transaction amount that reflects realistic patterns:
    - Corporate transactions are larger on average
    - SWIFT tends to be high-value
    - Card payments are smaller
    """
    if payment_type == "Card Payment":
        amount = np.random.lognormal(mean=4.5, sigma=1.0)   # ~€90 median
        amount = np.clip(amount, 5, 5_000)
    elif payment_type == "SWIFT":
        amount = np.random.lognormal(mean=9.0, sigma=1.5)   # ~€8k median
        amount = np.clip(amount, 1_000, 2_000_000)
    elif segment == "Corporate":
        amount = np.random.lognormal(mean=8.5, sigma=1.3)
        amount = np.clip(amount, 500, 1_500_000)
    elif segment == "SME":
        amount = np.random.lognormal(mean=7.0, sigma=1.2)
        amount = np.clip(amount, 100, 500_000)
    else:  # Retail
        amount = np.random.lognormal(mean=5.5, sigma=1.1)
        amount = np.clip(amount, 10, 50_000)
    return round(float(amount), 2)


def get_bic(country: str) -> str:
    prefixes = BIC_PREFIXES.get(country, BIC_PREFIXES["OTHER"])
    return random.choice(prefixes) + str(random.randint(100, 999))


def calculate_risk_score(row: dict) -> float:
    """
    Rule-based risk scoring (0–100).
    Higher score = higher risk. Rules mirror real compliance logic.
    """
    score = 0.0

    # Rule 1: High-value transaction
    if row["amount_eur"] > 100_000:
        score += 25
    elif row["amount_eur"] > 50_000:
        score += 15
    elif row["amount_eur"] > 10_000:
        score += 8

    # Rule 2: Off-hours transaction (22:00 – 05:00)
    hour = row["transaction_date"].hour
    if hour >= 22 or hour <= 5:
        score += 15

    # Rule 3: Cross-border to non-EU country
    if row["receiver_country"] in NON_EU_COUNTRIES:
        score += 20
    # Rule 4: Sender and receiver in different continents (SWIFT)
    if row["payment_type"] == "SWIFT" and row["receiver_country"] in ["AE", "SG", "HK", "US"]:
        score += 20

    # Rule 5: High-risk merchant category
    if row["merchant_category"] in ["Gambling", "Crypto Exchange"]:
        score += 25

    # Rule 6: Failed or reversed status
    if row["processing_status"] in ["Failed", "Reversed"]:
        score += 10

    # Rule 7: Mismatch — Retail customer sending Corporate-scale amount
    if row["customer_segment"] == "Retail" and row["amount_eur"] > 20_000:
        score += 20

    # Add small random noise to make scores realistic (not perfectly rule-based)
    score += np.random.uniform(0, 5)

    return round(min(score, 100.0), 2)


def inject_anomalies(df: pd.DataFrame, pct: float = 0.03) -> pd.DataFrame:
    """
    Inject deliberate anomalies into ~3% of records to simulate
    real fraud/suspicious patterns for the risk dashboard.
    """
    n_anomalies = int(len(df) * pct)
    anomaly_idx = random.sample(range(len(df)), n_anomalies)

    for idx in anomaly_idx:
        anomaly_type = random.choice([
            "late_night_high_value",
            "rapid_repeat_sender",
            "unusual_country_pair",
            "retail_large_swift",
        ])

        if anomaly_type == "late_night_high_value":
            # Force off-hours + very high amount
            df.at[idx, "transaction_date"] = df.at[idx, "transaction_date"].replace(hour=random.randint(1, 4))
            df.at[idx, "amount_eur"] = round(random.uniform(80_000, 500_000), 2)
            df.at[idx, "payment_type"] = "SWIFT"

        elif anomaly_type == "unusual_country_pair":
            # EU sender → high-risk non-EU receiver
            df.at[idx, "receiver_country"] = random.choice(["AE", "SG", "HK"])
            df.at[idx, "amount_eur"] = round(random.uniform(50_000, 300_000), 2)

        elif anomaly_type == "retail_large_swift":
            # Retail customer sending large SWIFT — segment mismatch
            df.at[idx, "customer_segment"] = "Retail"
            df.at[idx, "payment_type"] = "SWIFT"
            df.at[idx, "amount_eur"] = round(random.uniform(40_000, 200_000), 2)

        elif anomaly_type == "rapid_repeat_sender":
            # High-risk merchant + high amount
            df.at[idx, "merchant_category"] = random.choice(["Gambling", "Crypto Exchange"])
            df.at[idx, "amount_eur"] = round(random.uniform(10_000, 80_000), 2)

    return df


# ── Main Generation Logic ─────────────────────────────────────────────────────

def generate_transactions(n: int = NUM_TRANSACTIONS) -> pd.DataFrame:
    print(f"Generating {n:,} transactions...")
    records = []

    for i in range(n):
        # Core fields
        payment_type     = weighted_choice(PAYMENT_TYPES)
        customer_segment = weighted_choice(CUSTOMER_SEGMENTS)
        sender_country   = weighted_choice({c: 1 for c in EU_COUNTRIES})  # always EU sender
        currency         = weighted_choice(CURRENCIES)
        merchant_cat     = weighted_choice(MERCHANT_CATEGORIES)
        status           = weighted_choice(PROCESSING_STATUS)
        txn_date         = random_date(START_DATE, END_DATE)
        amount_local     = generate_amount(customer_segment, payment_type)
        amount_eur       = round(amount_local * FX_TO_EUR[currency], 2)

        # Receiver country: mostly EU, some non-EU (more likely for SWIFT)
        if payment_type == "SWIFT":
            receiver_pool = EU_COUNTRIES + NON_EU_COUNTRIES
            receiver_weights = [1] * len(EU_COUNTRIES) + [3] * len(NON_EU_COUNTRIES)
        else:
            receiver_pool = EU_COUNTRIES + NON_EU_COUNTRIES
            receiver_weights = [4] * len(EU_COUNTRIES) + [1] * len(NON_EU_COUNTRIES)

        receiver_country = random.choices(receiver_pool, weights=receiver_weights, k=1)[0]

        row = {
            "transaction_id":    str(uuid.uuid4()),
            "transaction_date":  txn_date,
            "amount_local":      amount_local,
            "currency":          currency,
            "amount_eur":        amount_eur,
            "payment_type":      payment_type,
            "processing_status": status,
            "sender_country":    sender_country,
            "receiver_country":  receiver_country,
            "merchant_category": merchant_cat,
            "customer_segment":  customer_segment,
            "sender_bic":        get_bic(sender_country),
            "receiver_bic":      get_bic(receiver_country),
            "is_cross_border":   sender_country != receiver_country,
        }
        records.append(row)

        # Progress indicator every 2,000 records
        if (i + 1) % 2_000 == 0:
            print(f"  {i + 1:,} / {n:,} records generated...")

    df = pd.DataFrame(records)

    # ── Inject anomalies before scoring ──────────────────────────────────────
    print("Injecting anomalies...")
    df = inject_anomalies(df, pct=0.03)

    # ── Calculate risk score for every row ───────────────────────────────────
    print("Calculating risk scores...")
    df["risk_score"] = df.apply(calculate_risk_score, axis=1)

    # ── Derive flag: risk_score >= 60 is flagged for review ──────────────────
    df["is_flagged"] = df["risk_score"] >= 60

    # ── Add derived time columns (useful in Power BI) ─────────────────────────
    df["year"]          = df["transaction_date"].dt.year
    df["month"]         = df["transaction_date"].dt.month
    df["month_name"]    = df["transaction_date"].dt.strftime("%b")
    df["day_of_week"]   = df["transaction_date"].dt.day_name()
    df["hour"]          = df["transaction_date"].dt.hour
    df["quarter"]       = df["transaction_date"].dt.quarter
    df["week_number"]   = df["transaction_date"].dt.isocalendar().week.astype(int)
    df["is_weekend"]    = df["transaction_date"].dt.dayofweek >= 5
    df["is_off_hours"]  = df["hour"].apply(lambda h: h >= 22 or h <= 5)

    # ── Sort by date ──────────────────────────────────────────────────────────
    df = df.sort_values("transaction_date").reset_index(drop=True)

    print(f"\nDone! {len(df):,} transactions generated.")
    return df


# ── Summary Statistics ────────────────────────────────────────────────────────

def print_summary(df: pd.DataFrame) -> None:
    print("\n" + "="*55)
    print("  DATASET SUMMARY")
    print("="*55)
    print(f"  Total transactions   : {len(df):,}")
    print(f"  Date range           : {df['transaction_date'].min().date()} → {df['transaction_date'].max().date()}")
    print(f"  Total volume (EUR)   : €{df['amount_eur'].sum():,.0f}")
    print(f"  Avg transaction (EUR): €{df['amount_eur'].mean():,.2f}")
    print(f"  Flagged transactions : {df['is_flagged'].sum():,} ({df['is_flagged'].mean()*100:.1f}%)")
    print(f"  Cross-border txns    : {df['is_cross_border'].sum():,} ({df['is_cross_border'].mean()*100:.1f}%)")
    print()
    print("  Payment type breakdown:")
    pt = df["payment_type"].value_counts()
    for ptype, count in pt.items():
        print(f"    {ptype:<26}: {count:,}")
    print()
    print("  Processing status breakdown:")
    ps = df["processing_status"].value_counts()
    for status, count in ps.items():
        print(f"    {status:<26}: {count:,}")
    print("="*55)


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = generate_transactions()
    print_summary(df)

    # Save to CSV in the /data folder
    output_path = "../data/transactions_raw.csv"
    df.to_csv(output_path, index=False)
    print(f"\nFile saved to: {output_path}")
    print("Next step: open your Jupyter notebook for EDA analysis.")
