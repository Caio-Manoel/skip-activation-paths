# Problem Framing

*Phase 2 of "Finding Skip's Activation Paths".*

## Observation

Skip serves several different entrepreneur needs from one product: getting funding, creating marketing assets, analyzing a website or business, getting advice from an AI Cofounder, building an online presence, and writing a business plan. The homepage itself offers three different verbs — **Create, Analyze, Ask** — next to a live grants carousel. (Sources in [product-map.md](product-map.md).)

## Question

**Does Skip actually have a single activation event?**

Most products pick one "aha moment" and optimize onboarding toward it. If Skip's users come for different jobs, one universal activation metric would:

- **average away the signal** — a change that helps funding users and hurts content users can show up as "flat";
- **reward the wrong behavior** — e.g., counting a generated image as activation even when the user discarded it;
- **misread the funding segment** — scheduled drawings may produce returns that look like retention but are not engagement with the AI tools.

The broader question:

> **For each major intent, what is the shortest path from "I came to Skip for something" to "Skip delivered enough value that I want to come back"?**

## How to read the hypotheses

Every hypothesis below is a statement to test, not a finding. For each I list what would support and what would reject it, so the outcome is decided by the data rather than by how the story reads. Terms (FMO, activation, D7/D30 windows, value retention) are defined in [activation-framework.md](activation-framework.md); event names are from [event-tracking-plan.md](event-tracking-plan.md).

---

## H1 — Activation is intent-dependent rather than universal

| | |
|---|---|
| **Why it matters** | Determines whether Skip should run one onboarding and one north-star activation metric, or several. |
| **Metric** | For each intent, D30 value retention of users who reached each candidate FMO vs. those who did not; and the rank of the best candidate within each intent. |
| **Denominator** | Users who signed up in the cohort window, grouped by initial intent, with D30 fully observed. |
| **Required events** | `signup_completed`, `intent_selected`/landing, all FMO-class events, any events for retention. |
| **Segments** | Initial intent × platform × channel. |
| **Confounders** | Intent inference errors; early engagement (engaged users hit every milestone); channel mix differing by intent. |
| **Supports** | The best-predicting FMO differs across intents, **and** an intent-specific definition predicts D30 better than "any FMO within 7 days" (e.g., higher AUC or a larger adjusted lift) in most intents. |
| **Rejects** | The same event is best for every intent, or the universal definition predicts as well as the intent-specific ones. |
| **Product action** | Per-intent activation metrics in the weekly review; intent-aware onboarding (Experiment A). |

## H2 — Completing a meaningful output beats exploring

*Users who complete a meaningful output (keep/act/publish/apply) have higher retention than users who only open features.*

| | |
|---|---|
| **Why it matters** | Separates "make it easy to try many things" from "make sure one thing finishes". |
| **Metric** | D7 and D30 value retention, FMO-reached vs. explored-only (opened ≥1 feature, no FMO). |
| **Denominator** | Users with ≥1 `feature_opened` in their first 7 days. |
| **Required events** | `feature_opened`, FMO-class events. |
| **Segments** | Intent; number of features opened in week 1; day-0 sessions. |
| **Confounders** | Engagement propensity; users who fail due to bugs/latency (an AI-quality problem, not a motivation one). |
| **Supports** | A gap that persists within intent and after adjusting for day-0 engagement. |
| **Rejects** | The gap disappears once early engagement is controlled for. |
| **Product action** | Prioritize completion (defaults, templates, fewer steps) over feature discovery in the first session; Experiment C. |

## H3 — Cross-feature journeys predict stronger retention than single-feature use

| | |
|---|---|
| **Why it matters** | A "platform" thesis needs evidence that breadth itself creates value. |
| **Metric** | D30 value retention by number of distinct features with an FMO in days 0–6 (1 vs. 2+). |
| **Denominator** | Activated users (≥1 FMO in days 0–6). |
| **Required events** | FMO-class events with `feature`. |
| **Segments** | Intent; day-0 engagement; funding vs. non-funding. |
| **Confounders** | **Reverse causality / selection:** engaged users naturally use more features. **Incentives:** funding users may complete extra items because grant amounts depend on it (product map §B3). |
| **Supports** | Lift survives adjustment for engagement and intent, and is present outside the funding segment. |
| **Rejects** | Lift shrinks to near zero after adjustment, or exists only where breadth is incentive-driven. |
| **Product action** | Only if supported: cross-sell prompts after a first FMO. If rejected: invest in depth of the first job instead. |

## H4 — Analyze → Cofounder is an especially valuable loop

*Moving from insight (an analysis) to recommended action (Cofounder) could convert a one-off report into an ongoing relationship.*

