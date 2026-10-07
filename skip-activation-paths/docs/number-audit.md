# Number audit

Every number in [EXECUTIVE_SUMMARY.md](../EXECUTIVE_SUMMARY.md), [CASE_STUDY.md](../CASE_STUDY.md) and the dashboard's fixed copy is checked against the generated outputs by [`scripts/audit_numbers.py`](../scripts/audit_numbers.py):

```bash
python scripts/audit_numbers.py     # prints each claim, its documented value and the recomputed value
```

Current status: **53 / 53 claims reproduce.**

How the sources fit together:

| Claim type | Source |
|---|---|
| Activation, retention, conversion, cohort and channel figures | `analysis/results/results.json` (built from the views in `sql/`) |
| Analyze → Cofounder randomized results | `analysis/results/simulated_experiment_b.json` |
| Funding path and drawing-day figures | `analysis/sql_results/06_cross_feature_adoption__03.csv` and `__04.csv` |
| Sample size | `analysis/sample_size.py` |
| Dashboard numbers | computed live from `dashboard/data.js`, which is generated from the same `results.json` |

Label conventions used in the founder-facing documents:

- **Public observation** — visible on helloskip.com, with source URLs in [product-map.md](product-map.md).
- **Simulation · observational** — a comparison between groups of simulated users.
- **Simulation · randomized experiment** — from the simulated world where the Analyze → Cofounder offer was randomly assigned.
- **Real-data test** — what I would check with Skip's data; no result is claimed.

All numbers are synthetic. They describe the simulation and make no claim about Skip's users or performance.
