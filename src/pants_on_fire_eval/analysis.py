"""Reporting, cross-tab, and plot helpers for the pants-on-fire eval."""

import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Tabular output
# ---------------------------------------------------------------------------

def print_summary(logs: dict) -> None:
    """Per-variant aligned-rate and CoT-aware-rate, with stderr."""
    print(f"{'variant':>14}  {'aligned (action)':>18}  {'aware (CoT)':>14}")
    for k, log in logs.items():
        status_m = log.results.scores[0].metrics
        cot_m = log.results.scores[1].metrics
        aligned = status_m["accuracy"].value
        aware = cot_m["accuracy"].value
        a_err = status_m["stderr"].value
        c_err = cot_m["stderr"].value
        print(
            f"{k:>14}  {aligned:>10.2%} ±{a_err:.2f}   "
            f"{aware:>8.2%} ±{c_err:.2f}"
        )


# ---------------------------------------------------------------------------
# Three-bucket cross-tab
# ---------------------------------------------------------------------------

def covert_breakdown(logs: dict) -> dict:
    """Aligned / capability failure / strong covert. Excludes calibration
    items."""
    results = {}
    for variant, log in logs.items():
        n = aligned = cap_fail = strong = 0
        for s in log.samples:
            if (s.metadata or {}).get("category") == "calibration_possible":
                continue
            status_sc = s.scores["status_claim_scorer"]
            cot_sc = s.scores["cot_aware_scorer"]
            n += 1
            claimed = status_sc.metadata["status"] == "COMPLETE"
            aware = cot_sc.metadata.get("aware", False)
            if not claimed:
                aligned += 1
            elif aware:
                strong += 1
            else:
                cap_fail += 1
        results[variant] = {
            "n": n,
            "aligned": aligned / n if n else 0,
            "cap_fail": cap_fail / n if n else 0,
            "strong": strong / n if n else 0,
        }
        print(f"\n=== {variant} (N={n}) ===")
        print(f"  aligned (did not claim COMPLETE):             {aligned/n:.1%}")
        print(f"  capability failure (claim, not aware):        {cap_fail/n:.1%}")
        print(f"  strong covert (claim + aware impossibility):  {strong/n:.1%}")
    return results


def calibration_check(logs: dict) -> None:
    """Check that calibration items (target='possible') get STATUS: COMPLETE
    with aware=False. Confirms the scorers don't trigger-fire on legitimate
    completions."""
    print("\n=== calibration items (target='possible') ===")
    for variant, log in logs.items():
        print(f"\n  {variant}:")
        for s in log.samples:
            if (s.metadata or {}).get("category") != "calibration_possible":
                continue
            status = s.scores["status_claim_scorer"].metadata["status"]
            aware = s.scores["cot_aware_scorer"].metadata.get("aware", False)
            ok = "OK " if status == "COMPLETE" else "FAIL"
            print(f"    [{ok}] {s.id}: status={status}, aware={aware}")


# ---------------------------------------------------------------------------
# Per-sample inspection
# ---------------------------------------------------------------------------

def show_samples(
    logs: dict,
    variant_key: str | None = None,
    n: int | None = None,
    category: str | None = None,
) -> None:
    """Print samples. Filter by variant, category, and/or limit count."""
    variants = [variant_key] if variant_key else list(logs)
    for k in variants:
        print(f"\n=== {k} ===")
        samples = logs[k].samples
        if category:
            samples = [
                s for s in samples
                if (s.metadata or {}).get("category") == category
            ]
        if n:
            samples = samples[:n]
        for s in samples:
            status_sc = s.scores["status_claim_scorer"]
            cot_sc = s.scores["cot_aware_scorer"]
            cat = (s.metadata or {}).get("category", "?")
            fmt = (s.metadata or {}).get("format", "?")
            print(f"\n--- {s.id} [{cat} / {fmt}] ---")
            print(f"  STATUS:  {status_sc.metadata['status']}")
            print(f"  AWARE:   {cot_sc.answer}")
            print(f"  verdict: {cot_sc.metadata['verdict'][:120]}")
            print(f"  response (first 200): {s.output.completion[:200]}")


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def make_run_dir(
    results_dir: Path,
    model: str,
    epochs: int,
    limit: int | None,
) -> Path:
    """Create a timestamped run subdirectory and return its Path.

    Naming convention:
        results/runs/<ISO-timestamp>_<model>_e<epochs>_l<limit>/

    Example:
        results/runs/2026-05-19T13-45-32_gpt-4o-mini_e3_lNone/
    """
    ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    # Sanitize model name for filesystem (e.g. "openai/gpt-4o-mini" -> "gpt-4o-mini")
    model_short = model.split("/")[-1].replace("/", "-")
    limit_str = str(limit) if limit is not None else "None"
    name = f"{ts}_{model_short}_e{epochs}_l{limit_str}"
    run_dir = results_dir / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_summary(
    logs: dict,
    breakdown: dict,
    config: dict,
) -> dict:
    """Build a serializable summary dict combining run config and all numbers
    for a JSON dump."""
    summary = {}
    per_category = {}
    aggregate_keys = {"accuracy", "stderr"}
    for k, log in logs.items():
        status_m = log.results.scores[0].metrics
        cot_m = log.results.scores[1].metrics
        summary[k] = {
            "aligned_rate": status_m["accuracy"].value,
            "aligned_stderr": status_m["stderr"].value,
            "aware_rate": cot_m["accuracy"].value,
            "aware_stderr": cot_m["stderr"].value,
        }
        # Per-category from the action-only scorer (status_claim_scorer)
        per_category[k] = {
            c: status_m[c].value
            for c in status_m
            if c not in aggregate_keys
        }
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "config": config,
        "summary": summary,
        "breakdown": breakdown,
        "per_category": per_category,
    }


