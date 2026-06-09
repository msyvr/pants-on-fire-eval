"""Estimate the item-level ICC from pilot .eval logs.

The power analysis (stats.py) needs the intra-class correlation — how alike the
epochs of one item are — to set the design effect. This reads the inspect logs of
a run with >= 2 epochs, builds the per-item x per-epoch aligned/not matrix
(impossible items only; calibration excluded), and runs `estimate_icc`. It
confirms (or corrects) the ~0.68 figure backed out of the pilot's clustered stderr.

Run:  python -m pants_on_fire_eval.extract_icc            # scans logs/*.eval
      python -m pants_on_fire_eval.extract_icc <log> ...  # specific logs
"""
from __future__ import annotations

import glob
import sys
from collections import defaultdict

import numpy as np
from inspect_ai.log import read_eval_log

from .stats import design_effect, estimate_icc


def _aligned(sample) -> int:
    sc = (sample.scores or {}).get("status_claim_scorer")
    return 1 if (sc is not None and sc.value == "C") else 0   # CORRECT == aligned


def icc_for_log(path: str):
    log = read_eval_log(path)
    variant = (log.eval.task_args or {}).get("variant_key", "?")
    by_item: dict = defaultdict(dict)
    for s in log.samples or []:
        md = s.metadata or {}
        if md.get("category") == "calibration_possible":
            continue
        by_item[md.get("item_id", s.id)][s.epoch] = _aligned(s)
    if not by_item:
        return variant, None, 0, 0
    m = max(len(v) for v in by_item.values())
    rows = [[v[e] for e in sorted(v)] for v in by_item.values() if len(v) == m]
    if m < 2 or len(rows) < 3:
        return variant, None, len(rows), m
    return variant, estimate_icc(np.array(rows)), len(rows), m


def main(paths) -> None:
    print(f"{'variant':>16} {'ICC':>7} {'items':>6} {'epochs':>7}  DEFF@5ep")
    iccs = []
    for p in paths:
        try:
            variant, icc, n, m = icc_for_log(p)
        except Exception as e:  # a malformed/partial log shouldn't stop the scan
            print(f"  (skipped {p.split('/')[-1]}: {e})")
            continue
        if icc is None:
            continue
        iccs.append(icc)
        print(f"{variant:>16} {icc:7.3f} {n:6d} {m:7d}     {design_effect(5, icc):.2f}")
    if iccs:
        pooled = float(np.mean(iccs))
        print(f"\n  mean ICC across {len(iccs)} qualifying log(s): {pooled:.3f}"
              f"   -> design effect at 5 epochs: {design_effect(5, pooled):.2f}")
    else:
        print("\n  no logs with >= 2 epochs and >= 3 impossible items found.")


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(glob.glob("logs/*.eval")))
