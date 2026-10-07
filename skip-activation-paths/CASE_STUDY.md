# Finding Skip's Activation Paths

**Caio Manoel Almeida Souza** · Product / Data / Analytics · October 2026

> **Exploratory case study using synthetic data. Product observations are based on Skip's publicly available experience; no internal Skip data was used.** Every number below comes from a simulated dataset I built to pressure-test the hypotheses. The numbers describe that simulation, not Skip.

---

### The question

**Does Skip have one activation event, or does activation depend on why an entrepreneur came to Skip?**

### Why I asked

*Public observation.* Skip supports very different jobs from one prompt bar: getting funding, creating content, analyzing a website or business, asking the AI Cofounder, and setting up a business (website, business page, plan). Someone who arrives for a grant and someone who arrives to make a product video probably succeed at different moments. A single activation metric could average those differences away.

### What I found in the simulation

*Synthetic results. Observational findings and simulated-experiment findings are labelled separately.*

1. **Reaching a meaningful outcome mattered much more than exploring features.** Users who kept or acted on an output in week 1 were value-active in week 5 at 16.8%, vs 3.2% for users who only opened features. *(Observational; the gap held in all six intents.)*
2. **Cross-feature behavior looked strongly predictive, but much of it was selection.** Users with value in 2+ features retained at 31.3% vs 9.7% (odds ratio 4.3). Controls only brought it down to 2.8. The simulation's built-in true effect of breadth is small: engaged users simply do more of everything. *(Observational, checked against the simulation's ground truth.)*
3. **Analyze → Cofounder: +33 pp observed, about +3 pp when randomized.** Analyzers who went on to Cofounder retained 33 pp better than those who didn't. When the bridge was offered at random, the population-level effect was +3.1 pp (95% CI −0.9 to +7.0), about +14 pp per user who actually took it. *(Observational vs simulated randomized experiment.)*
4. **An apparent July retention decline disappeared after segmenting acquisition mix.** Week-2 retention dipped from ~29% to ~26% for two July cohorts. Excluding a paid-social campaign, those cohorts were flat at ~28%. *(Observational.)*
5. **Funding needs special treatment.** Grants can create incentive-driven usage and event-driven returns. 82% of funding users' later active days fell on live-drawing days, and funding users converted to paid at about half the rate of other intents (3.6% vs 7.4%). *(Observational; the drawing calendar is my assumption.)*

### So what should Skip do?

1. **Define activation as a meaningful outcome, reported by initial intent.** One shared definition (the user kept, used, published or submitted something Skip produced), measured separately for funding, create, analyze, ask and setup.
2. **Instrument outcome completion and downstream action, beyond clicks and feature visits.** Server-side outcome events and an ID on every AI output, so "generated → kept → used" can be followed.
3. **Test contextual bridges such as Analyze → Cofounder with randomized experiments**, sized for small effects. The observational gap is the hypothesis; the experiment is the answer.
4. **Separate grant-event retention from broader product retention.** Report drawing returns as their own metric, and judge funding by how many users go on to get value from the rest of Skip.
5. **Investigate whether a successful first outcome leads naturally to a second valuable job.** That is the real version of the cross-feature question, and the one worth building for.

---

## Contents

