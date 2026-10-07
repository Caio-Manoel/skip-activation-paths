-- =============================================================================
-- 02_activation_by_intent.sql
-- Question: does activation look different by initial intent, and does the
-- choice of definition (intent-specific vs. universal) change the picture? (H1)
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

-- Q: Activation funnel by initial intent (denominator = signups in that intent)
SELECT
    initial_intent,
    COUNT(*)                                                    AS signups,
    ROUND(COUNT(first_action_ts) / COUNT(*), 3)                 AS pct_first_action,
    ROUND(COUNT_IF(activated_intent_7d) / COUNT(*), 3)          AS pct_activated_intent_7d,
    ROUND(COUNT_IF(activated_any_7d) / COUNT(*), 3)             AS pct_activated_any_7d,
    -- users counted as "activated" by the universal metric but who never got
    -- value from the job they came for
    COUNT_IF(activated_any_7d AND NOT activated_intent_7d)      AS universal_only_activated,
    ROUND(COUNT_IF(activated_any_7d AND NOT activated_intent_7d)
          / NULLIF(COUNT_IF(activated_any_7d), 0), 3)           AS share_of_universal_not_intent
FROM user_milestones
GROUP BY 1
ORDER BY signups DESC;

-- Q: Step-level funnel per intent — where each intent loses users in week 1
WITH steps AS (
    SELECT
        e.initial_intent,
        e.user_id,
        MAX(IFF(e.event_name IN ('grant_viewed','create_prompt_submitted','analysis_started',
                                 'cofounder_message_sent','website_created','business_plan_started')
                AND e.day_n <= 6, 1, 0)) AS started,
        MAX(IFF(e.event_name IN ('grant_application_started','artifact_generated','analysis_completed',
                                 'cofounder_response_received','website_created','business_plan_started')
                AND e.day_n <= 6, 1, 0)) AS got_output,
        MAX(IFF(e.event_name IN ('grant_application_completed','instant_grant_entered','artifact_saved',
                                 'analysis_recommendation_clicked','cofounder_action_executed',
                                 'website_published','business_page_published','business_plan_created')
                AND e.day_n <= 6, 1, 0)) AS got_value
    FROM stg_events e
    GROUP BY 1, 2
)
SELECT
    initial_intent,
    COUNT(*)                         AS users_with_events,
    SUM(started)                     AS started,
    SUM(got_output)                  AS got_output,
    SUM(got_value)                   AS got_value,
    ROUND(SUM(got_output) / NULLIF(SUM(started), 0), 3)   AS output_given_start,
    ROUND(SUM(got_value)  / NULLIF(SUM(got_output), 0), 3) AS value_given_output
FROM steps
GROUP BY 1
ORDER BY 1;

-- Q: Declared vs inferred intent — agreement of the onboarding answer with the landing intent
WITH declared AS (
    SELECT e.user_id, e.initial_intent AS inferred_intent,
           JSON_EXTRACT_PATH_TEXT(ev.properties, 'intent') AS declared_intent
    FROM stg_events e
    JOIN events ev ON ev.event_id = e.event_id
    WHERE e.event_name = 'intent_selected'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY e.user_id ORDER BY e.event_ts) = 1
)
SELECT
    inferred_intent,
    COUNT(*)                                             AS users_who_declared,
    ROUND(COUNT_IF(declared_intent = inferred_intent) / COUNT(*), 3) AS agreement_rate
FROM declared
GROUP BY 1
ORDER BY 1;
