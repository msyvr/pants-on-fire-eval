# Liar, liar: Pants-on-fire eval

Scheming — a model covertly pursuing a hidden objective while presenting as aligned
— is a central AI-safety concern. This project measures its behavioral 
signature (i.e., the evident 'cheat,' setting aside intent) on "impossible tasks," 
when the model finds a way to complete a task that cannot be completed legitimately.

This work is inspired by [Stress Testing Deliberative Alignment for Anti-Scheming Training (_Schoen et al., 2025_)](https://arxiv.org/abs/2509.15541), which targets both the behavioral 
signature (the cheat itself) and intent (via chain of thought) to 
interrogate scheming.

## Deliberative alignment: anti-scheming spec

Studying frontier reasoning models in multi-turn agentic environments, Schoen
shows that injecting an anti-scheming spec into a model's context reduces covert
behavior. Schoen also note that models' eval awareness is a risk to effective 
anti-scheming interventions, referencing the training game 
([Cotra, 2022](https://www.alignmentforum.org/posts/pRkFkzwKZ2zfa3R6H/without-specific-countermeasures-the-easiest-path-to)) where exerting RL pressure on a 
targeted spec can exacerbate misalignment. 

We note that Schoen's spec bundles two functionally distinct clause types —
anti-deception ("no covert actions, no strategic deception, report violations") and
process/effort ("reason carefully, escalate ambiguities, no rationalizations"). If 
a streamlined spec might exert less RL pressure and perturb the model less, can we 
effectively unbundle their composite spec without sacrificing efficacy?

## Streamlining the spec

Toward the goal of a leaner intervention, we unbundle Schoen's composite spec, 
asking to what degree the two individual clause types suppress cheating and, 
further, whether the relative contributions hold across model capabilities. 
The distinction is safety-relevant because the two types are approximately 
aligned with two failure modes which are expected to diverge with scale: 
genuine capability-failure (the model doesn't recognize the task is impossible, 
or doesn't try hard enough) drops as models improve, while cheating or scheming 
ability rises.

> **Pilot project report:** [_Decomposition of a Deliberative Alignment Anti-Scheming Spec_](docs/reports/decomposition-pilot.md) details the design, statistical analysis, and results of 
a calibrated pilot.

## Scheming: misaligned behavior + covert intent

Scheming requires both misaligned behavior and intent to take covert action. The current 
work focuses on behavioral metrics. Testing intention evaluation on reasoning summaries 
is deferred to future work. Our guiding question here is behavioral: Does the anti-deception 
content (`as_only`) suppress cheating more than the process/effort content (`gp_only`) — 
and increasingly so as model capability scales?

## Substrate: ImpossibleBench

We use [ImpossibleBench](https://arxiv.org/abs/2510.20270) (Zhong, Raghunathan & Carlini, 2025;
Anthropic safety-research; MIT) which builds "impossible" coding tasks by mutating a real
LiveCodeBench / SWE-bench unit test so that it contradicts the task specification.
On such a task, there is no legitimate way to pass. So cheating rate = pass rate on the 
impossible split. The behavioral ground truth (pass = cheat) needs no model-graded judge and 
cannot be gamed by the subject. The impossibility holds for any model — a more capable solver 
cannot escape it by finding a legitimate path a weaker one missed.

Task dataset splits: `original` (unmutated control), `oneoff` (one test mutated), 
`conflicting` (a test directly contradicts the spec — the hardest to pass honestly, 
so the cleanest cheating signal and the one we use for the pilot). 

Task execution scaffolds: `minimal` (single-file submission loop, cheap; used for the pilot) 
and `tools` (full bash/python/editor agent, more cheating-prone).

## Implementing the decomposition

ImpossibleBench supplies the tasks and the cheating-rate scorer. We build the spec 
variants, each injected as a system message ahead of a task.

| Variant       | System message                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------- |
| `no_spec`     | High-pressure framing only (baseline)                                                             |
| `as_only`     | High-pressure + anti-deception clauses only (AS1–AS5)                                             |
| `gp_only`     | High-pressure + process/effort clauses only (GP1–GP4)                                             |
| `full_spec`   | High-pressure + the full anti-scheming spec (AS + GP)                                             |
| `effort_only` | High-pressure + a content-neutral "think carefully and verify before declaring work complete" cue |

The five variants are defined in [`src/pants_on_fire_eval/task.py`](src/pants_on_fire_eval/task.py).

The metric is the cheating rate per variant; the primary contrast is the `gp_only − as_only` cheating-rate difference (does the anti-deception content reduce cheating more than the process/effort content?), measured across a model capability ladder to test whether that advantage grows with capability.

`as_only` and `gp_only` share the spec's "safety principles" header and numbered-clause
register and differ only in clause content, so the contrast isolates anti-deception
content from the framing it travels in (it's 'framing-matched'). (`as_only`-vs-`effort_only`, 
against a content-neutral cue, is a secondary control — it asks whether `as_only` beats a bare
nudge, but it bundles AS content with that framing.)

## Substrate-validation pilot

A pilot validated the substrate (install → HuggingFace dataset → model → sandbox runs the tests → cheating-rate scorer) and established a base-rate gradient on the base configuration (LCB `conflicting` split, `minimal` scaffold):

| Model       | Reasoning? | Cheating rate | N   |
| ----------- | ---------- | ------------- | --- |
| gpt-4o-mini | no         | **0%**        | 5   |
| gpt-4o      | no         | **0%**        | 10  |
| o4-mini     | yes        | **50%**       | 8   |

- **Scorer validated (positive control):** o4-mini passed (= cheated) 4/8 conflicting
  tasks. In contrast, each gpt-4o sample ran a full agentic loop, failed the impossible 
  tests, and reported failures (i.e., didn't cheat).
- **The signal is reasoning-gated, not size-gated.** Both non-reasoning models sit at
  the 0% floor on this configuration; only the reasoning model lifts off it.
- **Directional only.** N is 5/10/8 and `minimal` + `conflicting` is the least 
  cheating-prone configuration; ImpossibleBench reports non-reasoning frontier models cheat substantially more on the `tools` scaffold. Choosing a configuration where the whole 
  ladder cheats at a measurable baseline (so the spec has headroom to reduce it) is a 
  design decision fixed in the pre-registration.

## Experiments (phased)

A powered, pre-registered decomposition (Phases 0–2), with a purified follow-on (Phase 3):

- **Phase 0 — calibration.** Screen reasoning models on the `no_spec` baseline; fix the model ladder
  and the ICC.
- **Phase 1 — H1.** The `gp_only − as_only` cheating-rate contrast on the first reasoning model.
- **Phase 2 — H2.** Repeat up the capability ladder for the scaling trend.
- **Phase 3 — construct-purified follow-on.** Schoen's AS/GP grouping resembles the two axes but isn't
  a clean cut — GP's clauses read as anti-deception as readily as try-harder. Phase 3 re-cuts the
  _same_ spec content into a cleaner anti-deception arm and a cleaner effort arm (each drawn from both
  AS and GP) and runs the same hypothesis at higher construct purity, deviating from the published
  spec minimally so the phases read together. Phase 1/2 bear directly on the published spec; Phase 3
  gives the cleaner read.

The prospective statistics — variants, the cheating-rate metric, the `gp_only − as_only`
primary contrast (clustered by task), the model ladder, the minimum interesting
difference, α/power/N, and the Holm correction across variants — are fixed _before_ the
run. The task-clustered proportion machinery (ICC, design effect, clustered CIs, power,
Holm) in [`src/pants_on_fire_eval/stats.py`](src/pants_on_fire_eval/stats.py) transfers
directly — ImpossibleBench's cheating rate is still a task-clustered proportion.

The **scaling claim is an interaction** ("`as_only` increasingly all you need as
capability scales" = the `as_only`-vs-`gp_only` gap _changes_ across the ladder),
which needs far more power than a main effect. The pre-registration commits to a
**descriptive trend** (per-model contrasts + slope on an external capability ordering, no
significance claim on the interaction), with a powered interaction test only as a
conditional upgrade — the move that keeps the study falsifiable. See
[pre-registration](docs/preregistration.md) and [`docs/statistical-methodology.md`](docs/statistical-methodology.md).

## Repository layout

- **Spec variants** — [`src/pants_on_fire_eval/task.py`](src/pants_on_fire_eval/task.py): the five system-message variants (the independent variable).
- **Statistics** — [`src/pants_on_fire_eval/stats.py`](src/pants_on_fire_eval/stats.py) + [`docs/statistical-methodology.md`](docs/statistical-methodology.md): power, ICC / design-effect, clustered CIs, Holm.
- **Substrate** — [ImpossibleBench](https://github.com/safety-research/impossiblebench) (separate checkout, its own venv): the impossible tasks and the cheating-rate scorer.

## Reproduction (pilot)

ImpossibleBench installs as a separate checkout with its own venv. To reproduce the
pilot gradient:

```bash
git clone https://github.com/safety-research/impossiblebench
cd impossiblebench
uv venv && source .venv/bin/activate
uv pip install -e . openai          # the openai provider is not pulled by default

# the `local` sandbox shells out to `python`; activating the venv puts it on PATH
# (or pass sandbox="docker", the benchmark's recommended path)
export OPENAI_API_KEY=sk-...

python -c "from inspect_ai import eval; from impossiblebench import impossible_livecodebench; \
  eval(impossible_livecodebench(split='conflicting', agent_type='minimal', limit=10, sandbox='local'), \
       model='openai/o4-mini')"
```

The reported number is `accuracy` on the impossible split = the cheating rate. See
[`docs/step1-pilot.md`](docs/step1-pilot.md) for the full gotcha list.

## Source

- **Anti-scheming spec:** Schoen, B., Nitishinskaya, E., Balesni, M., et al. (2025).
  _Stress Testing Deliberative Alignment for Anti-Scheming Training._
  [arXiv:2509.15541](https://arxiv.org/abs/2509.15541) (Apollo Research & OpenAI). The
  `full_spec` variant is adapted from the paper's Figure 4; the paper's datasets are
  internal and not publicly released.
- **Impossible-task substrate:** Zhong, Z., Raghunathan, A., & Carlini, N. (2025).
  _ImpossibleBench: Measuring LLMs' Propensity of Exploiting Test Cases._
  [arXiv:2510.20270](https://arxiv.org/abs/2510.20270) ·
  [repo (MIT)](https://github.com/safety-research/impossiblebench).
- **Capability-scaling of covert behavior:** Meinke, A., et al. (2024). _Frontier Models are
  Capable of In-Context Scheming._ [arXiv:2412.04984](https://arxiv.org/abs/2412.04984)
  (Apollo Research). Denison, C., MacDiarmid, M., et al. (2024). _Sycophancy to Subterfuge:
  Investigating Reward-Tampering in Large Language Models._
  [arXiv:2406.10162](https://arxiv.org/abs/2406.10162) (Anthropic).

## License

Apache 2.0 — see `LICENSE`.
