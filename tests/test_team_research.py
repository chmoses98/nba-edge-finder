"""Current-season team research: box rates, current-season-only adjustment, the fitted blend, the scheduled refresh and the freshness gate.

The blend tests use the committed ESPN history (real games). The 'early-season replay' relabels the first games of 2025-26 as if they were a new season
that follows 2024-25: a test fixture for the math (what the pipeline does n games into a season), never published data."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nba_edge.data.history import current_season
from nba_edge.team_research import blend as TB
from nba_edge.team_research import ratings as TR
from nba_edge.team_research.box import box_rates, enrich_team_games
from nba_edge.team_research.refresh import refresh, validate_explorer

ESPN = Path(__file__).resolve().parents[1] / "data" / "history" / "espn"
PARAMS = Path(__file__).resolve().parents[1] / "data" / "research" / "blend_params.json"


@pytest.fixture(scope="module")
def hist():
    seasons = ["2023-24", "2024-25", "2025-26"]
    tg = pd.concat([pd.read_parquet(ESPN / f"team_games_{s}.parquet") for s in seasons])
    pg = pd.concat([pd.read_parquet(ESPN / f"player_games_{s}.parquet") for s in seasons])
    return tg, pg


def test_current_season_label():
    from datetime import date
    assert current_season(date(2026, 11, 2)) == "2026-27"
    assert current_season(date(2027, 3, 1)) == "2026-27"
    assert current_season(date(2027, 7, 15)) == "2027-28"


def test_box_rates_from_real_player_sums(hist):
    tg, pg = hist
    t = tg[(tg.season == "2025-26") & (tg.season_type == "regular")]
    rows = enrich_team_games(t.to_dict("records"), pg[pg.season == "2025-26"].to_dict("records"))
    assert sum(r["box_complete"] for r in rows) / len(rows) > 0.99
    one = [r for r in rows if r["team_id"] == rows[0]["team_id"]]
    rates = box_rates(one)
    assert 0.45 < rates["efg"] < 0.65 and 0.2 < rates["orb_pct"] < 0.40 and 0.6 < rates["drb_pct"] < 0.85
    # the opponent's made shots are the opponent's own rows: a team's opp_efg equals its opponents' efg over the same games
    ids = {r["game_id"] for r in one}
    opp = [r for r in rows if r["game_id"] in ids and r["team_id"] != one[0]["team_id"]]
    assert box_rates(opp)["efg"] == pytest.approx(rates["opp_efg"], abs=1e-4)


def test_incomplete_box_is_skipped_not_zeroed():
    rows = enrich_team_games([{"game_id": "g", "team_id": 1, "opp_team_id": 2, "possessions": 100.0}], [])
    assert rows[0]["box_complete"] is False
    assert box_rates(rows)["efg"] is None


def test_adjusted_ratings_are_league_centered_and_remove_schedule(hist):
    tg, _ = hist
    g = TB.regular(tg[tg.season == "2025-26"])
    a = TR.adjusted(g)
    assert len(a) == 30
    assert abs(np.mean([x.net for x in a.values()])) < 1.0          # relative to the league
    raw = (100 * (g.pts - g.opp_pts) / g.possessions).groupby(g.team_id).mean()
    # adjustment changes ratings (a team's schedule matters) but keeps the order largely intact
    assert np.corrcoef([a[t].net for t in raw.index], raw.values)[0, 1] > 0.95
    assert max(abs(a[t].net - raw[t]) for t in raw.index) > 0.3


def test_weight_on_current_season_is_continuous_in_games():
    p = TB.BlendParams(rho_max=0.8, gamma=2.0, cbar=0.64, tau2=18.0, sigma2=200.0, n_transitions=2, n_team_seasons=60, k_tuned=4.0)
    ws = [p.weight_current(n) for n in range(0, 83)]
    assert ws[0] == 0.0 and ws == sorted(ws)                       # monotone: more games, more weight on this season
    assert all(b - a < 0.25 for a, b in zip(ws, ws[1:]))           # no step/cutoff anywhere
    assert p.weight_current(4) == pytest.approx(0.5) and 0.9 < p.weight_current(40) < 1.0


def test_blend_moves_from_prior_to_current_as_games_accumulate():
    p = TB.BlendParams(rho_max=0.8, gamma=2.0, cbar=0.64, tau2=18.0, sigma2=200.0, n_transitions=2, n_team_seasons=60, k_tuned=4.0)
    prior = TR.Adj(off=4.0, dfn=-2.0, n=82)                         # a strong team last year (net +6)
    est = [TB.estimate(p, prior, TR.Adj(off=-3.0, dfn=3.0, n=n), 0.64).net for n in (1, 5, 20, 60)]   # starts the season at net -6
    assert est == sorted(est, reverse=True)                        # slides monotonically toward the current evidence
    assert est[0] > 0 > est[-1] - 3
    none = TB.estimate(p, prior, None, 0.64)
    assert none.w_current == 0.0 and none.net == pytest.approx(p.rho(0.64) * 6.0)
    assert all(p.rho(c) < 1.0 for c in (0.0, 0.5, 1.0))   # last season is never carried over in full
    assert TB.estimate(p, None, TR.Adj(2.0, -1.0, 10), None).prior_net is None   # a team with no history uses the league as its prior


def test_lower_roster_continuity_means_less_credit_for_last_season():
    p = TB.load(PARAMS)
    assert p.rho(0.95) > p.rho(0.64) > p.rho(0.30)


def test_continuity_counts_prior_minutes_of_players_who_have_appeared(hist):
    _, pg = hist
    prev, cur = pg[pg.season == "2024-25"], pg[pg.season == "2025-26"]
    team = int(cur.team_id.iloc[0])
    full = TB.continuity(prev, cur, team)
    first = cur[cur.game_id.isin(sorted(cur[cur.team_id == team].game_id.unique())[:2])]
    early = TB.continuity(prev, first, team)
    assert 0.0 <= early <= full <= 1.0


def test_committed_parameters_are_the_fit_and_validated_out_of_sample():
    cal = json.loads(PARAMS.read_text())
    ck = cal["validation"]["checkpoints"]
    assert cal["params"]["n_transitions"] >= 2 and cal["params"]["tau2"] >= TB.MIN_TAU2
    assert 0.5 < cal["params"]["rho_max"] < 1.0 and cal["params"]["gamma"] > 0
    for n in ("5", "10", "20"):                                    # where the prior still matters, the blend beats both single sources, held out
        assert ck[n]["rmse_blend"] <= ck[n]["rmse_prior_only"] and ck[n]["rmse_blend"] <= ck[n]["rmse_current_only"] + 1e-9
    assert ck["60"]["rmse_blend"] - ck["60"]["rmse_current_only"] < 0.15   # late season: prior carries ~5% weight; no meaningful loss


def test_early_season_replay_through_the_exporter_inputs(hist, tmp_path):
    from nba_edge.research_export import _blend_inputs
    tg, pg = hist
    prior_t, prior_p = tg[tg.season == "2024-25"], pg[pg.season == "2024-25"]
    cur_t = TB.regular(tg[tg.season == "2025-26"]).sort_values(["game_date_et", "game_id"]).groupby("team_id").head(12).copy()
    cur_t["season"] = "2026-27"
    ids = set(cur_t.game_id)
    cur_p = pg[(pg.season == "2025-26") & pg.game_id.isin(ids)].copy()
    cur_p["season"] = "2026-27"
    rows_t = pd.concat([prior_t, cur_t]).to_dict("records")
    rows_p = pd.concat([prior_p, cur_p]).to_dict("records")
    (tmp_path / "research").mkdir()
    (tmp_path / "research" / "blend_params.json").write_bytes(PARAMS.read_bytes())
    warns: list[str] = []
    out, meta = _blend_inputs(rows_t, rows_p, "2026-27", tmp_path, warns)
    assert warns == [] and meta["prior_season"] == "2024-25" and len(out) == 30
    for v in out.values():
        assert v["n"] in (11, 12) or 10 <= v["n"] <= 12
        assert 0.6 < v["w"] < 0.85                                  # 12 games: mostly this season, prior still present
        assert v["cur_net"] is not None and v["prior_net"] is not None
    # the blend sits between the carried prior and the current evidence for every team
    for v in out.values():
        lo, hi = sorted((v["prior_net"], v["cur_net"]))
        assert lo - 1e-9 <= v["net"] <= hi + 1e-9


def test_refresh_skips_when_recent_and_records_status(tmp_path, monkeypatch):
    calls: list[dict] = []

    def fake_pull(out_root, seasons, what, **kw):
        calls.append({"seasons": seasons, **kw})
        (Path(out_root) / "espn").mkdir(parents=True, exist_ok=True)
        (Path(out_root) / "espn" / "MANIFEST.json").write_text(json.dumps({"seasons": {seasons[0]: {"n_games": 42, "date_max": "2026-11-01", "n_errors_this_run": 0}}}))
        return 0

    monkeypatch.setattr("nba_edge.team_research.refresh.run_history_pull", fake_pull)
    now = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    a = refresh(tmp_path, seasons=["2026-27"], min_interval_s=5400, now=now)
    assert a["games"] == {"2026-27": 42} and calls[0]["resume_window_days"] == 3
    b = refresh(tmp_path, seasons=["2026-27"], min_interval_s=5400, now=now + timedelta(minutes=30))
    assert b["skipped"] and len(calls) == 1
    refresh(tmp_path, seasons=["2026-27"], min_interval_s=5400, now=now + timedelta(minutes=100))
    assert len(calls) == 2


def _team_doc(season, as_of, n=12, with_blend=True):
    mets = [{"metric_id": "met_nba.team_blend_net", "sample_size": n}, {"metric_id": "met_nba.team_cur_adj_net", "sample_size": n}] if with_blend else []
    return {"entity_type": "TEAM", "entity": {"short_name": "XXX"}, "season": season, "metrics": mets, "quality": {"data_as_of": as_of}}


def test_validate_explorer_rejects_stale_wrong_season_or_missing_blend(tmp_path):
    d = tmp_path / "teams"
    d.mkdir()
    now = datetime(2026, 11, 2, 12, 0, tzinfo=UTC)
    for i in range(30):
        (d / f"t{i}.json").write_text(json.dumps(_team_doc("2026-27", "2026-11-02T01:00:00Z")))
    ok, rep = validate_explorer(tmp_path, season="2026-27", now=now)
    assert ok and rep["teams"] == 30
    (d / "t0.json").write_text(json.dumps(_team_doc("2025-26", "2026-06-14T00:30:00Z")))
    (d / "t1.json").write_text(json.dumps(_team_doc("2026-27", "2026-11-02T01:00:00Z", with_blend=False)))
    (d / "t2.json").write_text(json.dumps(_team_doc("2026-27", "2026-10-20T01:00:00Z")))
    (d / "t3.json").write_text(json.dumps(_team_doc("2026-27", "2026-11-02T01:00:00Z", n=0)))
    ok, rep = validate_explorer(tmp_path, season="2026-27", now=now)
    assert not ok and len(rep["problems"]) == 4
