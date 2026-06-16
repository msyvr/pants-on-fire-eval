# Post-mortem: pants-on-fire-eval

*Written 2026-06-11, at the pivot from the bespoke eval to an ImpossibleBench-based study.*

## Decision

**We proceed with Q1 and shelve Q2 — the latter on feasibility alone, not on scientific merit.**

- **Q1 — the anti-scheming spec decomposition** (does `as_only` / anti-deception
  content do the durable work as capability scales, vs process/effort): **proceed,
  using the field's instruments** — ImpossibleBench as the validated impossible-task
  substrate and its by-construction cheating-rate as the metric. Open in the
  literature and now cleanly executable.
- **Q2 — NLA-as-eval-judge for scheming the CoT judge misses**: **wrap up as not
  feasible now.** Anthropic's released NLA artifacts are for *non-reasoning* models;
  the scheming worth reading lives in *reasoning* models; no reasoning-model NLA
  exists; training one is out of scope for this project. The science is **not** the
  reason to stop — the NLA's whole purpose is to test the claim "scheming is
  verbalized," and **both outcomes are findings**: it surfaces unverbalized
  recognition the CoT judge missed (CoT monitoring is *insufficient* — the
  load-bearing safety concern), or it confirms recognition is reliably verbalized
  (CoT monitoring *suffices* here — a reassuring bound). That makes Q2 *more* worth
  revisiting, not less. It reopens the moment a reasoning-model NLA ships.

Both questions remain genuinely unanswered by external work. We pursue the one whose
path is clear and stop the one whose path is blocked.

## What we set out to answer

1. Split the Schoen anti-scheming spec into anti-deception (AS) vs process/effort
   (GP) vs neutral-effort, and test whether `as_only` "is all you need" — and
   increasingly so as capability scales.
2. Test whether an NLA (activation-level) judge can catch impossibility-recognition
   / scheming that a CoT text-judge misses.

Dataset creation was never a goal — it was instrumental.

## What happened

We built a bespoke single-turn eval to serve both: hand-authored 60 "impossible"
coding items, a dual-scorer cross-tab, and a 6-variant spec ablation. Over one
session, adversarial review dismantled it: the decomposition result was
measure-dependent and confounded; the awareness judge misfiled gaming as
capability-failure; the dataset contained at least 8 *false-impossible* items a
frontier solver cracked. A build-vs-buy scan then found **ImpossibleBench** (arXiv
2510.20270, Oct 2025, Anthropic safety-research) — essentially this eval, done
rigorously, open (MIT), on our exact framework (Inspect) — making the bespoke
dataset and scorer obsolete; an interventions check confirmed the spec
*decomposition* itself is still untouched by the field.

## Root causes

1. **Built before surveying the field.** The headline failure. For an eval project,
   "does a validated substrate already exist?" is the *first* question; we treated it
   as the last. ImpossibleBench and the Schoen tasks existed the whole time. A
   landscape scan up front would have skipped the entire dataset-build → audit →
   repair cycle.
2. **By-assertion ground truth.** "Impossible" was *asserted* by hand, making it
   capability-relative — every new model reopens it, forcing an endless
   adversarial-audit arms race. ImpossibleBench's by-*construction* impossibility
   (mutate a real test → passing *is* cheating) is the correct design; ours wasn't.
3. **A construct-invalid instrument.** The "did it verbalize impossibility?" judge
   measured the wrong thing — it scored deliberate test-gaming as honest failure. A
   behavioral ground truth (pass = cheat) needs no such judge and can't be gamed.
4. **Instrumental work eclipsed the research question.** Enormous effort went into a
   dataset that was never a goal; the two actual questions got buried under yak-shaving.
5. **Findings believed before they earned it.** "Effort dominates," "reasoning models
   aren't steered," "gaming-misfiled is a novel result" — each was an artifact,
   contradicted by larger external data, or an already-documented limitation. None
   survived a hostile read.

**What saved it:** the adversarial discipline — `/critique`, reading raw transcripts,
and surveying prior art — is exactly what exposed all five and converted a doomed
bespoke eval into a clear path. The failure was building first; the asset is the
willingness to attack our own work and check the field. Keep that; front-load it.

## What we got for it

