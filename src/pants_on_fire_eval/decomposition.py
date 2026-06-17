"""Decomposition figures: cheating rate by safety-spec variant and model.

Reads ImpossibleBench-style .eval logs (a single pass/cheat scorer, where a
CORRECT score == the model passed a test that contradicts the spec == cheated)
and renders the two slide figures for the AS-vs-GP decomposition:

  fig 1  grouped bars: cheating rate by variant, grouped by model, Wilson 95% CI
  fig 2  forest: the paired within-task contrasts with 95% CIs and a 0 reference
           - GP - AS within each model    (H1: does anti-deception suppress
                                            cheating more than process/effort?)
           - high-cap - low-cap, no_spec  (does cheating rise with capability?)

Each (model, variant) cell is identified from the log's task_args['variant_key']
when present, else by matching the injected system message against task.VARIANTS
(the preliminary runs inject the variant as a system_message rather than via the
`condition()` task, so they carry no variant_key). Per-cell outcomes are matched
by sample id, so the contrasts are *paired* (each item is its own control).

Read-only over logs — no API calls. The statistics live in stats.py (wilson_ci,
paired_diff_ci); this module is the log -> cells -> figures glue.

Run:
    python -m pants_on_fire_eval.decomposition --log-dir <dir> [--out <dir>]
    python -m pants_on_fire_eval.decomposition <log.eval> ... --out <dir>

`--out` defaults to <log-dir>/figures, so figures land beside the logs they
describe (and inherit logs/ being git-ignored).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from inspect_ai.log import read_eval_log
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter

from .stats import PairedDiff, paired_diff_ci, wilson_ci
from .task import VARIANTS

# Canonical display labels, ordered low -> high spec content. The preliminary
# run injects the no-spec baseline under the "high_pressure" key.
CANON_ORDER = ["no_spec", "as_only", "gp_only"]
_TO_CANON = {
    "high_pressure": "no_spec", "no_spec": "no_spec",
    "as_only": "as_only", "gp_only": "gp_only",
}
# Rough capability ordering for the x-axis (left = lower). Unknown models sort last.
_MODEL_RANK = {"openai/o4-mini": 0, "openai/o3-mini": 1, "openai/o3": 2}
# Colour-blind-safe (Wong). no_spec grey (baseline), as_only blue, gp_only vermillion.
_PALETTE = {"no_spec": "#999999", "as_only": "#0072B2", "gp_only": "#D55E00"}
_H1_COLOR = "#0072B2"          # GP - AS contrasts
_CAP_COLOR = "#009E73"         # capability contrast (Wong green)


def _model_short(m: str) -> str:
    return m.split("/")[-1]


def _cheat(sample) -> int | None:
    """1 if the sample cheated (scorer CORRECT == passed an impossible test),
    0 if not, None if the sample carries no score (errored / incomplete)."""
    scores = sample.scores or {}
    if not scores:
        return None
    val = next(iter(scores.values())).value
    return 1 if (str(val).upper().startswith("C") or val in (1, 1.0, True)) else 0


def _variant_of(log) -> str | None:
    """Identify the variant cell: prefer task_args['variant_key']; else match the
    injected system message against VARIANTS (longest match wins, so a baseline
    prompt nested inside a spec prompt resolves to the spec)."""
    key = (log.eval.task_args or {}).get("variant_key")
    if key in _TO_CANON:
        return _TO_CANON[key]
    cands = [(_TO_CANON[k], VARIANTS[k].strip()) for k in _TO_CANON if k in VARIANTS]
    for s in (log.samples or [])[:5]:
        sys_text = "\n".join(
            (m.text or "") for m in (s.messages or [])
            if getattr(m, "role", None) == "system"
        )
        hits = [(lbl, txt) for lbl, txt in cands if txt and txt in sys_text]
        if hits:
            return max(hits, key=lambda lt: len(lt[1]))[0]
    return None


def collect_cells(paths) -> tuple[dict, dict]:
    """Map (model, variant) -> {sample_id: 0/1}. When several logs map to the
    same cell (e.g. a 3-item smoke and the full run), keep the one with the most
    scored samples."""
    cells: dict = {}
    src: dict = {}
    for path in paths:
        log = read_eval_log(path)
        if not (log.samples or []):
            continue
        variant = _variant_of(log)
        if variant is None:
            print(f"  (skipped {os.path.basename(path)}: no variant identified)")
            continue
        outcomes = {}
        for s in log.samples:
            c = _cheat(s)
            if c is not None:
                outcomes[str(s.id)] = c
        if not outcomes:
            continue
        key = (log.eval.model, variant)
        if key not in cells or len(outcomes) > len(cells[key]):
            cells[key] = outcomes
            src[key] = os.path.basename(path)
    return cells, src


def _paired(cell_a: dict, cell_b: dict) -> PairedDiff:
    """paired_diff_ci over the intersection of sample ids (Δ = rate_b - rate_a)."""
    ids = sorted(set(cell_a) & set(cell_b))
    return paired_diff_ci([cell_a[i] for i in ids], [cell_b[i] for i in ids])


def build_stats(cells: dict):
    models = sorted({m for (m, _) in cells}, key=lambda m: (_MODEL_RANK.get(m, 99), m))
    variants = [v for v in CANON_ORDER if any((m, v) in cells for m in models)]
    cell_stats = {}
    for (m, v), o in cells.items():
        k, n = sum(o.values()), len(o)
        lo, hi = wilson_ci(k, n)
        cell_stats[(m, v)] = {"cheats": k, "n": n, "rate": k / n, "lo": lo, "hi": hi}
    # H1: GP - AS within each model
    within = {}
    for m in models:
        if cells.get((m, "as_only")) and cells.get((m, "gp_only")):
            within[m] = _paired(cells[(m, "as_only")], cells[(m, "gp_only")])
    # capability: highest - lowest model, per variant
    across = {}
    if len(models) >= 2:
        lo_m, hi_m = models[0], models[-1]
        for v in variants:
            if cells.get((lo_m, v)) and cells.get((hi_m, v)):
                across[v] = _paired(cells[(lo_m, v)], cells[(hi_m, v)])
    return models, variants, cell_stats, within, across


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

_SUB = ("Impossible-LiveCodeBench (conflicting split) · minimal agent · "
        "1 epoch · directional pilot, not powered")


def _draw_rates(ax, models, variants, cell_stats) -> None:
    x = np.arange(len(models))
    w = 0.8 / max(len(variants), 1)
    for i, v in enumerate(variants):
        offs = x + (i - (len(variants) - 1) / 2) * w
        rates, lo_err, hi_err = [], [], []
        for m in models:
            st = cell_stats.get((m, v))
            r = st["rate"] if st else 0.0
            rates.append(r)
            lo_err.append(r - st["lo"] if st else 0.0)
            hi_err.append(st["hi"] - r if st else 0.0)
        ax.bar(offs, rates, w, yerr=[lo_err, hi_err], capsize=4,
               color=_PALETTE.get(v, "#777777"), label=v, edgecolor="white")
        for xi, r, he, m in zip(offs, rates, hi_err, models):
            st = cell_stats.get((m, v))
            if st:
                ax.text(xi, r + he + 0.02, f"{r:.0%}", ha="center", va="bottom",
                        fontsize=8.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([_model_short(m) for m in models])
    ax.set_xlabel("model  (left → right: lower → higher capability)")
    ax.set_ylabel("cheating rate  (passed an impossible test)")
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    # horizontal legend in the empty top band (tallest bar + CI tops out ~87%)
    ax.legend(fontsize=9, loc="upper center", ncol=len(variants), frameon=False)
    ax.spines[["top", "right"]].set_visible(False)


def _forest_rows(within, across, models):
    """Ordered (label, PairedDiff, color, is_separator_before) rows, top -> bottom:
    the H1 spec contrasts first, then the capability contrast under each variant."""
    rows = []
    for m in reversed(models):                       # higher-capability model on top
        if m in within:
            rows.append((f"GP − AS   ({_model_short(m)})", within[m], _H1_COLOR, False))
    first_cap = True
    if len(models) >= 2:
        hi_lo = f"{_model_short(models[-1])} − {_model_short(models[0])}"
        for v in CANON_ORDER:
            if v in across:
                rows.append((f"{hi_lo}   ({v})", across[v], _CAP_COLOR, first_cap))
                first_cap = False
    return rows


def _draw_forest(ax, rows) -> None:
    ys = list(range(len(rows)))[::-1]                # row 0 at top
    pad = 6.0
    extent = max((max(abs(pd.lo), abs(pd.hi)) for _, pd, _, _ in rows), default=0.2) * 100
    for y, (label, pd, color, sep) in zip(ys, rows):
        xerr = [[(pd.delta - pd.lo) * 100], [(pd.hi - pd.delta) * 100]]
        ax.errorbar(pd.delta * 100, y, xerr=xerr, fmt="o", color=color,
                    capsize=5, markersize=8, elinewidth=2, capthick=2)
        ax.text(extent + pad, y,
                f"{pd.delta * 100:+.0f}pp  [{pd.lo * 100:+.0f}, {pd.hi * 100:+.0f}]"
                f"   p={pd.mcnemar_p:.2f}",
                va="center", ha="left", fontsize=8.5, family="monospace")
        if sep:                                       # divider above the capability row
            ax.axhline(y + 0.5, color="#cccccc", lw=0.8, ls="-")
    ax.axvline(0, ls="--", color="#888888", lw=1.2)
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(-extent - pad, extent + pad + 26)     # right margin for annotations
    ax.set_xlabel("Δ cheating rate  (percentage points, paired within-task)")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)


def plot_rates(models, variants, cell_stats, out_path, footnote="", show=False):
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    _draw_rates(ax, models, variants, cell_stats)
    fig.suptitle("Cheating rate by safety-spec variant and model",
                 fontsize=13, y=0.98)
    ax.set_title(_SUB + " · Wilson 95% CI", fontsize=8.5, color="#555555")
    if footnote:
        fig.text(0.5, 0.005, footnote, ha="center", fontsize=7.5, color="#777777")
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    fig.savefig(out_path, dpi=150)
    plt.show() if show else plt.close(fig)


def plot_forest(within, across, models, out_path, show=False):
    rows = _forest_rows(within, across, models)
    fig, ax = plt.subplots(figsize=(9.0, max(2.8, 0.82 * len(rows) + 2.0)))
    _draw_forest(ax, rows)
    ax.text(0.015, 0.99, "Δ > 0  ⟹  more cheating in the first-named condition",
            transform=ax.transAxes, fontsize=8, color="#555555", va="top")
    handles = [
        Line2D([0], [0], marker="o", color=_H1_COLOR, lw=2, label="spec contrast: GP − AS"),
        Line2D([0], [0], marker="o", color=_CAP_COLOR, lw=2,
               label=f"capability: {_model_short(models[-1])} − {_model_short(models[0])}"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, frameon=False)
    fig.suptitle("Paired within-task contrasts (95% CI)", fontsize=13, y=0.99)
    ax.set_title("Impossible-LiveCodeBench (conflicting) · 1 epoch · "
                 "Newcombe 95% CI · exact McNemar p · directional pilot",
                 fontsize=8.5, color="#555555")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    fig.savefig(out_path, dpi=150)
    plt.show() if show else plt.close(fig)


# ---------------------------------------------------------------------------
# Reporting + driver
# ---------------------------------------------------------------------------

def _print_tables(models, variants, cell_stats, within, across) -> None:
    print("\n=== cheating rate per cell (Wilson 95% CI) ===")
    print(f"{'model':14}{'variant':10}{'cheat/n':>10}{'rate':>8}{'   95% CI':>18}")
    for m in models:
        for v in variants:
            st = cell_stats.get((m, v))
            if st:
                print(f"{_model_short(m):14}{v:10}{f'{st['cheats']}/{st['n']}':>10}"
                      f"{st['rate']:>8.1%}   [{st['lo']:>5.1%}, {st['hi']:>5.1%}]")
    print("\n=== H1  paired Δ = c(gp_only) − c(as_only)   "
          "[Δ>0 ⟹ AS suppresses more]  (Newcombe 95% CI, exact McNemar p) ===")
    for m in models:
        pd = within.get(m)
        if pd:
            print(f"{_model_short(m):14} n={pd.n:3d}  Δ={pd.delta:+.1%}  "
                  f"95% CI [{pd.lo:+.1%}, {pd.hi:+.1%}]  "
                  f"discordant b(AS-only)={pd.b} c(GP-only)={pd.c}  "
                  f"McNemar p={pd.mcnemar_p:.3f}")
    print("\n=== capability  paired Δ = c(high-cap) − c(low-cap), per variant   "
          "(Newcombe 95% CI, exact McNemar p) ===")
    for v in variants:
        pd = across.get(v)
        if pd:
            print(f"{v:14} n={pd.n:3d}  Δ={pd.delta:+.1%}  "
                  f"95% CI [{pd.lo:+.1%}, {pd.hi:+.1%}]  McNemar p={pd.mcnemar_p:.3f}")


def _compare_methods(cells, models, variants) -> None:
    """Side-by-side Wald vs Newcombe (Wilson-based) for every paired contrast —
    shows whether the textbook Wald interval misbehaves on this data."""
    print("\n=== paired-CI method check: Wald (McNemar) vs Newcombe (Wilson-based) ===")
    print(f"{'contrast':22}{'Δ':>7}{'Wald 95% CI':>20}{'Newcombe 95% CI':>20}")

    def row(name, ca, cb):
        ids = sorted(set(ca) & set(cb))
        x, y = [ca[i] for i in ids], [cb[i] for i in ids]
        w = paired_diff_ci(x, y, method="wald")
        nc = paired_diff_ci(x, y, method="newcombe")
        print(f"{name:22}{w.delta:>+7.1%}  [{w.lo:>+6.1%},{w.hi:>+6.1%}]"
              f"  [{nc.lo:>+6.1%},{nc.hi:>+6.1%}]")

    for m in models:
        if cells.get((m, "as_only")) and cells.get((m, "gp_only")):
            row(f"GP−AS ({_model_short(m)})", cells[(m, "as_only")], cells[(m, "gp_only")])
    if len(models) >= 2:
        lo_m, hi_m = models[0], models[-1]
        for v in variants:
            if cells.get((lo_m, v)) and cells.get((hi_m, v)):
                row(f"{_model_short(hi_m)}−{_model_short(lo_m)} ({v})",
                    cells[(lo_m, v)], cells[(hi_m, v)])


def _dump_json(path, models, variants, cell_stats, within, across, src) -> None:
    def pd_dict(pd: PairedDiff) -> dict:
        return {**pd._asdict()}
    payload = {
        "ci_method": "cells: Wilson; paired diff: Newcombe (Wilson-based, 1998); "
                     "McNemar: exact binomial",
        "cells": {f"{m}|{v}": {**cell_stats[(m, v)], "src": src.get((m, v))}
                  for (m, v) in cell_stats},
        "h1_gp_minus_as": {_model_short(m): pd_dict(within[m]) for m in within},
        "capability_high_minus_low": {v: pd_dict(across[v]) for v in across},
        "models": models, "variants": variants,
    }
    Path(path).write_text(json.dumps(payload, indent=2))


def make_figures(paths, out_dir) -> None:
    cells, src = collect_cells(paths)
    if not cells:
        print("no usable cells found in the given logs")
        return
    models, variants, cell_stats, within, across = build_stats(cells)
    _print_tables(models, variants, cell_stats, within, across)
    _compare_methods(cells, models, variants)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # footnote: flag any cell whose N differs from the modal N (e.g. truncated runs)
    ns = [st["n"] for st in cell_stats.values()]
    modal_n = max(set(ns), key=ns.count)
    odd = [f"{_model_short(m)}/{v}: {cell_stats[(m, v)]['n']}"
           for (m, v) in cell_stats if cell_stats[(m, v)]["n"] != modal_n]
    foot = f"N = {modal_n} items per cell" + (f"  (exceptions: {', '.join(odd)})" if odd else "")

    plot_rates(models, variants, cell_stats, out / "fig1_cheating_rates.png", footnote=foot)
    plot_forest(within, across, models, out / "fig2_paired_contrasts.png")
    _dump_json(out / "decomposition_stats.json", models, variants,
               cell_stats, within, across, src)
    print(f"\nwrote figures + decomposition_stats.json to {out}/")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(
        prog="pants_on_fire_eval.decomposition",
        description="Cheating-rate decomposition figures from .eval logs (no API).",
    )
    p.add_argument("logs", nargs="*", help="Specific .eval files (else use --log-dir).")
    p.add_argument("--log-dir", type=str, help="Directory of .eval logs to scan.")
    p.add_argument("--out", type=str, help="Output dir (default: <log-dir>/figures).")
    args = p.parse_args(argv)

    paths = list(args.logs)
    if args.log_dir:
        paths += sorted(glob.glob(os.path.join(args.log_dir, "*.eval")))
    if not paths:
        p.error("provide log files or --log-dir")
    out_dir = args.out or (
        os.path.join(args.log_dir, "figures") if args.log_dir
        else os.path.join(os.path.dirname(paths[0]) or ".", "figures")
    )
    make_figures(paths, out_dir)


if __name__ == "__main__":
    main()
