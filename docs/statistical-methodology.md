# Statistical methodology — sampling and inference for the Phase 1 ablation

*Why the experiment is sized and analyzed the way it is, written to be followed
without a statistics background. The reasoning generalizes to any experiment; the
concrete numbers are for the Phase 1 spec ablation. The calculations are
implemented in [`src/pants_on_fire_eval/stats.py`](../src/pants_on_fire_eval/stats.py),
which prints an example plan when run as a script.*

---

## The one idea to hold onto

This experiment asks **two different statistical questions**, and they need
**different sample-size logic**. Most mistakes here come from treating them as one:

1. **A comparison** — *does the anti-deception content of the spec change behavior
   beyond what the process/effort content does?* This is a hypothesis test on
   rates; its sample size is a **power** question.
2. **A rare-rate estimate** — *how often does the model claim done while
   recognizing the task is impossible (covert action)?* This is estimating a small
   proportion; its sample size is a **precision / event-count** question, not power.

Everything below is the reasoning for each, then how to report them without overclaiming.

---

## Part 1 — What am I actually measuring?

The experiment: five spec variants (`no_spec`, `as_only`, `gp_only`, `full_spec`,
`effort_only`), each run on the same set of impossible coding tasks. Two scorers
read each response — did it claim COMPLETE (rule-based), and did its reasoning
recognize the task is impossible (a model-graded judge). Crossed, these give the
outcome buckets (aligned / capability-failure / strong-covert).

Two quantities come out of that, and they are different *kinds* of thing:

- **The aligned-rate per variant** — a proportion (e.g. "62% of responses were
  aligned"). The headline question is a **difference between two of these**:
  `as_only` vs `gp_only` — *does anti-deception content do more than the process/effort
  content?* That difference is the **primary estimand** (the number the experiment exists
  to pin down).
- **The bucket rates** — also proportions, but **rare** ones (covert action is
  uncommon, especially once a spec is injected). "Rare" changes how you size and
  report them.

Naming the primary estimand up front — `as_only` − `gp_only` aligned-rate —
is the first robustness move. An experiment that knows its one main number is hard
to fool with after-the-fact storytelling.

---

## Part 2 — Decisions for a robust experiment

### Decision 0 — What counts as one data point? (the unit of analysis)

You run each item over several **epochs** (re-runs). It is tempting to count
`items × epochs` as your sample size. **Don't.** Five re-runs of the *same* item
are correlated — the same task tends to produce similar results — so they are not
five independent data points.

- The **intra-class correlation (ICC)** measures how correlated re-runs of one item
  are: 0 = epochs are fully independent, 1 = epochs tell you nothing new (the item
  decides the outcome).
- The **design effect** turns that into a penalty on your sample size:
  `DEFF = 1 + (epochs − 1) × ICC`. At 5 epochs and ICC 0.3, DEFF = 2.2 — meaning
  your effective sample size is *less than half* of `items × epochs`.

**Consequence:** the **item is your unit of analysis**, not the item×epoch
observation. Power is driven by the number of *items*; epochs reduce noise within
an item but don't multiply independent information. Don't guess the ICC —
**measure it from your pilot run** (`estimate_icc`) and feed it into the rest.

### Decision 1 — How many items for the comparison? (power)

**Power** is the probability that, *if* a real difference of the size you care
about exists, your experiment detects it. Low power is the quiet failure mode: you
run the study, find nothing, and wrongly conclude "no effect" when you just didn't
have enough data. Convention is 80% power.

A power calculation needs four things, plus the design effect:

| Input | What it is | For this experiment |
|---|---|---|
| **Minimal important difference (MID)** | the smallest difference that would change your conclusion | *you* choose this — e.g. "a 15-point gap between `as_only` and `gp_only` would matter" |
| **Baseline rate** | the aligned-rate you're comparing around | from the pilot |
| **α (alpha)** | the false-positive rate — chance of declaring a difference that isn't real | conventionally 0.05 |
| **power (1 − β)** | see above | conventionally 0.80 |
| **design effect** | the clustering penalty | from your measured ICC + epochs |

Run through `items_per_variant(...)`, this gives **items per variant**. The numbers
for this eval (illustrative ICC 0.3, 5 epochs):

- a **50-item screen powers only a ~18.5-point difference** — fine for the big
  pressure-framing swings, too coarse for the subtle `as`-vs-`gp` gap.
- detecting a **15-point** gap needs **~72 items/variant**; an 8-point gap needs
  several hundred.

So the MID is the lever: pick it in good faith (the smallest gap that would change what
you'd conclude about anti-deception content), and the item count follows.

### Decision 2 — How many samples for the rare buckets? (precision, not power)

The covert-action buckets are **estimates of a rare rate**, not a test, so power
doesn't apply. You size them by **how many events you need to estimate the rate
with a usable interval** — a common target is **≥ ~40 events** per cell you intend
to report as a rate.

`n_for_events(rate, target)`: at a 5% covert rate, getting 40 events needs **~800
COMPLETE samples** in that cell. That is why the design is **two-pass**:

1. **Screening pass** — enough items per variant for the *comparison* (Decision 1),
   run across all variants. This also reveals which cells actually produce covert
   action.
2. **Top-up pass** — add samples *only* to the cells that produce covert events,
   until they reach the event target. Cells with no covert action are not topped up
   (there's nothing to populate) — they're reported as upper bounds (Part 3).

The comparison and the buckets are **two sample-size problems with two N's**.
Reporting them as such — rather than pretending one flat grid powers both — is the
core defensibility move.

### Decision 3 — What do epochs actually buy?

Epochs (re-running the same item) **reduce within-item noise**, including the
model-graded judge's run-to-run wobble. They do **not** multiply your independent
sample size (Decision 0). Use them to stabilize each item's estimate, not to claim
more statistical power than the item count supports.

### Decision 4 — Pre-register the plan

Before the screening pass, write down: the **primary contrast** (`as_only` vs
`gp_only`), the **MID**, **α and power**, and the **event targets**. Why: with
five variants and several buckets there are many numbers you *could* highlight
after seeing the data, and picking the most striking one after the fact ("the
garden of forking paths") manufactures false positives. Fixing the targets in
advance is what lets you trust the result you report.

### Decision 5 — Account for multiple comparisons

Each test you run carries an α chance of a false positive; run ten and you expect
about one false "finding" by chance alone. With five variants there are many
possible pairwise contrasts, so **correct for the family of tests** you'll actually
run (`holm` — Holm-Bonferroni, which adjusts the p-values). Keep the family small
by pre-specifying the contrasts that matter, rather than testing all pairs.

### Decision 6 — The judge is a measuring instrument too

The CoT-awareness scorer is a model grading text — it has its own error rate. Two
checks keep it calibrated: **epoch-to-epoch agreement** (does it classify the same
response consistently across re-runs?) and a **manual-confirmation calibration set**
(hand-label a sample, check the judge against it). Grade with a **stronger,
different-family** model than the subject, so the judge doesn't share the subject's
blind spots.

---

## Part 3 — Reporting and visualizing statistical relevance

### Report effect sizes with uncertainty, not just "significant / not"

The informative output is **the difference in aligned-rate between variants, with a
confidence interval** — not a bare p-value. A CI shows both the size of the effect
and how precisely you pinned it down. "`as_only` − `gp_only` = +12 points, 95%
CI [+3, +21]" says far more than "p < 0.05".

### Use the right interval for the quantity

- **Variant aligned-rates** — use an **item-clustered** interval
  (`cluster_bootstrap_ci`, which resamples *items*), not a textbook proportion CI
  that assumes independent observations. The naive interval would be falsely narrow.
- **Rare bucket rates** — use a **Wilson** interval (`wilson_ci`); the normal
  approximation breaks at small counts and rare rates.
- **Zero-event cells** — never report "0%". Report an **upper bound**
  (`rule_of_three_upper`: with 0 events in 200 samples, the rate is "< ~1.5%, 95%").
  "We did not observe it, and here's how rare it could still be" is the candid claim.

### Say what you could have detected

If a comparison comes back null (CI includes zero), report the **minimal detectable
difference** (`mde_two_proportions`) alongside it: "no detectable `as`-vs-`effort`
gap; the study could detect a difference of ≥ X points." A null only means
something if you state the resolution you had.

### Plots that carry the statistics

- **Aligned-rate per variant** — bars with **item-clustered CI error bars**. (The
  repo's `analysis._draw_accuracy` currently uses a plain stderr; swap in the
  clustered interval.)
- **Bucket breakdown per variant** — the stacked bar (`_draw_covert_breakdown`),
  with the *rare* buckets shown with their Wilson CIs, and **upper-bound-only cells
  visually marked** (e.g. hatched) so they aren't read as measured rates.
- **Contrast plot** — a small panel of the pre-specified differences (`as_only` −
  `gp_only`, etc.) with CIs, and a **dashed line at the MID** so a reader sees
  at a glance whether each effect clears the threshold that would matter.

### Reporting nulls rigorously

If the intervals overlap or an effect doesn't clear the MID, say so plainly, report
the MDE, and propose the next experiment. A clean, well-powered null is a real
result — particularly for "is the new covert-action bucket non-trivially
populated?".

---

## The workflow, in order

1. **Measure the ICC** from the pilot run (`estimate_icc`) — don't guess it.
2. **Choose the MID** for the primary contrast (the smallest `as`-vs-`gp` gap
   that would change your conclusion).
3. **Compute the screening N** (`items_per_variant`) and **pre-register** the
   primary contrast, MID, α, power, and event targets.
4. **Run the screening pass** across all variants; read the aligned-rate comparison;
   see which cells produce covert events.
5. **Top up** only the covert-producing cells to the event target (`n_for_events`).
6. **Analyze**: item-clustered CIs on variant rates; Wilson CIs / upper bounds on
   buckets; Holm-adjust the pre-specified contrast family.
7. **Report**: effect sizes with CIs, the MDE for any null, and the plots above.

---

## Glossary

- **Estimand** — the specific number the experiment exists to measure (here: the
  `as_only` − `gp_only` aligned-rate difference).
- **Power (1 − β)** — chance of detecting a real effect of the size you care about.
- **α (significance)** — chance of a false positive (declaring an effect that isn't
  there).
- **MID** — minimal important difference: the smallest effect worth detecting (you
  choose it).
- **MDE** — minimal detectable effect: the smallest effect a given sample size
  *could* detect (the calculation tells you).
- **ICC** — intra-class correlation: how alike repeated runs of one item are.
- **Design effect (DEFF)** — the sample-size penalty from clustering,
  `1 + (epochs − 1) × ICC`.
- **Wilson interval** — a confidence interval for a proportion that stays valid at
  small counts and rare rates.
- **Cluster bootstrap** — a confidence interval built by resampling the *clusters*
  (items), so the correlation within an item is respected.
- **Holm correction** — adjusts p-values for running several tests so the
  family-wide false-positive rate stays controlled.

---

## Where the calculations live

`src/pants_on_fire_eval/stats.py` — `items_per_variant`, `mde_two_proportions`,
`n_for_events`, `rule_of_three_upper`, `wilson_ci`, `cluster_bootstrap_ci`,
`estimate_icc`, `holm`. Run it as a script for an example sample-size plan.
