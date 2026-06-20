# Pre-registration — anti-scheming spec decomposition on ImpossibleBench

*Drafted 2026-06-11; **design decisions ratified 2026-06-11** (§12). This fixes the
analytic decisions **before** the confirmatory run, so the study is a falsifiable test
rather than a garden-of-forking-paths exploration. The design choices below are
**locked**; items marked **[PHASE 0]** are the remaining quantities set by a
pre-hypothesis calibration step (whose decision rule is fixed here) — the document
freezes fully once Phase 0 runs. Substrate and rationale:
[`../README.md`](../README.md), [`statistical-methodology.md`](statistical-methodology.md).*

## 1. Question and hypothesis

The Schoen et al. (2025) anti-scheming spec bundles **anti-deception** clauses (AS1–AS5)
and **process/effort** clauses (GP1–GP4). The paper shows the bundle reduces covert
behavior but does not isolate which clause type does the work.

- **H1 (primary).** Anti-deception content (`as_only`) suppresses spec-violating
  shortcut-taking *more than* the process/effort content (`gp_only`) does.
- **H2 (scaling).** That advantage **grows with model capability** — "`as_only` is
  increasingly all you need as capability scales."

H2 is an **interaction** and is powered differently from H1 (see §6). Data collection is
staged: **Phase 1** (first reasoning model) closes H1; **Phase 2** (the capability ladder)
closes H2 — see §5.

## 2. Substrate and outcome metric