| | |
|---|---|
| **Why it matters** | This is the clearest AI-native loop in the product: Skip both diagnoses and helps fix. |
| **Metric** | D30 value retention of Analyze users who reach Cofounder within 24h of `analysis_completed` vs. Analyze users who do not. |
| **Denominator** | Users with ≥1 `analysis_completed`. |
| **Required events** | `analysis_completed`, `cofounder_message_sent` with `context_source = from_analysis`, `cofounder_action_executed`. |
| **Segments** | Analysis type; quality of analysis (n recommendations, latency); platform. |
| **Confounders** | Users who choose to continue into Cofounder are already more motivated (self-selection); small sample. |
| **Supports** | Positive adjusted lift whose confidence interval excludes zero; or, better, a positive result in Experiment B. |
| **Rejects** | No lift after adjustment, or a CI tightly around zero with adequate sample. |
| **Product action** | Analyze → Cofounder bridge (Experiment B). |

## H5 — Funding acquires well but retains differently

*Funding may be a powerful acquisition mechanism with a retention pattern unlike users who enter through AI tools.*

| | |
|---|---|
| **Why it matters** | If funding users' returns are driven by drawings rather than tools, activity retention overstates engagement, and monetization models built on blended retention will be wrong. |
| **Metric** | (a) Activity vs. value retention by intent; (b) share of funding users' active days that coincide with a drawing; (c) paid conversion by intent; (d) % of funding users who reach an FMO in a non-funding feature. |
| **Denominator** | All users with the window observed, by initial intent. |
| **Required events** | `instant_grant_entered`, `grant_*`, all FMO-class events, subscriptions; a drawing calendar. |
| **Segments** | Intent; drawing-day vs. non-drawing-day activity. |
| **Confounders** | Seasonality of grant calendars; channel (funding listings vs. paid social). |
| **Supports** | Large activity-vs-value retention gap specific to funding, with returns clustered on drawing days. |
| **Rejects** | Funding users' value retention is similar to other intents. |
| **Product action** | Report funding retention as value retention; design a deliberate funding → tools bridge (e.g., Cofounder-assisted applications that produce reusable assets). |

## H6 — Time-to-first-value matters more than number of features used

| | |
|---|---|
| **Why it matters** | Determines whether onboarding should optimize speed to one outcome or exposure to many features. |
| **Metric** | D30 value retention by TTFV bucket (same session, same day, 1–3d, 4–7d, never) and by week-1 feature count; both in one regression. |
| **Denominator** | All users (TTFV "never" is a real bucket, not missing data). |
| **Required events** | `signup_completed`, first FMO-class event, `feature_opened`. |
| **Segments** | Intent. |
| **Confounders** | The "never" bucket mechanically has low retention, which can make TTFV look predictive overall; engagement drives both speed and breadth. |
| **Supports** | Among users who **did** reach value, faster TTFV still predicts retention after controlling for feature count. |
| **Rejects** | Once "never reached value" is separated out, TTFV adds little — reach matters, speed does not. |
| **Product action** | If supported: aggressively shorten the first path. If rejected: focus on getting more users to value at all, even if slower. |

## H7 — Output acceptance is a leading indicator for AI features (AI quality)

*For Create and Cofounder, the share of AI outputs a user keeps or acts on in the first session predicts whether they return.*

| | |
|---|---|
| **Why it matters** | Connects model/prompt quality to business outcomes; gives the AI team a metric to move. |
| **Metric** | First-session acceptance rate = saved / generated (Create); action-executed or thumbs-up / responses (Cofounder). D30 retention by acceptance bucket. |
| **Denominator** | Users with ≥1 `artifact_generated` or `cofounder_response_received` on day 0. |
| **Required events** | `artifact_generated`, `artifact_regenerated`, `artifact_saved`, `cofounder_response_rated`, `cofounder_action_executed`, with `output_id` and `model_version`. |
| **Segments** | Artifact type, `model_version`, latency bucket. |
| **Confounders** | Users with clearer needs both accept more and retain more; regenerate behavior differs by artifact type. |
| **Supports** | Acceptance predicts retention within artifact type, and drops in acceptance after a `model_version` change precede retention drops. |
| **Rejects** | No relationship within type. |
| **Product action** | Track acceptance by model version as a release gate; route low-acceptance prompts to qualitative review (session replays, thumbs-down reasons). |

*H7 is framed but not simulated in the synthetic dataset; it is included because it is the hypothesis I would most want to test with real AI-output logs.*

---

## What a "good answer" looks like

Not a single number. A short table, per intent, of: the activation event to steer by, its current reach, its adjusted relationship with D30, and the experiment that would confirm it — plus a clear statement of which hypotheses the data rejected.
