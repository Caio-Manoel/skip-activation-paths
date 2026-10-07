"""
Synthetic data generator for "Finding Skip's Activation Paths".

ALL DATA PRODUCED BY THIS SCRIPT IS SYNTHETIC. It is used solely to demonstrate
the analytical methodology. It does not represent actual Skip users or performance.

The generative model is documented in data/README.md. In short: each user has a
latent engagement propensity `z` that is NEVER written to the output files. `z`
drives return probability, feature breadth, speed to value and paid conversion at
the same time — which is exactly what creates the selection bias the analysis must
deal with. Causal effects that are "true" in this synthetic world are set
explicitly in CAUSAL_EFFECTS so the analysis can be checked against ground truth.
"""
from __future__ import annotations

import csv
import json
import math
import os
import random
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 20261007
rng = random.Random(SEED)

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("OUT_DIR", ROOT / "data"))
OUT.mkdir(parents=True, exist_ok=True)
# Simulated experiment switch (see analysis/simulated_experiment_b.py):
#   natural    — users self-select into Analyze -> Cofounder (default; used for data/)
#   randomized — each user is randomly assigned control/treatment (50/50); treatment users
#                are offered the bridge, so uptake is at least 40% regardless of propensity
EXPERIMENT_B = os.environ.get("EXPERIMENT_B", "natural")

# ---------------------------------------------------------------- calendar
SIGNUP_START = date(2026, 6, 1)
SIGNUP_DAYS = 60                         # signups 2026-06-01 .. 2026-07-30
OBS_END = date(2026, 8, 30)              # events observed up to 2026-08-29 (90 days total)
DRAWING_WEEKDAYS = {1, 3}                # Tue, Thu — a SYNTHETIC assumption, not Skip's real schedule
CAMPAIGN = (date(2026, 7, 6), date(2026, 7, 19))   # synthetic paid-social campaign
TRACKING_BREAK = (date(2026, 7, 14), date(2026, 7, 18))  # iOS drops analysis_completed
HOLIDAY = date(2026, 7, 4)

BASE_DAILY_SIGNUPS = 255
N_TEST_ACCOUNTS = 30

# ---------------------------------------------------------------- vocab
INTENTS = ["funding", "create", "analyze", "ask", "presence", "start"]
PRIMARY_FEATURE = {"funding": "funding", "create": "create", "analyze": "analyze",
                   "ask": "cofounder", "presence": "website", "start": "business_plan"}
FEATURES = ["funding", "create", "analyze", "cofounder", "website", "business_plan"]

CHANNELS = {  # share, propensity mean, intent mix
    "organic_search":     (0.28,  0.10, [.30, .18, .14, .10, .16, .12]),
    "grant_listings":     (0.22, -0.10, [.78, .04, .03, .05, .05, .05]),
    "paid_social":        (0.18, -0.10, [.15, .42, .08, .12, .15, .08]),
    "referral_affiliate": (0.10,  0.30, [.30, .15, .12, .15, .18, .10]),
    "app_store":          (0.12,  0.00, [.40, .20, .06, .14, .12, .08]),
    "direct":             (0.10,  0.20, [.25, .15, .18, .18, .14, .10]),
}
CAMPAIGN_INTENT_MIX = [.08, .60, .06, .10, .10, .06]

# Day-0 success logits per intent (before propensity)
FMO_BASE = {"funding": 0.25, "create": -0.10, "analyze": -0.45, "ask": 0.00, "presence": -0.65, "start": 0.30}
# Baseline daily return logit per intent
ALPHA = {"funding": -3.50, "create": -2.55, "analyze": -2.75, "ask": -2.50, "presence": -2.85, "start": -3.25}

