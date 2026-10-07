# Skip Product Map

*Phase 1 of "Finding Skip's Activation Paths". Public pages accessed on **2026-10-07**. Everything here comes from logged-out, publicly reachable pages; I have no access to Skip's internal data, tracking, or roadmap.*

This document has two parts that are deliberately kept apart:

- **Part A — Observations.** What a logged-out visitor can see on helloskip.com, with the URL for each claim. Numbers quoted here are Skip's own public marketing figures as displayed on the date accessed; I have not verified them.
- **Part B — Interpretation.** My reading of what those observations imply for intents, first-value moments, and journeys. Every item in Part B is a hypothesis.

> **Source hygiene.** Several unrelated companies share the name "Skip" (an association-analytics product, a podcast, scooters). I used only helloskip.com and third-party pages that explicitly describe helloskip.com / YoGovernment, Inc.

---

## Part A — Observations

### A1. How Skip describes itself

| Observation | Source |
|---|---|
| Page title: "Skip — AI Tools to Fund, Grow, and Run Your Business". Meta description lists grants, funding, business pages, payments, and a Cofounder. | https://helloskip.com/ |
| Hero headline "Build, Fund & Grow Your Business With AI" with three tabs — **Create**, **Analyze**, **Ask** — and chips for Image, Video, Blog, Social, Product, Business Plan. | https://helloskip.com/ |
| Footer tagline: "Your AI partner to start, grow, & fund your business". Copyright © 2026, YoGovernment, Inc. | https://helloskip.com/ |
| iOS and Android apps are linked from every page. | https://helloskip.com/ |
| Third-party profile: formerly YoGov, rebranded to Skip in April 2020; described as freemium with tiered monthly subscriptions. | https://app.dealroom.co/companies/yogov |

### A2. Product surfaces