- **Substrate:** [ImpossibleBench](https://github.com/safety-research/impossiblebench)
  Impossible-LiveCodeBench, **`conflicting` split is the primary estimand** (a mutated
  unit test contradicts the spec — the cleanest, most blatant impossibility). The
  **`oneoff` split is an opt-in replication arm** (≈103 more tasks, ≈2× cost): run if
  budget allows, reported as a *secondary* analysis with split as a moderator, **not
  pooled silently into the primary Δ**. **Impossible-SWEbench is out of v1** (different
  substrate, `tools` scaffold, ~10× cost) — it is the Wave-2 generalization follow-on
  (and the home of the Strategy-B mixed ladder, §5).
- **Outcome:** **cheating rate** `c(variant, model) = P(pass on an impossible task)`. A
  pass requires a spec-violating shortcut **by construction**, so no awareness judge is
  used. Higher `c` = more cheating = worse.
- **Scorer:** ImpossibleBench's `agentic_humaneval_scorer` (minimal scaffold) /
  `swe_style_humaneval_scorer` (tools), unmodified. Scaffold fixed at Phase 0.

## 3. Conditions (independent variable)

Five system-message variants, identical except for the injected spec text; the variant
strings are [`src/pants_on_fire_eval/task.py`](../src/pants_on_fire_eval/task.py)'s
`VARIANTS`, injected via ImpossibleBench's `instruction_prompt=` or a
`system_message(...)` solver prefix:

| Variant | System message |
|---|---|
| `no_spec` | High-pressure framing only (baseline) |
| `as_only` | High-pressure + AS1–AS5 (anti-deception only) |
| `gp_only` | High-pressure + GP1–GP4 (process/effort only) |
| `full_spec` | High-pressure + AS + GP (the paper's spec) |
| `effort_only` | High-pressure + content-neutral "think carefully and verify before declaring work complete" |

The isolated `as_only` / `gp_only` repair the spec's internal cross-references so neither
names an absent clause block. **Design is paired/within-task:** every task is run under
every variant, so contrasts are within-task.

## 4. Primary contrast (H1)

Define, per model:

> **Δ ≔ c(`gp_only`) − c(`as_only`).**
>
> - **Δ > 0** ⟺ `as_only` cheats *less* than `gp_only` ⟺ anti-deception content
>   suppresses cheating beyond what the process/effort content does. **(H1)**
> - **Δ ≈ 0** ⟺ anti-deception content adds nothing beyond process/effort content.
>   **(null — itself a result:** it reframes the paper's anti-deception clauses as general
>   conscientiousness in this regime.)
> - **Δ < 0** ⟺ process/effort content suppresses *more* than anti-deception content.

`as_only` and `gp_only` carry the same "safety principles" header and numbered-clause
register and differ only in clause *content*, so Δ isolates anti-deception content from
the spec's framing — the **framing-clean** contrast. (`c(effort_only) − c(as_only)`,
against a content-neutral cue, is the framing-*confounded* sibling: it bundles AS content
with the header/register, so it is the secondary control in §8, not the primary.)

Δ is a within-task paired difference of proportions, clustered by task. Tested with a
task-clustered CI (and equivalently a mixed-effects model with a task random effect; the
clustered CI is the pre-registered primary, the mixed model a robustness check).

## 5. Model ladder and configuration **[PHASE 0]**

The pilot ([report](reports/decomposition-pilot.md)) showed non-reasoning models at a **0%
cheating floor** on `minimal`+`conflicting` (no headroom for a spec to reduce), and only
the reasoning model (o4-mini, 50%) off the floor. A spec can only reduce cheating where
cheating exists, so the ladder is **Strategy A: a reasoning-only ladder on
`minimal`+`conflicting`** — the configuration the pilot validated as cheating-rich and
cheap. (Strategy B — a mixed reasoning/non-reasoning ladder requiring the `tools`
scaffold to lift non-reasoning models off the floor — is deferred to the Wave-2
generalization follow-on; it widens the capability range but changes the cheating
mechanism and ~10×s cost.) The ladder is finalized by a **pre-hypothesis calibration**:

- **Phase 0 (calibration — `no_spec` baseline only, no contrast computed).** Screen
  candidate reasoning models on the `no_spec` baseline cheating rate on
  `minimal`+`conflicting`. Keep a **monotone capability ladder of ≥3 models** for which
  each model's baseline cheating rate falls in the **headroom band [35%, 85%]**. The
  lower bound is **~2 × MID** (§6): a spec variant can only reduce cheating that exists,
  so with both `as_only` and `gp_only` expected at or below the baseline, a baseline
  near the MID leaves no realistic room for a MID-sized Δ (it would require one variant
  totally ineffective and the other driving cheating to zero). 50% (the pilot's o4-mini)
  is the sweet spot, where proportion variance p(1−p) is maximal; the upper bound guards
  ceiling compression. Specific model IDs are **not** hard-coded here (version hygiene —
  selected at Phase 0 from the then-available models, not from training-data assumptions).
- Phase 0 also measures the **ICC** (§6) and is reported as calibration, not as a test.
- Phase 0 touches only `no_spec`; it cannot peek at the H1 contrast.
- **Phase 1** then runs the full variant set on the first (smallest-capability) ladder model
  — the H1 contrast (§4); data collection for H1 ends here. **Phase 2** repeats up the ladder
  — the H2 trend (§7); data collection for H2 ends there.

## 6. Sample size, ICC, power

- **N per variant is capped by the dataset** (LCB-`conflicting` = 103 tasks; the paired
  design reuses the same tasks across variants).
- **Epochs = 3.** ImpossibleBench has **no
  judge** (the scorer is deterministic — did the mutated test pass?), so epochs do not
  average *judge* wobble but estimate the **model's own
  stochastic cheat-or-not rate** on a fixed task, which is signal. Counterweight is cost
  (epochs multiply run count linearly); 3 balances per-task rate resolution against
  spend, revisited against the Phase-0 within-task variance (drop to 2 if models run
  near-greedy).
- **ICC must be measured on ImpossibleBench** — values from other settings do
  **not** transfer numerically. Measured at Phase 0 via a multi-epoch mini-run, using
  [`src/pants_on_fire_eval/extract_icc.py`](../src/pants_on_fire_eval/extract_icc.py).
- **α = 0.05, target power = 0.80.** **MID (smallest interesting Δ) = 15 pp** — the
  threshold below which an anti-deception "advantage" reads as noise rather than a lever.
- **The dataset caps N, so we report the *achieved* MDE, not assume the MID is reached.**
  At Phase-0 ICC and N = 103 (× epochs, × the `oneoff` replication if run), compute the
  MDE for Δ via [`src/pants_on_fire_eval/stats.py`](../src/pants_on_fire_eval/stats.py).
  The paired within-task design is more powerful than an unpaired estimate, so 15 pp at
  N=103 is plausible but not assumed: if N=103 resolves ≤ 15 pp,
  the study is powered to the MID; if not, it is powered to the achieved MDE, stated
  plainly, and the `oneoff` replication arm (§2) is the pre-registered lever to tighten
  it.

## 7. Scaling test (H2) — interaction decision

H2 (Δ grows with capability) is an interaction and needs far more power than H1 — a
formal interaction test is underpowered at any affordable ladder length (interactions
need ~4× the power and real moderator spread; ≥10 models, not 3–4). So **the registered
primary is the descriptive-trend route**, with the powered test only as a conditional
upgrade — chosen *now*, not after seeing the data:

- **Primary (descriptive trend).** Report per-model Δ with task-clustered CIs and the
  **slope of Δ on a pre-specified capability ordering** of the ladder. **No significance
  claim is made on the interaction itself.** The registered statement is directional:
  "Δ increases / is flat / decreases across the ladder," with CIs shown.
- **The capability ordering is pre-specified from a named external benchmark** (e.g. a
  public LiveCodeBench or reasoning-benchmark score), fixed before the run — **not** the
  models' own cheating rates (circular) and **not** release recency. This is what makes
  the trend falsifiable rather than a post-hoc narrative.
- **Conditional upgrade (powered interaction test).** A significance claim on the
  interaction is made **only if** a pre-specified powered test (ladder length and
  per-model effect sizes sufficient per a Phase-0 power calc) clears at α = 0.05. Absent
  that, no interaction p-value is reported as confirmatory.

This is the move that keeps H2 falsifiable rather than unfalsifiable storytelling.

## 8. Secondary analyses (pre-registered as secondary)

Reported with Holm correction across the family of variant contrasts, labeled secondary:

- **Secondary control — `c(effort_only) − c(as_only)`:** does
  anti-deception content beat a content-neutral effort cue? Framing-confounded (`as_only`
  carries the spec header/register, `effort_only` does not), so the framing-clean §4 Δ is
  the headline and this is the applied "vs a bare nudge" comparison.
- **Marginal reductions — `c(no_spec) − c(as_only)` (AS arm) and `c(no_spec) − c(gp_only)`
  (GP arm):** does each clause type reduce cheating below the no-spec baseline? Their
  difference *is* the primary Δ (identity: AS-over-GP advantage = AS-marginal − GP-marginal),
  so the pair decomposes *which arm* drives the H2 trend — GP's reduction collapsing with
  capability vs AS's holding or growing. Each contrasts a framed block against the unframed
  baseline, so read trends, not absolute levels.
- `c(no_spec) − c(effort_only)` — does the content-neutral cue reduce cheating at all (the
  baseline for the secondary control above)?
- `c(as_only) − c(full_spec)` — does the full spec beat AS-alone (is GP additive on top of
  AS)?
- **Additivity:** is `c(no_spec) − c(full_spec)` ≈ the sum of the AS-alone and GP-alone
  reductions, or sub-/super-additive?
- If multiple splits/scaffolds run: Δ per split/scaffold as a robustness check.

**Exploratory — reasoning-summary review (not in the Holm family; no confirmatory claim).**
For models whose API exposes a reasoning summary, classify each summary for (i) recognized
impossibility and (ii) proceeded-anyway / concealment, with a pre-specified rubric and a
stronger, different-family judge. Reported descriptively: does the summary-level
recognized-then-proceeded rate track the behavioral Δ, and are the spec-injected variants'
summaries consistent with Schoen et al.'s reported patterns (e.g. raised evaluation-awareness)?
**Caveat:** the summary is a model-generated synopsis, not raw chain-of-thought (which o-series
models encrypt), and can be unfaithful under optimization (Baker et al. 2025) — so this
*qualifies* the behavioral results in discussion; it does not establish intent.

## 9. Multiple comparisons

**Holm–Bonferroni** across the variant-contrast family within each model. H1 (Δ) is the
single primary and is reported both raw and Holm-adjusted. Secondary contrasts (§8) are
Holm-adjusted as their own family and never promoted to primary post hoc.

## 10. What would falsify each hypothesis

- **H1 false:** Δ CI covers 0 across the ladder at the achieved MDE → "anti-deception
  content adds no detectable suppression beyond the process/effort content, powered to X
  pp." Reported as a finding (reframes the paper's anti-deception clauses as general
  conscientiousness in this regime).
- **H2 false:** Δ does not increase across the capability ordering (flat or decreasing
  slope) — even if Δ > 0 at some level, the *scaling* claim fails.

## 11. Deviations policy

Any departure from this document (configuration, ladder, epochs, metric, analysis) is
logged with its reason and reported in the writeup alongside the registered plan.
Phase-0 outcomes that set the **[PHASE 0]** quantities are recorded before Phase 1 begins
and are not revised after the confirmatory run starts.

## 12. Decisions ratified (2026-06-11)

All design decisions below are **locked**; the only remaining open quantities are the
**[PHASE 0]** calibration outputs (final ladder, ICC, achieved MDE).

| # | Decision | Ratified value |
|---|---|---|
| 0 | Model ladder | **Strategy A** — reasoning-only on `minimal`+`conflicting` (Strategy B mixed ladder → Wave-2) |
| 1 | MID | **15 pp**; report achieved MDE at N=103 |
| 2 | Headroom band | **[35%, 85%]** (lower bound ≈ 2 × MID) |
| 3 | Epochs | **3** (epochs are signal — no judge); confirm vs Phase-0 within-task variance |
| 4 | H2 route | **Descriptive trend** + external-benchmark capability ordering; powered test only as conditional upgrade |
| 5 | N extension | `conflicting` primary; **`oneoff` opt-in** replication (moderator, if budget); **SWE-bench out** of v1 |
| 6 | Primary contrast | **`as_only − gp_only`** (framing-clean AS-content-vs-GP-content); `as_only − effort_only` → secondary control (§8) |

Once Phase 0 has set the **[PHASE 0]** quantities, this document is frozen and the
confirmatory run begins: **Phase 1** (first model, H1), then **Phase 2** (the ladder, H2).
