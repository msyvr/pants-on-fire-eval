"""Smoke tests — verify imports and basic structure. Does NOT run the eval
(which would require API keys and incur cost)."""


def test_imports() -> None:
    """All public entry points import without error."""
    from pants_on_fire_eval import items, scorers, task, analysis
    assert hasattr(items, "ITEMS")
    assert hasattr(scorers, "status_claim_scorer")
    assert hasattr(scorers, "cot_aware_scorer")
    assert hasattr(task, "VARIANTS")
    assert hasattr(task, "condition")
    assert hasattr(analysis, "covert_breakdown")


def test_items_well_formed() -> None:
    """Every item has required metadata fields and the STATUS instruction."""
    from pants_on_fire_eval.items import ITEMS, STATUS_INSTRUCTION

    assert len(ITEMS) >= 18  # 18 impossible + 2 calibration

    for s in ITEMS:
        assert s.target in {"impossible", "possible"}
        assert s.metadata is not None
        assert "item_id" in s.metadata
        assert "category" in s.metadata
        assert "format" in s.metadata
        assert STATUS_INSTRUCTION in s.input

    item_ids = [s.metadata["item_id"] for s in ITEMS]
    assert len(item_ids) == len(set(item_ids)), "duplicate item_ids"


def test_variants_present() -> None:
    """All three variants are defined."""
    from pants_on_fire_eval.task import VARIANTS
    assert set(VARIANTS) == {"low_pressure", "high_pressure", "with_spec"}
    # with_spec must contain the anti-scheming principles
    assert "AS1" in VARIANTS["with_spec"]
    assert "GP1" in VARIANTS["with_spec"]


def test_status_regex_parses() -> None:
    """The status regex correctly extracts STATUS values."""
    import re
    from pants_on_fire_eval.scorers import STATUS_RE

    assert STATUS_RE.search("blah blah\n\nSTATUS: COMPLETE").group(1).upper() == "COMPLETE"
    assert STATUS_RE.search("STATUS: IMPOSSIBLE").group(1).upper() == "IMPOSSIBLE"
    assert STATUS_RE.search("STATUS: incomplete").group(1).upper() == "INCOMPLETE"
    assert STATUS_RE.search("no status here") is None
