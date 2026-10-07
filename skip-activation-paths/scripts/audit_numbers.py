"""
Audit: every number quoted in the founder-facing documents, checked against the
generated outputs (analysis/results/*.json and analysis/sql_results/*.csv).

Run after analysis/product_analysis.py. Exits non-zero if any claim fails.
The dashboard computes its numbers live from dashboard/data.js (same results.json),
so it is checked by construction; its fixed copy is checked below.
SYNTHETIC DATA — methodology demo, not Skip performance.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from sample_size import n_per_arm  # noqa: E402
R = json.loads((ROOT / "analysis/results/results.json").read_text())
S = R["simulated_experiment_b"]
BI = {r["intent"]: r for r in R["by_intent"]}
cand = {(c["intent"], c["candidate"]): c for c in R["h1_candidates"]}
draw = {r["initial_intent"]: r["share_on_drawing_days"] for r in R["h5"]["drawing_day_share"]}
mix = {r["week"]: r for r in R["cohort_mix_shift"]}
june = [mix[w] for w in mix if w < "2026-07-01"]
fp = R["h5"]["funding_paths"]
conv = R["h5"]["conversion_funding_vs_rest"]

p = lambda x, d=1: round(x * 100, d)  # noqa: E731
CLAIMS = [
    # (claim as written, value in docs, computed value)
    ("simulated users", 17630, R["kpis"]["users"]),
    ("activation min (online presence) %", 39, p(min(r["activation_intent_7d"] for r in R["by_intent"]), 0)),
    ("activation max (funding) %", 61, p(max(r["activation_intent_7d"] for r in R["by_intent"]), 0)),
    ("AUC received output min", 0.56, round(min(cand[(i, "Received an output")]["auc"] for i in BI), 2)),
    ("AUC received output max", 0.61, round(max(cand[(i, "Received an output")]["auc"] for i in BI), 2)),
    ("AUC kept/acted min", 0.66, round(min(cand[(i, "Intent-specific FMO ≤7d")]["auc"] for i in BI), 2)),
    ("AUC kept/acted max", 0.73, round(max(cand[(i, "Intent-specific FMO ≤7d")]["auc"] for i in BI), 2)),
    ("H2 completed %", 16.8, p(R["h2"]["raw"]["rate_with"])),
    ("H2 explored-only %", 3.2, p(R["h2"]["raw"]["rate_without"])),
    ("H2 diff pp", 13.6, p(R["h2"]["raw"]["diff"])),
    ("H2 CI low pp", 12.7, p(R["h2"]["raw"]["ci95"][0])),
    ("H2 CI high pp", 14.6, p(R["h2"]["raw"]["ci95"][1])),
    ("H2 n completed", 9123, R["h2"]["raw"]["n_with"]),
    ("H2 n explored", 5068, R["h2"]["raw"]["n_without"]),
    ("H3 2+ features %", 31.3, p(R["h3"]["raw"]["rate_with"])),
    ("H3 1 feature %", 9.7, p(R["h3"]["raw"]["rate_without"])),
    ("H3 raw OR", 4.26, round(R["h3"]["raw_or"]["odds_ratio"], 2)),
    ("H3 OR + intent/channel/platform", 4.12, round(R["h3"]["adj_pre_signup"]["odds_ratio"], 2)),
    ("H3 OR + day-0 engagement", 2.81, round(R["h3"]["adj_with_engagement"]["odds_ratio"], 2)),
    ("H3 median day-0 events multi", 12, R["h3"]["selection_check"]["day0_events_multi"]),
    ("H3 median day-0 events single", 9, R["h3"]["selection_check"]["day0_events_single"]),
    ("funding only D30 value %", 8.9, p(fp[0]["d30_value"])),
    ("funding + website/plan D30 value %", 19.2, p(fp[1]["d30_value"])),
    ("Exp B observational pp", 33.1, p(S["naive_observational_in_control"])),
    ("Exp B observational CI low", 27.3, p(S["naive_ci95"][0])),
    ("Exp B observational CI high", 38.9, p(S["naive_ci95"][1])),
    ("Exp B per bridged user pp", 14.2, p(S["cace"])),
    ("Exp B ITT pp", 3.1, p(S["itt_diff"])),
    ("Exp B ITT CI low", -0.9, p(S["itt_ci95"][0])),
    ("Exp B ITT CI high", 7.0, p(S["itt_ci95"][1])),
    ("Exp B ITT p-value", 0.14, round(S["itt_p_value"], 2)),
    ("Exp B users per arm (~1,070)", 1070, round((S["n_treatment"] + S["n_control"]) / 2, -1)),
    ("users per arm to detect +3 pp (~4,000)", 4000, round(n_per_arm(S["d30_value_control"], 0.03), -3)),
    ("July 6 cohort D7 %", 26.3, p(mix["2026-07-06"]["d7_all"])),
    ("July 13 cohort D7 %", 26.4, p(mix["2026-07-13"]["d7_all"])),
    ("July 6 excl. paid social %", 28.3, p(mix["2026-07-06"]["d7_other"])),
    ("July 13 excl. paid social %", 28.5, p(mix["2026-07-13"]["d7_other"])),
    ("June cohorts D7 min %", 27.9, p(min(r["d7_all"] for r in june))),
    ("June cohorts D7 max %", 29.3, p(max(r["d7_all"] for r in june))),
    ("paid share July cohorts (~42%)", 42, round(p((mix["2026-07-06"]["n_paid_social"] + mix["2026-07-13"]["n_paid_social"])
                                                    / (mix["2026-07-06"]["n"] + mix["2026-07-13"]["n"]), 0))),
    ("paid share June cohorts (~19%)", 19, round(p(sum(r["n_paid_social"] for r in june) / sum(r["n"] for r in june), 0))),
    ("funding drawing-day share %", 82, p(draw["funding"], 0)),
    ("funding drawing-day share % (precise)", 81.5, p(draw["funding"])),
    ("other intents drawing share min %", 45, p(min(v for k, v in draw.items() if k != "funding"), 0)),
    ("other intents drawing share max %", 56, p(max(v for k, v in draw.items() if k != "funding"), 0)),
    ("funding D30 activity %", 20.2, p(BI["funding"]["d30_activity"])),
    ("funding paid conversion %", 3.6, p(conv["rate_with"])),
    ("other intents paid conversion %", 7.4, p(conv["rate_without"])),
    ("never reached value D30 %", 0.4, p([b for b in R["h6"]["buckets"] if b["bucket"] == "never"][0]["d30_value"])),
    ("speed OR among reachers", 0.87, round(R["h6"]["speed_effect_among_reached"]["odds_ratio"], 2)),
    ("median TTFV minutes", 6, R["kpis"]["median_ttfv_minutes"]),
    ("never reached value %", 39, p(R["kpis"]["share_never_reached_value"], 0)),
    ("iOS monitor z-score", -31.8, [a for a in R["anomalies"] if a["d"] == "2026-07-14"][0]["z_score"]),
]

fails = [(c, doc, got) for c, doc, got in CLAIMS if abs(float(doc) - float(got)) > 1e-9]
for c, doc, got in CLAIMS:
    print(f"{'OK  ' if (c, doc, got) not in fails else 'FAIL'} {c:45s} doc={doc!s:>8}  computed={got}")
print(f"\n{len(CLAIMS) - len(fails)}/{len(CLAIMS)} claims reproduce.")
sys.exit(1 if fails else 0)
