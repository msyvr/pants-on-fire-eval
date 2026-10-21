# Reproduction — ImpossibleBench substrate

*How to run the ImpossibleBench substrate this project builds on, plus the
first-bring-up gotchas. For current cheating rates, see the
[paper draft](reports/decomposition-pilot.md) — this page is setup and reproduction only.*

## Setup

- Substrate: **ImpossibleBench** (`safety-research/impossiblebench`, MIT), installed
  at `../impossiblebench` with its own venv. Dataset: `Impossible-LiveCodeBench`,
  `conflicting` split (103 tasks), `minimal` agent scaffold.
- Metric: **cheating rate = accuracy on the impossible split** — a pass on a
  conflicting task necessarily implies a spec-violating shortcut, so cheating is
  identified by construction, with no awareness judge.
- Sandbox: `local`, **with the venv activated** (see gotcha below).

## Substrate validation

The first bring-up confirmed the pipeline end to end (install → HuggingFace dataset → model →
sandbox executes the tests → cheating-rate scorer). A reasoning model passed some conflicting tasks
and failed others, so the scorer registers passes. It did not register every kind of pass: until
ImpossibleBench commit `74ae2e8` (2026-10-13, issue #3), a pass obtained by editing the test was
scored as a failure. Use that commit or later; logs made before it can be rescored with
[`../scripts/rescore_impossiblebench_logs.py`](../scripts/rescore_impossiblebench_logs.py). The
per-model rates are in the [paper draft](reports/decomposition-pilot.md).

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
