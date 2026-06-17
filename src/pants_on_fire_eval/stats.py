"""Phase 1 statistical toolkit — sample-size planning and defensible inference.

The Phase 1 ablation has two distinct sample-size problems (the proposal's
two-pass allocation), with different logic — conflating them is the trap:

  1. The AS-vs-GP aligned-rate *comparison* -> a power analysis on proportions,
     accounting for item x epoch clustering (the design effect). Sets the
     screening-pass items-per-variant.
  2. Populating the rare outcome buckets (strong_covert; Phase 2 implicit_covert)
     -> precision / event-count sizing, not power. Sets the top-up-pass N.

Plus the analysis-time companions:
  - item-clustered CIs (the unit is the *item*, not the item x epoch observation),
  - Wilson intervals for rare rates and rule-of-three upper bounds for 0-event cells,
  - an ICC estimator so the design effect uses a *measured* pilot ICC, not a guess,
  - Holm correction for the pre-specified family of variant contrasts.

Dependency-light: numpy + stdlib. Self-checks: python src/pants_on_fire_eval/stats.py
"""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np

_NORM = NormalDist()


def _z(p: float) -> float:
    return _NORM.inv_cdf(p)


# --- clustering / design effect -------------------------------------------

def design_effect(epochs: int, icc: float) -> float:
    """DEFF = 1 + (m-1)*ICC for m epochs/item. ICC=0 -> epochs independent;
    ICC=1 -> epochs add no independent information (the item is the unit)."""
    return 1.0 + (epochs - 1) * icc


# --- sample size: the comparison (power) ----------------------------------

def n_eff_two_proportions(p1: float, p2: float, alpha: float = 0.05,
                          power: float = 0.80) -> float:
    """Independent observations per group to detect p1 vs p2 (two-sided test)."""
    if p1 == p2:
        raise ValueError("p1 and p2 must differ")
    pbar = (p1 + p2) / 2
    za, zb = _z(1 - alpha / 2), _z(power)
    num = (za * math.sqrt(2 * pbar * (1 - pbar))
           + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return num / (p1 - p2) ** 2


def items_per_variant(p1: float, p2: float, epochs: int, icc: float,
                      alpha: float = 0.05, power: float = 0.80) -> int:
    """Items per variant for the aligned-rate comparison, with clustering folded in."""
    n_eff = n_eff_two_proportions(p1, p2, alpha, power)
    return math.ceil(n_eff * design_effect(epochs, icc) / epochs)


def mde_two_proportions(n_items: int, p_baseline: float, epochs: int, icc: float,
                        alpha: float = 0.05, power: float = 0.80) -> float:
    """Minimal detectable difference (proportion) for the items you can afford."""
    n_eff = n_items * epochs / design_effect(epochs, icc)
    return (_z(1 - alpha / 2) + _z(power)) * math.sqrt(
        2 * p_baseline * (1 - p_baseline) / n_eff)


# --- sample size: the rare buckets (precision / events) -------------------

def n_for_events(rate: float, target_events: int) -> int:
    """COMPLETE samples needed to expect `target_events` at the given rate."""
    return math.ceil(target_events / rate)


def rule_of_three_upper(n: int, conf: float = 0.95) -> float:
    """Upper bound on a rate when 0 events are seen in n trials (~3/n at 95%)."""
    return 1.0 - (1.0 - conf) ** (1.0 / n)


# --- inference: CIs for proportions ---------------------------------------

def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval — correct for small n and rare rates (where the
    normal approximation fails)."""
    if n == 0:
        return (0.0, 1.0)
    z = _z(1 - alpha / 2)
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def cluster_bootstrap_ci(item_rates, alpha: float = 0.05, n_boot: int = 5000,
                         seed: int = 0) -> tuple[float, float]:
    """Item-clustered CI on a variant's aligned-rate: resample ITEMS (the cluster
    unit) with replacement, recompute the mean. `item_rates`: per-item rates."""
    item_rates = np.asarray(item_rates, dtype=float)
    n = len(item_rates)
    rng = np.random.default_rng(seed)
    means = item_rates[rng.integers(0, n, size=(n_boot, n))].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return (float(lo), float(hi))


# --- ICC from pilot data (feeds the design effect) ------------------------

def estimate_icc(item_outcomes) -> float:
    """One-way random-effects ICC(1) from clustered binary outcomes.
    `item_outcomes`: 2D array (n_items, epochs) of 0/1. Lets the design effect
    use a measured pilot ICC rather than a guess."""
    x = np.asarray(item_outcomes, dtype=float)
    n_items, m = x.shape
    grand = x.mean()
    item_means = x.mean(axis=1)
    ms_between = m * np.sum((item_means - grand) ** 2) / (n_items - 1)
    ms_within = np.sum((x - item_means[:, None]) ** 2) / (n_items * (m - 1))
    icc = (ms_between - ms_within) / (ms_between + (m - 1) * ms_within)
    return float(max(0.0, min(1.0, icc)))


# --- multiple comparisons -------------------------------------------------

def holm(pvals) -> list[float]:
    """Holm-Bonferroni step-down adjusted p-values for the pre-specified family."""
    p = list(pvals)
    m = len(p)
    order = sorted(range(m), key=lambda i: p[i])
    adj = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[idx]))
        adj[idx] = running
    return adj


# --- self-checks + an example plan ----------------------------------------

def _self_check() -> None:
    assert design_effect(5, 0.0) == 1.0 and design_effect(5, 1.0) == 5.0
    assert abs(n_eff_two_proportions(0.5, 0.65) - 169.0) < 2.0
    assert wilson_ci(0, 0) == (0.0, 1.0)
    lo, hi = wilson_ci(50, 100)
    assert lo < 0.5 < hi
    assert abs(rule_of_three_upper(100) - 0.0295) < 1e-3
    assert n_for_events(0.05, 40) == 800
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    high_icc = np.repeat([[0], [1]], 5, axis=1)          # each item constant across epochs
    assert estimate_icc(high_icc) > 0.95
    rng = np.random.default_rng(0)
    low_icc = rng.integers(0, 2, size=(40, 5))           # independent across epochs
    assert estimate_icc(low_icc) < 0.2
    print("  all statistical self-checks passed")


def _demo_plan() -> None:
    p_gp, p_as = 0.45, 0.30            # illustrative cheating-rates (set from Stage 0)
    diff, epochs, icc = p_gp - p_as, 5, 0.30
    n_eff = n_eff_two_proportions(p_gp, p_as)
    deff = design_effect(epochs, icc)
    items = items_per_variant(p_gp, p_as, epochs, icc)
    print("\nPhase 1 sample-size plan (illustrative inputs):")
    print(f"  primary contrast gp_only {p_gp:.2f} vs as_only {p_as:.2f} (diff {diff:.2f}):")
    print(f"    independent obs/group needed:       {n_eff:.0f}")
    print(f"    design effect ({epochs} epochs, ICC={icc:.2f}):     {deff:.2f}")
    print(f"    -> items per variant:               {items}  (x{epochs} epochs)")
    print(f"  minimal detectable diff at 50 items:  "
          f"{mde_two_proportions(50, p_gp, epochs, icc):.3f}")
    print(f"  rare-rate cell (near-floor cheating ~0.05, target 40 events):")
    print(f"    samples needed:                     {n_for_events(0.05, 40)}")
    print(f"    0 events in 200 -> 95% upper bound: {rule_of_three_upper(200):.4f}")


if __name__ == "__main__":
    print("Phase 1 statistics toolkit:")
    _self_check()
    _demo_plan()
    print("\nall checks passed")
