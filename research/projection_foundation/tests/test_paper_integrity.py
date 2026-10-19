"""Integrity section: per-game evidence completeness, read from the archives only."""
import gzip
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
from nba.live import ledger as LED  # noqa: E402
from nba.paper import integrity as IG, schema as S, store  # noqa: E402
from pf_core import prospective as pr  # noqa: E402


def utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _ctx(tmp, tips):
    d = tmp / "ctx"
    (d / "context/schedule/dt=2026-10-20").mkdir(parents=True)
    rows = [{"game_id": f"espn:{i}", "season_type": "regular", "start_time_utc": t, "game_date_et": "2026-10-20", "home_tricode": "HHH",
             "away_tricode": "AAA"} for i, t in enumerate(tips)]
    with gzip.open(d / "context/schedule/dt=2026-10-20/s.jsonl.gz", "wt") as f:
        f.write("\n".join(json.dumps(r) for r in rows))
    return str(d)


def _fc(arch, gid, tip, fam, gen):
    pr.archive_forecasts([{"sport": "NBA", "family": fam, "model_id": f"pf-nba-{fam}", "model_role": "challenger", "model_version": "v", "game_id": gid,
                           "game_start_utc": tip, "entity_id": "espn:1", "entity_name": "A", "team": "AAA", "generated_utc": gen, "data_asof_utc": gen,
                           "mean": 1.0, "lo": 0, "probs": [0.5, 0.5], "gate_status": "PASS", "readiness": "SHADOW", "participation": {}}], str(arch), gen)


def test_integrity_lists_missing_items_explicitly_and_counts_complete_games(tmp_path):
    tips = ["2026-10-20T19:00:00Z", "2026-10-21T01:30:00Z"]
    ctx = _ctx(tmp_path, tips)
    arch = tmp_path / "arch"
    arch.mkdir()
    _fc(arch, "espn:0", tips[0], "points", "2026-10-20T15:30:00Z")
    _fc(arch, "espn:0", tips[0], "participation", "2026-10-20T15:30:00Z")
    now = utc("2026-10-21T20:00:00Z")
    rep = IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", now)
    assert rep["n_games"] == 2 and rep["n_started"] == 2 and rep["n_complete"] == 0
    g0 = next(g for g in rep["games"] if g["game_id"] == "espn:0")
    assert g0["has_forecast"] and g0["has_participation_forecast"] and not g0["has_outcome"]
    assert "availability_obs" in g0["missing"] and "game_forecast" in g0["missing"] and "paper_settlement" in g0["missing"]
    g1 = next(g for g in rep["games"] if g["game_id"] == "espn:1")
    assert "forecast" in g1["missing"]
    assert rep["missing_counts"]["forecast"] == 1
    assert "Data integrity" in IG.markdown(rep)


def test_missed_slots_are_reported_and_covered_by_later_runs(tmp_path):
    tips = ["2026-10-20T19:00:00Z"]
    ctx = _ctx(tmp_path, tips)
    arch = tmp_path / "arch"
    arch.mkdir()
    now = utc("2026-10-21T20:00:00Z")
    rep = IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", now)
    assert rep["slots"]["expected"] and rep["slots"]["missed"] == rep["slots"]["expected"]
    st = {"capture": {"n_observations": 5, "errors": [], "sources": {"official": {"status": "ok"}}},
          "project": {"games": 1, "status": "ok", "challenger_archive": {"written": 5, "duplicates": 0}}}
    rec = LED.build_record("pregame", st, {"slot_id": "manual-20261020T153000Z", "kind": "pregame"}, utc("2026-10-20T15:40:00Z"))
    rec["kind"] = "pregame"
    LED.write(str(arch), rec)
    rep = IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", now)
    assert len(rep["slots"]["missed"]) < len(rep["slots"]["expected"])


def test_replay_snapshots_are_excluded_from_prospective_integrity(tmp_path):
    tips = ["2026-10-20T19:00:00Z"]
    ctx = _ctx(tmp_path, tips)
    arch = tmp_path / "arch"
    arch.mkdir()
    now = utc("2026-10-21T20:00:00Z")
    snap = {"snapshot_id": "s", "game_id": "espn:0", "horizon": "T-60", "quote_class": "TWO_SIDED", "snapshot_gap_s": 100, "replay": True}
    store.write_once(str(arch), "market_snapshots", "2026-10-20", [snap], now)
    assert IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", now)["games"][0]["has_snapshot_T-60"] is False
    assert IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", now, replay_allowed=True)["games"][0]["has_snapshot_T-60"] is True
    assert S.SNAPSHOT_SCHEMA