# Ground-truth causal effects in this synthetic world (logit scale on daily return probability)
CAUSAL_EFFECTS = {
    "value_reached_by_intent": {"funding": 0.35, "create": 1.10, "analyze": 0.90,
                                "ask": 1.00, "presence": 0.70, "start": 0.40},
    "cross_feature_value": 0.12,          # small true effect of having value in 2+ features
    "incentive_completion": 0.00,          # completions driven by grant incentive add nothing
    "analyze_to_cofounder_bridge": 0.25,   # modest true effect
    "time_to_first_value": 0.00,           # speed itself has no effect beyond reaching value
    "drawing_day_boost": 3.40,             # for drawing-engaged users, on drawing days
}
PROPENSITY_COEF = 0.90
DAY_DECAY = 0.62

PLATFORM_APP_VERSION = {"web": "web", "ios": "3.11", "android": "3.11"}


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def new_id() -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def choice_w(options, weights):
    return rng.choices(options, weights=weights, k=1)[0]


def is_drawing_day(d: date) -> bool:
    return d.weekday() in DRAWING_WEEKDAYS


# ---------------------------------------------------------------- users
def make_users():
    users = []
    uid = 0
    for i in range(SIGNUP_DAYS):
        d = SIGNUP_START + timedelta(days=i)
        n = BASE_DAILY_SIGNUPS * (1 + 0.004 * i)            # mild growth
        n *= 0.78 if d.weekday() >= 5 else 1.0              # weekend dip
        n *= 0.55 if d == HOLIDAY else 1.0
        n = int(rng.gauss(n, n ** 0.5))
        in_campaign = CAMPAIGN[0] <= d <= CAMPAIGN[1]
        extra = int(rng.gauss(115, 10)) if in_campaign else 0
        for k in range(n + extra):
            uid += 1
            campaign_user = k >= n
            if campaign_user:
                channel, mu, mix = "paid_social", -0.30, CAMPAIGN_INTENT_MIX
            else:
                channel = choice_w(list(CHANNELS), [v[0] for v in CHANNELS.values()])
                _, mu, mix = CHANNELS[channel]
            intent = choice_w(INTENTS, mix)
            z = rng.gauss(mu, 1.0)
            platform = ("ios" if rng.random() < 0.68 else "android") if channel == "app_store" else \
                choice_w(["web", "ios", "android"], [.62, .25, .13])
            secondary = None
            if rng.random() < 0.30:
                secondary = choice_w([x for x in INTENTS if x != intent], None)
            country = choice_w(["US", "CA", "GB", "NG", "IN", "PH", "OTHER"],
                               [.90, .03, .02, .015, .015, .01, .01])
            signup_ts = datetime(d.year, d.month, d.day) + timedelta(
                seconds=int(rng.triangular(6 * 3600, 23.9 * 3600, 15 * 3600)))
            users.append(dict(
                user_id=f"u_{uid:06d}", signup_date=d, signup_ts=signup_ts, channel=channel,
                initial_intent=intent, secondary_intent=secondary, z=z, platform=platform,
                country=country, business_stage=choice_w(["new", "existing"], [.55, .45]),
                power=z > 1.9, campaign=campaign_user,
                drawing_affinity=rng.random() < (0.62 if intent == "funding" else 0.12),
                is_test=False,
                exp_b=(("treatment" if rng.random() < 0.5 else "control")
                       if EXPERIMENT_B == "randomized" else None),
            ))
    # internal / QA accounts with implausible activity
    for t in range(N_TEST_ACCOUNTS):
        d = SIGNUP_START + timedelta(days=rng.randrange(SIGNUP_DAYS))
        users.append(dict(
            user_id=f"u_test_{t:03d}", signup_date=d,
            signup_ts=datetime(d.year, d.month, d.day, 14), channel="direct",
            initial_intent=rng.choice(INTENTS), secondary_intent=None, z=3.5, platform="web",
            country="US", business_stage="existing", power=True, campaign=False,
            drawing_affinity=True, is_test=True))
    return users


# ---------------------------------------------------------------- events
EVENTS: list[list] = []


