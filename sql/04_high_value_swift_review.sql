-- ============================================================
-- Script  : 04_high_value_swift_review.sql
-- Purpose : Identify high-value SWIFT transactions needing review
-- KPI     : Top pending/flagged transactions for analyst queue
-- Used in : Review Queue dashboard page
-- ============================================================

-- ── Part A: Top 50 highest-risk transactions for review ──────
SELECT
    transaction_id,
    transaction_date,
    payment_type,
    sender_country,
    receiver_country,
    customer_segment,
    merchant_category,
    ROUND(amount_eur, 2)        AS amount_eur,
    processing_status,
    risk_score,
    is_flagged,
    is_off_hours,
    is_cross_border,

    -- Priority label based on risk score
    CASE
        WHEN risk_score >= 80 THEN 'CRITICAL'
        WHEN risk_score >= 60 THEN 'HIGH'
        WHEN risk_score >= 40 THEN 'MEDIUM'
        ELSE                       'LOW'
    END                         AS risk_priority

FROM transactions

WHERE
    is_flagged = 1              -- Only flagged transactions
    AND processing_status IN ('Completed', 'Pending')  -- Actionable statuses

ORDER BY
    risk_score DESC,            -- Highest risk first
    amount_eur DESC             -- Then by value

LIMIT 50;


-- ── Part B: Summary of review queue by priority band ─────────
SELECT
    CASE
        WHEN risk_score >= 80 THEN 'CRITICAL'
        WHEN risk_score >= 60 THEN 'HIGH'
        WHEN risk_score >= 40 THEN 'MEDIUM'
        ELSE                       'LOW'
    END                                         AS risk_priority,

    COUNT(*)                                    AS transaction_count,
    ROUND(SUM(amount_eur), 2)                   AS total_volume_eur,
    ROUND(AVG(amount_eur), 2)                   AS avg_amount_eur,
    ROUND(AVG(risk_score), 2)                   AS avg_risk_score

FROM transactions
WHERE is_flagged = 1

GROUP BY risk_priority
ORDER BY avg_risk_score DESC;
