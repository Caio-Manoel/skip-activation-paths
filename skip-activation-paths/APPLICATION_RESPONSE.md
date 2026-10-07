# Application response

**Caio Manoel Almeida Souza** · Product / Data / Analytics

---

**1. [Paste the job post's first question here]**

At RateHawk/ETG I worked on API and product analytics across the hotel booking funnel: search results, hotel page, prebook and booking. Using SQL and BI reporting, I tracked conversion metrics between those stages (L2Q, Q2B, L2B). When numbers looked inconsistent, or performance differed between segments, I worked backwards before trusting the metric: validated trusted IDs and source data, checked how each funnel stage was defined, compared supplier and API behavior, looked at latency and error rates, and checked the aggregation logic. That made the analysis more reliable and helped separate real funnel and API bottlenecks from reporting artifacts. It's the habit I'd bring to Skip: define the metric carefully, and check what produced a number before acting on it.

**2. Spend time using Skip before applying. Tell us something you noticed that you would want to investigate further. What questions would you ask, what data would you look at, and why?**

Skip's homepage offers Create, Analyze and Ask next to a live grants carousel, so people arrive for very different jobs. My question: does Skip have one activation event, or does activation depend on why someone came?

I'd ask, per initial intent: what is the first outcome users keep or act on, and how many reach it? Does a first success lead to a second valuable job? And for funding, since grant amounts depend on what the business has completed and entries open before live drawings, how much usage and return activity is driven by the grant itself?

I'd look at landing source, first-session events, outcome events (generated vs kept), drawing entries and subscriptions.

I went beyond the initial observation and built a small exploratory case with synthetic data to pressure-test these hypotheses. The clearest lesson: "users who do X retain better" can be mostly selection, so I'd confirm bridges like Analyze → Cofounder with randomized experiments.

- Interactive case: [link]
- Repository: [GitHub link]
- LinkedIn / resume: [link]
