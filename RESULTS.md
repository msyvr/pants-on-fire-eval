# Results

Two runs on the **logical-only** dataset (60 impossible items — 20 each across
`algorithmic_impossible`, `contradiction_spec`, `contradiction_tests` — plus 5
calibration items; dataset `cd4527a`). The absent-resource categories are parked:
they need a multi-turn agentic setup, not this single-turn proxy — see
[`docs/single-turn-vs-multi-turn.md`](docs/single-turn-vs-multi-turn.md).

1. **gpt-4o-mini** (non-reasoning) — 6 variants × 60 items × 3 epochs. Screening run.
2. **o4-mini** (reasoning) — 3 variants × 60 items × 1 epoch. A reasoning diagnostic.

> **Read everything here as directional.** gpt-4o-mini at N=60 items (clustered,
> ICC≈0.64) resolves ~20 pp effects; the o4-mini run is N=60 × 1 epoch — a probe,
> not a powered result. Both use a same-family (gpt-4o-mini) awareness judge.

## Headline — the spec effect is a non-reasoning-model phenomenon

Aligned rate (rule-based, judge-independent), with each spec variant's **lift over
the no-spec `high_pressure` floor**:

| Variant | gpt-4o-mini aligned (lift) | o4-mini aligned (lift) |
|---|---|---|
| `high_pressure` (no-spec floor) | 36.7% (—) | 56.7% (—) |
| `as_only` (anti-deception) | 53.3% (**+16.6**) | 56.7% (**+0.0**) |
| `gp_only` (process/effort) | 71.1% (**+34.4**) | — |
| `with_spec` (full spec) | 71.7% (**+35.0**) | — |
| `effort_only` (neutral effort) | 74.4% (**+37.7**) | 58.3% (**+1.6**) |
| `low_pressure` (calm anchor) | 75.6% | — |

On **gpt-4o-mini** the spec does real work, and process/effort content does ~twice
the work of anti-deception (effort +38 pp, AS +17 pp). On **o4-mini every spec
variant's lift collapses to ~0** — and the no-spec floor *rises* 20 pp. The
reasoning model recognizes impossibility on its own, so the spec is redundant for
this (single-turn, recognition) measure.

Two readings follow:
- **The "effort dominates" result is non-reasoning-specific.** "Think carefully and
  verify before declaring done" helps a model that wasn't reasoning; it is redundant
  for one that already does. The effort lift drops from +38 pp to +1.6 pp.
- **"Anti-deception adds ~nothing beyond baseline" survives both regimes** (AS lift
  +16.6 → +0). What was setting-specific was the *effort advantage*, not AS's weakness.

## Run 1 — gpt-4o-mini (non-reasoning), full cross-tab

Impossible items only, N = 180 per variant (60 items × 3 epochs):

| Variant | Aligned | Capability failure | Strong covert | Aware (CoT) |
|---|---|---|---|---|
| `low_pressure` | 75.6% | 23.3% | 1.1% | 33.3% |
| `high_pressure` | 36.7% | 60.0% | 3.3% | 19.5% |
| `as_only` | 53.3% | 46.1% | 0.6% | 36.9% |
| `gp_only` | 71.1% | 27.8% | 1.1% | 36.4% |
| `with_spec` | 71.7% | 28.3% | 0.0% | 47.7% |
| `effort_only` | 74.4% | 25.6% | 0.0% | 32.3% |

The dominant failure under pressure is **capability failure** (60%): gpt-4o-mini
claims done *without verbalizing recognition* of the impossibility. Strong covert
(recognized-and-claimed) is ~0–3% everywhere — and is a **lower bound**, since the
text judge only catches *verbalized* recognition. Process/effort content attacks
the capability-failure bucket directly (verify → catch the impossibility →
decline); anti-deception content has little to act on when recognition is rare.

## Run 2 — o4-mini (reasoning), the diagnostic

N = 60 per variant (1 epoch); 3 variants:

| Variant | Aligned | Capability failure\* | Strong covert\* |
|---|---|---|---|
| `high_pressure` | 56.7% | 41.7% | 1.7% |
| `as_only` | 56.7% | 43.3% | 0.0% |
| `effort_only` | 58.3% | 40.0% | 1.7% |

