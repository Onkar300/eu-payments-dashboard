-- ============================================================
-- Script  : 08_anomaly_detection_daily.sql
-- Purpose : Detect daily transaction volume spikes and anomalies
-- KPI     : Days where volume deviates significantly from average
-- Used in : Risk & Anomaly Monitor dashboard page
-- ============================================================

-- ── Daily transaction summary with anomaly flag ───────────────
WITH daily_stats AS (
    SELECT
        DATE(transaction_date)                              AS txn_date,
        year,
        month,
        month_name,

        COUNT(*)                                            AS daily_txn_count,
        ROUND(SUM(amount_eur), 2)                           AS daily_volume_eur,
        ROUND(AVG(amount_eur), 2)                           AS daily_avg_amount,
        ROUND(AVG(risk_score), 2)                           AS daily_avg_risk_score,

        -- Flagged transactions that day
        SUM(CASE WHEN is_flagged = 1 THEN 1 ELSE 0 END)    AS daily_flagged_count,

        -- Off-hours transactions that day
        SUM(CASE WHEN is_off_hours = 1 THEN 1 ELSE 0 END)  AS daily_off_hours_count,

        -- High-value transactions (above €50k)
        SUM(CASE WHEN amount_eur > 50000 THEN 1 ELSE 0 END) AS high_value_count

    FROM transactions
    GROUP BY DATE(transaction_date), year, month, month_name
),

-- Calculate the overall average daily volume to compare against
overall_avg AS (
    SELECT
        ROUND(AVG(daily_txn_count), 2)      AS avg_daily_txn_count,
        ROUND(AVG(daily_volume_eur), 2)     AS avg_daily_volume_eur
    FROM daily_stats
)

SELECT
    d.txn_date,
    d.year,
    d.month,
    d.month_name,
    d.daily_txn_count,
    d.daily_volume_eur,
    d.daily_avg_amount,
    d.daily_avg_risk_score,
    d.daily_flagged_count,
    d.daily_off_hours_count,
    d.high_value_count,

    -- Reference averages for comparison
    o.avg_daily_txn_count,
    o.avg_daily_volume_eur,

    -- Deviation from average (how much above/below normal)
    ROUND(d.daily_txn_count - o.avg_daily_txn_count, 2)     AS txn_count_vs_avg,
    ROUND(d.daily_volume_eur - o.avg_daily_volume_eur, 2)    AS volume_vs_avg_eur,

    -- Percentage deviation
    ROUND(
        100.0 * (d.daily_txn_count - o.avg_daily_txn_count) / o.avg_daily_txn_count,
        2
    )                                                        AS txn_deviation_pct,

    -- Anomaly flag: day is anomalous if volume is 50% above average
    CASE
        WHEN d.daily_txn_count > o.avg_daily_txn_count * 1.5  THEN 'VOLUME SPIKE'
        WHEN d.daily_txn_count < o.avg_daily_txn_count * 0.5  THEN 'VOLUME DROP'
        WHEN d.daily_avg_risk_score > 50                       THEN 'HIGH RISK DAY'
        WHEN d.daily_flagged_count > 5                         THEN 'MULTIPLE FLAGS'
        ELSE                                                        'NORMAL'
    END                                                      AS anomaly_type

FROM daily_stats d
CROSS JOIN overall_avg o

ORDER BY
    d.txn_date ASC;
