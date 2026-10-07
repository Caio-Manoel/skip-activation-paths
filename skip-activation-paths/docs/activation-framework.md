# Activation Framework

*Phase 3 of "Finding Skip's Activation Paths".*

> **Proposed analytical taxonomy.** The intents, stages and event names below are my proposal for how to analyze Skip. They are not Skip's internal categories or tracking implementation, which I have not seen.

## 1. The lifecycle hierarchy

```
Acquisition ─▶ Intent ─▶ First Action ─▶ First Meaningful Outcome ─▶ Activation ─▶ Repeat Value ─▶ Retention ─▶ Monetization
 (how they      (what they   (they touched    (Skip produced something      (that outcome    (they got value    (they keep     (they pay)
  arrived)       came for)    the feature)     the user kept or acted on)    happened fast)   a second time)     coming back)
```

| Stage | Definition | Why it is separate |
|---|---|---|
| **Acquisition** | Channel + landing surface of the first session | Landing page is the earliest, cheapest intent signal |
| **Intent** | What the user came to do (declared, or inferred from landing surface + first action) | Every later stage is judged relative to intent |
| **First Action** | First interaction with the feature that serves the intent | Separates "never started" from "started but failed" |
| **First Meaningful Outcome (FMO)** | The first time Skip produced something the user **kept, used, or acted on** | Generation ≠ value for AI products; keeping/using is closer to value |
| **Activation** | FMO within **7 days** of signup | A time-boxed version makes it comparable across cohorts |
| **Repeat Value** | A second FMO on a different calendar day | Distinguishes a one-off task from an ongoing job |
| **Retention** | Activity in a fixed weekly window (see §4) | Must be defined per intent (see the funding caveat) |
| **Monetization** | Paid subscription or one-off purchase, net of refunds within the 14-day guarantee | Gross conversion overstates value if refunds are high |

## 2. Proposed intents

| Intent (proposed) | Inferred from | Typical first action |
|---|---|---|
| **Funding** | Landing on a funding page; "Grants" chosen; first action on a grant | View an opportunity |
| **Create content** | Landing via Create / "Create Similar"; first action in Imagine/Posts | Submit a create prompt |
| **Analyze** | Website Evaluator / Business Reports first | Submit a site/business to analyze |
| **Ask (Cofounder)** | First action is a Cofounder message | Send a message |
| **Build online presence** | Website builder / business page / Agent first | Start a website or business page |
| **Start a business** | Business plan first | Start the plan questionnaire |

*"Grow an existing business" is a stage (existing vs. new), not a job, so I treat it as a segment dimension (`business_stage`) rather than an intent.*

Users can hold several intents. The **initial intent** is used for activation; **secondary intents** are recorded to study cross-feature journeys.

**Intent quality caveat.** Declared intent (an onboarding question) and inferred intent (landing + first action) can disagree. Both should be stored; the gap between them is itself a useful signal about onboarding.

## 3. Candidate activation events per intent

Each ladder goes from weakest to strongest signal. The **bold** step is my proposed FMO; alternatives are listed so the data can choose between them (see §5).

### Funding
```
grant_viewed ─▶ grant_eligibility_checked ─▶ grant_application_started ─▶ **grant_application_completed** (or instant_grant_entered)
```
- FMO: a completed application or a drawing entry.
- Caveat: a win is the outcome the user cares about but is mostly outside the user's control and rare. It should be studied as an outcome, not used as the activation definition.

### Create content
```
feature_opened(create) ─▶ create_prompt_submitted ─▶ artifact_generated ─▶ **artifact_saved** ─▶ artifact_exported
```
- FMO: the user keeps an artifact (saved, downloaded, posted, scheduled).
- Generation alone is excluded because an AI tool can generate output the user rejects. The ratio *saved / generated* is a direct AI-quality signal.

### Analyze
```
analysis_started ─▶ analysis_completed ─▶ analysis_recommendation_clicked ─▶ **follow-up action** (fix, create, or ask Cofounder within the session)
```
- FMO: the user acts on the analysis — clicking a recommendation, or a follow-up in the same session.
- Receiving a report is a weaker alternative FMO, tested in §5.

### Ask (Cofounder)
```
cofounder_message_sent ─▶ cofounder_response_received ─▶ continued conversation (≥3 user turns) ─▶ **cofounder_action_executed**
```
- FMO: the user executes something Cofounder suggested (launches a tool, accepts a plan step), or continues for 3+ turns.
- Response quality signals: `cofounder_response_rated`, regenerate rate, abandonment right after a response.

### Build online presence
```
feature_opened(website|business_page|agent) ─▶ website_created ─▶ **website_published / business_page_published**
```
- Stronger downstream signal: first external view or lead (requires server-side events).

### Start a business
```
business_plan_started ─▶ **business_plan_created** ─▶ plan revised or exported
```
- One-off by nature: repeat value is expected to come from *other* features (funding, presence), so this intent is mainly evaluated on cross-feature continuation.

### A universal candidate, for comparison
- **"Any FMO within 7 days"** — the single metric a company would naturally reach for. Comparing it against the intent-specific definitions is the core test of H1.

## 4. Retention definitions

| Metric | Definition |
|---|---|
| **D1** | Any qualifying event on day 1 after signup (UTC day difference = 1) |
| **D7** | Any qualifying event in days **[7, 14)** — "week-2 retention" |
| **D30** | Any qualifying event in days **[28, 35)** — "week-5 retention" |

Weekly windows rather than single days are used because several Skip mechanics (e.g., scheduled live drawings, weekly content) are likely periodic; a single-day definition would mostly measure which weekday the user signed up on.

Two flavors of "qualifying event":

- **Activity retention** — any event.
- **Value retention** — an FMO-class event (keep/act/publish/apply). Drawing entries count as activity retention but are reported separately for funding users so that drawing returns are visible and not mistaken for tool engagement (product map §B3).

Cohorts whose window is not fully observed are excluded from that metric (right-censoring), and the denominator is always stated.

## 5. How the data chooses the activation event

For each intent, compare candidate events on:

1. **Reach** — % of the intent's users who hit it within 7 days (too rare = not useful for steering).
2. **Lift** — D30 value retention for users who hit it vs. did not, **with a confidence interval**.
3. **Robustness** — lift after adjusting for early engagement (sessions on day 0) and channel, since early engagement drives both.
4. **Actionability** — whether product can plausibly move it.

The preferred event is high on all four, not the one with the largest raw lift. Raw lift is the metric most inflated by selection (engaged users do more of everything). Final confirmation requires an experiment (docs/experiments.md).

## 6. What this framework outputs

A per-intent table the team can steer by:

| Intent | First action | FMO | Activation target window | Primary retention metric |
|---|---|---|---|---|
| Funding | grant_viewed | application completed / drawing entered | 7d | **Value** retention excluding drawing-only weeks |
| Create | prompt submitted | artifact saved | 1d | Value retention |
| Analyze | analysis started | recommendation acted on | same session | Value retention |
| Ask | message sent | action executed or ≥3 turns | 1d | Value retention |
| Presence | builder opened | published | 7d | Activity + first lead |
| Start | plan started | plan created | 1d | Cross-feature continuation |

The targets in this table are starting points to be replaced by what the real data shows.
