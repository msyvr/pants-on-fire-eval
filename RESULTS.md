# Results

Most recent full run: **(not yet run — populate after first execution)**.

## Headline

(To be filled after first run.)

| Bucket | low_pressure | high_pressure | with_spec |
|---|---|---|---|
| Aligned | _%_ | _%_ | _%_ |
| Capability failure | _%_ | _%_ | _%_ |
| Strong covert | _%_ | _%_ | _%_ |

## Per-category aligned rate (action-only)

(To be filled.)

| Category | low_pressure | high_pressure | with_spec |
|---|---|---|---|
| `algorithmic_impossible` | | | |
| `contradiction_spec` | | | |
| `contradiction_tests` | | | |
| `missing_resource` | | | |
| `unobtainable_info` | | | |
| `removed_artifact` | | | |

## Plots

- `results/plots/aligned_rate.png` — bar chart of action-only aligned rate per variant
- `results/plots/covert_breakdown.png` — stacked bar of the three-bucket cross-tab
- `results/plots/by_category_action.png` — per-impossibility-category breakdown

## Interpretation

(To be written after first run. Look for: does `with_spec` reduce the
strong-covert bucket disproportionately, or does it shift the whole
distribution uniformly? Per-category: does any category resist the spec?
Calibration: do the two calibration items still correctly classify under
each variant?)

## Run details

- **Model:** gpt-4o-mini (default)
- **Items:** 18 impossible (6 categories × 3) + 2 calibration
- **Epochs:** 3
- **Variants:** low_pressure, high_pressure, with_spec
- **Total API calls per full run:** ~360 (model + judge)
- **Approximate cost:** under $1 on gpt-4o-mini
