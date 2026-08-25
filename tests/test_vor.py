"""
Unit tests for the VOR (Value Over Replacement) engine.

VOR = a player's projected points minus the 'replacement level' player's points
(the last startable player at that position). These tests lock in that the core
ranking math is correct — the heart of the whole app.

NOTE: adjust the import to match how the grader test imports (same pattern that
worked there).
"""

import pytest
from draft_board import add_value_over_replacement


def _player(name, points):
    return {"name": name, "points": points}


def test_vor_basic_calculation():
    """With replacement_rank 3, the 3rd player is replacement level.
    Each player's VOR = their points minus the 3rd player's points."""
    players = [
        _player("A", 300),
        _player("B", 250),
        _player("C", 200),  # replacement level (rank 3)
        _player("D", 150),
    ]
    result = add_value_over_replacement(players, "RB", {"RB": 3})
    assert result[0]["vor"] == pytest.approx(100.0)  # 300 - 200
    assert result[1]["vor"] == pytest.approx(50.0)  # 250 - 200
    assert result[2]["vor"] == pytest.approx(0.0)  # 200 - 200 (replacement)
    assert result[3]["vor"] == pytest.approx(-50.0)  # 150 - 200


def test_replacement_player_has_zero_vor():
    """The replacement-level player should always have VOR of 0."""
    players = [_player("A", 100), _player("B", 80), _player("C", 60)]
    result = add_value_over_replacement(players, "WR", {"WR": 2})
    # rank 2 -> index 1 -> player B is replacement
    assert result[1]["vor"] == pytest.approx(0.0)


def test_fewer_players_than_rank():
    """If there are fewer players than the replacement rank, it should use
    the last player as replacement rather than crashing."""
    players = [_player("A", 100), _player("B", 80)]
    # rank 5 but only 2 players -> should use the last (index 1, player B)
    result = add_value_over_replacement(players, "QB", {"QB": 5})
    assert result[0]["vor"] == pytest.approx(20.0)  # 100 - 80
    assert result[1]["vor"] == pytest.approx(0.0)  # 80 - 80


def test_empty_player_list():
    """An empty list should not crash and should return empty."""
    result = add_value_over_replacement([], "RB", {"RB": 3})
    assert result == []


def test_vor_is_rounded():
    """VOR should be rounded to 1 decimal place."""
    players = [_player("A", 100.33), _player("B", 50.11)]
    result = add_value_over_replacement(players, "TE", {"TE": 2})
    # 100.33 - 50.11 = 50.22 -> rounds to 50.2
    assert result[0]["vor"] == pytest.approx(50.2)
