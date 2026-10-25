"""Stat-refit challenger R1: the option is opt-in and consistent, the frozen history-minutes asset is well formed, and the eligibility rules refuse what they must."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "minutes_rebuild"))
from nba import minutes_jrm as J  # noqa: E402
from nba import project as P  # noqa: E402
import challenger_rules as CR  # noqa: E402


def test_refit_needs_the_joint_rotation_minutes():
    with pytest.raises(ValueError, match="stat_models='refit' needs minutes_engine='jrm'"):
        P.project_slate(None, None, stat_models="refit")                       # refused before any work is done
    with pytest.raises(ValueError):
        P.project_slate(None, None, stat_models="nonsense")


def test_the_history_minutes_asset_is_walk_forward_and_well_formed():
    h = J.history_minutes()
    assert h.index.is_unique and h.index.names == ["game_id", "pid"]
    assert np.isfinite(h.to_numpy()).all() and h.min() > 0 and h.max() <= 48
    import pandas as pd
    s = pd.read_parquet(J.ASSETS / "hist_minutes.parquet", columns=["season"])["season"]
    assert s.min() == 2020 and s.max() == 2026                                  # history seasons only: the slate season is never in the asset


def test_the_challenger_rules_refuse_unfrozen_or_unlabelled_snapshots(monkeypatch):
    ok, why = CR.challenger_ok(".", {"stats_refit_included": True, "code_commit": "0" * 40})
    if CR.FREEZE == "UNSET":
        assert not ok and "not set" in why
    monkeypatch.setattr(CR, "FREEZE", "a" * 40)
    ok, why = CR.challenger_ok(".", {"stats_refit_included": False, "code_commit": "b" * 40})
    assert not ok and "no stats.jrm_refit" in why
    ok, why = CR.challenger_ok(str(HERE.parent), {"stats_refit_included": True, "code_commit": "b" * 40})
    assert not ok                                                               # unknown commits are never eligible
