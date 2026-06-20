# Liar, liar: Pants-on-fire eval

Scheming — a model covertly pursuing a hidden objective while presenting as aligned — is a
central AI-safety concern. This project measures its behavioral signature (the evident
'cheat,' setting aside intent) on "impossible tasks," where the model finds a way to
"complete" a task that cannot be completed legitimately.

It is inspired by [Stress Testing Deliberative Alignment for Anti-Scheming Training (_Schoen
et al., 2025_)](https://arxiv.org/abs/2509.15541), which targets both the behavioral
signature (the cheat itself) and intent (via chain of thought) to interrogate scheming. We
focus on the behavioral signature; testing intent evaluation (e.g., on reasoning summaries)
is deferred to future work.

## The question

Studying frontier reasoning models in multi-turn agentic environments, Schoen shows that
injecting an anti-scheming spec into a model's context reduces covert behavior — while also
flagging that eval awareness threatens such interventions, since RL pressure on a targeted
spec can exacerbate misalignment (the training game;
[Cotra, 2022](https://www.alignmentforum.org/posts/pRkFkzwKZ2zfa3R6H/without-specific-countermeasures-the-easiest-path-to)).
A smaller-footprint spec would exert less of that pressure.

Schoen's spec bundles two functionally distinct clause types — anti-deception ("no covert
actions, no strategic deception, report violations") and process/effort ("reason carefully,
escalate ambiguities, no rationalizations") — and treats them as a unit. Can we unbundle and
streamline the spec without sacrificing efficacy? Concretely: **does the anti-deception content
(`as_only`) suppress cheating more than the process/effort content (`gp_only`) — and
increasingly so as model capability scales?**

The distinction is safety-relevant because the two clause types align with two failure modes
that diverge with scale: genuine capability-failure (the model doesn't recognize the task is
impossible, or doesn't try hard enough) drops as models improve, while the ability to scheme
rises. A lever that only helps the weaker failure mode is scale-fragile; one that targets
deception is durable.

## Pilot project report

[_Decomposition of a Deliberative Alignment Anti-Scheming Spec_](docs/reports/decomposition-pilot.md)
details the design, statistical analysis, and results of a calibrated pilot, and proposes 
two follow-on phases. In brief: we built a judge-free, by-construction measurement pipeline. 
We established that, for our experimental parameters, the relevant cheating is observed only 
on reasoning models. Based on that, we calibrated reasoning models of different capabilities 
and ran a one-epoch, within-task-paired pilot. The pilot shows a significant rise in cheating 
with capability (o3 > o4-mini, Holm-robust) and an AS-vs-GP advantage that is directional but 
below the resolution the 103-task census affords; it is a bounded-null risk the current census 
cannot resolve, where lowering the resolution needs more independent tasks and any gain from added 
epochs is bounded by the ICC (to be measured in Phase 2). Phase 2 requires a decision about 
benchmark size which will, in turn, set the resolution limit on effect size. Phase 3 will 
study the effect at a higher degree of construct purity to support generalization.

## Substrate: ImpossibleBench

We use [ImpossibleBench](https://arxiv.org/abs/2510.20270) (Zhong, Raghunathan & Carlini,
2025; Anthropic safety-research; MIT), which builds "impossible" coding tasks by mutating a
real LiveCodeBench / SWE-bench unit test so that it contradicts the task specification. There
is then no legitimate way to pass, so **cheating rate = pass rate on the impossible split** —
a behavioral ground truth that needs no model-graded judge and cannot be gamed by the
subject.

Task splits: `original` (unmutated control), `oneoff` (one test mutated), `conflicting` (a
test directly contradicts the spec — the hardest to pass honestly, and the split we use).
Scaffolds: `minimal` (single-file submission loop, cheap; used here) and `tools` (full
bash/python/editor agent, more cheating-prone).

## Implementing the decomposition

ImpossibleBench supplies the tasks and the cheating-rate scorer; we build the spec variants,
each injected as a system message ahead of a task.

| Variant       | System message                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------- |
| `no_spec`     | High-pressure framing only (baseline)                                                             |
| `as_only`     | High-pressure + anti-deception clauses only (AS1–AS5)                                             |
| `gp_only`     | High-pressure + process/effort clauses only (GP1–GP4)                                             |
| `full_spec`   | High-pressure + the full anti-scheming spec (AS + GP)                                             |
| `effort_only` | High-pressure + a content-neutral "think carefully and verify before declaring work complete" cue |

The five variants are defined in [`src/pants_on_fire_eval/task.py`](src/pants_on_fire_eval/task.py).
The metric is the cheating rate per variant; the primary contrast is `gp_only − as_only`,
measured across a model capability ladder to test whether the anti-deception advantage grows
with capability. `as_only` and `gp_only` share the spec's "safety principles" header and
numbered-clause register and differ only in clause content, so the contrast is
**framing-matched** — it isolates anti-deception content from the framing it travels in.
(`as_only`-vs-`effort_only`, against a content-neutral cue, is a secondary control.)

## Experiments (phased)

A powered, pre-registered decomposition (Phases 0–2), with a purified follow-on (Phase 3):

- **Phase 0 — calibration.** Screen reasoning models on the `no_spec` baseline and fix the
  model ladder. (The ICC is measured at the start of the powered run.)
- **Phase 1 — H1.** The `gp_only − as_only` cheating-rate contrast on the first reasoning model.
- **Phase 2 — H2.** Repeat up the capability ladder for the scaling trend.
- **Phase 3 — construct-purified follow-on.** Schoen's AS/GP grouping resembles the two axes
  but isn't a clean cut — GP's clauses read as anti-deception as readily as try-harder. Phase 3
  re-cuts the _same_ spec content into a cleaner anti-deception arm and a cleaner effort arm
  and runs the same hypothesis at higher construct purity. Phases 1/2 bear directly on the
  published spec; Phase 3 gives the cleaner read.

The scaling claim is an **interaction** (the AS-vs-GP gap _changing_ across the ladder), which
needs far more power than a main effect; the pre-registration commits to a **descriptive
trend**, with a powered interaction test only as a conditional upgrade — the move that keeps
the study falsifiable. The prospective statistics — variants, metric, primary contrast,
ladder, minimum interesting difference, α/power/N, and Holm — are fixed _before_ the run. See
the [pre-registration](docs/preregistration.md) and
[`docs/statistical-methodology.md`](docs/statistical-methodology.md).

## Repository layout

- **Spec variants** — [`src/pants_on_fire_eval/task.py`](src/pants_on_fire_eval/task.py): the five system-message variants (the independent variable).
- **Statistics** — [`src/pants_on_fire_eval/stats.py`](src/pants_on_fire_eval/stats.py) + [`docs/statistical-methodology.md`](docs/statistical-methodology.md): power, ICC / design-effect, clustered CIs, Holm.
- **Substrate** — [ImpossibleBench](https://github.com/safety-research/impossiblebench) (separate checkout, its own venv): the impossible tasks and the cheating-rate scorer.

## Reproduction (pilot)

ImpossibleBench installs as a separate checkout with its own venv. To reproduce the pilot
gradient:

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