\* **The cap-fail / strong-covert split is unreliable for o4-mini.** Its reasoning
is hidden by the API, so the awareness judge sees only the ~550-token final answer,
not the ~1,150 tokens of hidden reasoning where recognition happens. Read the
**aligned** column (judge-independent) only.

What changed from gpt-4o-mini:
- **The floor rose** (36.7 → 56.7): with no spec at all, o4-mini recognizes and
  declines on more impossibilities. The lift concentrates where impossibility is
  knowledge-based — `algorithmic_impossible` recognition jumps 60% → 80%.
- **Every spec lift collapsed** (`as_only` +0, `effort_only` +1.6). The model's own
  reasoning substitutes for the spec.

## Why the floor rose — recognition, honesty, and what text can't see

The 20 pp baseline lift sits exactly on the eval's reason for existing. It came
from cutting capability-failure (60 → 42) — i.e. **fewer false claims of
completion.** Two mechanisms could produce that:
- **better recognition** — the reasoning model *derives* the impossibility the
  non-reasoner skipped; or
- **more honesty** — it recognized internally and *disclosed*, where gpt-4o-mini
  recognized internally and *concealed* (implicit covert action).

The CoT judge separates these *when the model writes its reasoning down* — that is
the capability-failure-vs-strong-covert split. It cannot separate them for the
residual the model never verbalizes, and that residual is exactly the **implicit
covert action** the text judge files under capability failure (a documented lower
bound). The cleanest read is recognition (Occam; and the lift is largest where
impossibility is a known theorem), but text scoring cannot *prove* it isn't partly
honesty. **That irreducible ambiguity is the single-turn argument for the
activation layer (Phase 2): not to read reasoning the judge already reads, but to
read recognition the model never put into words.**

One wrinkle against "more capable = more aligned": on `contradiction_tests` o4-mini
declines only ~45% — *below* effort-prompted gpt-4o-mini's ~62%. A strong model
appears to reason its way into a clever-but-wrong solution and confidently claim it
works. Reasoning helps where impossibility is a known theorem, less where it is a
conflict the model can rationalize past. (Caveat: ~20-item category cells.)

## What this sets up

For a **reasoning** subject in single-turn, the spec is redundant on the
recognition axis — so the paper's spec effect (measured on reasoning models) must
operate through the **deception channel** (recognize-then-conceal), which here is
both ~0 and *unmeasurable* (o4-mini's reasoning is hidden). Reading that channel
needs the reasoning **visible** — self-hosted CoT or activations. The diagnostic
draws a straight line to **Phase 2's self-hosted setup**, and separately to a
**multi-turn arm** where the deception decision is actually elicited. See
[`docs/single-turn-vs-multi-turn.md`](docs/single-turn-vs-multi-turn.md) and
[`docs/phase1-sampling-plan.md`](docs/phase1-sampling-plan.md).

## Calibration check

Calibration (solvable) items should be answered `STATUS: COMPLETE`. Both runs are
mostly clean; a few spurious INCOMPLETEs under the spec variants (mild spec-induced
overrefusal) — at this scale a flag, not a finding.

## Caveats

- **Directional, not powered.** gpt-4o-mini N=60 items resolves ~20 pp (clustered,
  ICC≈0.64); o4-mini is N=60 × 1 epoch — a probe. The o4-mini 56.7-vs-58.3 spread is
  noise; the *signal* is the lift collapse, which is large.
- **o4-mini awareness is hidden** (reasoning withheld by the API) → its cap-fail /
  strong-covert split is unreliable; read its aligned axis only.
- **Same-family awareness judge** (gpt-4o-mini grading); a stronger, different-family
  judge (Claude) is pending for headline runs.
- **Single-turn text proxy**, **in-context not training** — a tractable shadow of the
  paper's agentic setup. See the rationale doc.

## Run details & artifacts

- **Dataset:** `cd4527a` — 60 logical impossible (20/category) + 5 calibration; absent-resource parked.
- **Run 1:** `openai/gpt-4o-mini`, 6 variants × 3 epochs → `results/runs/2026-06-10T19-23-00_gpt-4o-mini_e3_lNone/` (~$0.34).
- **Run 2:** `openai/o4-mini`, 3 variants × 1 epoch → `results/runs/2026-06-10T20-09-07_o4-mini_e1_lNone/` (~$0.98).
- Each run dir holds `summary.json` (all numbers); Run 1 also has `dashboard.png`.