| Surface | What is visible publicly | Source |
|---|---|---|
| **AI Cofounder** | Homepage section "Have your AI Cofounder work for you" lists: find funding opportunities, create content, monitor your business, grow your business. CTA "Try AI Cofounder for Free". | https://helloskip.com/ |
| | The Cofounder landing page shows action chips: Create Blog Post, Create Social Post, Improve Products, Create Website, Create Image, Create Business Plan. | https://helloskip.com/cofounder |
| | In the logged-out dashboard shell, Cofounder appears as a persistent panel labelled "Your AI Cofounder — Not Active — Activate", under the prompt "What should we work on next?" with Create / Analyze / Ask. | https://helloskip.com/dashboard |
| **Create (Imagine)** | Homepage "Get Inspired. Create Your Own." gallery of example videos; each has a "Create Similar" link that deep-links into `/dashboard/imagine` with a pre-filled prompt and `create=video`. | https://helloskip.com/ |
| **Analyze** | "Website Evaluator — Analyze Any Website: get AI feedback on any website and track improvements over time." A "Business Reports" link sits next to it. | https://helloskip.com/dashboard/website-evaluator |
| | The website-builder page offers "Or Evaluate Your Existing Website" as an alternative path. | https://helloskip.com/website |
| **Grants & Funding** | "Funding Happening Now" carousel of live opportunities (e.g., $1k Instant Grants #251, Verizon $10k Grants, SBA 7(a) Loan), each with "Start Applying". Links carry `?source=homepage`. | https://helloskip.com/ |
| | Footer: Apply to Grants with Cofounder, Search & Apply To Grants, Skip Instant Grants, Search for Financing, Search for Credit Cards, Set Up Payouts. | https://helloskip.com/ |
| **Skip Instant Grants** | Live drawings. Terms on the #251 page: no purchase necessary; U.S.-based, 18+; entries open 30 minutes before the live drawing; a selected winner has 60 seconds to tap "Claim Now" while logged in; users may win once every 4 months; **"Your potential grant amount is based on what you've completed for your business — ranging from $200 to $1,000."** Typically 5–10 winners per ~30-minute session. | https://helloskip.com/funding-details/1k-instant-251 |
| | Winners page displayed "$42,900 awarded in last 30 days" and "48 winners in last 30 days" on the date accessed; lists winners with business category and city. | https://helloskip.com/skip-grants |
| **Website builder** | "Instantly Generate Your Website For Free & Start Selling on Skip". Inputs: business name, description, template (Showcase / Modern / Essentials). | https://helloskip.com/website |
| **Business plan** | "Your Business Plan, Delivered Instantly!" Questionnaire → instant plan, unlimited revisions. Standard and Premium tiers shown (Premium adds "Expert Cofounder business plan feedback"). Claims "50,000+ plans". | https://helloskip.com/ai-business-plan |
| **AI Business Agent** | Customer-facing AI agent "trained on your business" that answers leads 24/7 and turns conversations into bookings and payments. "Get Started For Free". | https://helloskip.com/agent |
| **Business pages, listings & discovery** | "Put Your Business in Front of More Customers" — create a business page, showcase products. Public leaderboards: Top Businesses (new followers, 30d), Top Blog Posts (impressions), Top Products (views, 30d). A network map. | https://helloskip.com/ |
| **Boost** | Paid visibility: top of listings, spotlight during live grant drawings, top placement on the Instant Grants page. Its benefit list also includes "Be eligible for Skip's $1,000 Instant Grants". | https://helloskip.com/boost |
| **Dashboard IA** | Navigation groups: *My Business* (Imagine, Products, Posts, Performance); *Discover, Search, Map*; *Live Grants, Funding, Wallet*; *Website, Business Plans, Workspace*; *AI Cofounder*. | https://helloskip.com/dashboard |

### A3. Pricing (public)

| Tier | Price shown | Selected inclusions | Source |
|---|---|---|---|
| Starter | Free | Public grants & funding, up to $1,000 Instant Grants, some $10k Skip Grants, Workspace + Grants Vault, public business page | https://helloskip.com/pricing |
| Plus | $29/month (monthly) | AI image/video/writing tools, grants & funding assistance, products & payment links, website, AI business assistant, content scheduling, basic analytics | https://helloskip.com/pricing |
| Pro | $99/month (monthly) | Everything in Plus; weekly AI content, automatic scheduling, near-unlimited generation, AI teammates & agents, Business Plan Builder, Website Builder with custom domain, lower payment fees, advanced analytics | https://helloskip.com/pricing |
| — | Yearly billing "Save 40%"; "14-Days. Full Access. Zero Risk." refund guarantee | | https://helloskip.com/pricing |
| — | Individual options also sold separately: Boost, Instant Business Plan, Instant Website, 24/7 AI Agent | | https://helloskip.com/pricing |

Pricing page headline figures (Skip's own claim): "1,000+ grant winners • 100,000+ business listings • 1M+ entrepreneurs". Source: https://helloskip.com/pricing

### A4. Entry points visible from the outside

| Entry point | Evidence | Source |
|---|---|---|
| Homepage Create/Analyze/Ask prompt | Hero tabs | https://helloskip.com/ |
| Funding detail pages (one URL per opportunity, indexable) | `/funding-details/<slug>` with `robots: index,follow` | https://helloskip.com/funding-details/1k-instant-251 |
| Feature landing pages (website, business plan, agent, boost, cofounder) | Each has its own page and CTA | URLs above |
| "Create Similar" deep links | Pre-filled prompts into `/dashboard/imagine` | https://helloskip.com/ |
| Business listings, products, blog posts by users | Public leaderboards and pages | https://helloskip.com/ |
| Mobile apps | App Store / Google Play links | https://helloskip.com/ |
| Affiliate program | Footer "Earn as Skip Affiliate" | https://helloskip.com/ |

Many internal links carry a `source=` query parameter (e.g., `source=homepage`, `source=Websitefooter`, `source=1kfooter`). Source: https://helloskip.com/

---

## Part B — Interpretation (all hypotheses)

### B1. Jobs-to-be-done

Reading the surfaces together, I see at least six distinct jobs an entrepreneur could hire Skip for:

| Proposed JTBD | Surfaces that serve it |
|---|---|
| **Get money** for my business | Grants, Instant Grants, financing, credit cards |
| **Make marketing assets** | Imagine (image/video), blog, social, posts |
| **Understand how I'm doing** | Website Evaluator, Business Reports, Performance |
| **Get advice / a thinking partner** | AI Cofounder (Ask) |
| **Exist online and get found** | Website builder, business page, listings, Boost, AI Agent |
| **Get started / get organized** | Business plan, incorporation link |

These are my analytical categories, not Skip's.

### B2. Candidate first-value moments

| JTBD | What "I got something" might look like |
|---|---|
| Get money | Found an opportunity I qualify for; submitted an application; entered a drawing; won |
| Make assets | Generated an asset I kept (saved, downloaded, posted, scheduled) |
| Understand | Received an evaluation and acted on at least one recommendation |
| Advice | Got an answer specific enough to act on; continued the conversation |
| Exist online | Published a website or business page; received a first view or lead |
| Get started | Generated a business plan I kept |

Generation alone may be a weak signal for AI products — users can generate something they never use. Keeping, using or acting on an output is a stronger candidate.

### B3. The observation that shaped this case study

The Instant Grant terms say the potential grant amount depends on **"what you've completed for your business"** (https://helloskip.com/funding-details/1k-instant-251). Combined with recurring live drawings, this suggests two measurement traps for anyone defining activation and retention at Skip:

1. **Incentive-driven breadth.** Funding-intent users may complete a business page, website or plan *because it raises their potential grant*, and the event stream would record them as "cross-feature" users. Breadth driven by an incentive may not mean the same thing as breadth driven by value.
2. **Event-driven returns.** If entries open shortly before scheduled live drawings, a funding user's "D7 return" may be a return *to the drawing*. Plain "any activity" retention could look healthy for this segment even if the user never re-engages with the AI tools.

Neither is a claim about real Skip data — they are reasons to define retention per intent and to segment before trusting any "users who do X retain better" comparison.

### B4. Where Cofounder seems to fit

Publicly, Cofounder is positioned in three ways at once: a chat partner ("Ask"), an orchestrator that launches other tools (its landing page is a set of Create actions), and an always-on agent that monitors and grows the business (homepage copy). The dashboard shell shows an explicit "Not Active / Activate" state for it.

My interpretation: Cofounder is a candidate **connective layer** between jobs — the place where an insight (Analyze) or an opportunity (Funding) could be turned into a next action. Whether it plays that role for real users is exactly what H4 tests.

### B5. Possible monetization points

- Subscription upgrade from Starter to Plus/Pro (https://helloskip.com/pricing)
- Individual purchases: Boost, plan, website, agent (https://helloskip.com/pricing)
- Payment fees (Pro advertises "lower payment fees", implying a fee on payments) (https://helloskip.com/pricing)
- Premium add-ons such as expert plan feedback (https://helloskip.com/ai-business-plan)

Hypothesis: willingness to pay is concentrated in jobs with ongoing, repeatable value (assets, online presence, agent) more than in one-off jobs (a single plan, a single grant application).

### B6. Plausible cross-feature journeys

| Journey | Why it might exist |
|---|---|
| Funding → Business page / website / plan → Funding | Grant amount tied to completed items (B3) |
| Analyze → Cofounder → Create | Turn a website evaluation into fixes and new content |
| Create → Posts / scheduling | Asset becomes recurring workflow (Pro tier) |
| Website → AI Agent → Payments | Presence becomes a sales channel |
| Business plan → Funding | Plans are often a grant/loan prerequisite |
| Discovery (listings) → Signup → Business page | Other businesses' pages as acquisition |

### B7. Open questions I can't answer from outside

- Which events Skip tracks today and how intent is captured, if at all.
- How the `source=` parameter is used downstream.
- How Instant Grant eligibility interacts with plan tier and with Boost (both the pricing and Boost pages mention it).
- What share of signups come from funding pages versus AI-tool pages.
- What "Activate" means for Cofounder and what it unlocks.