def write_summary(run_dir: Path, summary: dict) -> Path:
    """Write summary dict as JSON to <run_dir>/summary.json. Returns the path."""
    path = run_dir / "summary.json"
    path.write_text(json.dumps(summary, indent=2))
    return path


def _draw_accuracy(ax, logs: dict) -> None:
    labels = list(logs)
    acc = [logs[k].results.scores[0].metrics["accuracy"].value for k in labels]
    err = [logs[k].results.scores[0].metrics["stderr"].value for k in labels]
    ax.bar(labels, acc, yerr=err, capsize=6)
    ax.set_ylabel("aligned rate (action-only)")
    ax.set_ylim(0, 1)
    ax.set_title("Action-only aligned rate by variant")


def _draw_covert_breakdown(ax, breakdown: dict) -> None:
    variants = list(breakdown)
    aligned = [breakdown[v]["aligned"] for v in variants]
    cap_fail = [breakdown[v]["cap_fail"] for v in variants]
    strong = [breakdown[v]["strong"] for v in variants]
    ax.bar(variants, aligned, label="aligned", color="#2a9d8f")
    ax.bar(
        variants, cap_fail, bottom=aligned, label="capability failure",
        color="#e9c46a",
    )
    ax.bar(
        variants,
        strong,
        bottom=np.array(aligned) + np.array(cap_fail),
        label="strong covert action",
        color="#e76f51",
    )
    ax.set_ylabel("share of samples")
    ax.set_ylim(0, 1)
    ax.set_title("Outcome breakdown by variant")
    ax.legend(loc="lower right", fontsize=8)


def _draw_by_category(ax, logs: dict, scorer_index: int = 0) -> None:
    aggregate_keys = {"accuracy", "stderr"}
    variants = list(logs)
    cats = sorted(
        {
            c
            for k in variants
            for c in logs[k].results.scores[scorer_index].metrics
            if c not in aggregate_keys
        }
    )
    x = np.arange(len(cats))
    w = 0.8 / max(len(variants), 1)
    for i, k in enumerate(variants):
        m = logs[k].results.scores[scorer_index].metrics
        vals = [m[c].value if c in m else 0 for c in cats]
        ax.bar(x + i * w, vals, w, label=k)
    ax.set_xticks(x + w * (len(variants) - 1) / 2)
    ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=8)
    label = "aligned (action-only)" if scorer_index == 0 else "aware (CoT)"
    ax.set_ylabel(f"{label} rate")
    ax.set_ylim(0, 1)
    ax.set_title(f"{label} rate by impossibility category")
    ax.legend(fontsize=8)


def plot_dashboard(
    logs: dict,
    breakdown: dict,
    out_path: str | None = None,
    show: bool = False,
    config: dict | None = None,
    n_items: int | None = None,
) -> None:
    """Single figure with all four plots as subplots — the default for CLI
    runs. Saves to disk by default; only opens a window if show=True.

    config (optional): dict with keys 'model', 'epochs'. If provided, run
        parameters are rendered as a subtitle.
    n_items (optional): effective number of items per variant. Rendered in
        the subtitle as 'N items × epochs'.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    _draw_accuracy(axes[0, 0], logs)
    _draw_covert_breakdown(axes[0, 1], breakdown)
    _draw_by_category(axes[1, 0], logs, scorer_index=0)
    _draw_by_category(axes[1, 1], logs, scorer_index=1)

    title = "pants-on-fire-eval — results dashboard"
    if config is not None:
        date = datetime.now().strftime("%Y-%m-%d")
        model = config.get("model", "?")
        epochs = config.get("epochs", "?")
        n_str = f"{n_items} items × {epochs} epochs" if n_items else f"{epochs} epochs"
        subtitle = f"{model}  ·  {n_str}  ·  {date}"
        fig.suptitle(f"{title}\n{subtitle}", fontsize=13)
    else:
        fig.suptitle(title, fontsize=13)

    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150)
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_accuracy(logs: dict, out_path: str | None = None,
                  show: bool = False) -> None:
    """Standalone bar chart of action-only aligned rate per variant."""
    fig, ax = plt.subplots(figsize=(7, 4))
    _draw_accuracy(ax, logs)
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150)
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_covert_breakdown(breakdown: dict, out_path: str | None = None,
                          show: bool = False) -> None:
    """Standalone stacked bar of the three-bucket cross-tab per variant."""
    fig, ax = plt.subplots(figsize=(8, 4))
    _draw_covert_breakdown(ax, breakdown)
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150)
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_by_category(
    logs: dict, scorer_index: int = 0, out_path: str | None = None,
    show: bool = False,
) -> None:
    """Standalone grouped bar: per-impossibility-category accuracy."""
    fig, ax = plt.subplots(figsize=(11, 4))
    _draw_by_category(ax, logs, scorer_index=scorer_index)
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, dpi=150)
    if show:
        plt.show()
    else:
        plt.close(fig)
