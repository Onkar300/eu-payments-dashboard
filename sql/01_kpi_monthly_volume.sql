-- ============================================================
-- Script  : 01_kpi_monthly_volume.sql
-- Purpose : Monthly transaction volume and value trends
-- KPI     : Total transactions and EUR volume per month
-- Used in : Executive Summary + Transaction Trends dashboard page
-- ============================================================

SELECT
    year,
    month,
    month_name,

    -- Transaction counts
    COUNT(*)                                                AS total_transactions,

    -- Volume in EUR
    ROUND(SUM(amount_eur), 2)                               AS total_volume_eur,

    -- Average transaction value
    ROUND(AVG(amount_eur), 2)                               AS avg_transaction_eur,

    -- Breakdown by payment type
    SUM(CASE WHEN payment_type = 'SEPA Credit Transfer' THEN 1 ELSE 0 END)  AS sepa_credit_count,
    SUM(CASE WHEN payment_type = 'SEPA Direct Debit'    THEN 1 ELSE 0 END)  AS sepa_debit_count,
    SUM(CASE WHEN payment_type = 'SWIFT'                THEN 1 ELSE 0 END)  AS swift_count,
    SUM(CASE WHEN payment_type = 'Card Payment'         THEN 1 ELSE 0 END)  AS card_count,

    -- Volume by payment type
    ROUND(SUM(CASE WHEN payment_type = 'SWIFT' THEN amount_eur ELSE 0 END), 2) AS swift_volume_eur,

    -- Cross-border share
    SUM(CASE WHEN is_cross_border = 1 THEN 1 ELSE 0 END)   AS cross_border_count,
    ROUND(
        100.0 * SUM(CASE WHEN is_cross_border = 1 THEN 1 ELSE 0 END) / COUNT(*),
        2
    )                                                       AS cross_border_pct

FROM transactions

GROUP BY
    year,
    month,
    month_name

ORDER BY
    year ASC,
    month ASC;
