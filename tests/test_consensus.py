"""
Unit tests for the multi-source consensus / disagreement logic in espn_ranks.

attach_ranks() blends Sleeper VOR rank, ESPN rank, and Berry rank into a
consensus, and flags 'disagreement' when the sources diverge by 15+ spots.

We MOCK the ESPN/Berry loaders so the tests control the input data and isolate
the blending math from the JSON files on disk — the test checks the LOGIC,
not whether the files loaded.

NOTE: adjust the import path to match your setup (same pattern as the other tests).
The monkeypatch targets assume the loaders live in the espn_ranks module.
"""

import pytest
import espn_ranks


def _player(name, vor, adp=None):
    p = {"name": name, "vor": vor}
    if adp is not None:
        p["adp"] = adp
    return p


def test_consensus_averages_three_sources(monkeypatch):
    """A player ranked 1 by Sleeper, 3 by ESPN, 5 by Berry -> consensus 3.0."""
    # Mock the loaders to return controlled ranks (keyed by normalized name)
    monkeypatch.setattr(espn_ranks, "load_espn_ranks", lambda: {"player a": 3})
    monkeypatch.setattr(espn_ranks, "load_berry_ranks", lambda: {"player a": 5})

    board = [_player("Player A", vor=100)]  # only player -> sleeper_rank 1
    result = espn_ranks.attach_ranks(board)
    # ranks = [1 (sleeper), 3 (espn), 5 (berry)] -> avg 3.0
    assert result[0]["consensus"] == pytest.approx(3.0)


def test_disagreement_flag_fires_on_large_spread(monkeypatch):
    """Sleeper 1 vs ESPN 20 = spread of 19 -> disagreement True."""
    monkeypatch.setattr(espn_ranks, "load_espn_ranks", lambda: {"player a": 20})
    monkeypatch.setattr(espn_ranks, "load_berry_ranks", lambda: {})

    board = [_player("Player A", vor=100)]
    result = espn_ranks.attach_ranks(board)
    assert result[0]["rank_spread"] == 19  # 20 - 1
    assert result[0]["disagreement"] is True


def test_no_disagreement_on_small_spread(monkeypatch):
    """Sleeper 1 vs ESPN 3 = spread of 2 -> disagreement False."""
    monkeypatch.setattr(espn_ranks, "load_espn_ranks", lambda: {"player a": 3})
    monkeypatch.setattr(espn_ranks, "load_berry_ranks", lambda: {})

    board = [_player("Player A", vor=100)]
    result = espn_ranks.attach_ranks(board)
    assert result[0]["rank_spread"] == 2
    assert result[0]["disagreement"] is False


def test_missing_source_uses_available_only(monkeypatch):
    """A player not in ESPN or Berry -> consensus is just the sleeper rank."""
    monkeypatch.setattr(espn_ranks, "load_espn_ranks", lambda: {})
    monkeypatch.setattr(espn_ranks, "load_berry_ranks", lambda: {})

    board = [_player("Player A", vor=100)]
    result = espn_ranks.attach_ranks(board)
    assert result[0]["espn_rank"] is None
    assert result[0]["berry_rank"] is None
    assert result[0]["consensus"] == pytest.approx(1.0)  # just sleeper_rank


def test_sleeper_rank_follows_vor_order(monkeypatch):
    """Higher VOR should get a better (lower) sleeper_rank."""
    monkeypatch.setattr(espn_ranks, "load_espn_ranks", lambda: {})
    monkeypatch.setattr(espn_ranks, "load_berry_ranks", lambda: {})

    board = [_player("Low", vor=10), _player("High", vor=100)]
    result = espn_ranks.attach_ranks(board)
    ranks = {p["name"]: p["sleeper_rank"] for p in result}
    assert ranks["High"] == 1  # highest VOR = rank 1
    assert ranks["Low"] == 2


def test_value_gap_positive_means_value(monkeypatch):
    """A player ranked well by VOR but drafted later (high ADP) = positive value_gap."""
    monkeypatch.setattr(espn_ranks, "load_espn_ranks", lambda: {})
    monkeypatch.setattr(espn_ranks, "load_berry_ranks", lambda: {})

    # High is VOR rank 1 but has a late ADP; Low is VOR rank 2 with early ADP
    board = [
        _player("High", vor=100, adp=5.0),  # sleeper_rank 1, adp_rank 2
        _player("Low", vor=10, adp=1.0),  # sleeper_rank 2, adp_rank 1
    ]
    result = espn_ranks.attach_ranks(board)
    gaps = {p["name"]: p["value_gap"] for p in result}
    # High: adp_rank 2 - sleeper_rank 1 = +1 (value)
    assert gaps["High"] == 1
    # Low: adp_rank 1 - sleeper_rank 2 = -1 (reach)
    assert gaps["Low"] == -1
