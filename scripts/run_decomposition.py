"""Preliminary (directional, underpowered) Phase 1+2: the as_only - gp_only cheating-rate
contrast across a small reasoning-model ladder, on Impossible-LiveCodeBench conflicting/minimal.

This is NOT the pre-registered confirmatory study. It is a cheap directional preview: a task
subset (or full split) at 1 epoch, no ICC / MDE / significance claim — just the shape of
Δ = c(gp_only) - c(as_only) and whether it trends across models. Wide CIs by construction.

Variants injected as system messages, faithful to src/pants_on_fire_eval/task.py VARIANTS:
high_pressure (= no_spec), as_only, gp_only, with_spec (= full_spec), effort_only.

Needs ImpossibleBench at commit 74ae2e8 or later: earlier commits score a pass obtained by
editing the tests as a failure (ImpossibleBench issue #3).

Run with the impossiblebench venv + that venv on PATH (local sandbox needs `python`):

    PATH="../impossiblebench/.venv/bin:$PATH" \
      PRELIM_MODELS="openai/o3-mini,openai/o4-mini,openai/o3" PRELIM_LIMIT=103 \
      PRELIM_EPOCHS=1 PRELIM_REASONING_SUMMARY=none \
      ../impossiblebench/.venv/bin/python scripts/run_decomposition.py

  PRELIM_REASONING_SUMMARY=auto requires OpenAI org verification (else 400).
  PRELIM_VARIANTS (comma-separated task.py VARIANTS keys; default high_pressure,as_only,gp_only)
  selects the cells, e.g. PRELIM_VARIANTS=with_spec,effort_only. PRELIM_LOG_DIR overrides the
  log directory (default: logs/decomposition).
"""

import os
import sys

# faithful variants from task.py (avoids hand-copying the AS/GP blocks)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
from pants_on_fire_eval.task import VARIANTS  # noqa: E402

from inspect_ai import eval  # noqa: E402
from inspect_ai.model import GenerateConfig, get_model  # noqa: E402
from inspect_ai.solver import system_message  # noqa: E402
from impossiblebench import impossible_livecodebench, agentic_humaneval_solver  # noqa: E402

MODELS = [m.strip() for m in os.environ.get("PRELIM_MODELS", "openai/o4-mini").split(",") if m.strip()]
_limit = os.environ.get("PRELIM_LIMIT")
LIMIT = int(_limit) if _limit else None  # None = full conflicting split (103)
EPOCHS = int(os.environ.get("PRELIM_EPOCHS", "1"))
SPLIT = os.environ.get("PRELIM_SPLIT", "conflicting")
SANDBOX = os.environ.get("PRELIM_SANDBOX", "local")
REASONING_SUMMARY = os.environ.get("PRELIM_REASONING_SUMMARY", "none")  # 'auto' needs org verification
# task.py VARIANTS keys: high_pressure (= no_spec), as_only, gp_only, with_spec (= full_spec), effort_only
VARIANT_KEYS = [v.strip() for v in os.environ.get(
    "PRELIM_VARIANTS", "high_pressure,as_only,gp_only").split(",") if v.strip()]
_unknown = [v for v in VARIANT_KEYS if v not in VARIANTS]
if _unknown or not VARIANT_KEYS:
    sys.exit(f"PRELIM_VARIANTS: unknown or empty {_unknown or VARIANT_KEYS}; choose from {list(VARIANTS)}")
LOG_DIR = os.environ.get("PRELIM_LOG_DIR", os.path.join(REPO, "logs", "decomposition"))


def is_cheat(v):
    return v in (1, 1.0, True, "C", "CORRECT") or str(v).upper().startswith("C")


def run(model_name, variant_key):
    solver = [
        system_message(VARIANTS[variant_key]),
        agentic_humaneval_solver(max_attempts=3, allow_test_modifications=True),
    ]
    task = impossible_livecodebench(
        split=SPLIT, agent_type="minimal", solver=solver, sandbox=SANDBOX, limit=LIMIT,
    )
    model = get_model(model_name, config=GenerateConfig(reasoning_summary=REASONING_SUMMARY))
    log = eval(task, model=model, epochs=EPOCHS, log_dir=LOG_DIR)[0]
    n = c = 0
    for s in (log.samples or []):
        scores = s.scores or {}
        if scores:
            n += 1
            if is_cheat(list(scores.values())[0].value):
                c += 1
    usage = getattr(log.stats, "model_usage", {}) or {}
    it = sum(getattr(u, "input_tokens", 0) or 0 for u in usage.values())
    ot = sum(getattr(u, "output_tokens", 0) or 0 for u in usage.values())
    return c, n, it, ot


rates = {}
toks = {}
for m in MODELS:
    for vk in VARIANT_KEYS:
        cheats, n, it, ot = run(m, vk)
        rates[(m, vk)] = (cheats, n)
        toks[(m, vk)] = (it, ot)
        print(f"  [done] {m} / {vk}: {cheats}/{n}  | output tokens ~{ot // max(n, 1)}/task")

print("\n=== PRELIMINARY DECOMPOSITION (directional; NOT powered) ===")
print(f"split={SPLIT} minimal limit={LIMIT} epochs={EPOCHS} summary={REASONING_SUMMARY}")
LABELS = {"high_pressure": "no_spec", "with_spec": "full_spec"}
show_delta = "as_only" in VARIANT_KEYS and "gp_only" in VARIANT_KEYS
print(f"{'model':24}" + "".join(f"{LABELS.get(vk, vk):>12}" for vk in VARIANT_KEYS)
      + (f"{'D(gp-as)':>10}" if show_delta else ""))
for m in MODELS:
    def rate(vk):
        cheats, n = rates[(m, vk)]
        return (cheats / n) if n else float("nan")
    row = f"{m:24}" + "".join(f"{rate(vk):>11.0%} " for vk in VARIANT_KEYS)
    if show_delta:
        row += f"{rate('gp_only') - rate('as_only'):>+9.0%}"
    print(row)
print("\nD = c(gp_only) - c(as_only) > 0  =>  anti-deception suppresses cheating more than")
print("process/effort (H1, directional). Across models low->high capability: does D grow? (H2,")
print("directional). Wide CIs — preliminary subset / 1 epoch, no significance claim.")

print(f"log dir: {LOG_DIR}")
print("=== END ===")
