-- =============================================================================
-- 00_staging.sql — cleaned, analysis-ready views
-- Dialect: Snowflake. scripts/run_sql.py transpiles to DuckDB (via sqlglot) to
-- validate every query against the synthetic dataset.
--
-- SYNTHETIC DATA: All behavioral data in this analysis is synthetic and is used
-- solely to demonstrate the analytical methodology. It does not represent actual
-- Skip users or performance.
-- =============================================================================

-- Analysis parameters in one place (observation window end is exclusive).
CREATE OR REPLACE VIEW analysis_params AS
SELECT CAST('2026-08-30' AS DATE) AS obs_end;

-- Users: exclude internal / QA accounts by default.
CREATE OR REPLACE VIEW stg_users AS
SELECT
    user_id,
    CAST(signup_ts AS TIMESTAMP)   AS signup_ts,
    CAST(signup_date AS DATE)      AS signup_date,
    DATE_TRUNC('week', CAST(signup_date AS DATE)) AS signup_week,
    country,
    acquisition_channel,
    platform,
    initial_intent,
    business_stage
FROM users
WHERE NOT is_test_account;

-- Events: deduplicated, test traffic removed, clock-skew repaired, classified.
CREATE OR REPLACE VIEW stg_events AS
WITH dedup AS (
    SELECT *
    FROM events
    QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY received_at) = 1
)
SELECT
    e.event_id,
    e.user_id,
    e.session_id,
    -- Device clocks occasionally report times before the user existed; fall back
    -- to collector time for those rows.
    IFF(CAST(e.event_timestamp AS TIMESTAMP) < u.signup_ts - INTERVAL '5 minutes',
        CAST(e.received_at AS TIMESTAMP), CAST(e.event_timestamp AS TIMESTAMP)) AS event_ts,
    CAST(e.received_at AS TIMESTAMP) AS received_at,
    e.event_name,
    e.feature,
    e.platform,
    e.output_id,
    u.initial_intent,
    u.signup_date,
    DATEDIFF(day, u.signup_date,
        CAST(IFF(CAST(e.event_timestamp AS TIMESTAMP) < u.signup_ts - INTERVAL '5 minutes',
                 CAST(e.received_at AS TIMESTAMP), CAST(e.event_timestamp AS TIMESTAMP)) AS DATE)) AS day_n,
    -- "Value" = an outcome the user kept, acted on, published or submitted (FMO class).
    e.event_name IN ('grant_application_completed', 'artifact_saved', 'artifact_exported',
                     'analysis_recommendation_clicked', 'cofounder_action_executed',
                     'website_published', 'business_page_published', 'business_plan_created')
        AS is_value_event,
    e.event_name = 'instant_grant_entered' AS is_drawing_entry
FROM dedup e
JOIN stg_users u ON u.user_id = e.user_id;

-- Proposed intent-specific First Meaningful Outcome (FMO) events.
-- Cofounder also counts a 3rd user message in one session ("sustained conversation").
CREATE OR REPLACE VIEW fmo_events AS
WITH cofounder_turns AS (
    SELECT
        user_id, event_ts, day_n, initial_intent,
        ROW_NUMBER() OVER (PARTITION BY user_id, session_id ORDER BY event_ts) AS turn_n
    FROM stg_events
    WHERE event_name = 'cofounder_message_sent' AND session_id IS NOT NULL
)
SELECT user_id, event_ts, day_n, initial_intent, feature,
       CASE
         WHEN feature = 'funding'       THEN 'funding'
         WHEN feature = 'create'        THEN 'create'
         WHEN feature = 'analyze'       THEN 'analyze'
         WHEN feature = 'cofounder'     THEN 'ask'
         WHEN feature = 'website'       THEN 'presence'
         WHEN feature = 'business_plan' THEN 'start'
       END AS fmo_intent,
       event_name
FROM stg_events
WHERE event_name IN ('grant_application_completed', 'instant_grant_entered', 'artifact_saved',
                     'analysis_recommendation_clicked', 'cofounder_action_executed',
                     'website_published', 'business_page_published', 'business_plan_created')
UNION ALL
SELECT user_id, event_ts, day_n, initial_intent, 'cofounder', 'ask', 'cofounder_third_turn'
FROM cofounder_turns
WHERE turn_n = 3;