class Session:
    def __init__(self, user, day_date: date, idx: int, start: datetime | None = None):
        self.user = user
        self.sid = f"s_{user['user_id']}_{(day_date - user['signup_date']).days}_{idx}"
        if start is None:
            hour = rng.triangular(7, 23.5, 19 if is_drawing_day(day_date) and user["drawing_affinity"] else 14)
            start = datetime(day_date.year, day_date.month, day_date.day) + timedelta(hours=hour)
        self.t = start
        self.day = day_date

    def emit(self, name, feature, output_id=None, props=None):
        self.t += timedelta(seconds=int(rng.expovariate(1 / 45)) + 2)
        u = self.user
        EVENTS.append([new_id(), u["user_id"], self.sid, self.t, name, feature,
                       u["initial_intent"], u["platform"], PLATFORM_APP_VERSION[u["platform"]],
                       output_id, json.dumps(props) if props else None])


def attempt(sess: Session, feature: str, p_success: float, context: str | None = None) -> bool:
    """Emit the event chain for one attempt at a feature; return True if an FMO happened."""
    s = rng.random() < p_success
    sess.emit("feature_opened", feature, props={"entry_point": context or "nav"})
    if feature == "funding":
        for _ in range(rng.randint(1, 4)):
            sess.emit("grant_viewed", feature, props={"opportunity_type": choice_w(
                ["grant", "loan", "card"], [.8, .12, .08])})
        if rng.random() < 0.7:
            sess.emit("grant_eligibility_checked", feature)
        if s or rng.random() < 0.35:
            sess.emit("grant_application_started", feature)
            if s:
                sess.emit("grant_application_completed", feature)
    elif feature == "create":
        sess.emit("create_prompt_submitted", feature,
                  props={"artifact_type": choice_w(["image", "video", "blog", "social", "product"],
                                                    [.35, .2, .15, .2, .1])})
        oid = None
        for g in range(1 + (rng.random() < 0.45) + (rng.random() < 0.2)):
            oid = new_id()
            sess.emit("artifact_generated" if g == 0 else "artifact_regenerated", feature, oid)
        if s:
            sess.emit("artifact_saved", feature, oid)
            if rng.random() < 0.45:
                sess.emit("artifact_exported", feature, oid)
    elif feature == "analyze":
        sess.emit("analysis_started", feature, props={"analysis_type": choice_w(
            ["website", "product", "business"], [.6, .2, .2])})
        oid = new_id()
        completed = rng.random() < 0.93 or s
        broken = (sess.user["platform"] == "ios" and TRACKING_BREAK[0] <= sess.day <= TRACKING_BREAK[1])
        if completed and not broken:
            sess.emit("analysis_completed", feature, oid)
        if completed and s:
            sess.emit("analysis_recommendation_clicked", feature, oid)
        return completed and s
    elif feature == "cofounder":
        conv = new_id()
        turns = 1 + (rng.random() < 0.5) + (rng.random() < 0.3) + (3 if s and rng.random() < 0.3 else 0)
        oid = None
        for k in range(turns):
            sess.emit("cofounder_message_sent", feature, props={"conversation_id": conv, "turn_index": k,
                                                                 "context_source": context or "blank"})
            oid = new_id()
            sess.emit("cofounder_response_received", feature, oid, props={"conversation_id": conv})
        if s and turns < 4:
            sess.emit("cofounder_action_executed", feature, oid)
        if rng.random() < 0.15:
            sess.emit("cofounder_response_rated", feature, oid,
                      props={"rating": "up" if rng.random() < (0.75 if s else 0.4) else "down"})
        return s
    elif feature == "website":
        if rng.random() < 0.25:   # business page path
            if s:
                sess.emit("business_page_published", feature)
        else:
            sess.emit("website_created", feature)
            if s:
                sess.emit("website_published", feature)
    elif feature == "business_plan":
        sess.emit("business_plan_started", feature)
        if s:
            sess.emit("business_plan_created", feature)
    return s


