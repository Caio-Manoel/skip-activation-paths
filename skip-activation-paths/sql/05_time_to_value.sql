-- =============================================================================
-- 05_time_to_value.sql
-- Questions: what does time-to-first-value (TTFV) look like as a distribution,
-- and how does retention vary by TTFV bucket? (H6)
-- TTFV = signup → first intent-specific FMO. Users who never reach it are a
-- bucket of their own, not missing data.
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

-- Q: TTFV distribution by intent (hours), among users who reached value — percentiles, not means
SELECT
    initial_intent,
    COUNT(*)                                                      AS signups,
    COUNT(ttfv_hours)                                             AS reached_value_ever,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ttfv_hours), 2) AS p25_hours,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ttfv_hours), 2) AS median_hours,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ttfv_hours), 2) AS p75_hours,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY ttfv_hours), 2) AS p90_hours,
    ROUND(AVG(ttfv_hours), 2)                                     AS mean_hours_misleading
FROM user_milestones
GROUP BY 1
ORDER BY 1;

-- Q: Retention by TTFV bucket — denominators shown; "never" is a real bucket
SELECT
    CASE
        WHEN ttfv_hours IS NULL  THEN '5. never'
        WHEN ttfv_hours <= 1     THEN '1. within 1 hour'
        WHEN ttfv_days = 0       THEN '2. same day'
        WHEN ttfv_days <= 3      THEN '3. day 1-3'
        ELSE                          '4. day 4+'
    END                              AS ttfv_bucket,
    COUNT(*)                         AS users,
    COUNT(d30_value)                 AS d30_observed,
    ROUND(AVG(d7_value), 3)          AS d7_value,
    ROUND(AVG(d30_value), 3)         AS d30_value
FROM user_retention
GROUP BY 1
ORDER BY 1;

-- Q: Same, by intent, excluding "never" — does speed matter once value is reached?
SELECT
    initial_intent,
    IFF(ttfv_days = 0, 'same day', 'later') AS ttfv_group,
    COUNT(d30_value)                        AS d30_observed,
    ROUND(AVG(d30_value), 3)                AS d30_value
FROM user_retention
WHERE ttfv_hours IS NOT NULL AND d30_value IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2 DESC;

-- Q: TTFV histogram (hours, log-ish bins) for the dashboard
SELECT
    CASE
        WHEN ttfv_hours <= 0.25 THEN '0-15m'
        WHEN ttfv_hours <= 1    THEN '15m-1h'
        WHEN ttfv_hours <= 6    THEN '1-6h'
        WHEN ttfv_hours <= 24   THEN '6-24h'
        WHEN ttfv_hours <= 72   THEN '1-3d'
        WHEN ttfv_hours <= 168  THEN '3-7d'
        ELSE '7d+'
    END AS bin,
    MIN(ttfv_hours) AS bin_min,
    COUNT(*) AS users
FROM user_milestones
WHERE ttfv_hours IS NOT NULL
GROUP BY 1
ORDER BY bin_min;
