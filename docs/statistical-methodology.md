# Statistical methodology — sampling and inference for the decomposition

*Why the experiment is sized and analyzed the way it is, written to be followed
without a statistics background. The reasoning generalizes; the concrete numbers for
this study live in the [pre-registration](preregistration.md) and the
[pilot report](reports/decomposition-pilot.md). The calculations are implemented in
[`src/pants_on_fire_eval/stats.py`](../src/pants_on_fire_eval/stats.py), which prints
an example plan when run as a script.*

---

## The one idea to hold onto

The experiment exists to pin down **one number**: the difference in **cheating rate**
between two spec variants — `as_only` vs `gp_only` — measured on the same tasks.
Everything else serves that. Two things make sizing it non-obvious, and most mistakes
come from missing them:

1. **The unit is the task, not the task×epoch run.** Re-running one task several
   times (epochs) gives correlated outcomes, not independent data — so power is driven
   by the number of **tasks**, not tasks×epochs.
2. **The design is paired.** Every task runs under every variant, so the contrast is
   *within task* — the task is its own control, which makes the comparison tighter
   than treating the two rates as independent.

---

## Part 1 — What we measure

ImpossibleBench mutates a real unit test so it contradicts the task spec; on such an
"impossible" task **any pass requires a spec-violating shortcut**, so a pass *is* a
cheat **by construction**. The outcome is a single deterministic, judge-free number:

> **cheating rate** `c(variant, model) = P(pass on an impossible task)` — higher = more cheating = worse.

The **primary estimand** is the within-task paired difference

> **Δ = c(`gp_only`) − c(`as_only`)**, where Δ > 0 means `as_only` cheats *less* — anti-deception content suppressing beyond what the process/effort content does.

Naming the one number up front is the first robustness move: an experiment that knows
its single headline quantity is hard to fool with after-the-fact storytelling. (There
is no awareness judge and no outcome cross-tab — the by-construction scorer replaces
both. Intent — aware vs unaware cheating — is out of scope; see the report.)

---

## Part 2 — Decisions for a robust experiment

### Decision 0 — What counts as one data point? (the unit of analysis)

You run each task over several **epochs** (re-runs). It is tempting to count
`tasks × epochs` as the sample size. **Don't.** Re-runs of the *same* task are
correlated, so they are not independent.

- The **intra-class correlation (ICC)** measures how alike re-runs of one task are:
  0 = epochs fully independent, 1 = epochs add nothing new (the task decides the outcome).
- The **design effect** turns that into a sample-size penalty:
  `DEFF = 1 + (epochs − 1) × ICC`.

**Consequence:** the **task is the unit**, not the task×epoch run. Power is driven by
the number of *tasks*; epochs reduce within-task noise but don't multiply independent
information. Don't guess the ICC — **measure it on ImpossibleBench** (`estimate_icc`,
via `extract_icc.py`); a value from any other setup does **not** transfer numerically.

### Decision 1 — How many tasks? (power)

**Power** is the probability that, *if* a real difference of the size you care about
exists, the experiment detects it. Low power is the quiet failure: you find nothing
and wrongly conclude "no effect." Convention is 80%.

A power calculation needs the following, plus the design effect:

| Input | What it is |
|---|---|
| **Minimal important difference (MID)** | the smallest Δ you'd treat as detectable — *you* choose it |
| **Baseline rate** | the cheating rate you're comparing around (from calibration) |
| **α** | false-positive rate (conventionally 0.05) |
| **power (1 − β)** | conventionally 0.80 |
| **design effect** | the clustering penalty, from the measured ICC + epochs |

Run through `items_per_variant(...)`, this gives the tasks needed; the lever is the
MID. Two structural facts bind this study (detail in the
[report](reports/decomposition-pilot.md) §4):

- The `conflicting` split is a **census** (103 tasks), so N can't grow on it — report
  the *achieved* resolution (MDE), don't assume it reaches the MID.
- The **paired** design resolves finer than the unpaired two-proportion formula in
  `stats.py` implies (treat that formula as a conservative ceiling), because the
  within-task correlation tightens the contrast.

### Decision 2 — What do epochs buy?

Epochs (re-running a task) **reduce within-task noise** — they estimate each task's
own stochastic cheat-or-not rate. They do **not** multiply independent sample size
(Decision 0). The fact that governs them: as epochs → ∞, the MDE floors at
**√ICC × the single-epoch MDE**, so epochs can never substitute for more tasks, and
at a high ICC the 2nd–3rd epoch buy little. Measure the ICC first, then set the epoch
count at the cost-effectiveness knee; more *tasks* is the only floor-free lever
(MDE ∝ 1/√tasks).

