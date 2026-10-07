-- =============================================================================
-- 06_cross_feature_adoption.sql
-- Questions: single-feature vs cross-feature behavior (H3), and funding-only vs
-- funding → broader product adoption (H5).
-- Breadth is measured in week 1 (days 0-6); retention in week 5 — so the
-- "cause" is measured before the "effect".
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

CREATE OR REPLACE VIEW user_breadth AS
SELECT
    user_id,
    COUNT(DISTINCT IFF(day_n <= 6 AND event_name = 'feature_opened', feature, NULL))            AS features_opened_w1,
    COUNT(DISTINCT IFF(day_n <= 6 AND (is_value_event OR is_drawing_entry), feature, NULL))      AS features_with_value_w1,
    COUNT(DISTINCT IFF(day_n = 0 AND event_name = 'session_started', session_id, NULL))          AS day0_sessions,
    MAX(IFF(day_n <= 6 AND feature IN ('create','analyze','cofounder')
            AND (is_value_event), 1, 0))                                                         AS w1_value_in_ai_tools,
    MAX(IFF(day_n <= 6 AND feature IN ('website','business_plan')
            AND (is_value_event), 1, 0))                                                         AS w1_value_in_profile_items
FROM stg_events
GROUP BY 1;

-- Q: Single- vs cross-feature (value in 1 vs 2+ features in week 1), activated users only
SELECT
    IFF(b.features_with_value_w1 >= 2, '2+ features', '1 feature') AS breadth,
    COUNT(r.d30_value)               AS d30_observed,
    ROUND(AVG(r.d30_value), 3)       AS d30_value,
    ROUND(AVG(b.day0_sessions), 2)   AS avg_day0_sessions   -- engagement differs before breadth does
FROM user_breadth b
JOIN user_retention r USING (user_id)
WHERE b.features_with_value_w1 >= 1 AND r.d30_value IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Q: Same comparison stratified by day-0 engagement — does the gap survive?
SELECT
    IFF(b.day0_sessions >= 2, 'day0: 2+ sessions', 'day0: 1 session') AS day0_engagement,
    IFF(b.features_with_value_w1 >= 2, '2+ features', '1 feature')    AS breadth,
    COUNT(r.d30_value)               AS d30_observed,
    ROUND(AVG(r.d30_value), 3)       AS d30_value
FROM user_breadth b
JOIN user_retention r USING (user_id)
WHERE b.features_with_value_w1 >= 1 AND r.d30_value IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;

-- Q: Funding users — funding-only vs funding + profile items vs funding + AI tools
SELECT
    CASE
        WHEN b.w1_value_in_ai_tools = 1      THEN 'c. funding + AI tools (create/analyze/cofounder)'
        WHEN b.w1_value_in_profile_items = 1 THEN 'b. funding + profile items (website/plan)'
        ELSE                                      'a. funding only'
    END                               AS funding_path,
    COUNT(*)                          AS users,
    COUNT(r.d30_value)                AS d30_observed,
    ROUND(AVG(r.d30_any), 3)          AS d30_activity,
    ROUND(AVG(r.d30_value), 3)        AS d30_value,
    ROUND(SUM(r.non_drawing_days_w2_w5) / NULLIF(SUM(r.active_days_w2_w5), 0), 3) AS share_of_active_days_not_drawing_only
FROM user_breadth b
JOIN user_retention r USING (user_id)
WHERE r.initial_intent = 'funding' AND r.activated_intent_7d
GROUP BY 1
ORDER BY 1;

-- Q: Drawing-day concentration of activity, by intent (H5) — share of week 2-5 active days that fall on drawing days
WITH active_days AS (
    SELECT DISTINCT e.user_id, e.initial_intent, CAST(e.event_ts AS DATE) AS d, e.day_n
    FROM stg_events e
    WHERE e.day_n BETWEEN 7 AND 34
)
SELECT
    a.initial_intent,
    COUNT(*)                                                         AS user_active_days,
    ROUND(COUNT_IF(c.drawing_date IS NOT NULL) / COUNT(*), 3)        AS share_on_drawing_days,
    2 / 7                                                            AS share_expected_if_uniform
FROM active_days a
LEFT JOIN drawing_calendar c ON c.drawing_date = a.d
GROUP BY 1
ORDER BY share_on_drawing_days DESC;
