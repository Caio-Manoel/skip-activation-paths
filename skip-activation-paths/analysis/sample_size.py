"""
Sample size per arm for a two-proportion test (fixed horizon).

Usage:  python analysis/sample_size.py                 # the three experiments in docs/experiments.md
        python analysis/sample_size.py 0.30 0.02       # baseline, absolute MDE
Baselines in docs/experiments.md are illustrative placeholders, not Skip numbers.
"""
import math
import sys

from scipy.stats import norm


def n_per_arm(p1: float, mde: float, alpha: float = 0.05, power: float = 0.80) -> int:
    p2 = p1 + mde
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    return math.ceil((za + zb) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / mde ** 2)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        print(n_per_arm(float(sys.argv[1]), float(sys.argv[2])))
    else:
        for name, p, d in [("A: intent-aware onboarding (activation)", 0.30, 0.02),
                           ("B: Analyze → Cofounder bridge (follow-up action)", 0.20, 0.03),
                           ("C: first-value recovery (FMO within 7d)", 0.15, 0.03)]:
            print(f"{name:52s} baseline={p:.0%}  MDE=+{d*100:.0f}pp  →  {n_per_arm(p, d):,} per arm")
