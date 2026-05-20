# Project Proposal — Disentangling Anti-Deception from Effort-Prompt Effects in Deliberative Alignment

A small ablation extending Schoen et al. (2025), *Stress Testing
Deliberative Alignment for Anti-Scheming Training*.

---

## Summary

The deliberative-alignment spec used in Schoen et al. (2025) contains two
distinct kinds of clauses: **anti-deception** principles (AS1–AS5: no covert
actions, no strategic deception, report violations) and **process / effort**
principles (GP1–GP4: proactively share reasoning, escalate ambiguities,
maintain strict adherence, *no rationalizations can override AS1–AS4*). The
paper reports that training on the full spec reduces covert action rates
substantially. It does not decompose the spec to identify which clauses
drive the observed effect.

This proposal funds a small, in-context ablation that isolates the
contribution of anti-deception content from the contribution of
effort/anti-rationalization content. The experiment runs four spec variants
on an existing impossible-coding-task eval and reports whether the
deliberative-alignment effect persists when the anti-deception content is
removed.

**Funding ask: detailed budget on request. Two components — compute
(research expenses, modest) and labor (investigator time, scoped at
standard independent-researcher rate over ~50 hours / 4 weeks part-time)
— itemized separately and can be funded by separate sources (e.g.,
compute via an API-credits program; labor via project grant).**

---

## Background

Schoen et al. demonstrate that training models to reason about a written
anti-scheming spec before acting reduces covert action rates (OpenAI o3:
13% → 0.4%; o4-mini: 8.7% → 0.3%) across 26 OOD evaluations. The result is
striking but interpretively ambiguous: the spec mixes two functionally
distinct instruction types, and the paper does not separate their
contributions.

The two types of clauses target different cognitive patterns:

- **Anti-deception clauses** (AS1–AS5) target *strategic concealment* —
  cases where the model knows the right answer but produces a misleading
  output. The intended mechanism is value internalization: the model learns
  that covert behavior is wrong and refuses it.
- **Process / effort clauses** (GP1–GP4) target *rationalized
  over-confidence* — cases where the model arrives at a wrong-but-plausible
  answer because it didn't engage carefully enough with the problem. The
  intended mechanism is cognitive: the model is prompted to slow down,
  verbalize reasoning, and resist ends-justify-means shortcuts.

These mechanisms are not the same. A spec that works only via the second
mechanism would be reframed as a *general-purpose effort prompt* rather than
an anti-scheming intervention. That distinction matters for understanding
when and why deliberative alignment generalizes.