1. [What I observed in Skip's public product](#1-what-i-observed-in-skips-public-product)
2. [Hypotheses](#2-hypotheses)
3. [What the simulation showed, in more detail](#3-what-the-simulation-showed-in-more-detail)
4. [What I would test with real Skip data](#4-what-i-would-test-with-real-skip-data)
5. [Experiments](#5-experiments)
6. [How I would instrument the product](#6-how-i-would-instrument-the-product)
7. [Method](#7-method)
8. [Limitations](#8-limitations)
9. [First 30 days](#9-first-30-days)

**Each section below is labelled by evidence type:** Public observation · Hypothesis · Synthetic result · Real-data test

---

## 1. What I observed in Skip's public product

*Public observation.* All from logged-out pages on helloskip.com; sources in [docs/product-map.md](docs/product-map.md).

- **One entry point, many jobs.** The homepage leads with **Create / Analyze / Ask** next to a live grants carousel. The dashboard groups the product into My Business, Discover, Live Grants & Funding, Website & Plans, and an AI Cofounder with an "Activate" state.
- **Cofounder sits between the jobs.** It is presented as an advisor, a launcher for Create actions, and an agent that monitors and grows the business.
- **Funding mechanics shape behavior.** Instant Grant terms say entries open 30 minutes before a live drawing, winners have 60 seconds to claim, and the grant amount depends on *what you've completed for your business*.

The last point shaped the investigation: an incentive that pushes users to complete other parts of the product, and a recurring event that pulls them back. Both can make an activation or retention metric look healthier than the underlying product engagement.

## 2. Hypotheses

*Hypotheses.* Full specification (metric, denominator, events, confounders, support/reject criteria, product action) in [docs/problem-framing.md](docs/problem-framing.md).

| | Hypothesis | Verdict in the simulation (synthetic) |
|---|---|---|
| H1 | Activation is intent-dependent | Mixed: one definition shape works; report it per intent |
| H2 | Completing an output beats exploring | Supported |
| H3 | Cross-feature journeys predict retention | Looks supported; mostly selection |
| H4 | Analyze → Cofounder is especially valuable | Real, much smaller than it looks |
| H5 | Funding acquires well but retains differently | Supported |
| H6 | Time-to-first-value beats feature count | Not supported: reaching value matters, speed doesn't |
| H7 | Output acceptance predicts retention (AI quality) | Framed for real data; not simulated |

I built the simulation so these would come out in different ways: some hold, some fail, some only look true. The point is that the method can tell them apart.

## 3. What the simulation showed, in more detail

*Synthetic results.* All numbers are reproducible from `analysis/results/` (see [docs/number-audit.md](docs/number-audit.md)). Full write-up in [analysis/FINDINGS.md](analysis/FINDINGS.md).

**Activation by intent (observational).** With activation defined as an intent-specific meaningful outcome within 7 days, rates ranged from 39% (online presence) to 61% (funding). "Received an AI output" separated retained from non-retained users poorly (AUC 0.56–0.61); "kept or acted on it" did better in every intent (0.66–0.73).

**Outcome vs exploration (observational).** 16.8% vs 3.2% week-5 value retention (+13.6 pp, 95% CI 12.7–14.6, n = 9,123 vs 5,068). The gap appears in all six intents.

**Cross-feature retention (observational, then checked).** 31.3% vs 9.7%. The odds ratio moved from 4.26 (raw) to 4.12 (intent, channel, platform) to 2.81 (plus day-0 engagement). Multi-feature users were already more active before breadth could matter (median 12 vs 9 day-0 events). Among funding users, breadth was partly incentive-driven: funding users who also completed a website or plan retained at 19.2% vs 8.9% for funding-only, while the simulation gives those completions no true effect.

**Analyze → Cofounder.**

| Estimate | Week-5 value retention difference | Type |
|---|---|---|
| Bridged vs not bridged | **+33.1 pp** (CI 27.3–38.9) | Observational (control arm) |
| Per user who actually bridged | **+14.2 pp** | Simulated experiment (ITT ÷ uptake gap) |
| Everyone offered the bridge | **+3.1 pp** (CI −0.9 to +7.0, p = 0.14) | Simulated experiment (intent-to-treat) |

The test had ~1,070 users per arm; detecting +3 pp from that baseline needs ~4,000 per arm. The lesson is to size experiments for small effects from the start.

**Acquisition mix (observational).** Week-2 activity retention for the 6 and 13 July cohorts was 26.3% and 26.4%, vs 27.9–29.3% for June cohorts. Excluding paid social: 28.3% and 28.5%. Paid social made up ~42% of those two cohorts vs ~19% of June cohorts.

**Funding (observational).** Funding users' week-5 activity retention (20.2%) looked normal, but 81.5% of their active days in weeks 2–5 fell on drawing days (other intents 45–56%; 29% if spread evenly). Paid conversion within 30 days: 3.6% vs 7.4% for all other intents.

**Speed vs reach (observational).** Users who never reached value were 0.4% value-active in week 5. Among those who did, reaching it the same day vs later made no positive difference (odds ratio 0.87).

## 4. What I would test with real Skip data

*Real-data tests.* These are the questions the simulation can't answer.

1. **Can intent be inferred?** Share of users assignable to an intent from landing page, `source` parameter and first action, and how often that agrees with what they say they want.
2. **Per-intent activation baseline.** How many users in each intent keep or act on an output, and where each intent drops off.
3. **The funding pattern.** Share of funding users' active days on drawing days; activity vs value retention; how many funding users ever get value from an AI tool; whether completions made for grant eligibility lead to continued use.
4. **First outcome → second job.** After a first meaningful outcome, which second job follows most often, how soon, and whether those users retain and convert differently.
5. **AI output quality.** Save/export rates by output type and model version; Cofounder ratings and action rates; whether changes follow model releases. Paired with thumbs-down reasons, support tickets and reviews to learn *why* outputs are rejected.
6. **Monetization path.** Which first outcome precedes Plus vs Pro, and refund rates within the 14-day guarantee by intent.

## 5. Experiments

Full designs in [docs/experiments.md](docs/experiments.md). Each targets a result that observational data can't settle.

| | Experiment | Tests | Primary metric |
|---|---|---|---|
| A | Intent-aware onboarding: ask what they want to get done, route to the shortest path | H1 | Intent-specific activation ≤ 7 days |
| B | Analyze → Cofounder bridge: "Want Cofounder to turn this into an action plan?" | H4 | Follow-up action ≤ 7 days after analysis |
| C | First-value recovery: one contextual nudge to users who started but didn't finish | H2 | Meaningful outcome ≤ 7 days after eligibility |

All randomize per user, analyze intent-to-treat with a pre-registered minimum detectable effect, and share guardrails on refunds, support load and AI error rates.

## 6. How I would instrument the product

Proposed in [docs/event-tracking-plan.md](docs/event-tracking-plan.md). The parts that matter most here:

- **Outcome events emitted server-side** (`artifact_saved`, `analysis_completed`, `grant_application_completed`, `website_published`).
- **An `output_id` on every AI output**, so "generated → kept → used" can be joined. This one field is what makes AI quality measurable.
- **Intent captured twice**: declared (an onboarding answer) and inferred (landing page + first action).
- **Validation as code**: dedup, orphan-event checks, identity stitching, internal-traffic flags, late-arrival windows, and ratio monitors (completed ÷ started, by platform and app version). In the simulation, a ratio monitor caught an injected iOS tracking break on its first day (z = −31.8).

## 7. Method

1. **Define before measuring.** A proposed lifecycle (Acquisition → Intent → First Action → First Meaningful Outcome → Activation → Repeat Value → Retention → Monetization) with candidate events per intent: [docs/activation-framework.md](docs/activation-framework.md).
2. **Synthetic data with a known ground truth**: 17,630 users over 90 days, with latent engagement, bouncers, power users, a paid campaign, a tracking outage, duplicates and late events. True effects are stored outside the analysis: [data/README.md](data/README.md).
3. **SQL for definitions** ([sql/](sql/)): Snowflake dialect, transpiled and validated against the data in DuckDB.
4. **Python for inference** ([analysis/](analysis/)): bootstrap confidence intervals, significance tests, effect sizes, logistic regression with stated controls, and selection checks.
5. **Distributions over averages.** Median time-to-value was 6 minutes among users who got there, but 39% never did.

## 8. Limitations

- **No Skip data.** Product observations come from logged-out public pages. Every number is synthetic.
- **The simulation reflects my assumptions,** including which effects are real. It shows that the method separates real effects from selection; it estimates nothing about Skip.
- **Intent is assumed inferable.** If it isn't, building that signal is step one.
- **The drawing calendar is invented.** Skip's real schedule, eligibility rules and their interaction with plans and Boost need checking.
- **Observational adjustment is limited.** The engagement controls I used are partly post-treatment, which is why causal questions end in experiments.

## 9. First 30 days

| Week | Focus | Output |
|---|---|---|
| 1 | Learn the product and the data; map existing events to the proposed schema | Gap list: which outcome events exist, which are client-only, where an output ID is missing |
| 2 | Data trust: dedup, test-account flags, identity stitching, ratio monitors | A short data-quality report and the first automated monitors |
| 3 | First answer: per-intent activation and value retention; check the funding pattern; first read of output acceptance | A one-page memo: the activation picture by intent and the three biggest open questions |
| 4 | First decision: design one experiment with Product (likely B), sized from real baselines | Pre-registered experiment brief and a weekly per-intent activation view |

---

*Executive summary: [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) · Interactive case: [dashboard/index.html](dashboard/index.html) · Repository guide: [README.md](README.md)*