def other_feature(u, primary_feature):
    feats = [f for f in FEATURES if f != primary_feature]
    w = []
    for f in feats:
        wt = 1.0
        if u["secondary_intent"] and PRIMARY_FEATURE[u["secondary_intent"]] == f:
            wt = 5.0
        if u["initial_intent"] == "funding" and f in ("website", "business_plan"):
            wt *= 3.0     # grant-amount incentive pulls funding users into these
        w.append(wt)
    return choice_w(feats, w)


def simulate_user(u):
    st = dict(value_features=set(), incentive_value=set(), first_value=None, bridged=False,
              active_days=0, primary_value=False)
    primary = PRIMARY_FEATURE[u["initial_intent"]]
    z = u["z"]
    horizon = (OBS_END - u["signup_date"]).days
    mult = 6 if u["is_test"] else 1

    def run_feature(sess, feature, day_idx, context=None):
        is_primary = feature == primary
        base = FMO_BASE[u["initial_intent"]] if is_primary else -0.5
        if u["initial_intent"] == "funding" and feature in ("website", "business_plan"):
            base += 0.6
        if day_idx > 0:
            base -= 0.2
        ok = attempt(sess, feature, sigmoid(base + 0.8 * z), context)
        if ok:
            if st["first_value"] is None:
                st["first_value"] = day_idx
            if is_primary:
                st["primary_value"] = True
            if u["initial_intent"] == "funding" and feature in ("website", "business_plan"):
                st["incentive_value"].add(feature)
            else:
                st["value_features"].add(feature)
            # Analyze -> Cofounder bridge (self-selected: more likely for high z)
            p_bridge = sigmoid(-2.0 + 0.5 * z)
            if u.get("exp_b") == "treatment":
                p_bridge = max(p_bridge, 0.40)
            if feature == "analyze" and rng.random() < p_bridge:
                run_feature(sess, "cofounder", day_idx, context="from_analysis")
                st["bridged"] = True
        return ok

    # ---- day 0
    day0 = u["signup_date"]
    s0 = Session(u, day0, 0, start=u["signup_ts"])
    s0.t -= timedelta(seconds=30)
    s0.emit("session_started", "account", props={"landing": primary})
    s0.emit("signup_completed", "account", props={"source": u["channel"]})
    if rng.random() < 0.65:
        declared = u["initial_intent"] if rng.random() < 0.88 else rng.choice(INTENTS)
        s0.emit("intent_selected", "account", props={"intent": declared})
    # One-session bouncers: sign up and leave before touching any feature
    bounce = rng.random() < sigmoid(-2.0 - 0.6 * z + (0.8 if u["campaign"] else 0))
    if bounce:
        st["active_days"] = 1
        horizon = horizon if rng.random() < 0.35 else 1   # most never come back
    else:
        run_feature(s0, primary, 0)
    if not bounce and rng.random() < sigmoid(-1.1 + 0.6 * z):        # explorers
        run_feature(s0, other_feature(u, primary), 0)
    extra0 = 0 if bounce else int(rng.random() < sigmoid(-1.4 + 0.7 * z)) + (2 if u["power"] else 0)
    for k in range(extra0):
        s = Session(u, day0, k + 1, start=s0.t + timedelta(minutes=rng.randint(35, 240)))
        if s.t.date() != day0:
            break
        s.emit("session_started", "account")
        run_feature(s, primary if rng.random() < 0.6 else other_feature(u, primary), 0)
    st["active_days"] = 1

    # ---- days 1..horizon
    for d in range(1, horizon):
        day = day0 + timedelta(days=d)
        drawing = is_drawing_day(day) and u["drawing_affinity"]
        ce = CAUSAL_EFFECTS
        logit = (ALPHA[u["initial_intent"]] - DAY_DECAY * math.log1p(d) + PROPENSITY_COEF * z
                 + (ce["value_reached_by_intent"][u["initial_intent"]] if st["first_value"] is not None else 0)
                 + (ce["cross_feature_value"] if len(st["value_features"]) >= 2 else 0)
                 + (ce["analyze_to_cofounder_bridge"] if st["bridged"] else 0)
                 + (ce["drawing_day_boost"] if drawing else 0)
                 + (-0.25 if day.weekday() >= 5 else 0)
                 + (1.0 if u["power"] else 0))
        if rng.random() >= sigmoid(logit) * mult and not (u["is_test"] and rng.random() < 0.5):
            continue
        st["active_days"] += 1
        n_sess = 1 + (rng.random() < 0.25) + (rng.randint(1, 3) if u["power"] else 0)
        for k in range(n_sess):
            s = Session(u, day, k)
            s.emit("session_started", "account")
            if drawing and k == 0 and rng.random() < 0.85:
                s.emit("grant_viewed", "funding", props={"opportunity_type": "instant"})
                s.emit("instant_grant_entered", "funding")
                if st["first_value"] is None:
                    st["first_value"] = d
                    if u["initial_intent"] == "funding":
                        st["primary_value"] = True
                if rng.random() < 0.75:
                    continue        # drawing-only visit
            p_primary = min(0.85, max(0.35, 0.70 - 0.10 * z))
            f = primary if rng.random() < p_primary else other_feature(u, primary)
            run_feature(s, f, d)
    return st


