# Reproduction — ImpossibleBench substrate

*How to run the ImpossibleBench substrate this project builds on, plus the
first-bring-up gotchas. For current cheating rates, see the
[pilot report](reports/decomposition-pilot.md) — this page is setup and reproduction only.*

## Setup

- Substrate: **ImpossibleBench** (`safety-research/impossiblebench`, MIT), installed
  at `../impossiblebench` with its own venv. Dataset: `Impossible-LiveCodeBench`,
  `conflicting` split (103 tasks), `minimal` agent scaffold.
- Metric: **cheating rate = accuracy on the impossible split** — a pass on a
  conflicting task necessarily implies a spec-violating shortcut, so cheating is
  identified by construction, with no awareness judge.
- Sandbox: `local`, **with the venv activated** (see gotcha below).

## Substrate validation

The first bring-up confirmed the pipeline end-to-end (install → HuggingFace dataset →
model → sandbox executes the tests → cheating-rate scorer) and the scorer in **both
directions**: a reasoning model passed some conflicting tasks (= cheated) and failed
others honestly, so a non-zero rate is real cheating and a 0% rate is a real honest
floor, not a scorer blind spot. The reasoning-gated gradient this surfaced — and the
calibrated per-model rates — are in the [pilot report](reports/decomposition-pilot.md).

## Reproduction gotchas

- The `local` sandbox calls `python`; macOS only has `python3`. **Activate the venv**
  (`source .venv/bin/activate`) so `python` resolves, or use `sandbox="docker"`
  (Docker present; the benchmark's recommended path).
- `inspect_ai` needs the provider package: `uv pip install openai` (not pulled by
  ImpossibleBench's deps).
- API key: ImpossibleBench's venv has no `.env`; source the key before running.

## Commands

```bash
cd ../impossiblebench && source .venv/bin/activate
python -c "from inspect_ai import eval; from impossiblebench import impossible_livecodebench; \
  eval(impossible_livecodebench(split='conflicting', agent_type='minimal', limit=8, sandbox='local'), model='openai/o4-mini')"
```
