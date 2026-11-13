"""Human-readable spread orientation regression tests for the NBA producer."""
from nba_edge.workflows.simulate import format_projected_spread, slate_markdown


def test_favourites_are_named_and_negative_in_sportsbook_notation():
    assert format_projected_spread(6.5, "PHI", "TOR") == "PHI -6.5"
    assert format_projected_spread(-1.7, "PHI", "TOR") == "TOR -1.7"
    assert format_projected_spread(25.3, "WAS", "DET") == "WAS -25.3"
    assert format_projected_spread(-25.3, "WAS", "DET") == "DET -25.3"
    assert format_projected_spread(3, "PHI", "TOR") == "PHI -3"
    assert format_projected_spread(30, "PHI", "TOR") == "PHI -30"
    assert format_projected_spread(0, "PHI", "TOR") == "Pick'em"


def test_slate_report_never_exposes_unqualified_raw_signed_margin():
    game = {
        "away": "TOR", "home": "PHI", "tip_utc": "2026-11-13T00:00:00Z",
        "p_home_win": .457, "margin_mean": -1.7, "margin_sd": 16.3,
        "total_mean": 216.2, "total_sd": 20.1, "ot_rate": .048,
        "n_sims": 40000, "inputs_trusted": True, "input_reasons": [],
    }
    slate = {
        "date_et": "2026-11-12", "generated_at_utc": "2026-11-12T22:56:27Z",
        "model_version": "nba-sim-0.1.0", "authority_note": "RESEARCH_ONLY",
        "coverage": {}, "games": [game], "contracts": [], "theses": [],
    }
    out = slate_markdown(slate)
    assert "TOR -1.7" in out
    assert "PHI -1.7" not in out
    assert "model spread" in out
    assert "HOME score minus AWAY score" in out
    assert game["margin_mean"] == -1.7  # display must never mutate model data
