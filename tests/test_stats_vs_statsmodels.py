"""Pin the hand-rolled CIs in stats.py to statsmodels' reference implementations.

statsmodels is a dev-only dependency (the package never imports it at runtime),
so these tests skip cleanly when it is absent. They exist because of a concrete
fact: the interval we actually need — the *paired* (within-task) difference of
proportions, Newcombe's Wilson-based method — has no statsmodels equivalent.
`confint_proportions_2indep` is the *independent*-sample estimand, which ignores
the pairing. So the paired interval is ours; here we (a) pin the pieces
statsmodels *does* cover — single-proportion Wilson and exact McNemar — and
(b) confirm pairing is tighter than the independent interval, i.e. that reaching
for the 2indep function on within-task data would be the wrong, looser tool.
"""
import pytest

sm_prop = pytest.importorskip("statsmodels.stats.proportion")
sm_cont = pytest.importorskip("statsmodels.stats.contingency_tables")

from pants_on_fire_eval.stats import paired_diff_ci, wilson_ci  # noqa: E402


def _xy_from_counts(a: int, b: int, c: int, d: int):
    """Aligned 0/1 sequences with paired 2x2 counts a=(x1,y1) b=(x1,y0)
    c=(x0,y1) d=(x0,y0)."""
    x = [1] * a + [1] * b + [0] * c + [0] * d
    y = [1] * a + [0] * b + [1] * c + [0] * d
    return x, y


@pytest.mark.parametrize("k,n", [(70, 103), (57, 103), (2, 20), (17, 20), (0, 20), (20, 20)])
def test_wilson_matches_statsmodels(k, n):
    mine = wilson_ci(k, n)
    ref = sm_prop.proportion_confint(k, n, alpha=0.05, method="wilson")
    assert mine == pytest.approx(ref, abs=1e-9)


@pytest.mark.parametrize("a,b,c,d", [
    (63, 5, 11, 18),    # o3 GP-AS pilot cell
    (50, 17, 17, 19),   # balanced discordance (b == c -> no evidence)
    (40, 0, 12, 51),    # all discordance one way
    (30, 3, 1, 10),     # small, lopsided
])
def test_exact_mcnemar_matches_statsmodels(a, b, c, d):
    x, y = _xy_from_counts(a, b, c, d)
    mine = paired_diff_ci(x, y).mcnemar_p
    ref = sm_cont.mcnemar([[a, b], [c, d]], exact=True).pvalue
    assert mine == pytest.approx(ref, abs=1e-9)


def test_pairing_tighter_than_independent():
    """Positively-correlated paired data: the Newcombe *paired* interval must be
    narrower than statsmodels' *independent* two-proportion interval — pairing
    carries information, and the independent estimand is the wrong, looser tool
    for a within-task contrast."""
    x, y = _xy_from_counts(a=63, b=5, c=11, d=18)   # o3 GP-AS, phi ~ +0.59
    nc = paired_diff_ci(x, y, method="newcombe")
    n = len(x)
    lo, hi = sm_prop.confint_proportions_2indep(
        sum(y), n, sum(x), n, method="newcomb", compare="diff")
    assert (nc.hi - nc.lo) < (hi - lo)


def test_statsmodels_has_no_paired_diff_ci():
    """Guardrail/doc: statsmodels exposes only the *2indep* (independent) family,
    no public paired difference-of-proportions CI — which is why ours is
    hand-rolled. If a public 'paired' interval ever appears here, revisit whether
    to adopt it."""
    public = [name for name in dir(sm_prop) if not name.startswith("_")]
    assert "confint_proportions_2indep" in public
    assert not [name for name in public if "paired" in name.lower()]
