"""
Product analysis for "Finding Skip's Activation Paths".

SYNTHETIC DATA: All behavioral data in this analysis is synthetic and is used solely
to demonstrate the analytical methodology. It does not represent actual Skip users
or performance.

Builds on the views defined in sql/ (single source of truth for metric definitions),
then does what SQL is bad at: bootstrap CIs, regression adjustment, effect sizes,
and figures. Writes:
  analysis/results/results.json   — every number quoted in FINDINGS.md / CASE_STUDY.md
  assets/figures/*.png            — static figures for the docs
  dashboard/data.js               — data for the dashboard

Run:  python analysis/product_analysis.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_sql  # noqa: E402

RES = ROOT / "analysis" / "results"
FIG = ROOT / "assets" / "figures"
RES.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(7)
N_BOOT = 2000
INTENTS = ["funding", "create", "analyze", "ask", "presence", "start"]
INTENT_LABEL = {"funding": "Funding", "create": "Create content", "analyze": "Analyze",
                "ask": "Ask Cofounder", "presence": "Online presence", "start": "Start a business"}
DISCLAIMER = "Synthetic data — methodology demo, not Skip performance"

# ------------------------------------------------------------------ styling
INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
C1, C2, C3, C4 = "#2563eb", "#f59e0b", "#10b981", "#ef4444"
INTENT_COLORS = {"funding": "#2563eb", "create": "#f59e0b", "analyze": "#10b981",
                 "ask": "#8b5cf6", "presence": "#ef4444", "start": "#64748b"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "figure.dpi": 130})


def stamp(fig):
    fig.text(0.99, 0.01, DISCLAIMER, ha="right", va="bottom", fontsize=7.5, color=C4)


# ------------------------------------------------------------------ stats helpers
def boot_diff(a: np.ndarray, b: np.ndarray, n=N_BOOT):
    """Bootstrap 95% CI for mean(a) - mean(b) (binary outcomes)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ia = RNG.integers(0, len(a), (n, len(a)))
    ib = RNG.integers(0, len(b), (n, len(b)))
    d = a[ia].mean(1) - b[ib].mean(1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def boot_mean(a, n=N_BOOT):
    a = np.asarray(a, float)
    m = a[RNG.integers(0, len(a), (n, len(a)))].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def two_prop(a, b):
    """Two-proportion z-test p-value and Cohen's h."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    p1, p2, n1, n2 = a.mean(), b.mean(), len(a), len(b)
    p = (a.sum() + b.sum()) / (n1 + n2)
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se if se > 0 else 0.0
    h = 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))
    return float(2 * (1 - stats.norm.cdf(abs(z)))), float(h)


def compare(df, flag, outcome="d30_value"):
    d = df[df[outcome].notna()]
    a, b = d.loc[d[flag] == 1, outcome].values, d.loc[d[flag] == 0, outcome].values
    lo, hi = boot_diff(a, b)
    p, h = two_prop(a, b)
    return dict(n_with=int(len(a)), n_without=int(len(b)), rate_with=round(float(a.mean()), 4),
                rate_without=round(float(b.mean()), 4), diff=round(float(a.mean() - b.mean()), 4),
                ci95=[round(lo, 4), round(hi, 4)], p_value=p, cohens_h=round(h, 3))


def logit_or(df, formula, term):
    """Odds ratio + 95% CI for `term` from a logistic regression."""
    m = smf.logit(formula, data=df).fit(disp=0)
    b, (lo, hi) = m.params[term], m.conf_int().loc[term]
    return dict(odds_ratio=round(float(np.exp(b)), 3), ci95=[round(float(np.exp(lo)), 3),
                round(float(np.exp(hi)), 3)], p_value=float(m.pvalues[term]), n=int(m.nobs))


# ------------------------------------------------------------------ data
def load():
    con = run_sql.get_connection()
    users = con.sql("""
        SELECT r.*, b.features_opened_w1, b.features_with_value_w1, b.day0_sessions,
               b.w1_value_in_ai_tools, b.w1_value_in_profile_items,
               c.paid_30d_net, c.paid_30d_gross, c.conv_observed,
               DAYOFWEEK(r.signup_date) AS signup_dow
        FROM user_retention r
        LEFT JOIN user_breadth b USING (user_id)
        LEFT JOIN user_conversion c USING (user_id)
    """).df()
    week1 = con.sql("""
        SELECT user_id,
          MAX(IF(day_n <= 6 AND event_name = 'feature_opened' AND feature = CASE initial_intent
              WHEN 'funding' THEN 'funding' WHEN 'create' THEN 'create' WHEN 'analyze' THEN 'analyze'
              WHEN 'ask' THEN 'cofounder' WHEN 'presence' THEN 'website' ELSE 'business_plan' END, 1, 0)) AS w1_first_action,
          MAX(IF(day_n <= 6 AND event_name IN ('grant_application_started','artifact_generated',
              'analysis_completed','analysis_started','cofounder_response_received','website_created',
              'business_plan_started','business_page_published','website_published','instant_grant_entered'), 1, 0)) AS w1_output,
          COUNT(IF(day_n = 0, 1, NULL)) AS day0_events,
          MAX(IF(event_name = 'analysis_recommendation_clicked', 1, 0)) AS acted_on_analysis
        FROM stg_events GROUP BY 1""").df()
    bridge = con.sql("""
        WITH fa AS (SELECT user_id, MIN(event_ts) t FROM stg_events WHERE event_name='analysis_started' GROUP BY 1)
        SELECT fa.user_id, 1 AS analyzed,
               MAX(IF(e.event_name='cofounder_message_sent' AND e.event_ts BETWEEN fa.t AND fa.t + INTERVAL 24 HOUR,1,0)) AS bridged_24h,
               COUNT(IF(e.event_ts < fa.t, 1, NULL)) AS events_before_analysis
        FROM fa LEFT JOIN stg_events e USING (user_id) GROUP BY 1""").df()
    weekly = con.sql("""
        SELECT u.user_id, u.initial_intent, u.acquisition_channel, u.signup_week, u.activated_intent_7d,
               w.k AS week_k,
               MAX(IF(e.day_n BETWEEN 7*w.k AND 7*w.k+6, 1, 0)) AS active,
               MAX(IF(e.day_n BETWEEN 7*w.k AND 7*w.k+6 AND e.is_value_event, 1, 0)) AS value_active
        FROM user_retention u
        CROSS JOIN (SELECT range AS k FROM range(0, 9)) w
        LEFT JOIN stg_events e ON e.user_id = u.user_id
        WHERE u.signup_date + INTERVAL (7*w.k + 7) DAY <= u.obs_end
        GROUP BY ALL""").df()
    steps = pd.read_csv(ROOT / "analysis" / "sql_results" / "04_feature_sequences__01.csv")
    journeys = pd.read_csv(ROOT / "analysis" / "sql_results" / "04_feature_sequences__03.csv")
    ttfv_hist = pd.read_csv(ROOT / "analysis" / "sql_results" / "05_time_to_value__04.csv")
    funnel = pd.read_csv(ROOT / "analysis" / "sql_results" / "02_activation_by_intent__02.csv")
    anomalies = pd.read_csv(ROOT / "analysis" / "sql_results" / "08_anomaly_detection__03.csv")
    dq = pd.read_csv(ROOT / "analysis" / "sql_results" / "08_anomaly_detection__01.csv")
    drawing = pd.read_csv(ROOT / "analysis" / "sql_results" / "06_cross_feature_adoption__04.csv")
    funding_paths = pd.read_csv(ROOT / "analysis" / "sql_results" / "06_cross_feature_adoption__03.csv")
    u = users.merge(week1, on="user_id", how="left").merge(bridge, on="user_id", how="left")
    for c in ["analyzed", "bridged_24h", "w1_first_action", "w1_output", "day0_events", "events_before_analysis",
              "features_with_value_w1", "features_opened_w1", "day0_sessions", "acted_on_analysis"]:
        u[c] = u[c].fillna(0).astype(int)
    for c in ["activated_intent_7d", "activated_any_7d"]:
        u[c] = u[c].astype(int)
    u["log_day0_events"] = np.log1p(u["day0_events"])
    u = u.sort_values("user_id").reset_index(drop=True)   # DuckDB row order is not deterministic
    return dict(u=u, weekly=weekly, steps=steps, journeys=journeys, ttfv_hist=ttfv_hist,
                funnel=funnel, anomalies=anomalies, dq=dq, drawing=drawing, funding_paths=funding_paths)


# ------------------------------------------------------------------ analyses
def kpis(u):
    obs30 = u[u.d30_any.notna()]
    reached = u[u.ttfv_hours.notna()]
    conv = u[u.conv_observed == True]  # noqa: E712
    return dict(
        users=int(len(u)),
        activation_intent_7d=round(u.activated_intent_7d.mean(), 4),
        activation_any_7d=round(u.activated_any_7d.mean(), 4),
        activation_ci=[round(x, 4) for x in boot_mean(u.activated_intent_7d)],
        median_ttfv_minutes=round(float(reached.ttfv_hours.median() * 60), 1),
        p75_ttfv_hours=round(float(reached.ttfv_hours.quantile(.75)), 1),
        share_never_reached_value=round(float(u.ttfv_hours.isna().mean()), 4),
        d7_activity=round(float(u.d7_any.mean()), 4), d7_value=round(float(u.d7_value.mean()), 4),
        d30_activity=round(float(obs30.d30_any.mean()), 4), d30_value=round(float(obs30.d30_value.mean()), 4),
        d30_observed=int(len(obs30)),
        paid_conv_30d_net=round(float(conv.paid_30d_net.mean()), 4),
        paid_conv_30d_gross=round(float(conv.paid_30d_gross.mean()), 4),
        conv_observed=int(len(conv)),
    )


def by_intent(u):
    rows = []
    for i in INTENTS:
        d = u[u.initial_intent == i]
        o = d[d.d30_any.notna()]
        c = d[d.conv_observed == True]  # noqa: E712
        r = d[d.ttfv_hours.notna()]
        rows.append(dict(intent=i, label=INTENT_LABEL[i], users=int(len(d)),
                         first_action=round(d.w1_first_action.mean(), 4),
                         activation_intent_7d=round(d.activated_intent_7d.mean(), 4),
                         activation_any_7d=round(d.activated_any_7d.mean(), 4),
                         median_ttfv_min=round(float(r.ttfv_hours.median() * 60), 1) if len(r) else None,
                         d7_activity=round(float(d.d7_any.mean()), 4), d7_value=round(float(d.d7_value.mean()), 4),
                         d30_activity=round(float(o.d30_any.mean()), 4), d30_value=round(float(o.d30_value.mean()), 4),
                         d30_observed=int(len(o)), paid_conv_30d=round(float(c.paid_30d_net.mean()), 4)))
    return rows


def h1_activation_candidates(u):
    """For each intent: which candidate activation event best predicts D30 value retention?"""
    d = u[u.d30_value.notna()].copy()
    d["universal_only"] = ((d.activated_any_7d == 1) & (d.activated_intent_7d == 0)).astype(int)
    cands = {"First action (opened feature)": "w1_first_action",
             "Received an output": "w1_output",
             "Universal: any FMO ≤7d": "activated_any_7d",
             "Intent-specific FMO ≤7d": "activated_intent_7d"}
    out = []
    for i in INTENTS:
        s = d[d.initial_intent == i]
        for name, col in cands.items():
            hit = s[col] == 1
            y = s.d30_value.values
            if hit.all() or (~hit).all():
                continue
            sens = (hit & (s.d30_value == 1)).sum() / max((s.d30_value == 1).sum(), 1)
            spec = (~hit & (s.d30_value == 0)).sum() / max((s.d30_value == 0).sum(), 1)
            c = compare(s.assign(_f=hit.astype(int)), "_f")
            adj = logit_or(s.assign(_f=hit.astype(int)),
                           "d30_value ~ _f + C(acquisition_channel) + C(platform) + log_day0_events", "_f")
            out.append(dict(intent=i, candidate=name, reach=round(float(hit.mean()), 4),
                            auc=round(float((sens + spec) / 2), 4), lift_pp=round(c["diff"] * 100, 1),
                            ci95_pp=[round(x * 100, 1) for x in c["ci95"]], adj_odds_ratio=adj["odds_ratio"],
                            adj_or_ci=adj["ci95"], n=int(len(s))))
    # who the universal metric miscounts
    uni = []
    for i in INTENTS:
        s = d[d.initial_intent == i]
        for label, mask in [("Intent-activated", s.activated_intent_7d == 1),
                            ("Activated elsewhere only", s.universal_only == 1),
                            ("Not activated", s.activated_any_7d == 0)]:
            g = s[mask]
            if len(g):
                lo, hi = boot_mean(g.d30_value)
                uni.append(dict(intent=i, group=label, n=int(len(g)), d30_value=round(float(g.d30_value.mean()), 4),
                                ci95=[round(lo, 4), round(hi, 4)]))
    return out, uni


def h2_complete_vs_explore(u):
    d = u[(u.features_opened_w1 >= 1) & u.d30_value.notna()].copy()
    d["completed"] = (d.features_with_value_w1 >= 1).astype(int)
    raw = compare(d, "completed")
    adj = logit_or(d, "d30_value ~ completed + C(initial_intent) + C(acquisition_channel) + C(platform)", "completed")
    adj2 = logit_or(d, "d30_value ~ completed + C(initial_intent) + C(acquisition_channel) + C(platform) "
                       "+ log_day0_events", "completed")
    within = []
    for i in INTENTS:
        c = compare(d[d.initial_intent == i], "completed")
        within.append(dict(intent=i, **c))
    return dict(denominator="users who opened ≥1 feature in week 1, D30 observed", raw=raw,
                adj_pre_signup=adj, adj_with_day0=adj2, within_intent=within)


def h3_cross_feature(u):
    d = u[(u.features_with_value_w1 >= 1) & u.d30_value.notna()].copy()
    d["multi"] = (d.features_with_value_w1 >= 2).astype(int)
    d["d0_multi_session"] = (d.day0_sessions >= 2).astype(int)
    raw = compare(d, "multi")
    adj1 = logit_or(d, "d30_value ~ multi + C(initial_intent) + C(acquisition_channel) + C(platform)", "multi")
    adj2 = logit_or(d, "d30_value ~ multi + C(initial_intent) + C(acquisition_channel) + C(platform) "
                       "+ log_day0_events + d0_multi_session", "multi")
    raw_or = logit_or(d, "d30_value ~ multi", "multi")
    # where does breadth come from? funding users via incentive items vs others
    non_funding = compare(d[d.initial_intent != "funding"], "multi")
    funding = compare(d[d.initial_intent == "funding"], "multi")
    # selection check: are multi-feature users different BEFORE breadth could matter?
    pre = dict(day0_events_multi=round(float(d[d.multi == 1].day0_events.median()), 1),
               day0_events_single=round(float(d[d.multi == 0].day0_events.median()), 1))
    return dict(denominator="activated users (value in ≥1 feature in week 1), D30 observed",
                raw=raw, raw_or=raw_or, adj_pre_signup=adj1, adj_with_engagement=adj2,
                funding=funding, non_funding=non_funding, selection_check=pre)


def h4_analyze_cofounder(u):
    d = u[(u.analyzed == 1) & u.d30_value.notna()].copy()
    raw = compare(d, "bridged_24h")
    d["log_pre"] = np.log1p(d.events_before_analysis)
    adj = logit_or(d, "d30_value ~ bridged_24h + C(initial_intent) + C(acquisition_channel) + C(platform) "
                      "+ log_pre", "bridged_24h")
    analyze_intent = d[d.initial_intent == "analyze"]
    raw_ai = compare(analyze_intent, "bridged_24h")
    adj_ai = logit_or(analyze_intent, "d30_value ~ bridged_24h + C(acquisition_channel) + C(platform) "
                                      "+ log_pre", "bridged_24h")
    pre = dict(median_events_before_analysis_bridged=float(d[d.bridged_24h == 1].events_before_analysis.median()),
               median_events_before_analysis_not=float(d[d.bridged_24h == 0].events_before_analysis.median()),
               d1_activity_bridged=round(float(d[d.bridged_24h == 1].d1_any.mean()), 3),
               d1_activity_not=round(float(d[d.bridged_24h == 0].d1_any.mean()), 3))
    acted = d[d.acted_on_analysis == 1]
    matched = compare(acted, "bridged_24h")
    return dict(denominator="users with ≥1 analysis_started, D30 observed", all_analyzers=raw, adj_all=adj,
                acted_on_analysis_only=matched,
                analyze_intent_only=raw_ai, adj_analyze_intent=adj_ai, n_bridged_analyze_intent=int(
                    analyze_intent.bridged_24h.sum()), selection_check=pre)


def h5_funding(u, drawing, funding_paths):
    d = u[u.d30_any.notna()].copy()
    d["is_funding"] = (d.initial_intent == "funding").astype(int)
    gap = []
    for i in INTENTS:
        s = d[d.initial_intent == i]
        gap.append(dict(intent=i, d30_activity=round(float(s.d30_any.mean()), 4),
                        d30_value=round(float(s.d30_value.mean()), 4),
                        value_to_activity=round(float(s.d30_value.mean() / s.d30_any.mean()), 3)))
    c = u[u.conv_observed == True].copy()  # noqa: E712
    c["is_funding"] = (c.initial_intent == "funding").astype(int)
    conv = compare(c.rename(columns={"paid_30d_net": "y"}).assign(y=lambda x: x.y.astype(float)), "is_funding", "y")
    conv_adj = logit_or(c.assign(y=c.paid_30d_net.astype(int)),
                        "y ~ is_funding + activated_intent_7d + C(acquisition_channel) + C(platform)", "is_funding")
    return dict(activity_vs_value=gap, drawing_day_share=drawing.to_dict("records"),
                conversion_funding_vs_rest=conv, conversion_adj=conv_adj,
                funding_paths=funding_paths.to_dict("records"))


def h6_ttfv(u):
    d = u[u.d30_value.notna()].copy()
    d["reached"] = d.ttfv_hours.notna().astype(int)
    r = d[d.reached == 1].copy()
    r["fast"] = (r.ttfv_hours <= 1).astype(int)
    r["same_day"] = (r.ttfv_days == 0).astype(int)
    m_reach = logit_or(d, "d30_value ~ reached + features_opened_w1 + C(initial_intent) + C(acquisition_channel)",
                       "reached")
    m_fast = logit_or(r, "d30_value ~ same_day + features_opened_w1 + C(initial_intent) + C(acquisition_channel)",
                      "same_day")
    m_feat = logit_or(r, "d30_value ~ same_day + features_opened_w1 + C(initial_intent) + C(acquisition_channel)",
                      "features_opened_w1")
    buckets = []
    for name, mask in [("≤1 hour", d.ttfv_hours <= 1), ("1–24 hours", (d.ttfv_hours > 1) & (d.ttfv_days == 0)),
                       ("day 1–3", d.ttfv_days.between(1, 3)), ("day 4+", d.ttfv_days >= 4),
                       ("never", d.ttfv_hours.isna())]:
        g = d[mask]
        lo, hi = boot_mean(g.d30_value)
        buckets.append(dict(bucket=name, n=int(len(g)), d30_value=round(float(g.d30_value.mean()), 4),
                            ci95=[round(lo, 4), round(hi, 4)]))
    return dict(reach_effect=m_reach, speed_effect_among_reached=m_fast, features_effect_among_reached=m_feat,
                buckets=buckets)


def channel_simpson(u):
    d = u[u.d30_value.notna()]
    overall = d.groupby("acquisition_channel").d30_value.mean()
    intent_rate = d.groupby("initial_intent").d30_value.mean()
    mix = d.assign(exp=d.initial_intent.map(intent_rate)).groupby("acquisition_channel").exp.mean()
    paid = d[d.acquisition_channel == "paid_social"]
    rest = d[d.acquisition_channel != "paid_social"]
    within = []
    for i in INTENTS:
        a, b = paid[paid.initial_intent == i].d30_value, rest[rest.initial_intent == i].d30_value
        within.append(dict(intent=i, paid_social=round(float(a.mean()), 4), other_channels=round(float(b.mean()), 4),
                           n_paid=int(len(a))))
    adj = logit_or(d.assign(paid=(d.acquisition_channel == "paid_social").astype(int)),
                   "d30_value ~ paid + C(initial_intent) + C(platform)", "paid")
    raw_or = logit_or(d.assign(paid=(d.acquisition_channel == "paid_social").astype(int)), "d30_value ~ paid", "paid")
    return dict(raw=overall.round(4).to_dict(), expected_from_mix=mix.round(4).to_dict(),
                paid_social_within_intent=within, paid_raw_or=raw_or, paid_adj_or=adj,
                paid_intent_mix=paid.initial_intent.value_counts(normalize=True).round(3).to_dict(),
                other_intent_mix=rest.initial_intent.value_counts(normalize=True).round(3).to_dict())


def cohort_mix_shift(u):
    """Did retention drop for July cohorts, or did the mix change?"""
    d = u[u.d7_any.notna()].copy()
    d["signup_week"] = pd.to_datetime(d.signup_week).dt.strftime("%Y-%m-%d")
    rows = []
    for wk, g in d.groupby("signup_week"):
        ps = g[g.acquisition_channel == "paid_social"]
        rest = g[g.acquisition_channel != "paid_social"]
        rows.append(dict(week=wk, n=int(len(g)), d7_all=round(float(g.d7_any.mean()), 4),
                         n_paid_social=int(len(ps)), d7_paid_social=round(float(ps.d7_any.mean()), 4),
                         n_other=int(len(rest)), d7_other=round(float(rest.d7_any.mean()), 4)))
    return rows


def retention_curves(weekly):
    def curve(df, key):
        g = df.groupby([key, "week_k"]).agg(n=("active", "size"), active=("active", "mean"),
                                            value=("value_active", "mean")).reset_index()
        return {str(k): [dict(week=int(r.week_k), n=int(r.n), activity=round(r.active, 4), value=round(r.value, 4))
                         for r in sub.itertuples()] for k, sub in g.groupby(key)}
    w = weekly.copy()
    w["signup_week"] = pd.to_datetime(w.signup_week).dt.strftime("%Y-%m-%d")
    w["activated"] = np.where(w.activated_intent_7d, "activated", "not activated")
    return dict(intent=curve(w, "initial_intent"), channel=curve(w, "acquisition_channel"),
                cohort=curve(w, "signup_week"), activation=curve(w, "activated"))


# ------------------------------------------------------------------ figures
def fig_activity_vs_value(rows):
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(rows))
    ax.bar(x - 0.2, [r["d30_activity"] for r in rows], 0.38, color="#c7d2fe", label="D30 activity retention")
    ax.bar(x + 0.2, [r["d30_value"] for r in rows], 0.38, color=C1, label="D30 value retention")
    ax.set_xticks(x, [INTENT_LABEL[r["intent"]] for r in rows], rotation=0, fontsize=8.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    ax.set_title("Activity vs value retention by initial intent (week 5)", loc="left", fontsize=11, color=INK)
    ax.legend(frameon=False, fontsize=8.5)
    stamp(fig); fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(FIG / "activity_vs_value.png"); plt.close(fig)


def fig_h3(h3):
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    labels = ["Raw", "+ intent, channel,\nplatform", "+ day-0 engagement\nproxies"]
    ors = [h3["raw_or"], h3["adj_pre_signup"], h3["adj_with_engagement"]]
    y = np.arange(len(ors))[::-1]
    for yi, o in zip(y, ors):
        ax.plot(o["ci95"], [yi, yi], color=C1, lw=2)
        ax.plot(o["odds_ratio"], yi, "o", color=C1, ms=7)
        ax.text(o["ci95"][1] + 0.1, yi, f'OR {o["odds_ratio"]:.2f}', va="center", fontsize=8.5, color=INK)
    ax.axvline(1, color=MUTED, ls="--", lw=1)
    ax.set_yticks(y, labels, fontsize=8.5)
    ax.set_xlabel("Odds ratio: D30 value retention, 2+ vs 1 feature with value in week 1")
    ax.set_title("H3: the cross-feature 'effect' shrinks as controls are added", loc="left", fontsize=11, color=INK)
    stamp(fig); fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(FIG / "h3_cross_feature_or.png"); plt.close(fig)


def fig_ttfv(h6):
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    b = h6["buckets"]
    x = np.arange(len(b))
    vals = [r["d30_value"] for r in b]
    err = [[r["d30_value"] - r["ci95"][0] for r in b], [r["ci95"][1] - r["d30_value"] for r in b]]
    ax.bar(x, vals, color=[C1] * 4 + ["#cbd5e1"], yerr=err, capsize=3, ecolor=MUTED)
    for xi, r in zip(x, b):
        ax.text(xi, r["d30_value"] + 0.02, f'n={r["n"]:,}', ha="center", fontsize=7.5, color=MUTED)
    ax.set_xticks(x, [r["bucket"] for r in b], fontsize=8.5)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    ax.set_title("H6: reaching value matters; speed among reachers doesn't", loc="left", fontsize=11, color=INK)
    ax.set_ylabel("D30 value retention")
    stamp(fig); fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(FIG / "h6_ttfv.png"); plt.close(fig)


def fig_curves(curves):
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for i in INTENTS:
        pts = curves["intent"][i]
        ax.plot([p["week"] for p in pts], [p["value"] for p in pts], marker="o", ms=3, lw=1.8,
                color=INTENT_COLORS[i], label=INTENT_LABEL[i])
    ax.set_xlabel("Weeks since signup"); ax.set_ylabel("Value-active in week")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, 0))
    ax.set_title("Value retention curves by initial intent", loc="left", fontsize=11, color=INK)
    ax.legend(frameon=False, fontsize=8, ncol=3)
    stamp(fig); fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(FIG / "retention_curves_intent.png"); plt.close(fig)


def fig_exp_b(sim):
    if not sim:
        return
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    rows = [("Observational:\nbridged vs not (control arm)", sim["naive_observational_in_control"], sim["naive_ci95"], "#94a3b8"),
            ("Randomized, per user who bridged\n(ITT ÷ uptake difference)", sim["cace"], None, C1),
            ("Randomized, intent-to-treat\n(everyone offered the bridge)", sim["itt_diff"], sim["itt_ci95"], C1)]
    y = np.arange(len(rows))[::-1]
    for yi, (lab, v, ci, col) in zip(y, rows):
        ax.barh(yi, v * 100, color=col, height=0.55)
        if ci:
            ax.plot([ci[0] * 100, ci[1] * 100], [yi, yi], color=INK, lw=1.2)
        ax.text(max(v * 100, (ci[1] * 100) if ci else 0) + 0.8, yi, f"{v*100:+.1f} pp", va="center", fontsize=9)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_yticks(y, [r[0] for r in rows], fontsize=8.5)
    ax.set_xlabel("Difference in D30 value retention (percentage points)")
    ax.set_title("H4: the observational gap is ~2x the causal effect", loc="left", fontsize=11, color=INK)
    stamp(fig); fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(FIG / "h4_simulated_experiment.png"); plt.close(fig)


# ------------------------------------------------------------------ main
def main():
    D = load()
    u = D["u"]
    R = dict(disclaimer="All behavioral data in this analysis is synthetic and is used solely to demonstrate "
                        "the analytical methodology. It does not represent actual Skip users or performance.")
    R["kpis"] = kpis(u)
    R["by_intent"] = by_intent(u)
    R["h1_candidates"], R["h1_universal_miscount"] = h1_activation_candidates(u)
    R["h2"] = h2_complete_vs_explore(u)
    R["h3"] = h3_cross_feature(u)
    R["h4"] = h4_analyze_cofounder(u)
    R["h5"] = h5_funding(u, D["drawing"], D["funding_paths"])
    R["h6"] = h6_ttfv(u)
    R["channel_simpson"] = channel_simpson(u)
    R["cohort_mix_shift"] = cohort_mix_shift(u)
    sim = ROOT / "analysis" / "results" / "simulated_experiment_b.json"
    R["simulated_experiment_b"] = json.loads(sim.read_text()) if sim.exists() else None
    R["curves"] = retention_curves(D["weekly"])
    R["sequences"] = D["steps"].to_dict("records")
    R["journeys"] = D["journeys"].to_dict("records")
    R["ttfv_hist"] = D["ttfv_hist"].to_dict("records")
    R["funnel"] = D["funnel"].to_dict("records")
    R["anomalies"] = D["anomalies"].assign(d=lambda x: x.d.astype(str)).to_dict("records")
    R["data_quality"] = D["dq"].to_dict("records")[0]
    R["ground_truth"] = json.loads((ROOT / "scripts" / "ground_truth.json").read_text())

    (RES / "results.json").write_text(json.dumps(R, indent=1, default=float))
    (ROOT / "dashboard" / "data.js").write_text(
        "// Generated by analysis/product_analysis.py — SYNTHETIC DATA, not Skip performance.\n"
        "window.SKIP_DATA = " + json.dumps(R, default=float) + ";\n")

    fig_activity_vs_value(R["by_intent"]); fig_h3(R["h3"]); fig_ttfv(R["h6"]); fig_curves(R["curves"]); fig_exp_b(R["simulated_experiment_b"])

    # console summary
    print(json.dumps({k: R[k] for k in ["kpis"]}, indent=1))
    print(pd.DataFrame(R["by_intent"]).to_string(index=False))
    print(pd.DataFrame(R["h1_candidates"]).to_string(index=False))
    print(pd.DataFrame(R["h1_universal_miscount"]).to_string(index=False))
    for h in ["h2", "h3", "h4", "h6", "channel_simpson"]:
        print(f"\n--- {h}"); print(json.dumps({k: v for k, v in R[h].items() if k not in ("buckets",)}, indent=1, default=float)[:3000])
    print("\n--- h5"); print(json.dumps({k: R["h5"][k] for k in ["activity_vs_value", "conversion_funding_vs_rest", "conversion_adj"]}, indent=1, default=float))


if __name__ == "__main__":
    main()