# ---------------------------------------------------------------- subscriptions
PRICES = {("plus", "monthly"): 29.0, ("pro", "monthly"): 99.0,
          ("plus", "yearly"): 29.0 * 12 * 0.6, ("pro", "yearly"): 99.0 * 12 * 0.6}
INTENT_PAY = {"funding": -0.45, "create": 0.50, "analyze": 0.20, "ask": 0.30, "presence": 0.60, "start": 0.10}


def maybe_subscribe(u, st, user_events):
    if u["is_test"]:
        return None
    logit = (-4.0 + 0.7 * u["z"] + (0.9 if st["first_value"] is not None else 0)
             + INTENT_PAY[u["initial_intent"]] + 0.05 * min(st["active_days"], 20))
    if rng.random() >= sigmoid(logit):
        return None
    active_days = sorted({e[3].date() for e in user_events})
    eligible = [d for d in active_days if (d - u["signup_date"]).days <= 45]
    if not eligible:
        return None
    day = eligible[min(int(rng.expovariate(0.6)), len(eligible) - 1)]
    tier = "pro" if rng.random() < (0.35 if u["initial_intent"] in ("presence", "create") else 0.2) else "plus"
    period = "yearly" if rng.random() < 0.2 else "monthly"
    started = datetime(day.year, day.month, day.day) + timedelta(hours=rng.uniform(9, 22))
    refunded = rng.random() < sigmoid(-2.2 - 0.6 * u["z"])
    cancelled_at = None
    if refunded:
        cancelled_at = started + timedelta(days=rng.uniform(1, 13.5))
    elif period == "monthly" and rng.random() < 0.18:
        cancelled_at = started + timedelta(days=rng.uniform(25, 60))
    if cancelled_at and cancelled_at.date() >= OBS_END:
        cancelled_at, refunded = None, False
    trigger = rng.choice([e[5] for e in user_events if e[5] not in ("account",)] or ["account"])
    return dict(subscription_id=new_id(), user_id=u["user_id"], tier=tier, billing_period=period,
                price_usd=round(PRICES[(tier, period)], 2), started_at=started,
                cancelled_at=cancelled_at, refunded=refunded, trigger_feature=trigger)


# ---------------------------------------------------------------- data-quality noise
def add_noise(events):
    out = []
    for e in events:
        ts = e[3]
        lag = timedelta(seconds=rng.randint(1, 20))
        if e[7] != "web" and rng.random() < 0.05:                 # offline mobile queue
            lag = timedelta(minutes=rng.randint(30, 60 * 72))
        received = ts + lag
        sid = e[2]
        if e[7] == "android" and rng.random() < 0.012:            # missing session id
            sid = None
        if e[7] != "web" and rng.random() < 0.003:                # device clock skew
            ts = ts - timedelta(days=1, hours=rng.randint(0, 6))
        row = [e[0], e[1], sid, ts, received] + e[4:]
        out.append(row)
        if rng.random() < 0.005:                                  # retry duplicates
            out.append(list(row))
    return out


