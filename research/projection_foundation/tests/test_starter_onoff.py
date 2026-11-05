"""Starter input ON/OFF on the real participation path: starters act on P(play) only; they must never switch the minutes model."""
import sys
from pathlib import Path

PF = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PF))
from nba.live import participation as PART  # noqa: E402
from nba.live import starter_onoff as X  # noqa: E402


def test_fixed_rule_never_flips_minutes_model_and_legacy_rule_did():
    r = X.run()
    assert r["fixed_rule_flips_minutes_model_in"] == []
    assert set(r["legacy_rule_flips_minutes_model_in"]) == {"listed_ACTIVE_on_official_report", "listed_PROBABLE_on_official_report",
                                                            "listed_QUESTIONABLE_on_official_report", "not_listed_implicit_available"}


def test_starters_change_p_play_to_the_confirmed_value_and_nothing_else_numeric():
    r = X.run()
    for name, e in r["scenarios"].items():
        for ph, v in e.items():
            assert v["ON_fixed_rule"]["p_play"] == PART.CONFIRMED_STARTER_P
            assert v["ON_fixed_rule"]["class"] == "STARTER_CONFIRMED" and v["OFF"]["class"] != "STARTER_CONFIRMED"
            assert v["ON_fixed_rule"]["minutes_model"] == v["OFF"]["minutes_model"], (name, ph)


def test_confirmed_out_still_wins_over_a_starter_row():
    rows = [X._row("injury", "OUT", "REPORTED", X.SRC_OFFICIAL, X.CAPTURED_INJ), X.STARTER]
    d = X.decide(rows, 0.9, PART.load_calibration(), legacy=False)
    assert d["participation_status"] in ("CONFIRMED_OUT",) and d["p_play"] == 0.0


def test_stale_or_unconfirmed_starter_does_not_become_confirmed():
    from nba.live.availability import SRC_STARTERS
    proj = X._row("starter", "STARTING", "PROJECTED", SRC_STARTERS, X.CAPTURED_START)
    d = X.decide(X.SCENARIOS["listed_ACTIVE_on_official_report"] + [proj], 0.9, PART.load_calibration(), legacy=False)
    assert d["class"] != "STARTER_CONFIRMED"
