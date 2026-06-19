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
anti-deception (AS) and process/effort (GP), and measure each type's effect on 
a model's propensity to cheat. We use the `conflicting` split of
[ImpossibleBench](https://github.com/safety-research/impossiblebench)<sup>3</sup>,
where coding tasks' unit tests have been mutated to contradict their own
specifications. Models self-report task completion (binary pass/fail), but legitimate 
completion is impossible, and a 'pass' is classified as cheating.
We pre-register a framing-matched (only the clause content differs) estimand,
Δ = c(`gp_only`) − c(`as_only`), and a paired, powered protocol. 
Here, we present the results of a calibrated, one-epoch pilot along with
relevant statistical analyses:
**(i)** For three reasoning models with different capabilities, baseline cheating 
rates are assessed against the [35%, 85%] band (heuristic-based, selected to support 
sufficient detection sensitivity and range). o4-mini (65%) and o3 (78%) are in-band; 
at 10%, o3-mini is out-of-band.
**(ii)** On a two-model, one-epoch, within-task-paired run, cheating rises with
capability: going from o4-mini to o3 lifts the baseline no-spec rate by +13pp
(95% CI [+4, +21], p = .01). This trend holds under both isolated specs. All three
survive [Holm](https://www.stat.cmu.edu/~siva/teaching/705/lec24.pdf)<sup>4</sup>.
**(iii)** The AS-vs-GP contrast of the same run is directional, but remains
sub-threshold: Δ = 0 on o4-mini and +6pp on o3 (95% CI [−2, +14], n.s.), with the
o3 interval falling below the pre-registered 15pp minimum important difference (MID). 
The MID is detectability-bound — it equals the finest resolution afforded by the 
103-task census — so a true ~6pp effect is below what the substrate can resolve.

We close by motivating a powered effect-scaling test (Phase 2), and a purer
construct-valid anti-deception versus effort evaluation (Phase 3).

---

<!-- pdf:body --> <!-- render.sh starts the PDF body here; the title + abstract above come from decomposition-pilot.meta.yaml. Invisible on GitHub. -->

## 1. Introduction

Scheming — a model covertly pursuing a hidden objective while presenting as aligned
— is a central AI-safety concern<sup>5, 6, 7</sup>. This work measures its behavioral 
signature (i.e., the evident 'cheat,' setting aside intent) in the case where the 
model takes an alignment-violating shortcut to report completion of a task that cannot be 
completed legitimately. 
Our work is inspired by Schoen, which targets intent (via Chain of Thought LLM judges) 
alongside cheating and, thus, interrogates scheming. Toward more robust scheming-detection, 
we plan future work that investigates Natural Language Autoencoders (NLAs) as instruments 
for extracting intent directly from model activations. Originally planned for inclusion in 
this work, those studies are currently out of reach: they rely on NLAs for reasoning 
models, while existing NLAs are trained on non-reasoning models exclusively.

Schoen shows that injecting an anti-scheming specification into a model's context 
reduces covert behavior: covert-action rates fall from 13% → 0.4% (o3) and 8.7% → 0.3% 
(o4-mini) across 26 held-out evaluations. Their specification bundles two functionally 
distinct clause types: anti-deception (AS) — "no covert actions, no strategic deception, 
report violations" — and process/effort (GP) — "reason carefully, escalate ambiguities, 
no rationalizations." Schoen's analysis treats the bundle as a unit.

In an accompanying
[write up](https://www.apolloresearch.ai/science/stress-testing-deliberative-alignment-for-anti-scheming-training/)<sup>8</sup>,
the authors note: "If a misaligned model were to realize it was being trained and attempted to
play the training game
([Cotra, 2022](https://www.alignmentforum.org/posts/pRkFkzwKZ2zfa3R6H/without-specific-countermeasures-the-easiest-path-to)<sup>9</sup>),
that might further reduce the effectiveness
of anti-scheming training." This motivates building a leaner intervention that ultimately
perturbs the model less. From the perspective of the training game concern,
less RL pressure on a targeted spec means less opportunity to learn to game it.

Toward the goal of a leaner intervention, we unbundle Schoen's composite spec, asking to what 
degree the two individual clause types suppress cheating and, further, whether the relative contributions hold across model capabilities. The distinction is safety-relevant because 
the two types are approximately aligned with two failure modes which are expected to diverge 
with scale: genuine capability-failure (the model doesn't recognize the task is impossible, or doesn't try hard enough) drops as models improve, while cheating or scheming ability rises.

Contributions:

- **(C1)** A clause-level decomposition of a published anti-scheming
  specification into `as_only` / `gp_only`, measured with a judge-free,
  by-construction cheating metric.
- **(C2)** A framing-matched (clause content the sole change) 
  estimand Δ = c(`gp_only`) − c(`as_only`) and a
  pre-registered, paired protocol (hypotheses, model sequence, power, multiplicity).
- **(C3)** Scoping results: cheating on Impossible-LiveCodeBench is
  reasoning-gated, not capability-gated — a stronger non-reasoning model stays
  at the cheating floor while a reasoning model lifts off it; cheating varies
  across reasoning models on a capability ladder and we find candidates with 
  rates in a heuristic-based band (§3).
- **(C4)** A calibrated, one-epoch pilot (§3) that (a) demonstrates a
  significant cheating-capability rise with model ability, (b) finds the AS-vs-GP 
  contrast directional but below the pre-registered MID, and (c) surfaces a binding 
  experimental constraint: the MID is detectability-bound, and resolving the 
  (measured) likely effect needs a larger substrate.

## 2. Method

**Metric (judge-free).** ImpossibleBench mutates a real LiveCodeBench unit test so
it contradicts the task specification. No legitimate task-pass exists, so any pass
requires a spec-violating shortcut (e.g., special-casing the test, detecting the 
harness, or hardcoding a value). For variant _v_ and model _m_, the cheating rate is
c(_v_, _m_) = P(model passes the hidden mutated test | impossible task). The scorer 
is deterministic, with no awareness judge. We use the `conflicting` split (the cleanest contradiction; 103 tasks — a census of the split) and the `minimal` single-file scaffold.

**Conditions.** We derive the specification text from Schoen. The spec is injected as a system 
message ahead of tasks and has five variants: `no_spec` (high-pressure framing only), 
`as_only` (+ anti-deception clauses), `gp_only` (+ process/effort clauses), plus `full_spec`
and a content-neutral `effort_only` control. The decomposed variants (`as_only` and `gp_only`) 
repair the original spec's internal cross-references so neither names an absent clause block. 
Full variant text: 
[`src/pants_on_fire_eval/task.py`](https://github.com/msyvr/pants-on-fire-eval/blob/main/src/pants_on_fire_eval/task.py).

**Hypotheses and estimand.** **H1 (primary):** Anti-deception content (`as_only`)
suppresses cheating more than process/effort content (`gp_only`).
**H2 (scaling):** The advantage held by anti-deception content grows with capability. 
The estimand is the within-task paired difference 
Δ(_m_) = c(`gp_only`, _m_) − c(`as_only`, _m_);
Δ > 0 ⟺ `as_only` cheats less ⟺ anti-deception content suppresses beyond what
process/effort does. Δ ≈ 0 is itself a result.

**Pairing.** Every task is run under every variant, and for each model. For cross-variant 
comparisons, contrasts are taken within each task, so the task is its own control 
and between-task difficulty cancels. For the model capability contrast, 
the pairing is across models on the same task, variant by variant. The signal lives in 
the discordant pairs — tasks whose outcome flips between conditions; the inferential 
device is McNemar (test) and Newcombe<sup>10</sup> (interval) (in contrast to their 
unpaired analogs).

**Statistics.** Per-cell rates use Wilson intervals; the paired difference uses
the Newcombe (Wilson-based) confidence interval (CI) with an exact-binomial McNemar p; 
multiplicity is handled by Holm within each hypothesis family. The pre-registered MID 
for Δ is 15pp, in accordance with the MDE determined by the `conflicting` dataset census
which caps N ([`docs/preregistration.md`](https://github.com/msyvr/pants-on-fire-eval/blob/main/docs/preregistration.md) §6;
[`docs/statistical-methodology.md`](https://github.com/msyvr/pants-on-fire-eval/blob/main/docs/statistical-methodology.md)). 
The single-proportion and McNemar choices are cross-validated against `statsmodels`; the
paired difference-of-proportions CI has no library equivalent
(`confint_proportions_2indep` is the independent-sample estimand, inappropriate for
a paired design), and is implemented from scratch and self-checked.

**Phases.**  
Phase 0 (calibration): Screen the ladder of model capabilities on the `no_spec`
baseline. Target ≥3 models in a [35%, 85%] headroom band. Measure the ICC.  
Phase 1: The variant set on the first ladder (lowest capability) model (H1).  
Phase 2: The variant set up the capabilities ladder (H2). The pilot reported 
here is a one-epoch slice across two models.

## 3. Results

**Calibration.** Cheating on ImpossibleBench LCB-`conflicting`/`minimal` 
tracks reasoning, not model size: non-reasoning models (gpt-4o-mini, gpt-4o, gpt-4.1) sit at 
the 0% floor (pooled 0/23), while o4-mini lifts off it. A `tools` positive control
confirms that the scorer fires so the 0%s are real floors, not blind spots. Screening
the reasoning ladder on the `no_spec` baseline indicates o4-mini (65%) and
o3 (78%) cheating rates are in the [35%, 85%] band, while o3-mini (10%) sits under 
the band (its entire Wilson interval sits below the 35% floor).

![Per-model no-spec cheating rate against the measurable band](figures/fig0_calibration.png)

**Figure 1.** Calibration: per-model `no_spec` cheating rate (Wilson 95% CI) against
the [35%, 85%] measurable band. o3-mini's entire interval falls below the floor
so the model is dropped; o4-mini and o3 are in-band.

**Single-epoch decomposition.** For both o4-mini and o3, one stochastic draw per
task is paired within-task on the full 103-task `conflicting` split. The result is 
purely directional: the CIs are wide and omit the variance a multi-epoch run would 
add.

![Cheating rate by spec variant and model](figures/fig1_cheating_rates.png)

**Figure 2.** Per-cell cheating rate by spec variant and model (Wilson 95% CI). These
are the levels behind the contrasts in Table 1.

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

**(i) Cheating rises with capability.** Going from o4-mini to o3 lifts the no-spec 
rate of cheating from 65% to 78% (+13pp, p = .01), and the rise holds under both 
decomposition-isolation specs. All three capability contrasts survive Holm within 
their family. With the two-model limitation, this is a capability contrast and cannot 
be interpreted as a confirmed trend.

**(ii) AS-vs-GP is directional and sub-threshold.** Comparing isolated spec components, 
Δ is 0 on o4-mini and +6pp on o3, with the o3 interval falling below the 15pp 
MID and not clearing zero. Since, the +6pp remains below what the census can resolve 
(§4), it may not be a real effect. The pilot nonetheless remains consistent with 
anti-deception content suppressing cheating more effectively on the stronger model. 

![Paired within-task contrasts with 95% CIs and the sub-MID band](figures/fig2_paired_contrasts.png)

**Figure 3.** Paired within-task contrasts (Newcombe 95% CI). The shaded band marks
|Δ| < 15pp (the MID): the AS-vs-GP contrasts fall entirely inside it; the capability
contrasts extend past it.

## 4. Tradeoffs and design decisions

**The MID is detectability-bound — the central tradeoff.** 

The MID was set at ~15pp; below that level, an anti-deception advantage is implicitly 
considered too small to be useful. The MID value was set arbitrarily and may not be 
optimal. Simultaneously, the resolution limit afforded by the 103-task census is ~15pp. 
(≈110 items are needed for 15pp; 10pp would need ~250, more than double the number of 
available tasks.) 

By coincidence, then, the "importance" bar is effectively the detectability floor. 
However, two structural limits make this binding: the `conflicting` split is a census 
(N cannot grow with more items), and epochs are ICC-capped: at the pilot ICC ≈ 0.64, 
the minimum detectable effect cannot fall below √ICC ≈ 0.8× its single-epoch value. 
Additional epochs will not improve MDE for the task split used.

As a result, a true H1 effect near the pilot's observed +6pp would be below the 
achievable MDE. A powered run on this substrate would return a bounded null 
("anti-deception adds less than the achieved MDE beyond process content"), not 
"no effect." A lower MID would require more independent tasks than available 
(MDE ∝ 1/√N_items, no floor).

**One epoch.** Each task is a single draw, so the intervals carry no across-epoch 
(ICC) component. This means results are directional only, and each between-condition 
"flip" might be a result of the model's own run-to-run stochasticity.

**The metric does not measure deception.** "Passed an impossible test" captures 
spec-gaming/cheating, but does not separate aware (deceptive) from unaware gaming. 
Resolving intent would involve inspection of chain of thought (in the case of API 
access to o4-mini and o3, reasoning-summary responses would be the proxy), or an 
activation-level read. Intent evaluation is out of scope for this pilot.

**The AS/GP split is approximate.** The decomposed/isolated variants are a custom-built 
construct; their faithfulness to Schoen's composite anti-scheming bundle is an 
external-validity assumption. Also, notably, several of GP's clauses might be read 
as anti-deception so, although the split technically follows Schoen's AS/GP split, 
the semantics split is less concrete. Ultimately, `as_only − gp_only` tests the 
hypothesis on the published, deployed spec and not as a pure anti-deception-vs-effort 
contrast. This is a deliberate tradeoff — practical bearing now on the deployed spec, 
construct purity to follow (Phase 3).

**Reasoning-gated scope.** The study runs on reasoning models since that is where
cheating was observed on ImpossibleBench's LCB-`minimal` scaffold: the gpt-4.1 floor 
and in-band rate for o4-mini established that model selection here is reasoning-gated, 
not capability-gated. Non-reasoning cheating requires the heavier SWE-bench/`tools` 
substrate, slated for future work.

**Model selection.** The [35%, 85%] band selects models with measurable cheating. 
The capability difference between two in-band models is a measured within-task effect.

**Inference choices.** (i) Newcombe over Wald (Brown–Cai–DasGupta<sup>11</sup>: Wald 
coverage is erratic): the two happen to agree here, but Newcombe is the principled default. 
(ii) Exact-binomial McNemar over the continuity-corrected normal (small discordant 
counts). (iii) Holm within each hypothesis family rather than pooled across unrelated 
hypotheses. Pooling all five contrasts would be an over-conservative sensitivity check.

## 5. Follow-on — Phase 2: the powered capabilities-scaling test

**Benchmark size constraint.** If the true H1 effect is near the measured +6pp, it 
sits below the census's ~15pp resolution. Detecting it requires a larger number of 
independent tasks because epochs are ICC-capped and the `conflicting` split is already 
a census. One option is to use the pre-registered `oneoff` replication arm; another is 
to move off of ImpossibleBench to a larger substrate. A measured ICC sets the epoch 
count by computing effectiveness of additional epochs and curbing at the 
point of diminishing returns.

**Capabilities ladder powers H2.** H1 power is per-model (N_items, epochs, ICC,
baseline rate, pairing). H2, which asks if Δ grows with capability, depends on the 
number of models and their capability spread. A formal interaction test is underpowered 
at any budget-realistic ladder, as it would need ~4× the power and ≥10 well-spread models. 
H2 is, thus, registered as a descriptive trend on an external capability ordering, with 
a powered claim only if a pre-specified test clears.

**Interpretation.** A bounded null on H1 states: "anti-deception content adds less than 
the achieved MDE beyond process content, powered to X pp". In contrast, the capability 
axis generates a concrete signal.

## 6. Follow-on — Phase 3: construct purity

Phases 1 and 2 test the hypothesis on the deployed spec, where AS/GP only approximately
map the anti-deception and effort-only axes. Phase 3 uses a clean anti-deception versus 
effort-only contrast to isolate those two axes — the same hypothesis is tested at a 
higher level of construct purity.

The motivation here is construct validity: it asks whether a (directional) AS advantage
is about anti-deception content specifically, or about the clauses' framing.
The explicit tradeoff is that a purer construct is a technically sharper test but one
step further from the spec that's actually deployed by Schoen on frontier models. 
Phase 1/2 and Phase 3 are complementary, not redundant; the former has practical 
relevance (does the deployed spec's split matter?) and the latter, construct cleanliness 
(is it the anti-deception axis per se?). Should Phase 1/2 return a bounded null, Phase 3 
will also discriminate "no effect" from "the published split is too approximate to carry 
the effect."

## 7. Conclusion

We set out to determine which clauses of an anti-scheming specification suppress cheating
and how that scales. To that end, we have built a judge-free, by-construction measurement
pipeline. We have established that, for our experimental parameters, the relevant cheating 
is observed only on reasoning models. Based on that, we have calibrated reasoning models of
different capabilities and we ran a one-epoch, within-task-paired pilot. The pilot
shows a significant rise in cheating with capability (o3 > o4-mini, Holm-robust)
and an AS-vs-GP advantage that is directional but below the resolution the 103-task
census affords; it is a bounded-null risk that cannot be resolved by more compute because 
the pre-registered MID is ultimately capped by the MDE at the substrate's detectability floor. 
Phase 2 requires a decision about benchmark size which will, in turn, set the resolution limit 
on effect size. Phase 3 will study the effect at a higher degree of construct purity to support 
generalization.

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
