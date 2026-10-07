-- =============================================================================
-- 01_user_activation.sql
-- Question: what share of users reach a proposed activation event?
-- Builds `user_milestones`, the one-row-per-user table every later file uses.
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

CREATE OR REPLACE VIEW user_milestones AS
WITH first_action AS (
    -- First interaction with the feature that serves the user's initial intent.
    SELECT e.user_id, MIN(e.event_ts) AS first_action_ts
    FROM stg_events e
    WHERE e.event_name = 'feature_opened'
      AND e.feature = CASE e.initial_intent
                        WHEN 'funding'  THEN 'funding'
                        WHEN 'create'   THEN 'create'
                        WHEN 'analyze'  THEN 'analyze'
                        WHEN 'ask'      THEN 'cofounder'
                        WHEN 'presence' THEN 'website'
                        WHEN 'start'    THEN 'business_plan'
                      END
    GROUP BY 1
),
fmo AS (
    SELECT
        user_id,
        -- intent-specific: FMO in the feature that matches the initial intent
        MIN(IFF(fmo_intent = initial_intent, event_ts, NULL)) AS intent_fmo_ts,
        -- universal: the first FMO of any kind
        MIN(event_ts)                                        AS any_fmo_ts,
        MIN_BY(feature, event_ts)                            AS first_fmo_feature
    FROM fmo_events
    GROUP BY 1
)
SELECT
    u.user_id,
    u.signup_ts,
    u.signup_date,
    u.signup_week,
    u.initial_intent,
    u.acquisition_channel,
    u.platform,
    u.country,
    fa.first_action_ts,
    f.intent_fmo_ts,
    f.any_fmo_ts,
    f.first_fmo_feature,
    DATEDIFF(minute, u.signup_ts, f.intent_fmo_ts) / 60.0 AS ttfv_hours,
    DATEDIFF(day, u.signup_date, CAST(f.intent_fmo_ts AS DATE)) AS ttfv_days,
    COALESCE(DATEDIFF(day, u.signup_date, CAST(f.intent_fmo_ts AS DATE)) <= 6, FALSE) AS activated_intent_7d,
    COALESCE(DATEDIFF(day, u.signup_date, CAST(f.any_fmo_ts AS DATE)) <= 6, FALSE)    AS activated_any_7d
FROM stg_users u
LEFT JOIN first_action fa ON fa.user_id = u.user_id
LEFT JOIN fmo f           ON f.user_id  = u.user_id;

-- Q: Activation funnel, all users (denominator = every non-test signup)
SELECT
    COUNT(*)                                                     AS signed_up,
    COUNT(first_action_ts)                                       AS took_first_action,
    COUNT(intent_fmo_ts)                                         AS reached_intent_fmo_ever,
    COUNT_IF(activated_intent_7d)                                AS activated_intent_7d,
    COUNT_IF(activated_any_7d)                                   AS activated_any_7d,
    ROUND(COUNT(first_action_ts)  / COUNT(*), 3)                 AS pct_first_action,
    ROUND(COUNT_IF(activated_intent_7d) / COUNT(*), 3)           AS pct_activated_intent_7d,
    ROUND(COUNT_IF(activated_any_7d)    / COUNT(*), 3)           AS pct_activated_any_7d
FROM user_milestones;

-- Q: Where activation happens — first FMO feature vs. initial intent (activated users only)
SELECT
    initial_intent,
    first_fmo_feature,
    COUNT(*) AS users,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY initial_intent), 3) AS share_within_intent
FROM user_milestones
WHERE activated_any_7d
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
