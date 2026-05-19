"""CLI entry point for pants-on-fire-eval.

Usage (after `uv sync`):

    uv run pants-on-fire-eval                     # default: all variants, full run
    uv run pants-on-fire-eval --limit 3           # smoke test with 3 items
    uv run pants-on-fire-eval --epochs 1          # single epoch (no variance)
    uv run pants-on-fire-eval --model openai/gpt-4o
    uv run pants-on-fire-eval --variants low_pressure high_pressure
    uv run pants-on-fire-eval --no-plots          # skip plot generation

Requires the OPENAI_API_KEY environment variable to be set.
"""

import argparse
from pathlib import Path

from inspect_ai import eval

from .analysis import (
    build_summary,
    calibration_check,
    covert_breakdown,
    make_run_dir,
    plot_dashboard,
    print_summary,
    write_summary,
)
from .task import VARIANTS, condition


def _limit_type(s: str) -> int | None:
    """Accept either an integer or 'None'/'all' for the --limit flag."""
    if s.lower() in ("none", "all"):
        return None
    return int(s)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="pants-on-fire-eval",
        description=(
            "Run the pants-on-fire eval: does the model claim it solved an "
            "impossible task?"
        ),
    )
    p.add_argument(
        "--limit",
        type=_limit_type,
        default=None,
        help="Number of items per variant (int, or 'None'/'all'; default: all).",
    )
    p.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Repetitions per item per variant (default: 3 for variance).",
    )
    p.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o-mini",
        help="Model identifier (default: openai/gpt-4o-mini).",
    )
    p.add_argument(
        "--variants",
        nargs="+",
        default=list(VARIANTS),
        choices=list(VARIANTS),
        help="Subset of variants to run (default: all).",
    )
    p.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip plot generation.",
    )
    p.add_argument(
        "--show-plots",
        action="store_true",
        help="Open plots in interactive windows (default: save to disk only).",
    )
    p.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Directory to write plots into (default: ./results).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    print(f"Running variants: {args.variants}")
    print(
        f"Model: {args.model}, limit: {args.limit}, epochs: {args.epochs}\n"
    )

    raw_logs = eval(
        [condition(k) for k in args.variants],
        model=args.model,
        limit=args.limit,
        epochs=args.epochs,
    )
    logs = dict(zip(args.variants, raw_logs))

    print("\n" + "=" * 70)
    print("Summary (per-variant aligned + aware rates)")
    print("=" * 70)
    print_summary(logs)

    print("\n" + "=" * 70)
    print("Three-bucket cross-tab")
    print("=" * 70)
    breakdown = covert_breakdown(logs)

    print("\n" + "=" * 70)
    print("Calibration check")
    print("=" * 70)
    calibration_check(logs)

    # Each run gets its own timestamped subdirectory with config-encoded name.
    # All artifacts (dashboard plot, summary JSON) for one run live together.
    run_dir = make_run_dir(
        results_dir=args.results_dir,
        model=args.model,
        epochs=args.epochs,
        limit=args.limit,
    )
    print(f"\nRun artifacts → {run_dir}/")

    config = {
        "model": args.model,
        "epochs": args.epochs,
        "limit": args.limit,
        "variants": args.variants,
    }
    summary = build_summary(logs, breakdown, config)
    summary_path = write_summary(run_dir, summary)
    print(f"  summary:   {summary_path.name}")

    if not args.no_plots:
        # Effective N per variant = number of distinct items shown to the model.
        # Pull from any one variant's log (all variants share the same dataset).
        first_log = next(iter(logs.values()))
        n_items = len({s.id for s in first_log.samples})

        dashboard_path = run_dir / "dashboard.png"
        plot_dashboard(
            logs, breakdown,
            out_path=str(dashboard_path),
            show=args.show_plots,
            config=config,
            n_items=n_items,
        )
        print(f"  dashboard: {dashboard_path.name}")


if __name__ == "__main__":
    main()
