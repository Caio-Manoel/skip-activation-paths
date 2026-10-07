# Experiments

*Phase 8 of "Finding Skip's Activation Paths".*

Observational analysis can rank hypotheses; it cannot establish that changing a journey changes retention. Each experiment below is designed to answer one causal question that the synthetic analysis shows is **confounded** when measured observationally.

> **Baselines are illustrative.** Sample sizes use placeholder baseline rates (stated in each section) because I do not have Skip's real numbers. The method — not the numbers — is the point. Recompute with `python analysis/sample_size.py` once real baselines are known.

**Shared conventions**

- Randomize at the **user** level with a deterministic hash on `user_id` (survives devices; avoids one person seeing both variants).
- Analyze **intent-to-treat** on assignment; use `experiment_exposed` only to check dilution.
- Pre-register the primary metric, the minimum detectable effect (MDE) and the stopping rule. No peeking-based stopping; fixed horizon.
- α = 0.05 two-sided, power = 0.80.
- Every experiment carries the same **guardrails**: refund rate within the 14-day guarantee, support contacts per user, unsubscribe/notification opt-out rate, and AI error/latency rate.

---

## Experiment A — Intent-aware onboarding

**Question it answers:** H1 — does routing users to an intent-specific shortest path increase activation, or is a single path good enough?

| | |
|---|---|
| **Hypothesis** | Asking "What do you want to get done first?" after signup and routing to the shortest path for that intent (e.g., Funding → matched opportunity + "apply with Cofounder"; Create → a template that ends in *save*; Analyze → evaluator pre-filled with the user's site) increases 7-day activation versus the current generic dashboard. |
| **Variants** | Control: current post-signup experience. Treatment: one-question intent picker (skippable) + routed first screen. |
| **Primary metric** | **Activation** = intent-specific FMO within 7 days. For skipped/unknown intent, the universal definition (any FMO within 7 days). |
| **Secondary** | TTFV (median and P75); D7 and D30 value retention; % of users declaring intent; agreement between declared and inferred intent. |
| **Guardrails** | Signup → first action drop-off (the extra question must not cost users); shared guardrails above. |
| **Unit** | User, assigned at `signup_completed`. |
| **Sample size** | Illustrative baseline activation 30%, MDE +2 pp absolute → ≈ **8,400 users per arm**. Per-intent reads need more; treat them as pre-registered secondary analyses with wider CIs. |
| **Duration** | Until sample reached and at least **2 full weeks** of signups (weekday + drawing cycles), then wait for D30 on the secondary metric. |
| **Success** | Primary lift with CI > 0, no guardrail regression. Ship per intent only where that intent's lift is non-negative. |
| **Risks** | The question itself changes behavior (priming); routing can over-commit users who wanted to browse; intent labels from the picker become a *new* data source, so mapping needs to be versioned. |

---

## Experiment B — Analyze → Cofounder bridge

**Question it answers:** H4 — is the Analyze → Cofounder association causal, or do motivated users just do both?

| | |
|---|---|
| **Hypothesis** | Offering *"Want Cofounder to turn this into an action plan?"* immediately after `analysis_completed`, with the analysis passed as context, increases the share of Analyze users who act on the analysis and increases D30 value retention. |
| **Variants** | Control: current analysis results page. Treatment: inline bridge card that opens Cofounder pre-loaded with the analysis and proposes 3 concrete next steps that launch tools. |
| **Primary metric** | **% of analyzed users with a follow-up action within 7 days** (recommendation clicked, Cofounder action executed, or a create/website event referencing the analysis). |
| **Secondary** | D30 value retention; Cofounder conversation depth; `cofounder_response_rated` up-rate; paid conversion within 30 days. |
| **Guardrails** | Cofounder latency P95; thumbs-down rate; LLM cost per analyzed user; shared guardrails. |
| **Unit** | User, assigned at first `analysis_completed` (only users who complete an analysis enter the experiment). |
| **Sample size** | Illustrative baseline 20% follow-up, MDE +3 pp → ≈ **2,900 analyzed users per arm**. |
| **Duration** | Driven by Analyze volume; at least 2 weeks. |
| **Success** | Primary lift with CI > 0 **and** no increase in thumbs-down rate. A primary win without a D30 effect is still informative: it means the bridge creates action but not lasting value. |
| **Risks** | If Cofounder's plan is generic, the bridge can *reduce* trust in both features. Mitigation: monitor response ratings in the first 48h with a pre-agreed kill switch. |

**Why an experiment and not more analysis:** in the synthetic data, bridged users were already more engaged before their first analysis, and the gap survived every observational control. A simulated randomized version of this experiment (`analysis/simulated_experiment_b.py`) showed the observational gap (+33 pp) was more than twice the causal effect per bridged user (+14 pp), and the intent-to-treat effect (+3 pp, CI −0.9 to +7.0) was too small to detect with ~1,070 users per arm. More observational slicing would not have revealed that; randomization did. It is also why the MDE above is set at +3 pp rather than something more optimistic.

---

## Experiment C — First-value recovery

**Question it answers:** H2 — does completing an outcome cause retention, or do users who complete just differ?

| | |
|---|---|
| **Hypothesis** | Detecting users who **started but did not complete** an outcome (e.g., generated but did not save; started an application but did not finish; opened the website builder but did not publish) and sending one contextual nudge within 24h — a return link to exactly where they stopped, plus the most common blocker for that step — increases FMO completion and D30 value retention. |
| **Eligibility** | Signed up ≤ 7 days ago; ≥1 "started" event; no FMO; not already nudged. |
| **Variants** | Control: no nudge. Treatment: one in-app + email nudge, content specific to the stalled step. |
| **Primary metric** | **FMO within 7 days of eligibility.** |
| **Secondary** | D30 value retention; time from nudge to FMO; which stalled step recovers best. |
| **Guardrails** | Email unsubscribe rate; complaint rate; shared guardrails. |
| **Unit** | User, at first moment of eligibility. |
| **Sample size** | Illustrative baseline 15% recovery, MDE +3 pp → ≈ **2,400 eligible users per arm**. |
| **Duration** | 2–3 weeks of eligibility, then D30. |
| **Success** | Primary lift with CI > 0 and no unsubscribe regression. |
| **Risks** | Recovery may "pull forward" completions that would have happened anyway (check D30, not just D7); generic nudges train users to ignore messages. |

**Why this design is useful beyond the nudge:** because only the nudge is randomized, the treatment-vs-control difference in D30 among *recovered* users is the closest thing to a causal estimate of "completing a first outcome → retention" that the product can produce.

---

## Decision framework

| Result | A: Intent onboarding | B: Analyze → Cofounder | C: First-value recovery |
|---|---|---|---|
| Primary ↑, D30 ↑ | Ship; adopt per-intent activation as the north-star family | Ship; make "insight → action" a pattern for other features (funding, performance) | Ship; build a general "stalled outcome" system |
| Primary ↑, D30 flat | Ship for activation, but question the FMO definition — it may not be a value moment | Bridge creates action but not habit; improve plan quality before scaling | Nudges move timing, not value; keep only where cheap |
| Primary flat | Keep single onboarding; H1 may be true but routing isn't the lever | Drop the bridge; revisit H4 | Completion isn't the bottleneck — look at quality of outputs (H7) |
| Guardrail ↓ | Do not ship regardless of primary | Do not ship; investigate response quality | Do not ship; reduce frequency |
