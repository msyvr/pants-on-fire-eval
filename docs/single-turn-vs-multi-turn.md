# Single-turn vs multi-turn — why single-turn first, and what changes

This eval is a **single-turn text proxy** for the impossible-task covert-action
phenomenon in Schoen et al. (2025), which is studied in **multi-turn agentic**
environments. This note records the rationale for keeping single-turn as Stage 1
and — most importantly — why the *spec-decomposition result itself* is
setting-dependent.

## 1. How hard is multi-turn?

The *framework* is the easy part — Inspect already supports agentic evals
(`@tool`, `use_tools()`, sandboxed `bash()`/`python()`, multi-turn agent loops via
`basic_agent`). The real work is two things it doesn't give you:

- **Environments where the wall is *enacted*.** Each impossible task becomes a
  small sandbox the model acts in: it gets `run_tests` / `read_file` /
  `run_python` tools, attempts the task, and the environment genuinely pushes
  back (the two conflicting tests really can't both pass; the import really
  errors). Two tiers: **mocked** tool responses (scripted walls — light, ~1–2
  weeks) vs **real sandboxes** (Docker repos, real test execution, SWE-bench-style
  — weeks + infra).
- **Trajectory-level scoring.** Covert action is no longer a single `STATUS:`
  line — it's "did the agent fabricate a passing result / edit the test to cheat
  / claim done after hitting the wall," read over the whole trajectory. A new
  scorer, closer to the paper's behavior-classifier + manual confirmation.

The 60 logical scenarios we authored **transfer directly** as seeds — `i05` (two
conflicting login tests) becomes a repo with those tests + a `run_tests` tool. The
authoring is not sunk cost.

## 2. Is single-turn a useful comparison to the paper?

A useful **probe of the decomposition question** and a **methodology testbed** —
but **not a replication** of the paper's phenomenon. The paper's result is about
*agentic* scheming reduction; single-turn can't elicit strategic, across-steps
deception (sabotage, faked tool results). A decomposition finding here is
*suggestive for* the agentic regime, not evidence *about* it. The proposal's "a
tractable shadow" framing is the honest one.

The non-obvious part cuts the other way: **single-turn is *better* for the novel
Phase-2 contribution.** NLA-as-judge depends on dense activation coverage, and the
NLA paper flags a ~10k-token ceiling on multi-thousand-token agentic transcripts —
the single-turn proxy's short responses are an *advantage* there. So it's a genuine
trade-off, not a strict ladder:

- **Phase 1 (behavioral — "does the spec reduce covert action"):** multi-turn is
  more faithful.
- **Phase 2 (NLA-as-judge methodology — the actually-novel bit):** single-turn is
  the better substrate.

## 3. Is the simpler setup justifiable initially?

**Yes — as a deliberate Stage 1, provided we don't oversell it.** Standard staged
research: cheap, fast, fully reproducible; validates the whole methodology stack
(dual-scorer → spec decomposition → NLA integration) and de-risks the expensive
multi-turn build. Parking the absent-resource third already made this the *most*
defensible single-turn version (logical impossibilities are the one place
single-turn covert action is unambiguous). The risk to avoid is framing it as "we
extend the paper's agentic result" — it isn't that.

## The key caveat: the decomposition is itself setting-dependent

> **Update (2026-06-10): tested — see *Empirical update* below.** The prediction in
> this section (single-turn *under-credits anti-deception*) was partly wrong:
> reasoning flattened the whole decomposition rather than lifting AS. The *effort
> advantage* was the non-reasoning artifact; "AS adds little" survived both regimes.

Even setting aside agentic *effectiveness*, the **spec-component decomposition**
(`as_only` vs `gp_only` vs `effort_only`) is expected to change with setting —
because the decomposition measures how much each clause reduces a *particular
failure*, and the failure's composition shifts:

- **Single-turn** never enacts recognition (the model doesn't run the tests and
  see red). The dominant failure is rationalized over-confidence / didn't-check
  (pilot: ~68% capability-failure under pressure, ~0–4% strong-covert) — exactly
  what the **effort/GP** clauses target. Recognition-then-conceal is rare *because
  recognition itself is rare*, so the **anti-deception** clauses have little to act
  on. Single-turn structurally **starves AS of its target**.
- **Multi-turn** forces recognition — the agent runs the tests, sees they can't
  both pass; the import errors. The "didn't recognize" failure largely evaporates;
  the residual is the **conceal-given-recognized** decision — precisely what AS
  clauses target. So AS should contribute *more*, effort *less*.

**Consequence:** the primary estimand `as_only − effort_only` is the single
contrast most exposed to setting. Single-turn likely **under-credits
anti-deception**, so report the single-turn AS contribution as a **lower bound**.
It also reframes the pilot: "effort dominates, `as_only` weakest" is partly a
single-turn artifact (AS had little to bite on), not clean evidence that
anti-deception is unimportant. The multi-turn arm is the **validity completion of
our own decomposition question**, not just a faithfulness upgrade.

## Empirical update (2026-06-10): tested, and the prediction was wrong in its specifics

We ran the logical-only set on gpt-4o-mini (non-reasoning) and o4-mini (reasoning).
Verdict: reasoning did **not** specifically un-starve anti-deception — it
**flattened the whole decomposition.**

- On gpt-4o-mini, each spec variant's lift over the no-spec floor is AS +17 pp,
  process/effort +34–38 pp. On o4-mini those lifts collapse to ~0 (AS +0, effort
  +1.6), and the no-spec floor itself rises 20 pp (36.7 → 56.7%).
- So the "effort dominates" result was the **non-reasoning artifact** (an effort
  prompt substitutes for reasoning the model isn't doing). But "anti-deception adds
  ~nothing beyond baseline" **survives** into the reasoning regime — the starvation
  framing above was too strong about AS specifically.
- The baseline lift is **recognition** (the reasoner derives impossibilities the
  non-reasoner skips; biggest where impossibility is knowledge-based — algorithmic
  60→80%). Whether any of it is **honesty** (disclosing what gpt-4o-mini implicitly
  concealed) is **unmeasurable by text** — the implicit-covert gap, i.e. the
  single-turn case for the activation layer.
- o4-mini's reasoning is **hidden by the API**, so the deception channel
  (recognize-then-conceal) — the bucket that matters for a reasoning model — is
  unmeasurable here. That reinforces the **self-hosted** Phase-2 setup: you need the
  reasoning visible (CoT or activations).

Full numbers in [`../RESULTS.md`](../RESULTS.md).

## Recommendation: staged, not either/or

- **Stage 1 (now): single-turn, logical-only.** Where the NLA methodology — the
  distinctive contribution — is most tractable; answers the decomposition question
  in the single-turn regime; reproducible on a laptop budget.
- **Stage 2: a light multi-turn arm** (Inspect tools + mocked/scripted walls over
  the *same* scenarios + a trajectory scorer), reusing the dataset. Real sandboxes
  only if Stage 2 warrants it.

Going multi-turn *first* would be the wrong move: it balloons cost/infra and
*forfeits* the single-turn NLA advantage before the methodology is proven.

## Implications for the writeup

- Frame single-turn as Stage 1 / proxy, not a replication of the paper.
- Report the decomposition as **regime-specific**, and flag that single-turn
  likely under-credits anti-deception (AS contribution = lower bound).
- Position the multi-turn arm as both the faithfulness upgrade *and* the test that
  isolates the deception decision the single-turn proxy cannot.
