-- =============================================================================
-- 07_conversion.sql
-- Question: how does paid conversion vary by activation path? Net of refunds
-- inside the 14-day guarantee, since gross conversion overstates value.
-- Window: subscription started within 30 days of signup; only users with the
-- full 30 days observed.
-- SYNTHETIC DATA — demonstrates methodology, not Skip performance.
-- =============================================================================

CREATE OR REPLACE VIEW user_conversion AS
SELECT
    r.user_id,
    r.initial_intent,
    r.acquisition_channel,
    r.activated_intent_7d,
    r.d30_value,
    DATEADD(day, 30, r.signup_date) <= r.obs_end                                     AS conv_observed,
    MAX(IFF(DATEDIFF(day, r.signup_date, CAST(s.started_at AS DATE)) <= 29, 1, 0))  AS paid_30d_gross,
    MAX(IFF(DATEDIFF(day, r.signup_date, CAST(s.started_at AS DATE)) <= 29
            AND NOT s.refunded, 1, 0))                                              AS paid_30d_net,
    MIN(DATEDIFF(day, r.signup_date, CAST(s.started_at AS DATE)))                   AS days_to_paid,
    MAX(s.tier)                                                                     AS tier
FROM user_retention r
LEFT JOIN subscriptions s ON s.user_id = r.user_id
GROUP BY 1, 2, 3, 4, 5, 6;

-- Q: Paid conversion (30d) by intent × activation, gross and net of refunds
SELECT
    initial_intent,
    activated_intent_7d,
    COUNT(*)                                  AS users,
    SUM(paid_30d_gross)                       AS paid_gross,
    SUM(paid_30d_net)                         AS paid_net,
    ROUND(AVG(paid_30d_gross), 4)             AS conv_gross,
    ROUND(AVG(paid_30d_net), 4)               AS conv_net,
    ROUND(1 - SUM(paid_30d_net) / NULLIF(SUM(paid_30d_gross), 0), 3) AS refund_share
FROM user_conversion
WHERE conv_observed
GROUP BY 1, 2
ORDER BY 1, 2;

-- Q: Conversion by intent overall — with tier mix
SELECT
    initial_intent,
    COUNT(*)                                       AS users,
    ROUND(AVG(paid_30d_net), 4)                    AS conv_net_30d,
    COUNT_IF(paid_30d_net = 1 AND tier = 'pro')    AS pro_subs,
    COUNT_IF(paid_30d_net = 1 AND tier = 'plus')   AS plus_subs
FROM user_conversion
WHERE conv_observed
GROUP BY 1
ORDER BY conv_net_30d DESC;

-- Q: Days from signup to first paid subscription — distribution, not average
SELECT
    CASE
        WHEN days_to_paid = 0             THEN '0. signup day'
        WHEN days_to_paid BETWEEN 1 AND 6 THEN '1. days 1-6'
        WHEN days_to_paid BETWEEN 7 AND 13 THEN '2. days 7-13'
        WHEN days_to_paid BETWEEN 14 AND 29 THEN '3. days 14-29'
        ELSE '4. day 30+'
    END                  AS time_to_paid,
    COUNT(*)             AS subscribers,
    ROUND(COUNT(*) / SUM(COUNT(*)) OVER (), 3) AS share
FROM user_conversion
WHERE days_to_paid IS NOT NULL
GROUP BY 1
ORDER BY 1;
