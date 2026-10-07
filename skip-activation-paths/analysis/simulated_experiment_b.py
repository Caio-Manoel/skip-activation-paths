"""
Simulated Experiment B (Analyze -> Cofounder bridge) inside the synthetic world.

SYNTHETIC DATA — methodology demo, not Skip performance.

Why this exists: the observational analysis shows a very large retention gap between
Analyze users who continue into Cofounder and those who don't. Because the synthetic
world has a known ground truth, we can run the experiment we would propose at Skip and
see how far the observational estimate was from the causal one.

Steps:
 1. Regenerate the synthetic world with EXPERIMENT_B=randomized (50/50 per user).
 2. Intent-to-treat: compare D30 value retention for all users who completed an
    analysis action, by assigned variant.
 3. Inside the control arm only, compute the naive observational estimate
    (bridged vs not bridged) for comparison.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import product_analysis  # noqa: E402
from product_analysis import boot_diff, two_prop  # noqa: E402

product_analysis.RNG = np.random.default_rng(11)  # fixed seed so bootstrap CIs are reproducible

WORLD = Path(os.environ.get("EXP_DIR", ROOT / "analysis" / ".exp_b_world"))


def main():
    if not (WORLD / "events.csv").exists():
        env = dict(os.environ, EXPERIMENT_B="randomized", OUT_DIR=str(WORLD))
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_synthetic_data.py")], env=env, check=True)
    c = duckdb.connect()
    c.execute(f"create view e as select * from read_csv_auto('{WORLD / 'events.csv'}')")
    c.execute(f"create view u as select * from read_csv_auto('{WORLD / 'users.csv'}') where not is_test_account")
    df = c.sql("""
        with ev as (
          select e.user_id, u.experiment_b_variant v, u.signup_date,
                 date_diff('day', u.signup_date, cast(e.event_timestamp as date)) dn, e.event_name, e.properties
          from e join u using (user_id))
        select user_id, any_value(v) v,
          max(case when event_name='analysis_recommendation_clicked' then 1 else 0 end) eligible,
          max(case when event_name='cofounder_message_sent' and properties like '%from_analysis%' then 1 else 0 end) bridged,
          max(case when dn between 28 and 34 and event_name in ('grant_application_completed','artifact_saved',
              'artifact_exported','analysis_recommendation_clicked','cofounder_action_executed','website_published',
              'business_page_published','business_plan_created') then 1 else 0 end) d30_value,
          any_value(signup_date) signup_date
        from ev group by 1""").df()
    df = df.sort_values("user_id").reset_index(drop=True)  # deterministic row order for the bootstrap
    df = df[(df.eligible == 1) & (df.signup_date <= np.datetime64("2026-07-26"))]
    t, ctl = df[df.v == "treatment"], df[df.v == "control"]
    lo, hi = boot_diff(t.d30_value.values, ctl.d30_value.values)
    p, h = two_prop(t.d30_value.values, ctl.d30_value.values)
    obs_lo, obs_hi = boot_diff(ctl[ctl.bridged == 1].d30_value.values, ctl[ctl.bridged == 0].d30_value.values)
    res = dict(
        eligible_users=int(len(df)), n_treatment=int(len(t)), n_control=int(len(ctl)),
        uptake_treatment=round(float(t.bridged.mean()), 4), uptake_control=round(float(ctl.bridged.mean()), 4),
        d30_value_treatment=round(float(t.d30_value.mean()), 4), d30_value_control=round(float(ctl.d30_value.mean()), 4),
        itt_diff=round(float(t.d30_value.mean() - ctl.d30_value.mean()), 4), itt_ci95=[round(lo, 4), round(hi, 4)],
        itt_p_value=p,
        # Wald / CACE estimate: effect per additional user who actually bridged
        cace=round(float((t.d30_value.mean() - ctl.d30_value.mean()) / (t.bridged.mean() - ctl.bridged.mean())), 4),
        naive_observational_in_control=round(float(ctl[ctl.bridged == 1].d30_value.mean()
                                                   - ctl[ctl.bridged == 0].d30_value.mean()), 4),
        naive_ci95=[round(obs_lo, 4), round(obs_hi, 4)],
    )
    out = ROOT / "analysis" / "results" / "simulated_experiment_b.json"
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
