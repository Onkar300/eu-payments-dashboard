-- ============================================================
-- Script  : 07_customer_segment_performance.sql
-- Purpose : KPI performance breakdown by customer segment
-- KPI     : How do Retail, SME and Corporate segments compare?
-- Used in : Executive Summary dashboard page
-- ============================================================

SELECT
    customer_segment,

    -- Transaction volume
    COUNT(*)                                                AS total_transactions,
    ROUND(SUM(amount_eur), 2)                               AS total_volume_eur,
    ROUND(AVG(amount_eur), 2)                               AS avg_amount_eur,

    -- Share of total volume
    ROUND(
        100.0 * SUM(amount_eur) / SUM(SUM(amount_eur)) OVER(),
        2
    )                                                       AS volume_share_pct,

    -- Payment type preferences per segment
    SUM(CASE WHEN payment_type = 'SEPA Credit Transfer' THEN 1 ELSE 0 END) AS sepa_credit_count,
    SUM(CASE WHEN payment_type = 'SEPA Direct Debit'    THEN 1 ELSE 0 END) AS sepa_debit_count,
    SUM(CASE WHEN payment_type = 'SWIFT'                THEN 1 ELSE 0 END) AS swift_count,
    SUM(CASE WHEN payment_type = 'Card Payment'         THEN 1 ELSE 0 END) AS card_count,

    -- Approval rate per segment
    ROUND(
        100.0 * SUM(CASE WHEN processing_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS approval_rate_pct,

    -- Failure rate per segment
    ROUND(
        100.0 * SUM(CASE WHEN processing_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS failure_rate_pct,

    -- Risk profile per segment
    ROUND(AVG(risk_score), 2)                               AS avg_risk_score,
    SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END)         AS flagged_count,
    ROUND(
        100.0 * SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS flag_rate_pct,

    -- Cross-border activity per segment
    ROUND(
        100.0 * SUM(CASE WHEN is_cross_border = 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS cross_border_pct,

    -- Off-hours activity (potential risk indicator)
    SUM(CASE WHEN is_off_hours = 1 THEN 1 ELSE 0 END)       AS off_hours_count,
    ROUND(
        100.0 * SUM(CASE WHEN is_off_hours = 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS off_hours_pct

FROM transactions

GROUP BY
    customer_segment

ORDER BY
    total_volume_eur DESC;
