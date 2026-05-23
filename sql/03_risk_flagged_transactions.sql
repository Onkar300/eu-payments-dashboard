-- ============================================================
-- Script  : 03_risk_flagged_transactions.sql
-- Purpose : Analyse flagged high-risk transactions
-- KPI     : Risk Flag Rate = Flagged / Total Transactions
-- Used in : Risk & Anomaly Monitor dashboard page
-- ============================================================

-- ── Part A: Monthly risk flag summary ────────────────────────
SELECT
    year,
    month,
    month_name,

    COUNT(*)                                                        AS total_transactions,

    -- Flagged counts and rate
    SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END)                AS flagged_count,
    ROUND(
        100.0 * SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                               AS flag_rate_pct,

    -- Flagged volume (how much EUR is at risk)
    ROUND(
        SUM(CASE WHEN is_flagged = 1 THEN amount_eur ELSE 0 END),
        2
    )                                                               AS flagged_volume_eur,

    -- Average risk score of flagged transactions
    ROUND(
        AVG(CASE WHEN is_flagged = 1 THEN risk_score END),
        2
    )                                                               AS avg_risk_score_flagged,

    -- Flagged breakdown by payment type
    SUM(CASE WHEN is_flagged = 1 AND payment_type = 'SWIFT'               THEN 1 ELSE 0 END) AS flagged_swift,
    SUM(CASE WHEN is_flagged = 1 AND payment_type = 'SEPA Credit Transfer' THEN 1 ELSE 0 END) AS flagged_sepa_credit,
    SUM(CASE WHEN is_flagged = 1 AND payment_type = 'Card Payment'         THEN 1 ELSE 0 END) AS flagged_card,

    -- Off-hours flagged transactions
    SUM(CASE WHEN is_flagged = 1 AND is_off_hours = 1 THEN 1 ELSE 0 END)  AS flagged_off_hours

FROM transactions

GROUP BY
    year,
    month,
    month_name

ORDER BY
    year ASC,
    month ASC;
