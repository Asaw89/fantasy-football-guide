"""
Unit tests for the trade logic in trades.py.

These cover the pure decision logic — trade valuation, roster surplus/need
analysis, and the recommendation engine. player_vor() reads from the draft
board (a real data dependency), so we MOCK it to supply controlled VOR values,
isolating the trade logic from the live board.

Also tests _normalize(), the name-matching helper the whole multi-source
consensus depends on.
"""

import pytest
import trades


# ---------- _normalize (name matching) ----------


def test_normalize_lowercases_and_strips():
    assert trades._normalize("Bijan Robinson") == "bijan robinson"


def test_normalize_removes_apostrophes_and_periods():
    assert trades._normalize("Ja'Marr Chase") == "jamarr chase"
    assert trades._normalize("A.J. Brown") == "aj brown"


def test_normalize_strips_suffixes():
    # "James Cook III" and "James Cook" should match
    assert trades._normalize("James Cook III") == trades._normalize("James Cook")
    assert trades._normalize("Odell Beckham Jr.") == trades._normalize("Odell Beckham")


# ---------- evaluate_trade ----------


def test_evaluate_trade_lopsided_gain(monkeypatch):
    """Give a low-VOR player, get a high-VOR one -> 'You gain value'."""
    vors = {"scrub": 5, "star": 80}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors[n])
    result = trades.evaluate_trade(["scrub"], ["star"])
    assert result["diff"] == pytest.approx(75)
    assert result["verdict"] == "You gain value"


def test_evaluate_trade_lopsided_loss(monkeypatch):
    """Give a high-VOR player, get a low one -> 'You lose value'."""
    vors = {"scrub": 5, "star": 80}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors[n])
    result = trades.evaluate_trade(["star"], ["scrub"])
    assert result["diff"] == pytest.approx(-75)
    assert result["verdict"] == "You lose value"


def test_evaluate_trade_roughly_even(monkeypatch):
    """Similar value on both sides -> 'Roughly even'."""
    vors = {"a": 40, "b": 42}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors[n])
    result = trades.evaluate_trade(["a"], ["b"])
    assert result["verdict"] == "Roughly even"


def test_evaluate_trade_boundary(monkeypatch):
    """A diff of exactly 5 is 'Roughly even' (verdict uses > 5, not >= 5)."""
    vors = {"a": 40, "b": 45}  # diff = 5 exactly
    monkeypatch.setattr(trades, "player_vor", lambda n: vors[n])
    result = trades.evaluate_trade(["a"], ["b"])
    assert result["diff"] == pytest.approx(5)
    assert result["verdict"] == "Roughly even"  # 5 is not > 5


def test_evaluate_trade_sums_multiple_players(monkeypatch):
    """Multi-player sides sum correctly."""
    vors = {"a": 30, "b": 20, "c": 45}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors[n])
    result = trades.evaluate_trade(["a", "b"], ["c"])  # give 50, get 45
    assert result["give_vor"] == pytest.approx(50)
    assert result["get_vor"] == pytest.approx(45)
    assert result["diff"] == pytest.approx(-5)


# ---------- analyze_roster ----------


def _p(name, position):
    return {"name": name, "position": position}


def test_analyze_roster_finds_rb_surplus(monkeypatch):
    """4 valuable RBs when you start 2 -> RB is a surplus of 2."""
    vors = {"rb1": 50, "rb2": 40, "rb3": 30, "rb4": 20}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors.get(n, 0))
    roster = [_p("rb1", "RB"), _p("rb2", "RB"), _p("rb3", "RB"), _p("rb4", "RB")]
    _, surplus, need = trades.analyze_roster(roster)
    assert "RB" in surplus
    assert len(surplus["RB"]) == 2  # 4 valuable - 2 starters = 2 extra


def test_analyze_roster_finds_wr_need(monkeypatch):
    """Only 1 valuable WR when you start 2 -> WR is a need."""
    vors = {"wr1": 50}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors.get(n, 0))
    roster = [_p("wr1", "WR")]
    _, surplus, need = trades.analyze_roster(roster)
    assert "WR" in need
    assert need["WR"] == 1  # need 2, have 1


def test_analyze_roster_ignores_zero_vor(monkeypatch):
    """Players with 0 VOR don't count as 'valuable' for surplus."""
    vors = {"good": 50, "bench": 0}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors.get(n, 0))
    roster = [_p("good", "TE"), _p("bench", "TE")]
    _, surplus, need = trades.analyze_roster(roster)
    # Only 1 valuable TE, start 1 -> no surplus, no need
    assert "TE" not in surplus


# ---------- recommend_trade ----------


def test_recommend_trade_complementary_needs(monkeypatch):
    """I'm deep at RB / thin at WR; they're deep at WR / thin at RB -> a trade."""
    vors = {
        "my_rb1": 50,
        "my_rb2": 40,
        "my_rb3": 35,  # deep at RB
        "my_wr1": 30,  # thin at WR (need 2, have 1)
        "th_wr1": 45,
        "th_wr2": 40,
        "th_wr3": 38,  # they deep at WR
        "th_rb1": 30,
    }  # they thin at RB
    monkeypatch.setattr(trades, "player_vor", lambda n: vors.get(n, 0))
    mine = [
        _p("my_rb1", "RB"),
        _p("my_rb2", "RB"),
        _p("my_rb3", "RB"),
        _p("my_wr1", "WR"),
    ]
    theirs = [
        _p("th_wr1", "WR"),
        _p("th_wr2", "WR"),
        _p("th_wr3", "WR"),
        _p("th_rb1", "RB"),
    ]
    recs = trades.recommend_trade(mine, theirs)
    assert len(recs) > 0
    # Should suggest giving an RB and getting a WR
    assert any(r["give_pos"] == "RB" and r["get_pos"] == "WR" for r in recs)


def test_recommend_trade_no_complementary_match(monkeypatch):
    """Two balanced rosters with no complementary needs -> no suggestions."""
    vors = {"a": 50, "b": 40}
    monkeypatch.setattr(trades, "player_vor", lambda n: vors.get(n, 0))
    # Both rosters minimal and balanced - no surplus/need overlap
    mine = [_p("a", "QB")]
    theirs = [_p("b", "QB")]
    recs = trades.recommend_trade(mine, theirs)
    assert recs == []
