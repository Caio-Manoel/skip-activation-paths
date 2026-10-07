-- =============================================================================
-- 08_anomaly_detection.sql
-- Questions: is the data trustworthy, and did anything change that would make
-- an activation metric move for reasons unrelated to users?
-- Ratio monitors are used because ratios stay stable when traffic changes;
-- raw counts move with every campaign and weekday.
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

-- Q: Data-quality summary on the raw events table
SELECT
    (SELECT COUNT(*) FROM events)                                              AS raw_events,
    (SELECT COUNT(*) - COUNT(DISTINCT event_id) FROM events)                   AS duplicate_rows,
    (SELECT COUNT(*) FROM events e JOIN users u USING (user_id) WHERE u.is_test_account) AS test_account_events,
    (SELECT COUNT_IF(session_id IS NULL AND platform <> 'server') FROM events) AS client_events_missing_session,
    (SELECT COUNT(*) FROM events e JOIN users u USING (user_id)
      WHERE CAST(e.event_timestamp AS TIMESTAMP) < CAST(u.signup_ts AS TIMESTAMP) - INTERVAL '5 minutes') AS events_before_signup,
    (SELECT COUNT_IF(DATEDIFF(hour, CAST(event_timestamp AS TIMESTAMP), CAST(received_at AS TIMESTAMP)) >= 24)
       FROM events)                                                            AS late_arriving_24h_plus;

-- Q: Orphan outcomes — child events without their parent (ordering / dropped events)
SELECT
    'artifact_saved without artifact_generated (same output_id)' AS check_name,
    COUNT(*) AS orphans
FROM stg_events s
WHERE s.event_name = 'artifact_saved'
  AND NOT EXISTS (SELECT 1 FROM stg_events g
                  WHERE g.output_id = s.output_id
                    AND g.event_name IN ('artifact_generated', 'artifact_regenerated'))
UNION ALL
SELECT
    'analysis_recommendation_clicked without analysis_completed (same output_id)',
    COUNT(*)
FROM stg_events s
WHERE s.event_name = 'analysis_recommendation_clicked'
  AND NOT EXISTS (SELECT 1 FROM stg_events g
                  WHERE g.output_id = s.output_id AND g.event_name = 'analysis_completed');

-- Q: Daily completion-ratio monitor by platform — flag |z| >= 3 vs trailing 28 days
WITH daily AS (
    SELECT
        CAST(event_ts AS DATE) AS d,
        platform,
        COUNT_IF(event_name = 'analysis_started')   AS started,
        COUNT_IF(event_name = 'analysis_completed') AS completed
    FROM stg_events
    WHERE feature = 'analyze'
    GROUP BY 1, 2
),
ratio AS (
    SELECT *, completed / NULLIF(started, 0) AS completion_ratio
    FROM daily
    WHERE started >= 25                       -- avoid noisy small-denominator days
),
scored AS (
    SELECT
        *,
        AVG(completion_ratio)    OVER (PARTITION BY platform ORDER BY d ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS trailing_mean,
        STDDEV(completion_ratio) OVER (PARTITION BY platform ORDER BY d ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS trailing_sd,
        COUNT(*)                 OVER (PARTITION BY platform ORDER BY d ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS trailing_n
    FROM ratio
)
SELECT
    d, platform, started, completed,
    ROUND(completion_ratio, 3)                                   AS completion_ratio,
    ROUND(trailing_mean, 3)                                      AS trailing_mean,
    ROUND((completion_ratio - trailing_mean) / NULLIF(trailing_sd, 0), 1) AS z_score
FROM scored
WHERE trailing_n >= 14
  AND ABS((completion_ratio - trailing_mean) / NULLIF(trailing_sd, 0)) >= 3
ORDER BY d, platform;

-- Q: Signup volume anomalies — daily signups vs the trailing 4 same-weekday average
-- (a mean is used because Snowflake's MEDIAN does not accept a window frame)
WITH daily AS (
    SELECT signup_date AS d, acquisition_channel, COUNT(*) AS signups
    FROM stg_users GROUP BY 1, 2
),
scored AS (
    SELECT *,
        AVG(signups) OVER (PARTITION BY acquisition_channel, DAYOFWEEK(d)
                              ORDER BY d ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING) AS same_weekday_avg
    FROM daily
)
SELECT d, acquisition_channel, signups, same_weekday_avg,
       ROUND(signups / NULLIF(same_weekday_avg, 0), 2) AS ratio
FROM scored
WHERE same_weekday_avg IS NOT NULL
  AND (signups >= 1.6 * same_weekday_avg OR signups <= 0.5 * same_weekday_avg)
ORDER BY d, acquisition_channel;
