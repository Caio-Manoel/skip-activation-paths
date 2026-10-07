# Event Tracking Plan

*Phase 4 of "Finding Skip's Activation Paths".*

> **Proposed instrumentation only.** I do not know what Skip tracks today. This is the schema I would want in order to answer the activation questions, written so Engineering can compare it with what already exists and fill gaps rather than start over.

## 1. Design principles

1. **One event = one user-meaningful state change**, named `object_action` in past tense (`artifact_saved`, not `click_save_button`).
2. **Outcome events are emitted server-side** when the outcome is a backend fact (analysis finished, plan generated, payment succeeded). Client events can be lost to ad blockers, closed tabs and app crashes; server events cannot.
3. **Intent travels with the user**, not only with the event: stored once on the user/profile, and stamped on events as `intent_context` for convenience.
4. **AI outputs get an ID.** Every generated artifact, analysis or Cofounder response gets an `output_id` so that "generated → kept → used" can be joined. This is what makes AI quality measurable.
5. **Schema is versioned** (`schema_version`) and validated at ingestion.

## 2. Common envelope (every event)

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | UUID | ✅ | Generated client-side; dedup key |
| `event_name` | string | ✅ | From the registry below |
| `event_timestamp` | timestamp (UTC) | ✅ | When it happened (device or server clock) |
| `received_at` | timestamp (UTC) | ✅ | Set by the collector; used to detect clock skew and late arrival |
| `user_id` | string | after auth | Null before signup |
| `anonymous_id` | string | ✅ | Device/browser ID; stitched to `user_id` at signup/login |
| `session_id` | string | ✅ | 30-minute inactivity rule, defined in one place |
| `business_id` | string | if exists | A user can own more than one business |
| `platform` | enum | ✅ | `web`, `ios`, `android`, `server` |
| `app_version` | string | client | Key for diagnosing tracking breaks |
| `feature` | enum | ✅ | `funding`, `create`, `analyze`, `cofounder`, `website`, `business_page`, `business_plan`, `agent`, `payments`, `discovery`, `account` |
| `intent_context` | enum | optional | Current intent if known |
| `source` | string | first event of session | e.g., the `source=` URL parameter |
| `acquisition_channel` | enum | user-level | Derived at signup, copied for convenience |
| `subscription_tier` | enum | ✅ | `starter`, `plus`, `pro` at event time |
| `country` | string | ✅ | ISO-3166 alpha-2 |
| `experiment_assignments` | array<struct{experiment_id, variant}> | ✅ (may be empty) | Exposure logged separately, see §4 |
| `schema_version` | int | ✅ | |
| `properties` | JSON | — | Event-specific fields |

## 3. Event registry

### Lifecycle
| Event | Emitted | Key properties |
|---|---|---|
| `signup_completed` | server | `signup_method`, `landing_path`, `source`, `utm_*` |
| `session_started` | client | `landing_path`, `referrer` |
| `intent_selected` | client | `intent`, `selection_surface` (onboarding, prompt bar, …), `is_declared` |
| `feature_opened` | client | `feature`, `entry_point` |

### Funding
| Event | Emitted | Key properties |
|---|---|---|
| `grant_viewed` | client | `opportunity_id`, `opportunity_type` (grant, loan, card, instant) |
| `grant_eligibility_checked` | server | `opportunity_id`, `is_eligible` |
| `grant_application_started` | server | `opportunity_id`, `assisted_by_cofounder` |
| `grant_application_completed` | server | `opportunity_id`, `assisted_by_cofounder`, `duration_sec` |
| `instant_grant_entered` | server | `drawing_id` |
| `instant_grant_won` / `instant_grant_claimed` | server | `drawing_id`, `amount_usd`, `claim_latency_sec` |

### Create
| Event | Emitted | Key properties |
|---|---|---|
| `create_prompt_submitted` | client | `artifact_type` (image, video, blog, social, product), `prompt_source` (typed, create_similar, cofounder) |
| `artifact_generated` | server | `output_id`, `artifact_type`, `latency_ms`, `model_version`, `generation_status` (success, failed, filtered) |
| `artifact_regenerated` | server | `output_id`, `parent_output_id` |
| `artifact_saved` | server | `output_id` |
| `artifact_exported` | server | `output_id`, `destination` (download, post, schedule, website) |

### Analyze
| Event | Emitted | Key properties |
|---|---|---|
| `analysis_started` | server | `analysis_type` (website, product, business), `target_hash` |
| `analysis_completed` | server | `output_id`, `latency_ms`, `n_recommendations`, `status` |
| `analysis_recommendation_clicked` | client | `output_id`, `recommendation_id`, `action_type` |

