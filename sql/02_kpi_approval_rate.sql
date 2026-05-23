-- ============================================================
-- Script  : 02_kpi_approval_rate.sql
-- Purpose : Transaction approval, failure and reversal rates
-- KPI     : Approval Rate = Completed / Total Transactions
-- Used in : Executive Summary dashboard page
-- ============================================================

SELECT
    year,
    month,
    month_name,

    -- Total count
    COUNT(*)                                                        AS total_transactions,

    -- Count by status
    SUM(CASE WHEN processing_status = 'Completed'  THEN 1 ELSE 0 END)  AS completed_count,
    SUM(CASE WHEN processing_status = 'Pending'    THEN 1 ELSE 0 END)  AS pending_count,
    SUM(CASE WHEN processing_status = 'Failed'     THEN 1 ELSE 0 END)  AS failed_count,
    SUM(CASE WHEN processing_status = 'Reversed'   THEN 1 ELSE 0 END)  AS reversed_count,

    -- Rate calculations (expressed as percentages)
    ROUND(
        100.0 * SUM(CASE WHEN processing_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                               AS approval_rate_pct,

    ROUND(
        100.0 * SUM(CASE WHEN processing_status = 'Failed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                               AS failure_rate_pct,

    ROUND(
        100.0 * SUM(CASE WHEN processing_status = 'Reversed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                               AS reversal_rate_pct,

    -- Volume lost to failures and reversals
    ROUND(
        SUM(CASE WHEN processing_status IN ('Failed','Reversed') THEN amount_eur ELSE 0 END),
        2
    )                                                               AS lost_volume_eur

FROM transactions

GROUP BY
    year,
    month,
    month_name

ORDER BY
    year ASC,
    month ASC;
