"""Integrity section: per-game evidence completeness, read from the archives only."""
import gzip
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
from nba.live import ledger as LED, watchdog as WD  # noqa: E402
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


def test_games_beyond_the_projection_window_are_not_reported_as_missing_and_prior_day_slots_count(tmp_path):
    tips = ["2026-10-20T19:00:00Z", "2026-10-26T23:00:00Z"]
    ctx = _ctx(tmp_path, tips)
    arch = tmp_path / "arch"
    arch.mkdir()
    now = utc("2026-10-20T16:30:00Z")
    rep = IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", now)
    far = next(g for g in rep["games"] if g["game_id"] == "espn:1")
    assert far["scheduled_later"] and far["missing"] == [] and "forecast" not in rep["missing_counts"] or rep["missing_counts"].get("forecast") == 1
    st = {"capture": {"n_observations": 5, "errors": [], "sources": {"official": {"status": "ok"}}},
          "project": {"games": 1, "status": "ok", "challenger_archive": {"written": 5, "duplicates": 0}}}
    rec = LED.build_record("pregame", st, {"slot_id": "2026-10-19@2120", "kind": "pregame"}, utc("2026-10-20T02:20:00Z"))
    rec["kind"] = "pregame"
    LED.write(str(arch), rec)
    rep = IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", now)
    assert "2026-10-19@2120" in rep["slots"]["executed"] or "2026-10-19@2120" not in rep["slots"]["missed"]


def test_a_game_owes_forecasts_only_after_a_slot_whose_window_contained_it(tmp_path):
    """2026-10-21 report: CLE@PHI (tip 36 h out) was listed as missing forecasts, but the projection window is 30 h and the first slot that
    can contain it had not run. A game is owed once a pregame slot >= 1 h old has it inside its 30 h window."""
    tip = utc("2026-10-22T23:00:00Z")
    assert not IG.owed_projection(tip, utc("2026-10-21T13:30:00Z"))      # 33.5 h out: the window opens at 17:00Z, first containing slot is 13:50 ET = 17:50Z
    assert not IG.owed_projection(tip, utc("2026-10-21T18:30:00Z"))      # that slot ran 40 min ago: still inside the 1 h allowance
    assert IG.owed_projection(tip, utc("2026-10-21T19:00:00Z"))          # now owed
    assert IG.owed_projection(tip, utc("2026-10-22T20:00:00Z")) and IG.owed_projection(tip, utc("2026-10-23T05:00:00Z"))
    tips = ["2026-10-20T19:00:00Z", "2026-10-22T23:00:00Z"]
    ctx = _ctx(tmp_path, tips)
    arch = tmp_path / "arch"
    arch.mkdir()
    rep = IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", utc("2026-10-21T13:30:00Z"))
    later = next(g for g in rep["games"] if g["game_id"] == "espn:1")
    assert later["scheduled_later"] and later["missing"] == []
    assert rep["games"][0]["missing"]                                    # the played game still reports its missing evidence


def test_integrity_covers_every_game_of_the_week_not_only_the_newest_snapshots(tmp_path):
    """2026-10-27: the week-1 integrity table listed 9 of the week's 52 games because the schedule loader read only the last 6 snapshot files.
    With several snapshots per day, earlier days fell out of the table and their missing evidence was never reported."""
    d = tmp_path / "ctx"
    for day in ("2026-10-20", "2026-10-21", "2026-10-22"):
        (d / f"context/schedule/dt={day}").mkdir(parents=True)
        rows = [{"game_id": f"espn:{day}", "season_type": "regular", "start_time_utc": f"{day}T23:00:00Z", "game_date_et": day,
                 "home_tricode": "HHH", "away_tricode": "AAA"}]
        for k in range(8):                                               # eight snapshots per day, like the capture worker writes
            with gzip.open(d / f"context/schedule/dt={day}/s{k}.jsonl.gz", "wt") as f:
                f.write("\n".join(json.dumps(r) for r in rows))
    ctx = str(d)
    assert {g["game_id"] for g in WD.load_schedule(ctx)} == {"espn:2026-10-22"}                      # watchdog default: recent snapshots only
    assert {g["game_id"] for g in WD.load_schedule(ctx, per_day=True)} == {f"espn:2026-10-2{i}" for i in (0, 1, 2)}
    arch = tmp_path / "arch"
    arch.mkdir()
    rep = IG.build(str(arch), ctx, "2026-10-20", "2026-10-26", utc("2026-10-27T13:00:00Z"))
    assert rep["n_games"] == 3 and len(rep["games"]) == 3