### Decision 3 — Pre-register the plan

Before the confirmatory run, fix: the **primary contrast** (`gp_only − as_only`), the
**MID**, **α and power**, the **ladder-selection rule**, and the **scaling-test**
decision. With five variants and several models there are many numbers you *could*
highlight after the fact ("the garden of forking paths"); fixing the targets in
advance is what lets you trust the result. (See [`preregistration.md`](preregistration.md).)

### Decision 4 — Account for multiple comparisons

Each test carries an α chance of a false positive; run several and you expect one by
chance alone. Pre-specify the small family of contrasts that matter and **Holm-adjust**
within each family (`holm`), rather than testing all pairs.

---

## Part 3 — Reporting and visualizing

### Report effect sizes with uncertainty, not just "significant / not"

The informative output is **the cheating-rate difference with a confidence interval**,
not a bare p-value. "Δ = +6pp, 95% CI [−2, +14]" says far more than "n.s.": it shows
both the effect and how precisely it was pinned down.

### Use the right interval for the quantity

- **Per-variant cheating rates** — **Wilson** intervals (`wilson_ci`); the normal
  approximation breaks at small counts and rates near 0 or 1.
- **The paired difference Δ** — the **Newcombe** (Wilson-based) paired interval
  (`paired_diff_ci`) with an **exact-binomial McNemar** p-value. The textbook Wald
  interval has erratic small-sample coverage; Newcombe is the principled default. The
  signal lives in the **discordant pairs** (tasks whose outcome flips between
  conditions) — which is why McNemar/Newcombe, not their unpaired analogues.
- **Zero-cheat cells** — never report a bare "0%". Give an **upper bound**
  (`rule_of_three_upper`: 0 in 23 trials → "≤ ~12%, 95%"). "We didn't observe it, and
  here's how rare it could still be" is the candid claim.

### Say what you could have detected

If a contrast comes back null (CI includes 0), report the **minimal detectable effect**
(`mde_two_proportions`) alongside it: "no detectable AS-vs-GP gap; the run resolved to
≈ X pp." A null only means something once you state the resolution you had.

### Plots that carry the statistics

- **Cheating rate per variant/model** — bars with Wilson CIs.
- **Contrast panel** — the pre-specified paired differences with Newcombe CIs and a
  band at the MID, so a reader sees at a glance whether each effect clears the
  threshold (see the report's figures).

A clean, well-powered **null is a real result** — report it plainly with its MDE and
propose the next experiment.

---

## The workflow, in order

1. **Measure the ICC** from a multi-epoch mini-run (`estimate_icc`) — don't guess it.
2. **Choose the MID** for the primary contrast.
3. **Compute the task count** (`items_per_variant`) and **pre-register** the contrast, MID, α, power, and ladder rule.
4. **Calibrate** the model ladder on the no-spec baseline; **run** the variant set.
5. **Analyze:** Wilson CIs per cell, the Newcombe paired Δ per model with exact-McNemar p, Holm within family, and the across-model trend.
6. **Report:** effect sizes with CIs, the MDE for any null, and the plots above.

---

## Glossary

- **Estimand** — the number the experiment exists to measure (here: the `gp_only − as_only` cheating-rate difference).
- **Power (1 − β)** — chance of detecting a real effect of the size you care about.
- **α** — chance of a false positive (declaring an effect that isn't there).
- **MID** — minimal important difference: the smallest effect worth detecting (you choose it).
- **MDE** — minimal detectable effect: the smallest effect a given sample size *could* detect.
- **ICC** — intra-class correlation: how alike repeated runs of one task are.
- **Design effect (DEFF)** — the sample-size penalty from clustering, `1 + (epochs − 1) × ICC`.
- **Wilson interval** — a proportion CI that stays valid at small counts and rare rates.
- **Newcombe paired interval** — the Wilson-based CI for a paired difference of proportions.
- **McNemar test** — the exact test for a paired difference, computed on the discordant pairs.
- **Holm correction** — adjusts p-values across a family of tests to control the family-wide false-positive rate.

---

## Where the calculations live

`src/pants_on_fire_eval/stats.py` — `items_per_variant`, `mde_two_proportions`,
`wilson_ci`, `paired_diff_ci` (Newcombe + exact McNemar), `rule_of_three_upper`,
`cluster_bootstrap_ci`, `estimate_icc`, `holm`. Run it as a script for an example plan.
