-- =============================================================================
-- 04_feature_sequences.sql
-- Questions: what are the most common first three steps? How does the
-- Analyze → Cofounder journey relate to retention? (H4)
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

-- A "step" is a meaningful event collapsed to feature:stage, with consecutive
-- repeats removed so "create:output, create:output" counts once.
CREATE OR REPLACE VIEW user_steps AS
WITH typed AS (
    SELECT
        user_id, event_ts, initial_intent,
        feature || ':' || CASE
            WHEN is_value_event OR is_drawing_entry                      THEN 'value'
            WHEN event_name IN ('artifact_generated','artifact_regenerated','analysis_completed',
                                'cofounder_response_received','grant_application_started',
                                'website_created','business_plan_started') THEN 'output'
            ELSE 'start'
        END AS step
    FROM stg_events
    WHERE feature NOT IN ('account', 'payments')
      AND event_name NOT IN ('feature_opened', 'session_started', 'cofounder_response_rated')
),
dedup AS (
    SELECT *, LAG(step) OVER (PARTITION BY user_id ORDER BY event_ts) AS prev_step
    FROM typed
)
SELECT user_id, initial_intent, event_ts, step,
       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_ts) AS step_n
FROM dedup
WHERE prev_step IS NULL OR prev_step <> step;

-- Q: Top 15 first-three-step sequences, with D30 value retention
WITH seq AS (
    SELECT
        user_id,
        LISTAGG(step, ' → ') WITHIN GROUP (ORDER BY step_n) AS first_three
    FROM user_steps
    WHERE step_n <= 3
    GROUP BY 1
)
SELECT
    s.first_three,
    COUNT(*)                                   AS users,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 3) AS share_of_users,
    COUNT(r.d30_value)                         AS d30_observed,
    ROUND(AVG(r.d30_value), 3)                 AS d30_value
FROM seq s
JOIN user_retention r USING (user_id)
GROUP BY 1
ORDER BY users DESC
LIMIT 15;

-- Q: Analyze → Cofounder within 24h of the first analysis (H4), D30 value retention
WITH first_analysis AS (
    -- analysis_started is used as the anchor because analysis_completed has a known
    -- tracking gap on iOS (see 08_anomaly_detection.sql)
    SELECT user_id, MIN(event_ts) AS first_analysis_ts
    FROM stg_events
    WHERE event_name = 'analysis_started'
    GROUP BY 1
),
bridged AS (
    SELECT a.user_id,
           MAX(IFF(e.event_name = 'cofounder_message_sent'
                   AND e.event_ts BETWEEN a.first_analysis_ts
                                      AND DATEADD(hour, 24, a.first_analysis_ts), 1, 0)) AS to_cofounder_24h
    FROM first_analysis a
    LEFT JOIN stg_events e ON e.user_id = a.user_id
    GROUP BY 1
)
SELECT
    r.initial_intent = 'analyze'        AS analyze_was_initial_intent,
    b.to_cofounder_24h,
    COUNT(*)                            AS analyzed_users,
    COUNT(r.d30_value)                  AS d30_observed,
    ROUND(AVG(r.d30_value), 3)          AS d30_value,
    -- early-engagement proxy: was the user active on day 1? (confounder check)
    ROUND(AVG(r.d1_any), 3)             AS d1_activity
FROM bridged b
JOIN user_retention r USING (user_id)
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- Q: Canonical journeys — how many users complete each multi-step path
SELECT
    'Funding → Grant viewed → Application completed' AS journey,
    COUNT(DISTINCT IFF(event_name = 'grant_viewed', user_id, NULL))                AS step1,
    COUNT(DISTINCT IFF(event_name = 'grant_application_started', user_id, NULL))   AS step2,
    COUNT(DISTINCT IFF(event_name = 'grant_application_completed', user_id, NULL)) AS step3
FROM stg_events
UNION ALL
SELECT
    'Create → Artifact generated → Saved/Exported',
    COUNT(DISTINCT IFF(event_name = 'create_prompt_submitted', user_id, NULL)),
    COUNT(DISTINCT IFF(event_name = 'artifact_generated', user_id, NULL)),
    COUNT(DISTINCT IFF(event_name IN ('artifact_saved','artifact_exported'), user_id, NULL))
FROM stg_events
UNION ALL
SELECT
    'Analyze users → also used Cofounder (any order) → executed a Cofounder action',
    COUNT(DISTINCT IFF(event_name = 'analysis_started', user_id, NULL)),
    COUNT(DISTINCT IFF(event_name = 'cofounder_message_sent' AND feature = 'cofounder'
                       AND user_id IN (SELECT user_id FROM stg_events WHERE event_name = 'analysis_started'),
                       user_id, NULL)),
    COUNT(DISTINCT IFF(event_name = 'cofounder_action_executed'
                       AND user_id IN (SELECT user_id FROM stg_events WHERE event_name = 'analysis_started'),
                       user_id, NULL))
FROM stg_events;
