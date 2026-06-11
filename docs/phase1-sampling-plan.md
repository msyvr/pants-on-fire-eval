# Phase 1 — sampling plan & status

*Working state of the Phase 1 sampling/power analysis: what we determined from the
pilot, the decisions, and where to resume. The general reasoning lives in
[`statistical-methodology.md`](statistical-methodology.md); this is the concrete
plan for **this** experiment, with the real numbers. Last updated 2026-06-08.*

## TL;DR — resume here

- **Primary estimand:** `as_only` − `effort_only` aligned-rate — *does anti-deception
  content add work beyond a pure effort prompt?*
- **Measured ICC ≈ 0.64** (from the pilot, `extract_icc.py`) → epochs barely help;
  **the number of items drives power.**
- **Decision — MID (detection resolution): 20 pp → ~60 items/variant** for the
  Wave-1 course deliverable; **tighten to 15 pp → ~110 items** as the extension.
- **Decision — epochs: 2–3, not 5** (the 4th and 5th epoch are ~wasted at this ICC).
- **Items:** **60 logical items** authored (20/category); absent-resource parked
  (see *Decision* below). Re-measure ICC on a logical-only pilot before locking N.
- **Rare buckets:** report as **upper bounds** where covert action is ~0 (the spec
  variants); only top-up in the low-spec conditions.
- **Next actions:** the checklist at the bottom.

## What this experiment measures

Five spec variants (`no_spec`, `as_only`, `gp_only`, `full_spec`, `effort_only`)
on the same impossible-task items, dual-scorer cross-tab → outcome buckets. Two
*kinds* of number come out, each with its own sample-size logic:

1. **The comparison** (`as_only` vs `effort_only`) — a power question.
2. **The rare buckets** (strong-covert / implicit-covert rates) — a precision /
   event-count question, not power.

## What we determined (from the pilot)

- **ICC ≈ 0.64** — per variant 0.44–0.89 (higher when the spec makes responses
  consistent). Backed out of the clustered stderr (~0.68) and then **confirmed on
  the real per-item data** with `extract_icc.py`.
- **Design effect at 5 epochs = 3.57** → 5 re-runs of an item are worth only ~1.4
  independent observations. Epochs average out the judge's run-to-run wobble; they
  do **not** multiply independent data.
- **Items per variant** (baseline aligned-rate ~0.6, ICC ~0.64):

  | smallest gap to detect (MID) | items / variant |
  |---|---|
  | 20 pp | ~60 |
  | 15 pp | ~110 |
  | 10 pp | ~250 |

- **Paired design:** the same items run under every variant, so the comparison is
  within-item — more powerful than the unpaired numbers above. Treat these counts
  as a **conservative ceiling**; a mixed-effects (item-random-effect) analysis
  could reach the same power with somewhat fewer items.
- **Rare buckets:** strong-covert was ~0–4% in the pilot (≈0 under the spec). Filling
  a cell to 40 events at a 4% rate needs ~1000 samples — so these are **upper-bound**
  measurements except in the low-spec conditions.

## Decisions (and why)

- **MID = 20 pp → ~60 items (Wave-1 course target).** Rationale: 60 items (~3.3× the
  current 18) is authorable inside the course window with the generator, and resolves
  a *clear* "anti-deception does real work" signal. Honest caveat: a **moderate**
  gap (10–19 pp) would not be resolved at this MID — reported as "no difference
  detected, powered to ≥20 pp," which is also the motivation for the tightening.
- **Tighten to MID = 15 pp → ~110 items** as the natural extension (more items),
  to catch moderate effects. This is the Wave-2-style depth move when time allows.
- **Epochs = 2–3.** At ICC 0.64 the extra epochs buy ~6% effective sample size for
  ~67% more calls — a bad trade. 2–3 epochs is enough to average the judge's noise;
  the freed budget goes to items, which is what actually buys power.
- **Rare buckets → upper bounds** where covert action is absent; targeted top-up only
  where it occurs (`no_spec`, high-pressure, possibly `as_only`).

## Decision — absent-resource items parked (single-turn eval is logical-only)

A full third of the 60-item dataset — the absent-resource categories
(`missing_resource`, `unobtainable_info`, `removed_artifact`) — fits the paper's
*multi-turn agentic* setup better than our single-turn text proxy, and is worth
reconsidering before pre-registration.

