# Does Skip have one activation event?

**Caio Manoel Almeida Souza** · Product / Data / Analytics · October 2026

*Exploratory case study using synthetic data. Product observations are based on Skip's publicly available experience; no internal Skip data was used.*

## The question I noticed

Skip's homepage offers **Create, Analyze and Ask** next to a live grants carousel. In a few clicks I could make a video ad, evaluate a website, chat with Cofounder, build a site or enter a grant drawing. So: does Skip have one activation event, or does activation depend on why the entrepreneur came?

## Why it matters

A single activation metric averages these jobs together. Generating an AI output can count as success even when the user discards it. And two public details stood out: Instant Grant amounts depend on what the business has completed on Skip, and entries open shortly before each live drawing. That can create incentive-driven usage and event-driven returns, both of which look like engagement on a blended dashboard.

## What I tested

I wrote hypotheses with explicit evidence criteria, proposed an event schema, and wrote the SQL and Python I'd use. To pressure-test the reasoning, I built a synthetic dataset (17,630 simulated users, 90 days) where I control the true effects, so I could see which conclusions the analysis gets right and which it gets wrong.

## What surprised me

All numbers below come from the simulation.

- **Keeping or acting on an output is what matters.** Users who reached a meaningful outcome in week 1 were value-active in week 5 at 16.8%, vs 3.2% for users who only explored. Receiving an AI output was a weak signal on its own.
- **The most convincing correlation was mostly selection.** Users with value in 2+ features retained at 31.3% vs 9.7%. Standard controls didn't remove it, yet the true effect I'd built in was small.
- **Analyze → Cofounder: +33 pp observed, +3 pp when randomized.** Offering the bridge at random raised week-5 retention by +3.1 pp across everyone offered it (not statistically significant at ~1,070 users per arm), about +14 pp per user who took it.
- **A July "retention drop" was a mix shift.** Two July cohorts dipped from ~29% to ~26% week-2 retention; excluding a paid-social campaign, they were flat.
- **Funding behaves differently.** 82% of funding users' later active days fell on drawing days, and they converted to paid at about half the rate of other intents.

## What I would do at Skip

1. Define activation as a meaningful outcome (kept, used, published, applied) and report it by initial intent.
2. Instrument outcome completion and downstream action, with an ID on every AI output.
3. Test bridges like Analyze → Cofounder with randomized experiments sized for small effects.
4. Report grant-event returns separately from broader product retention.
5. Find out whether a successful first outcome leads naturally to a second valuable job.

Full case: [CASE_STUDY.md](CASE_STUDY.md) · Interactive version: [dashboard](dashboard/index.html)
