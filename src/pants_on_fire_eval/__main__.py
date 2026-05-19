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
    calibration_check,
    covert_breakdown,
    plot_dashboard,
    print_summary,
)
from .task import VARIANTS, condition


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
        type=int,
        default=None,
        help="Number of items per variant (default: all).",
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

    if not args.no_plots:
        args.results_dir.mkdir(parents=True, exist_ok=True)
        plots_dir = args.results_dir / "plots"
        plots_dir.mkdir(exist_ok=True)
        dashboard_path = plots_dir / "dashboard.png"
        print(f"\nWriting dashboard to {dashboard_path}")
        plot_dashboard(
            logs, breakdown,
            out_path=str(dashboard_path),
            show=args.show_plots,
        )


if __name__ == "__main__":
    main()