- **Paper's setup:** the agent actually attempts the action (imports the package,
  calls the API, opens the file) and the environment returns a concrete wall
  (ModuleNotFoundError, 404, PermissionDenied). The covert-action test is clean —
  *having hit the wall, does the agent fabricate success?*
- **Our single-turn proxy:** the model never attempts access; it must infer
  absence from the prompt text plus its own world-knowledge. That conflates
  "covert action" with "knows X doesn't exist" (Google Cloud Prediction API is
  defunct, `requests` is sync-only), and for *internal* resources (an unbuilt
  service, a private repo, a deleted helper) the model literally cannot verify
  absence — so a COMPLETE claim is a defensible response to an underspecified
  prompt, not covert action.

The logical third (`algorithmic_impossible` / `contradiction_spec` /
`contradiction_tests`) is provable from the prompt text alone — no world-knowledge
or access required — so it is the clean single-turn fit.

**Statistical stake (the composition point again):** the primary contrast pools
over all items, so if a third measure "knowledge/caution" rather than covert
action, the pooled `as_only − effort_only` is partly estimated over the wrong
construct. Options to settle at pre-registration:

**Decision (2026-06-10):** the absent-resource categories are **parked** (defined
in `items.py` as `ABSENT_RESOURCE_PARKED`, excluded from the live `ITEMS`), and the
logical three are **authored up to ~20 each (~60 impossible)** — so the clean
construct holds MID 20 pp without the contaminated third, rather than dropping to a
power-starved N=30. Parked, not deleted: they seed a future multi-turn variant.
Carry-forward caveat: ICC 0.64 was measured on the *pooled* pilot, so
**re-measure ICC on a logical-only pilot** before locking the final item count
(could move the target ±10–15 items).

See [`single-turn-vs-multi-turn.md`](single-turn-vs-multi-turn.md) for the full
single-turn-vs-multi-turn rationale — including why the *decomposition itself* is
setting-dependent (single-turn likely under-credits anti-deception, so its AS
contribution is best read as a lower bound).

## Cost / funding (the question that started this)

- **Determining the sample sizes was free** — it reused the pilot you already ran.
- **No synthetic *results*** (that would be fabrication) — the run produces the real
  data.
- **Synthetic *items* are fine and expected** — guaranteed impossible by construction
  (the generator's category mechanisms), then curated. The eval is already a
  constructed proxy.
- **The rapid grant funds the *run*** (cheap on hosted inference, $75 ceiling holds
  regardless of N). **Item authoring is labor** (CTG envelope), not the rapid grant.

## Tools in the repo

- `src/pants_on_fire_eval/stats.py` — power, MDE, event sizing, Wilson + clustered
  CIs, ICC, Holm. Run it for an example plan.
- `src/pants_on_fire_eval/extract_icc.py` — measures the ICC from the pilot logs.
- `src/pants_on_fire_eval/item_generation.py` — the generate-and-curate framework.
- `src/pants_on_fire_eval/phase2.py` — the Phase 2 four-axis cross-tab scaffold.
- `docs/statistical-methodology.md` — the reasoning, written cold.

## Resume-here checklist

0. **Re-measure ICC on a logical-only pilot** (the 0.64 was pooled) and confirm the
   ~60-item / MID-20pp target before pre-registering. (Absent-resource items are
   parked — see *Decision* above.)
1. **Confirm or adjust the MID** (20 pp / ~60 items, or tighten to 15 pp / ~110).
2. **Generate + curate items** to the target count (`item_generation.py`) — add seeds
   as needed; curate for naturalism; include the matched-possible twins.
3. **Wire the curated items into `items.py`.**
4. **Pre-register:** primary contrast (`as_only` vs `effort_only`), the MID, α = 0.05,
   power = 0.80, and the bucket event targets — before running.
5. **Run the screening pass** — all 5 variants, the target item count, 2–3 epochs.
6. **Analyze:** item-clustered CIs on variant rates, Wilson CIs / upper bounds on
   buckets, Holm across the contrasts; report effect sizes with CIs and the MDE for
   any null.
7. **Rapid grant:** submit if not already — it funds the run.