def main():
    users = make_users()
    all_events, subs = [], []
    for u in users:
        start = len(EVENTS)
        st = simulate_user(u)
        u_events = [e for e in EVENTS[start:] if e[3].date() < OBS_END]
        del EVENTS[start:]
        sub = maybe_subscribe(u, st, u_events)
        if sub:
            subs.append(sub)
            u_events.append([new_id(), u["user_id"], None, sub["started_at"], "subscription_started",
                             "payments", u["initial_intent"], "server", "server", None,
                             json.dumps({"tier": sub["tier"], "billing_period": sub["billing_period"]})])
            if sub["cancelled_at"]:
                u_events.append([new_id(), u["user_id"], None, sub["cancelled_at"],
                                 "subscription_refunded" if sub["refunded"] else "subscription_cancelled",
                                 "payments", u["initial_intent"], "server", "server", None, None])
            u["tier_now"] = "starter" if sub["cancelled_at"] else sub["tier"]
        else:
            u["tier_now"] = "starter"
        all_events.extend(u_events)

    all_events = add_noise(all_events)
    all_events.sort(key=lambda r: (r[3], r[1]))

    with open(OUT / "users.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["user_id", "signup_ts", "signup_date", "country", "acquisition_channel", "platform",
                    "initial_intent", "business_stage", "subscription_tier", "is_test_account"]
                   + (["experiment_b_variant"] if EXPERIMENT_B == "randomized" else []))
        for u in users:
            w.writerow([u["user_id"], u["signup_ts"].isoformat(sep=" "), u["signup_date"].isoformat(),
                        u["country"], u["channel"], u["platform"], u["initial_intent"],
                        u["business_stage"], u["tier_now"], str(u["is_test"]).lower()]
                       + ([u.get("exp_b") or ""] if EXPERIMENT_B == "randomized" else []))

    with open(OUT / "events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "user_id", "session_id", "event_timestamp", "received_at", "event_name",
                    "feature", "intent", "platform", "app_version", "output_id", "properties"])
        for e in all_events:
            w.writerow([e[0], e[1], e[2] or "", e[3].isoformat(sep=" "), e[4].isoformat(sep=" ")]
                       + [x if x is not None else "" for x in e[5:]])

    with open(OUT / "subscriptions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["subscription_id", "user_id", "tier", "billing_period", "price_usd", "started_at",
                    "cancelled_at", "refunded", "trigger_feature"])
        for s in subs:
            w.writerow([s["subscription_id"], s["user_id"], s["tier"], s["billing_period"], s["price_usd"],
                        s["started_at"].isoformat(sep=" "),
                        s["cancelled_at"].isoformat(sep=" ") if s["cancelled_at"] else "",
                        str(s["refunded"]).lower(), s["trigger_feature"]])

    with open(OUT / "drawing_calendar.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["drawing_date"])
        d = SIGNUP_START
        while d < OBS_END:
            if is_drawing_day(d):
                w.writerow([d.isoformat()])
            d += timedelta(days=1)

    if EXPERIMENT_B != "natural":
        print(f"users={len(users):,} events={len(all_events):,} (experiment world written to {OUT})")
        return
    # Ground truth is kept OUT of data/ so the analysis can't peek at it.
    (ROOT / "scripts" / "ground_truth.json").write_text(json.dumps(
        {"seed": SEED, "causal_effects_logit": CAUSAL_EFFECTS,
         "note": "Synthetic ground truth. Used only to check whether the analysis recovers it."}, indent=2))
    print(f"users={len(users):,} events={len(all_events):,} subscriptions={len(subs):,}")


if __name__ == "__main__":
    main()