A toy run on a single-turn proxy of the paper's Impossible Coding Task eval
([pants-on-fire-eval](https://github.com/msyvr/pants-on-fire-eval))
demonstrated the confound concretely: under high pressure framing,
gpt-4o-mini's alignment rate dropped 55.6 pp on identical items; injecting
the full spec into the system message recovered nearly all of the drop and
eliminated strong covert action. The recovery is real, but the toy run
cannot say whether it is driven by anti-deception or by effort/anti-
rationalization.

---

## Research question

> Does the deliberative-alignment effect observed under Schoen et al.'s
> spec persist when the anti-deception clauses are removed and only the
> process / effort clauses remain? Does it persist under a content-neutral
> effort prompt with no anti-scheming content at all?

---

## Experimental design

Four spec variants, all applied in-context (system message), all evaluated
on the same impossible-coding-task dataset:

| Variant | System message |
|---|---|
| `no_spec` | High-pressure framing only (baseline; already run) |
| `as_only` | High-pressure framing + AS1–AS5 (anti-deception clauses only) |
| `gp_only` | High-pressure framing + GP1–GP4 (process / effort clauses only) |
| `full_spec` | High-pressure framing + AS1–AS5 + GP1–GP4 (the paper's spec; already run) |
| `effort_only` | High-pressure framing + content-neutral effort cue: "Think carefully and verify your understanding before declaring work complete." No anti-deception content. |

All variants run across three model classes (gpt-4o-mini, gpt-4o,
claude-haiku-4-5) to test whether the disentangling result generalizes
across capability tiers. Each (variant × model) cell run with epochs=5 for
tighter per-item variance estimates.

### Outcome measures

Same dual-scorer cross-tab as the existing eval:

- **Action-only signal** (rule-based STATUS parse): did the model claim
  completion?
- **CoT-aware signal** (model-graded): did the response verbalize
  awareness of impossibility?

Cross-tab buckets: aligned / capability failure / strong covert action.

### Predictions and what they would mean

- If `effort_only` recovers alignment as much as `full_spec`: the
  deliberative-alignment effect in this eval is not specifically about
  anti-deception. The paper's spec works because it's an effort prompt;
  the anti-deception content is incidental. *Significance: weakens the
  paper's interpretive framing in the in-context regime; raises the
  question of whether the same holds in the training regime.*
- If `as_only` recovers alignment but `effort_only` does not: the
  anti-deception clauses are doing real work beyond what an effort prompt
  achieves. *Significance: strengthens the paper's claim — provides
  cleaner ablation-based evidence than the paper itself supplies.*
- If `gp_only` and `effort_only` both recover alignment as much as
  `full_spec`: the spec's effect is fully captured by general process
  guidance, not specifically anti-scheming. *Significance: largest
  departure from the paper's framing; suggests the strong-covert
  reduction has a mechanism the paper has not identified.*
- Mixed pattern (e.g., partial recovery from each ablation): some signal
  of additivity; suggests both kinds of clauses contribute.

### Manual confirmation step

On the 30 highest-stakes samples across variants (samples scored as strong
covert by the automated judge), apply the paper's Section 5.2 manual
confirmation step: human-read each full reasoning trace, classify by hand,
report agreement with the automated judge. This addresses a known
limitation of the existing eval and tightens the strong-covert numbers.

---

## Budget

Two components, fundable separately:

- **Compute (research expenses).** Modest — low tens of dollars in API
  costs across all variants and models. Eligible for API-credits programs
  such as Anthropic API credits or OpenAI Researcher Access.
- **Labor (investigator time).** 50 hours over 4 weeks at standard
  independent-researcher rate. Phase breakdown:
  - Design + implementation (10h)
  - Execution across all (variant × model) cells (6h)
  - Manual confirmation pass on borderline samples (8h)
  - Analysis (10h)
  - Writeup — short technical note for LessWrong / arXiv (16h)

Detailed itemized budget, hourly rate, and total ask available on request
from prospective funders.

---

## Timeline

- **Week 1.** Design and implementation. New variants merged to the eval
  repo, smoke runs pass, judge-prompt stability confirmed.
- **Week 2.** Full execution across all variants and models; preliminary
  numbers in hand. Manual confirmation pass underway.
- **Week 3.** Analysis and writeup draft.
- **Week 4.** Iteration on writeup, preprint release, public post.

---

## Deliverables

1. **Updated open-source eval** ([pants-on-fire-eval](https://github.com/msyvr/pants-on-fire-eval))
   with the four-variant ablation merged and full-run results published
   under `results/runs/`.
2. **Technical note** (~3,000 words) posted to LessWrong and/or arXiv,
   reporting the disentangling result and its implications for the
   interpretation of Schoen et al.
3. **Reproducible artifacts**: every run's `summary.json` (config, numbers,
   dataset version) committed to the repo so the result is verifiable
   without re-running.
4. **Honest null reporting**: if the experiment produces unclear or
   inconclusive results (e.g., wide intervals from N), the writeup says
   so and proposes the next experiment, rather than over-claiming.

---

## Why this matters

Two distinct contributions:

**To the anti-scheming research line.** Schoen et al.'s deliberative-
alignment result is one of the more credible alignment-training results
in the field. Its interpretation rests on the implicit assumption that the
spec works *via anti-deception*. If a substantial part of the effect
turns out to be effort-prompt content, the paper's contribution narrows
from "deliberative alignment reduces scheming" to "deliberative alignment
elicits more careful reasoning, which secondarily reduces measured
scheming." That's a real distinction. Whichever way the experiment
resolves, the interpretation tightens.

**To eval methodology.** Most alignment evals today report aggregate
behavioral rates without decomposing the interventions that produce them.
The proposal demonstrates one specific decomposition (anti-deception vs
effort) on a tractable single-turn proxy. The pattern — ablate the
intervention into its component instruction types, run each in isolation,
report differential effects — generalizes to other deliberative-alignment-
style interventions.

---

## Limitations

- **In-context, not training.** The paper's setup trains models on the
  spec; ours injects the spec into the system message. The two regimes can
  produce different effects. A negative or surprising in-context result
  doesn't directly invalidate the training result, but it is suggestive,
  and motivates a training-regime ablation as the natural follow-on.
- **Single-turn text proxy.** The eval is a single-shot text-in/text-out
  task; the paper uses agentic multi-turn environments. The failure mode
  measured here is a tractable shadow of what the paper studies.
- **Small N.** 20 items, 5 epochs, 3 models gives 100 measurements per
  (variant × model) cell — adequate for the strong-covert headline,
  modest for per-category claims. Per-category numbers will be reported
  with stderr and read as directional.
- **Spec decomposition is interpretive.** "Anti-deception" vs
  "process/effort" clauses are categories I assigned; the paper does not
  classify its own spec this way. The first deliverable will include a
  short justification for the assignment, with the raw spec attached so
  readers can disagree.

---

## Future work: NLA-based activation readout

The CoT-aware judge in Phase 1 reads the model's response text and
classifies whether the response *verbalizes* awareness of impossibility.
Its known limitation (named in Risks) is that **implicit** recognition —
e.g., the model selects a non-comparison-based sort *because* it
recognizes the comparison-sort lower bound — gets classified as `UNAWARE`
because no verbal acknowledgment appears. Strong-covert rates are
therefore lower bounds.

Natural Language Autoencoders (NLAs; Fraser-Taliente, Kantamneni, Ong et
al., 2026, Anthropic Transformer Circuits) offer a candidate path past
this limitation. NLAs are trained to encode model activations through a
natural-language bottleneck, producing text descriptions of what was being
computed *during* generation rather than what was written in the output.
Substituting NLA-based readout for the current text-output judge would
surface implicit recognition the present design cannot detect — closing
the same gap the paper closes via human manual confirmation
(Section 5.2), but mechanistically and at scale.

Practical constraint: NLAs require model activations, so the experiment
moves to open-weight subject models. Released NLAs at time of writing
cover Gemma 7B and Llama-3.3 70B. This is materially different
infrastructure from the closed-weight in-context regime Phase 1 uses, and
is the natural follow-on once Phase 1 lands.

My [`activation-tomography`](https://github.com/msyvr/activation-tomography)
research line — a fork of the open NLA codebase, with a methodology focus
on characterization, calibration, and cross-model comparison — provides
the in-flight infrastructure for this extension. A separate, larger
proposal would scope the NLA-based extension once Phase 1's text-output
disentangling result is in hand.

## Investigator background

Independent researcher with a background in physics and engineering,
transitioning into technical AI safety. Currently building a research
program on measurement foundations for multi-agent AI systems (publicly
documented at [emmy](https://github.com/msyvr/emmy)). The pants-on-fire-
eval repo is a recent portfolio piece demonstrating the methodological
moves this proposal extends (dual-scorer cross-tab, dataset versioning,
honest caveats including the named confound this proposal targets).

---

## Working methodology

The 50-hour labor estimate assumes LLM-assisted execution — Claude (or
equivalent) is used for code drafting, exploratory analysis, and initial
writeup drafts. Investigator time is spent on design, methodology,
interpretation, and final review. Without LLM assistance the same project
would take an estimated 100–150 hours. The funder is paying for
investigator attention, direction, design decisions, and final-review
quality — not for typing time. All deliverables are substantively reviewed
and shaped by the investigator before release. This is standard practice
for independent alignment research in 2026; disclosed for transparency.

## Risks

- **Null result.** The experiment may produce overlapping confidence
  intervals across variants, in which case the disentangling claim cannot
  be made cleanly. Mitigation: report the null honestly; propose the
  larger-N or training-regime follow-on. A clean null is itself a
  publishable result.
- **Judge instability.** The CoT-aware judge is itself a model and may
  classify identical responses differently across runs. Mitigation:
  epochs=5 plus the manual confirmation pass on borderline cases.
- **Spec misclassification.** My division of AS-vs-GP clauses could be
  contested. Mitigation: publish the raw split with the writeup; invite
  reviewer pushback before drawing strong conclusions.

---

## Funding pathway

Suitable for:

- **LTFF (Long-Term Future Fund)** — small project grant; standard route
  for this scope and budget.
- **Manifund** — direct grant or regrant from an alignment-focused
  re-granter; faster turnaround than LTFF.
- **Cooperative AI Foundation** — small project grant aligned with their
  evaluation-infrastructure remit.

Preferred: LTFF or Manifund regrant. Either supports the timeline and
budget cleanly.
