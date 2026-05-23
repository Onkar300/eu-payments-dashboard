-- ============================================================
-- Script  : 06_merchant_category_breakdown.sql
-- Purpose : Performance and risk breakdown by merchant category
-- KPI     : Which merchant categories drive risk and volume?
-- Used in : Transaction Trends dashboard page
-- ============================================================

SELECT
    merchant_category,

    -- Volume metrics
    COUNT(*)                                                AS total_transactions,
    ROUND(SUM(amount_eur), 2)                               AS total_volume_eur,
    ROUND(AVG(amount_eur), 2)                               AS avg_amount_eur,
    ROUND(MIN(amount_eur), 2)                               AS min_amount_eur,
    ROUND(MAX(amount_eur), 2)                               AS max_amount_eur,

    -- Share of total transactions
    ROUND(
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER(),
        2
    )                                                       AS pct_of_total_txns,

    -- Status breakdown
    SUM(CASE WHEN processing_status = 'Completed'  THEN 1 ELSE 0 END)  AS completed_count,
    SUM(CASE WHEN processing_status = 'Failed'     THEN 1 ELSE 0 END)  AS failed_count,
    ROUND(
        100.0 * SUM(CASE WHEN processing_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS approval_rate_pct,

    -- Risk metrics
    ROUND(AVG(risk_score), 2)                               AS avg_risk_score,
    SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END)         AS flagged_count,
    ROUND(
        100.0 * SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS flag_rate_pct,

    -- Flagged volume (EUR at risk per category)
    ROUND(
        SUM(CASE WHEN is_flagged = 1 THEN amount_eur ELSE 0 END),
        2
    )                                                       AS flagged_volume_eur,

    -- Risk classification
    CASE
        WHEN AVG(risk_score) >= 60 THEN 'HIGH RISK'
        WHEN AVG(risk_score) >= 35 THEN 'MEDIUM RISK'
        ELSE                            'LOW RISK'
    END                                                     AS risk_classification

FROM transactions

GROUP BY
    merchant_category

ORDER BY
    avg_risk_score DESC,
    total_volume_eur DESC;
