-- =============================================================================
-- 03_retention_cohorts.sql
-- Questions: D1/D7/D30 retention by cohort, intent, activation path, first
-- meaningful outcome and channel. Activity vs. value retention.
--   D1  = active on day 1
--   D7  = active in days [7, 14)   (week-2)
--   D30 = active in days [28, 35)  (week-5)
-- A window only counts for users whose window is fully observed (right-censoring);
-- censored users get NULL, so they drop out of numerators AND denominators.
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

CREATE OR REPLACE VIEW user_retention AS
WITH flags AS (
    SELECT
        user_id,
        MAX(IFF(day_n = 1, 1, 0))                                          AS d1_any,
        MAX(IFF(day_n = 1 AND is_value_event, 1, 0))                       AS d1_value,
        MAX(IFF(day_n BETWEEN 7 AND 13, 1, 0))                             AS d7_any,
        MAX(IFF(day_n BETWEEN 7 AND 13 AND is_value_event, 1, 0))          AS d7_value,
        MAX(IFF(day_n BETWEEN 28 AND 34, 1, 0))                            AS d30_any,
        MAX(IFF(day_n BETWEEN 28 AND 34 AND is_value_event, 1, 0))         AS d30_value,
        -- activity that was ONLY a drawing entry (no other non-session event that day)
        COUNT(DISTINCT IFF(day_n BETWEEN 7 AND 34, day_n, NULL))           AS active_days_w2_w5,
        COUNT(DISTINCT IFF(day_n BETWEEN 7 AND 34 AND NOT is_drawing_entry
                           AND event_name NOT IN ('session_started','grant_viewed'), day_n, NULL))
                                                                           AS non_drawing_days_w2_w5
    FROM stg_events
    GROUP BY 1
)
SELECT
    m.*,
    p.obs_end,
    IFF(DATEADD(day, 2,  m.signup_date) <= p.obs_end, COALESCE(f.d1_any, 0), NULL)    AS d1_any,
    IFF(DATEADD(day, 2,  m.signup_date) <= p.obs_end, COALESCE(f.d1_value, 0), NULL)  AS d1_value,
    IFF(DATEADD(day, 14, m.signup_date) <= p.obs_end, COALESCE(f.d7_any, 0), NULL)    AS d7_any,
    IFF(DATEADD(day, 14, m.signup_date) <= p.obs_end, COALESCE(f.d7_value, 0), NULL)  AS d7_value,
    IFF(DATEADD(day, 35, m.signup_date) <= p.obs_end, COALESCE(f.d30_any, 0), NULL)   AS d30_any,
    IFF(DATEADD(day, 35, m.signup_date) <= p.obs_end, COALESCE(f.d30_value, 0), NULL) AS d30_value,
    COALESCE(f.active_days_w2_w5, 0)       AS active_days_w2_w5,
    COALESCE(f.non_drawing_days_w2_w5, 0)  AS non_drawing_days_w2_w5
FROM user_milestones m
CROSS JOIN analysis_params p
LEFT JOIN flags f ON f.user_id = m.user_id;

-- Q: Retention by weekly signup cohort (activity), with denominators
SELECT
    signup_week,
    COUNT(*)                         AS cohort_size,
    COUNT(d7_any)                    AS d7_observed,
    ROUND(AVG(d1_any), 3)            AS d1,
    ROUND(AVG(d7_any), 3)            AS d7,
    COUNT(d30_any)                   AS d30_observed,
    ROUND(AVG(d30_any), 3)           AS d30
FROM user_retention
GROUP BY 1
ORDER BY 1;

-- Q: Activity vs value retention by initial intent (D30 cohort = fully observed users)
SELECT
    initial_intent,
    COUNT(d30_any)                   AS users_d30_observed,
    ROUND(AVG(d7_any), 3)            AS d7_activity,
    ROUND(AVG(d7_value), 3)          AS d7_value,
    ROUND(AVG(d30_any), 3)           AS d30_activity,
    ROUND(AVG(d30_value), 3)         AS d30_value,
    ROUND(AVG(d30_value) / NULLIF(AVG(d30_any), 0), 3) AS value_share_of_d30_active
FROM user_retention
WHERE d30_any IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Q: Retention by activation path — intent × activated (intent-specific, 7d)
SELECT
    initial_intent,
    activated_intent_7d,
    COUNT(d30_value)                 AS users_d30_observed,
    ROUND(AVG(d1_any), 3)            AS d1_activity,
    ROUND(AVG(d7_value), 3)          AS d7_value,
    ROUND(AVG(d30_value), 3)         AS d30_value
FROM user_retention
WHERE d30_value IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;

-- Q: Retention by first meaningful outcome (what the user got value from first)
SELECT
    COALESCE(first_fmo_feature, '(none)') AS first_fmo_feature,
    COUNT(d30_value)                 AS users_d30_observed,
    ROUND(AVG(d7_value), 3)          AS d7_value,
    ROUND(AVG(d30_value), 3)         AS d30_value
FROM user_retention
WHERE d30_value IS NOT NULL
GROUP BY 1
ORDER BY users_d30_observed DESC;

-- Q: Channel view — overall vs within-intent (watch for mix effects)
WITH by_channel AS (
    SELECT acquisition_channel, COUNT(*) AS n, AVG(d30_value) AS d30_value_raw
    FROM user_retention WHERE d30_value IS NOT NULL GROUP BY 1
),
intent_rates AS (
    SELECT initial_intent, AVG(d30_value) AS intent_rate
    FROM user_retention WHERE d30_value IS NOT NULL GROUP BY 1
),
expected AS (
    -- what each channel would retain if its users behaved like the average user of their intent
    SELECT r.acquisition_channel, AVG(i.intent_rate) AS d30_value_expected_from_mix
    FROM user_retention r JOIN intent_rates i USING (initial_intent)
    WHERE r.d30_value IS NOT NULL
    GROUP BY 1
)
SELECT
    c.acquisition_channel,
    c.n                                            AS users_d30_observed,
    ROUND(c.d30_value_raw, 3)                      AS d30_value_raw,
    ROUND(e.d30_value_expected_from_mix, 3)        AS expected_from_intent_mix,
    ROUND(c.d30_value_raw - e.d30_value_expected_from_mix, 3) AS within_intent_gap
FROM by_channel c JOIN expected e USING (acquisition_channel)
ORDER BY d30_value_raw;
