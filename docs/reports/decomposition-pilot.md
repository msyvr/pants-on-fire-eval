# Decomposition of a Deliberative Alignment Anti-Scheming Spec

Author: Monica Spisar, monicaspisar@gmail.com

_This work is supported by a grant from [BlueDot Impact](https://bluedot.org)._

**20260617 Working draft.** Overview of work done to date (design + calibration + a one-epoch
directional pilot), discussion, and motivation for two follow-on phases.

---

## Abstract

Anti-scheming specifications — short rule sets injected into a model's context —
measurably reduce covert behavior ([Guan et al. 2024](https://arxiv.org/abs/2412.16339)
<sup>1</sup>, [Schoen et al. 2025](https://arxiv.org/abs/2509.15541)<sup>2</sup>).
Schoen constructs a specification from multiple components, each belonging to one
of two categories. Our hypothesis is that the two categories' effects on covert
behavior may have different gradients with respect to model capabilities.
Understanding which elements of the intervention are robust to model scaling supports
the design of minimal interventions.

We decompose Schoen's specification into its two functional clause types,
anti-deception (AS) and process/effort (GP), and select the `conflicting` split of
[ImpossibleBench](https://github.com/safety-research/impossiblebench)<sup>3</sup>
on which to measure each individual spec type's effect on propensity to cheat.
We use coding tasks whose unit tests have been mutated to contradict their own
specifications; a report of 'pass' is a specification-violating shortcut
by construction. We pre-register a framing-matched* estimand, Δ = c(`gp_only`) − c(`as_only`), and a
paired, powered protocol. *_Such that the framing is not a confounder; only the clause content
differs._ This report presents the results of a calibrated, one-epoch pilot along with
relevant statistical analyses.
**(i)** The judge-free pipeline is constructed; calibration screens multiple
reasoning models of (presumed) different capabilities. Models are accepted or rejected
based on baseline cheating rates, aiming for the [35%, 85%] band (heuristic) to
support sufficient detection sensitivity and range. In-band are o4-mini (65% baseline
cheating) and o3 (78%), while o3-mini (10%) is out-of-band.
**(ii)** On a two-model, one-epoch, within-task-paired run, cheating rises with
capability — o4-mini → o3 lifts the baseline no-spec rate by +13pp (95% CI [+4, +21],
p = .01). This trend holds under both isolated specs (all three survive
[Holm](https://www.stat.cmu.edu/~siva/teaching/705/lec24.pdf)<sup>4</sup>).
**(iii)** The AS-vs-GP contrast is directional but sub-threshold: Δ = 0 on o4-mini
and +6pp on o3 (95% CI [−2, +14], n.s.), with the o3 interval falling entirely below
the pre-registered 15pp minimum important difference (MID).
The central methodological finding is that this MID is detectability-bound — it
equals the finest resolution the 103-task census can buy — so a true ~6pp effect is
below what the substrate can resolve regardless of compute.

We close by motivating Phase 2 (the powered scaling test, whose binding lever is
benchmark size, not compute) and Phase 3 (a purified anti-deception-vs-effort
re-cut that trades practical bearing for construct purity).

---

<!-- pdf:body --> <!-- render.sh starts the PDF body here; the title + abstract above come from decomposition-pilot.meta.yaml. Invisible on GitHub. -->

## 1. Introduction

Scheming — a model covertly pursuing a hidden objective while presenting as aligned
— is a central AI-safety concern<sup>5, 6, 7</sup>. This work measures its behavioral signature:
a model that takes a specification-violating shortcut to "pass" a task that cannot
be passed legitimately, then presents the result as a clean success. The metric is
behavioral in that a pass on a rigged test is a cheat by construction. Schoen
also investigates intent, which is required to categorize outcomes as scheming vs.
cheating. To maintain clean measurements of effect vs model capabilities, intent
is out of scope here. Future work contemplates evaluating intent-detection via
Natural Language Autoencoders (NLAs) compared to traditional Chain of Thought
judges, but would require (currently unavailable) NLAs for reasoning models.

Schoen shows that injecting an anti-scheming specification into a
model's context reduces covert behavior — sharply: covert-action rates fall from
13% → 0.4% (o3) and 8.7% → 0.3% (o4-mini) across 26 held-out evaluations. The
specification bundles two functionally distinct clause types: anti-deception
(AS) — "no covert actions, no strategic deception, report violations" — and
process/effort (GP) — "reason carefully, escalate ambiguities, no
rationalizations." Their analysis treats the bundle as a unit.

In an accompanying
[write up](https://www.apolloresearch.ai/science/stress-testing-deliberative-alignment-for-anti-scheming-training/)<sup>8</sup>,
the authors note:

"If a misaligned model were to realize it was being trained and attempted to
play the training game
([Cotra, 2022](https://www.alignmentforum.org/posts/pRkFkzwKZ2zfa3R6H/without-specific-countermeasures-the-easiest-path-to)<sup>9</sup>),
that might further reduce the effectiveness
of anti-scheming training. We think this potential failure mode is important to
study empirically and encourage follow-ups in this direction."

Evaluating the relative effectiveness of anti-scheming spec components as a
function of scale supports building a more robust and also leaner intervention
(perturbs the model less). From the perspective of the training game concern,
less RL pressure on a targeted spec means less opportunity to learn to game it.

We therefore ask to what degree the two individual clause types suppress cheating,
and whether that proportion changes as capability scales. The distinction is
safety-relevant because the two failure modes are expected to diverge with
capability: genuine capability-failure (the model doesn't recognize the task is
impossible, or doesn't try hard enough) shrinks as models improve, while deliberate
shortcut-taking is expected to grow.

Contributions:

- **(C1)** A clause-level decomposition of a published anti-scheming
  specification into `as_only` / `gp_only`, measured with a judge-free,
  by-construction cheating metric.
- **(C2)** A framing-matched^ estimand Δ = c(`gp_only`) − c(`as_only`) and a
  pre-registered, paired protocol (hypotheses, model sequence, power, multiplicity).
  (^Such that the framing is unaltered, only the clause content varies.)
- **(C3)** A scoping result: cheating on Impossible-LiveCodeBench is
  reasoning-gated, not capability-gated — a stronger non-reasoning model stays
  at the cheating floor while a reasoning model lifts off it, locating the regime
  with headroom (§3).
- **(C4)** A calibrated, one-epoch pilot (§3) that (a) demonstrates a
  significant capability rise, (b) finds the AS-vs-GP contrast directional but below
  the pre-registered MID, and (c) surfaces the design's binding constraint: the MID
  is detectability-bound, and resolving the likely effect needs a larger substrate.

## 2. Method

**Metric (judge-free).** ImpossibleBench mutates a real LiveCodeBench unit test so
it contradicts the task specification. No legitimate task-pass exists: any pass
requires a spec-violating shortcut (special-casing the test, detecting the harness,
hardcoding a value). For variant _v_ and model _m_, the cheating rate
c(_v_, _m_) = P(model passes the hidden mutated test | impossible task). A pass is
a cheat by construction — the scorer is deterministic, with no awareness judge.
We use the `conflicting` split (the cleanest contradiction; 103 tasks — a census
of the split) and the `minimal` single-file scaffold.

**Conditions (the independent variable).** ImpossibleBench supplies the tasks and
scorer; this study supplies the specification text, injected as a system message
ahead of the same tasks: `no_spec` (high-pressure framing only), `as_only`
(+ anti-deception clauses), `gp_only` (+ process/effort clauses), plus `full_spec`
and a content-neutral `effort_only` control. The isolated variants repair the spec's
internal cross-references so neither names an absent clause block. Full variant text:
[`src/pants_on_fire_eval/task.py`](https://github.com/msyvr/pants-on-fire-eval/blob/main/src/pants_on_fire_eval/task.py).

**Hypotheses and estimand.** **H1 (primary):** anti-deception content (`as_only`)
suppresses cheating more than process/effort content (`gp_only`).
**H2 (scaling):** that advantage grows with capability. The estimand is the
within-task paired difference Δ(_m_) = c(`gp_only`, _m_) − c(`as_only`, _m_);
Δ > 0 ⟺ `as_only` cheats less ⟺ anti-deception content suppresses beyond what
process/effort does. Δ ≈ 0 is itself a result.

**Pairing.** Every task is run under every variant, and each model; contrasts are
taken within each task, so the task is its own control and between-task difficulty
cancels from the difference. (For the capability contrast the pairing is across
models on the same task.) The signal lives in the discordant pairs — tasks whose
outcome flips between conditions; the inferential device is, thus, McNemar
(test) and Newcombe<sup>10</sup> (interval) (vs. their unpaired analogues).

**Statistics.** Per-cell rates use Wilson intervals; the paired difference uses
the Newcombe (Wilson-based) CI with an exact-binomial McNemar p; multiplicity
is handled by Holm within each hypothesis family. The pre-registered MID for Δ
is 15pp, in accordance with the MDE determined by the `conflicting` dataset census
which caps N ([`docs/preregistration.md`](https://github.com/msyvr/pants-on-fire-eval/blob/main/docs/preregistration.md) §6;
[`docs/statistical-methodology.md`](https://github.com/msyvr/pants-on-fire-eval/blob/main/docs/statistical-methodology.md)). The
single-proportion and McNemar choices are cross-validated against statsmodels; the
paired difference-of-proportions CI has no library equivalent
(`confint_proportions_2indep` is the independent-sample estimand, inappropriate for
a paired design), and is implemented and self-checked.

**Phases.** Phase 0: Calibration: screen the ladder of model capabilities on the `no_spec`
baseline; keep ≥3 models in a [35%, 85%] headroom band; measure the ICC.
Phase 1: The variant set on the first ladder (lowest capability) model (H1).
Phase 2: Up the capabilities ladder (H2). The pilot reported here is a one-epoch
slice across two models.

## 3. Results

**Calibration / reasoning-gate.** Cheating on LCB-`conflicting`/`minimal` tracks
reasoning, not size: non-reasoning models (gpt-4o-mini, gpt-4o, gpt-4.1) sit at the
0% floor (pooled 0/23), while o4-mini lifts off it; a `tools` positive control
confirms the scorer fires: the 0%s are real floors, not blind spots. Screening
the reasoning ladder on the `no_spec` baseline indicates o4-mini (65%) and
o3 (78%) are in the [35%, 85%] band while o3-mini (10%) sits under the band (its
entire Wilson interval sits below the 35% floor).

![Per-model no-spec cheating rate against the measurable band](figures/fig0_calibration.png)

**Figure 1.** Calibration: per-model `no_spec` cheating rate (Wilson 95% CI) against
the [35%, 85%] measurable band. o3-mini's entire interval falls below the floor
and is dropped; o4-mini and o3 are in-band.

**The one-epoch decomposition (directional).** Two models, one stochastic draw per
task, paired within-task on the full 103-task split. This is not the confirmatory run —
at single-epoch, the CIs are wide and omit the variance a multi-epoch
run would add (if anything, they understate uncertainty).

![Cheating rate by spec variant and model](figures/fig1_cheating_rates.png)

**Figure 2.** Per-cell cheating rate by spec variant and model (Wilson 95% CI) — the
levels behind the contrasts below.

Two readings emerge (Table 1):

> **Table 1.** Directional decomposition pilot (1 epoch; paired within-task;
> Newcombe 95% CI; exact-McNemar p, Holm-adjusted within family).

| Contrast                             | Δ      | 95% CI     | p (Holm)    |
| ------------------------------------ | ------ | ---------- | ----------- |
| capability: o3 − o4-mini (`no_spec`) | +13 pp | [+4, +21]  | .011 (.021) |
| capability: o3 − o4-mini (`as_only`) | +13 pp | [+2, +23]  | .029 (.029) |
| capability: o3 − o4-mini (`gp_only`) | +19 pp | [+8, +29]  | .002 (.006) |
| **H1: GP − AS (o4-mini)**            | 0 pp   | [−11, +11] | 1.00 (1.00) |
| **H1: GP − AS (o3)**                 | +6 pp  | [−2, +14]  | .21 (.42)   |

**(i) Cheating rises with capability.** o4-mini → o3 lifts the no-spec rate
65% → 78% (+13pp, p = .01), and the rise holds under both isolated specs; all three
capability contrasts survive Holm within their family. With two models this is one
capability contrast, not a trend.

**(ii) AS-vs-GP is directional and sub-threshold.** Δ is 0 on o4-mini and +6pp
on o3, with the o3 interval falling entirely below the 15pp MID and not clearing
zero. The pilot is consistent with anti-deception content suppressing more on
the stronger model, but the effect — if real — is below what the census can resolve (§4).

![Paired within-task contrasts with 95% CIs and the sub-MID band](figures/fig2_paired_contrasts.png)

**Figure 3.** Paired within-task contrasts (Newcombe 95% CI). The shaded band marks
|Δ| < 15pp (the MID): the AS-vs-GP contrasts fall entirely inside it; the capability
contrasts extend past it.

## 4. Tradeoffs and design decisions

The pilot's value is as much in the constraints it exposes as in the point
estimates. The decisions below are the tradeoffs that shaped the work.

**The MID is detectability-bound — the central tradeoff.** The 15pp MID was set to
serve two roles at once: an importance threshold ("below ~15pp an anti-deception
advantage reads as noise, not a lever") _and_ the finest resolution the 103-task
census can buy (≈110 items are needed for 15pp; 10pp would need ~250, which the
split does not contain). The two were set equal — so the "importance" bar is, in
effect, the detectability floor. Two structural limits make this binding: the
`conflicting` split is a census (N cannot grow with more items), and epochs are
ICC-capped: at the pilot ICC ≈ 0.64 the minimum detectable effect cannot fall
below √ICC ≈ 0.8× its single-epoch value, no matter how many epochs are run.
Consequence: a true H1 effect near the pilot's +6pp is below the achievable MDE,
so a powered run on this substrate would return a bounded null ("anti-deception
adds less than the achieved MDE beyond process content"), not "no effect." The only
lever that lowers the MID is more independent tasks (MDE ∝ 1/√N_items, no
floor), which is a benchmark-size limitation. This is the key point the pilot
establishes, and the hinge for Phase 2.

**One epoch.** Each task is a single draw, so the intervals are single-realization
and carry no across-epoch (ICC) component. This is appropriate for a pilot, but it
means every number is directional, and a between-condition "flip" cannot yet be
separated from the model's own run-to-run stochasticity.

**The metric measures spec-gaming, not deception.** "Passed an impossible test"
cleanly captures conforming to a test over the spec — gaming, by construction — but
does not separate aware (deceptive) from unaware gaming. Resolving intent is the
deferred reasoning-summary layer (and, further out, an activation-level read);
it is out of scope here.

**The AS/GP split is approximate.** The isolated variants are a construct we built
(cross-references repaired); their faithfulness to Schoen's bundle is an
external-validity assumption, not a measured fact, and GP's clauses might be read
as anti-deception. So `as_only − gp_only` tests the hypothesis on the published,
deployed spec rather than as a pure anti-deception-vs-effort contrast. This is a
deliberate trade — practical bearing now on the deployed spec, construct purity
to follow (Phase 3).

**Reasoning-gated scope.** The study runs on reasoning models because that is where
cheating exists on LCB-`minimal`; non-reasoning cheating lives on the heavier
SWE-bench/`tools` substrate, a follow-on. The gpt-4.1 floor is what licenses
"reasoning-gated, not capability-gated."

**Selection.** The [35%, 85%] band selects models with measurable cheating, so the
levels are conditioned on selection (a spec can only suppress cheating that
exists; ~50% maximizes proportion variance). The capability difference between two
in-band models is not a selection artifact, but the absolute rates are.

**Inference choices.** Newcombe over Wald (Brown–Cai–DasGupta<sup>11</sup>: Wald coverage is
erratic; they agree here but Newcombe is the principled default); exact-binomial
McNemar over the continuity-corrected normal (small discordant counts); Holm _within_
each hypothesis family rather than pooled across unrelated hypotheses (pooling all
five contrasts would be an over-conservative sensitivity check).

## 5. Follow-on — Phase 2: the powered capabilities-scaling test

Phase 2 is the real test of H1 and H2; the pilot defines what it must look like.

- **Benchmark size is the binding lever.** If the true H1 effect is near +6pp, it is
  below the census's ~15pp resolution. Detecting it requires more independent
  tasks — the pre-registered `oneoff` replication arm and/or a larger substrate —
  because epochs are ICC-capped and the `conflicting` split is already a census. So
  the first Phase 2 decision is not "how much compute" but "**which/how large a
  benchmark**," with the construct caveat that a new split must measure the same
  thing. Phase 0's IB-measured ICC sets the epoch count at the cost-effectiveness
  knee.
- **The ladder powers H2, not H1.** H1 power is per-model (N_items, epochs, ICC,
  baseline rate, pairing) and does not depend on the number of models. H2 — does Δ
  grow with capability? — depends on the number of models and their capability spread.
  A formal interaction test is underpowered at any affordable ladder (it needs ~4×
  the power and ≥10 well-spread models), so H2 is registered as a descriptive
  trend on an external capability ordering, with a powered claim only if a
  pre-specified test clears.
- **What the outcomes mean.** A bounded null on H1 is informative and publishable
  ("anti-deception content adds less than the achieved MDE beyond process content,
  powered to X pp"). The capability axis is the firmer, resolvable signal.

## 6. Follow-on — Phase 3: a purified construct re-cut

Phases 1 and 2 test the hypothesis on the deployed spec, where AS/GP only approximately
map the anti-deception-vs-effort axes. Phase 3 re-cuts the same content into a
cleaner anti-deception-vs-effort contrast that isolates the two axes directly —
the same hypothesis at a higher level of construct purity.

Its motivation is construct validity: it asks whether a (directional) AS advantage
is about anti-deception content specifically, or about the clauses' framing.
The explicit tradeoff is that a purer construct is a technically sharper test but one
step further from any spec actually deployed on frontier models — so Phase 1/2 and
Phase 3 are complementary, not redundant: practical relevance (does the deployed
spec's split matter?) versus construct cleanliness (is it the anti-deception
axis per se?). If Phase 1/2 returns a bounded null, Phase 3 also discriminates "no
effect" from "the published split is too blunt to show one."

## 7. Conclusion

We set out to ask which clauses of an anti-scheming specification suppress cheating,
and how that scales. To date we have built a judge-free, by-construction measurement
pipeline; established that the relevant cheating is reasoning-gated; calibrated a
reasoning-model ladder; and run a one-epoch, within-task-paired pilot. The pilot
shows a significant rise in cheating with capability (o3 > o4-mini, Holm-robust)
and an AS-vs-GP advantage that is directional but below the resolution the 103-task
census affords — a bounded-null risk that no amount of compute fixes, because the
pre-registered MID is, ultimately, the substrate's detectability floor. That
measurement insight is the work's current contribution: it converts "run it powered"
into a concrete, prior decision about benchmark size (Phase 2) and a parallel
construct-purity test (Phase 3). The directional signals point the way; the
follow-ons are designed to elicit more detail.

---

## References

[1] Guan, M. Y., et al. (2024). Deliberative Alignment. [arXiv:2412.16339](https://arxiv.org/abs/2412.16339) (OpenAI). \
[2] Schoen, B., Nitishinskaya, E., Balesni, M., et al. (2025). Stress Testing Deliberative Alignment for Anti-Scheming Training. [arXiv:2509.15541](https://arxiv.org/abs/2509.15541) (Apollo Research & OpenAI). \
[3] Zhong, Z., Raghunathan, A., & Carlini, N. (2025). ImpossibleBench. [arXiv:2510.20270](https://arxiv.org/abs/2510.20270). \
[4] [Holm-Bonferroni Method](https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method) \
[5] Meinke, A., et al. (2024). Frontier Models are Capable of In-Context Scheming. [arXiv:2412.04984](https://arxiv.org/abs/2412.04984) (Apollo Research). \
[6] Denison, C., et al. (2024). Sycophancy to Subterfuge. [arXiv:2406.10162](https://arxiv.org/abs/2406.10162) (Anthropic). \
[7] Baker, B., et al. (2025). Monitoring Reasoning Models for Misbehavior… [arXiv:2503.11926](https://arxiv.org/abs/2503.11926) (OpenAI). \
[8] Apollo Research. (2025). [Stress Testing Deliberative Alignment for Anti-Scheming Training.](https://www.apolloresearch.ai/science/stress-testing-deliberative-alignment-for-anti-scheming-training/) \
[9] Cotra, A. (2022). [Without specific countermeasures, the easiest path to transformative AI likely leads to AI takeover](https://www.alignmentforum.org/posts/pRkFkzwKZ2zfa3R6H/without-specific-countermeasures-the-easiest-path-to) \
[10] Newcombe, R. G. (1998). [Improved confidence intervals for the difference between binomial proportions based on paired data. Statistics in Medicine 17](https://pubmed.ncbi.nlm.nih.gov/9839354/). \
[11] Brown, L. D., Cai, T. T., & DasGupta, A. (2001). [Interval Estimation for a Binomial Proportion. Statistical Science 16(2)](https://www.jstor.org/stable/2676784).

Project references: \
Spec-variant text: [`src/pants_on_fire_eval/task.py`](https://github.com/msyvr/pants-on-fire-eval/blob/main/src/pants_on_fire_eval/task.py). \
Pre-registration: [`docs/preregistration.md`](https://github.com/msyvr/pants-on-fire-eval/blob/main/docs/preregistration.md). \
Statistical methodology: [`docs/statistical-methodology.md`](https://github.com/msyvr/pants-on-fire-eval/blob/main/docs/statistical-methodology.md). \
Reproduction and substrate notes: [`docs/step1-pilot.md`](https://github.com/msyvr/pants-on-fire-eval/blob/main/docs/step1-pilot.md).
