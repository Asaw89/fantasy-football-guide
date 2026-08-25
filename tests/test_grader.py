"""
Unit tests for the draft grader.

These test that grade_draft produces sensible, predictable output for known
rosters — the kind of validation we did manually when we caught the D-vs-B
miscalibration. Now it's automated so a future change can't silently break it.

NOTE: adjust the import to match your project. If grader.py is in src/ and you
run pytest from the project root, it may need to be `from src.grader import grade_draft`
or you run pytest from inside src/. We'll sort the import path when you run it.
"""

import pytest
from grader import grade_draft

STARTERS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}
BENCH_SPOTS = 8


def _player(name, position, vor):
    """Helper to build a minimal player dict the grader needs."""
    return {"name": name, "position": position, "vor": vor}


def test_empty_roster_returns_none():
    """An empty roster has nothing to grade."""
    assert grade_draft([], STARTERS, BENCH_SPOTS) is None


def test_grade_has_expected_keys():
    """A graded roster returns the expected fields."""
    roster = [_player("A", "RB", 50), _player("B", "WR", 40)]
    result = grade_draft(roster, STARTERS, BENCH_SPOTS)
    assert result is not None
    for key in (
        "score",
        "letter",
        "total_vor",
        "avg_vor",
        "slots_filled",
        "slots_total",
    ):
        assert key in result


def test_letter_grade_is_valid():
    """The letter grade is always one of A-F."""
    roster = [_player("A", "RB", 50), _player("B", "WR", 40)]
    result = grade_draft(roster, STARTERS, BENCH_SPOTS)
    assert result["letter"] in {"A", "B", "C", "D", "F"}


def test_total_vor_sums_correctly():
    """Total VOR should be the sum of the roster's VOR values."""
    roster = [_player("A", "RB", 50), _player("B", "WR", 40), _player("C", "QB", 30)]
    result = grade_draft(roster, STARTERS, BENCH_SPOTS)
    assert result["total_vor"] == pytest.approx(120, abs=0.1)


def test_better_roster_scores_higher():
    """A roster of high-VOR players should score >= a weak one."""
    strong = [_player(f"S{i}", "RB", 60) for i in range(8)]
    weak = [_player(f"W{i}", "RB", 5) for i in range(8)]
    strong_score = grade_draft(strong, STARTERS, BENCH_SPOTS)["score"]
    weak_score = grade_draft(weak, STARTERS, BENCH_SPOTS)["score"]
    assert strong_score >= weak_score


def test_missing_positions_flagged():
    """A roster missing a starter position should report it in 'missing'."""
    # Only RBs — should be missing QB, WR, TE, K, DEF
    roster = [_player("A", "RB", 50), _player("B", "RB", 40)]
    result = grade_draft(roster, STARTERS, BENCH_SPOTS)
    assert "QB" in result["missing"]