### Cofounder
| Event | Emitted | Key properties |
|---|---|---|
| `cofounder_message_sent` | client | `conversation_id`, `turn_index`, `context_source` (blank, from_analysis, from_grant, …) |
| `cofounder_response_received` | server | `conversation_id`, `output_id`, `latency_ms`, `model_version`, `suggested_actions` |
| `cofounder_response_rated` | client | `output_id`, `rating` (up/down), `reason` |
| `cofounder_action_executed` | client | `output_id`, `action_type`, `target_feature` |

### Online presence & start
| Event | Emitted | Key properties |
|---|---|---|
| `website_created` | server | `template` |
| `website_published` | server | `has_custom_domain` |
| `business_page_published` | server | `category` |
| `agent_created` | server | |
| `business_plan_started` / `business_plan_created` | server | `plan_tier` |
| `lead_received` | server | `channel` (page, agent, website) |

### Monetization
| Event | Emitted | Key properties |
|---|---|---|
| `paywall_viewed` | client | `trigger_feature`, `trigger_reason` (limit, upsell, pricing_page) |
| `subscription_started` | server (billing) | `tier`, `billing_period`, `price_usd`, `trigger_feature` |
| `subscription_cancelled` / `subscription_refunded` | server (billing) | `reason`, `days_since_start` |
| `purchase_completed` | server (billing) | `product` (boost, plan, website, agent) |

## 4. Experiment exposure

- `experiment_exposed` (server or client) is emitted **the first time the user actually sees the treatment surface**, not at assignment. Analysis is intent-to-treat on assignment, with exposure used to check dilution.
- Assignment is deterministic on `user_id` (hash + salt per experiment) so it survives devices.

## 5. Event quality validation

These run as automated tests in the transformation layer (e.g., dbt tests) with an alert channel, plus a daily anomaly monitor (sql/08_anomaly_detection.sql).

| Problem | Detection | Handling |
|---|---|---|
| **Duplicates** | Count of `event_id` > 1; plus near-duplicates: same user + event_name + output_id within 2s | Dedup on `event_id` with `QUALIFY ROW_NUMBER() = 1`; monitor the dup rate per `app_version` |
| **Missing IDs** | `user_id` null after `signup_completed` for the same `anonymous_id`; null `session_id`; outcome events missing `output_id` | Not-null tests by event class; null rate by `platform × app_version` |
| **Event ordering** | Child before parent: `artifact_saved` without a prior `artifact_generated` for the same `output_id`; `analysis_completed` without `analysis_started` | Orphan-rate test; compare on `received_at` as well as `event_timestamp` |
| **Timestamp problems** | `event_timestamp` before `signup_completed` or in the future; `received_at − event_timestamp` > 24h | Clamp to `received_at` for client events beyond a tolerance; flag device clocks |
| **Identity stitching** | One `anonymous_id` → several `user_id`s; several devices → one user | Identity graph table (`anonymous_id`, `user_id`, `first_seen`, `last_seen`); pre-signup events attributed to the stitched user so acquisition/landing are correct |
| **Bot / internal traffic** | Internal email domains, staff `business_id`s, QA accounts, implausible rates (e.g., >200 events/hour), headless user agents | `is_internal` / `is_test` flags on the user dimension; excluded by default in all models |
| **Schema changes** | New/renamed properties, type changes, enum drift | Schema registry with `schema_version`; contract tests in CI for client SDKs; breaking changes need a migration note |
| **Late-arriving events** | Distribution of `received_at − event_timestamp` (mobile offline queues) | Incremental models reprocess a trailing 3-day window; daily metrics marked provisional for 72h |
| **Silent tracking breaks** | Ratio monitors that are stable when the product is healthy: `analysis_completed / analysis_started`, `artifact_saved / artifact_generated`, events per active user by platform | z-score vs. trailing 28 days by `platform × app_version` (sql/08) |

The last row matters most for activation work: a release that drops one outcome event on one platform looks exactly like an activation drop. The synthetic dataset includes such a break so the monitor can be demonstrated.

## 6. Modelled tables (analytics layer)

| Model | Grain | Purpose |
|---|---|---|
| `fct_events` | event | Deduplicated, stitched, internal traffic removed |
| `dim_users` | user | Signup, channel, landing, initial intent, flags |
| `fct_user_day` | user × day | Active flag, value-active flag, features used |
| `fct_user_milestones` | user | First action / FMO / activation timestamps per intent |
| `fct_subscriptions` | subscription | Start, tier, cancel, refund |

The SQL in `sql/` is written against a simplified version of these tables (`users`, `events`, `subscriptions`).