Not nothing. We exit with: both questions **cleanly scoped against the literature**; a
**validated, free substrate** (ImpossibleBench) installed and running; the **wiring**
to inject the spec; and durable conceptual clarity (recognition-vs-honesty,
single-turn-vs-multi-turn, the CoT-hiding problem for reasoning models). The grant
narrative is *stronger*: "I'm running the spec decomposition neither Schoen nor
ImpossibleBench did, on their validated substrate" beats "I built my own eval."

## The two calls, justified

- **Q1 — go.** Open (Schoen bundled AS+GP and said so; ImpossibleBench varied
  strictness/access/escalation, never the functional cut). Cleanly doable
  (ImpossibleBench substrate + construct-valid cheating-rate + a model range for the
  scaling claim). Safety-relevant (tells the field where to invest). **Even a null is
  a result** — "AS adds nothing beyond effort, at any scale" would reframe the paper's
  intervention as scaffolding.
- **Q2 — shelve, on feasibility only.** Blocked on the reasoning-model-NLA gap
  (released NLAs are non-reasoning; the scheming is in reasoning models; training one
  is out of scope). The **value is not in doubt** — the NLA exists to challenge
  "scheming is verbalized," and either result is publishable: unverbalized recognition
  the CoT judge missed (CoT monitoring insufficient), or reliably-verbalized
  recognition (a bound on when text monitoring is trustworthy). A weaker feasible-now
  variant — running the NLA on a non-reasoning released-NLA model (e.g. Llama-3.3-70B)
  if it games ImpossibleBench enough — is declined as **off-thesis** (weak scheming,
  not the capability-scaling regime). Revisit when a reasoning-model NLA ships.

## Next steps (Q1)

Order matters — step 1 first, and the statistics live in steps 2 and 3.

1. **Smoke + baseline pilot (first).** Confirm ImpossibleBench runs end-to-end on the
   box (model → sandbox → cheating-rate scorer), then run a no-spec baseline on enough
   tasks to estimate the **base cheating rate and its task-level ICC** for the
   model/scaffold we'll use. Scope it to the baseline only — *not* the AS-vs-GP
   contrast — so it powers the design without peeking at the hypothesis.
2. **Pre-register — where the prospective statistics live.** Fix, before the real run:
   variants (`no_spec`/`as_only`/`gp_only`/`effort_only`/`full_spec` as system
   messages); metric (cheating rate on conflicting/oneoff splits); the primary contrast
   (`as_only − gp_only`); the test (paired difference, clustered by task); MID, α,
   power, and the resulting N (tasks × runs × models), computed from step 1's base rate
   + ICC; and the multiple-comparison correction (Holm) across variants. **The earlier
   `stats.py` machinery (ICC, design-effect, clustered CIs, power, Holm) transfers
   directly** — ImpossibleBench's cheating rate is still a task-clustered proportion.
   - **The scaling claim is an interaction, and the hard part.** "`as_only`
     increasingly all you need as capability scales" = the (`as_only − gp_only`)
     gap *changes* across the model ladder. Interactions need far more power than main
     effects. Decide *now* whether it's a **powered test** (needs many models or large
     per-model effects) or a **pre-registered descriptive trend** (per-model contrasts
     + slope, no significance claim on the interaction). Pre-registering this transparently
     is what stops the study from being unfalsifiable.
3. **Run + inferential analysis.** Run the variant × model ladder. Then: clustered CIs
   per variant, the `as_only − gp_only` contrast per model, Holm across variants,
   and the across-model trend/interaction per the step-2 decision. Report effect sizes
   with CIs, and the MDE for any null.
4. **This repo is and stays the project — same question, validated substrate.**
   pof-e began as exactly this study (the spec decomposition); it built a dataset from
   scratch *only* for lack of awareness that ImpossibleBench existed. The problem space
   is unchanged. ImpossibleBench becomes a dependency that supplies the impossible
   tasks, superseding the hand-built `items.py` and dual-scorer — not the repo, and not
   the project. The spec variants (`task.py`'s AS/GP/effort system messages), the
   statistical machinery (`stats.py`, `docs/statistical-methodology.md`,
   `docs/phase1-sampling-plan.md`), the Inspect run-discipline, and this post-mortem all
   carry forward. The name still fits — it was always about false completion claims.

## Sources

- ImpossibleBench — paper: https://arxiv.org/abs/2510.20270 ; repo (MIT):
  https://github.com/safety-research/impossiblebench
- Schoen et al. (Apollo/OpenAI), anti-scheming: https://arxiv.org/abs/2509.15541
  (datasets internal — not publicly released)
