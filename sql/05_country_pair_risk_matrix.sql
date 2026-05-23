-- ============================================================
-- Script  : 05_country_pair_risk_matrix.sql
-- Purpose : Analyse risk levels across sender/receiver country pairs
-- KPI     : Which country corridors carry the highest risk?
-- Used in : Transaction Trends + Risk dashboard page
-- ============================================================

SELECT
    sender_country,
    receiver_country,

    -- Volume metrics
    COUNT(*)                                                AS total_transactions,
    ROUND(SUM(amount_eur), 2)                               AS total_volume_eur,
    ROUND(AVG(amount_eur), 2)                               AS avg_amount_eur,

    -- Risk metrics
    ROUND(AVG(risk_score), 2)                               AS avg_risk_score,
    SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END)         AS flagged_count,
    ROUND(
        100.0 * SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS flag_rate_pct,

    -- Flagged volume exposure
    ROUND(
        SUM(CASE WHEN is_flagged = 1 THEN amount_eur ELSE 0 END),
        2
    )                                                       AS flagged_volume_eur,

    -- Cross-border indicator
    is_cross_border,

    -- Risk band for the corridor
    CASE
        WHEN AVG(risk_score) >= 60 THEN 'HIGH RISK'
        WHEN AVG(risk_score) >= 35 THEN 'MEDIUM RISK'
        ELSE                            'LOW RISK'
    END                                                     AS corridor_risk_band

FROM transactions

GROUP BY
    sender_country,
    receiver_country,
    is_cross_border

HAVING
    COUNT(*) >= 10              -- Only corridors with meaningful volume

ORDER BY
    avg_risk_score DESC,
    total_volume_eur DESC;
