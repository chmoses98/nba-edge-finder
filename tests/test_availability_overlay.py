"""PIT availability overlay: point-in-time status resolution, OUT / not-on-roster suppression, W2 caps,
optional minutes redistribution, distribution scaling, and an end-to-end replay on a synthetic store."""

from __future__ import annotations

import gzip
import json

import pytest

from nba_edge.availability.overlay import (
    MAX_MINUTES,
    PI_W2,
    AvailabilityIndex,
    _survival_knots,
    apply_overlay,
    scale_projection,
    survival,
)
from nba_edge.research.availability_replay import calibration_slope, evaluate, quantile_score

GAME, TEAM, TID = "espn:1", "AAA", 1610612737
TRI = {TID: TEAM}
KICK = "2026-11-10T00:00:00Z"
AS_OF = "2026-11-09T23:00:00Z"
ROSTER = [f"-{100 + i}" for i in range(10)]


def rec(pid, status="ACTIVE", certainty="PROJECTED", t="2026-11-09T22:00:00Z", source="nba_official_injury_report",
        team=TEAM, event=GAME):
    return {"captured_utc": t, "certainty": certainty, "entity_id": "espn:" + pid.lstrip("-"), "event_id": event,
            "kind": "injury", "schema": "sift.availability.v1", "source": source, "status": status, "team": team}


def snapshot(t="2026-11-09T22:00:00Z", overrides=None, omit=()):
    overrides = overrides or {}
    out = []
    for pid in ROSTER:
        if pid in omit:
            continue
        if pid in overrides:
            out.append(rec(pid, status=overrides[pid], certainty="REPORTED", t=t))
        else:
            out.append(rec(pid, t=t))
    return out


def proj(mean, quantiles, thresholds):
    return {"mean": mean, "median": quantiles[3], "p10": quantiles[1], "p90": quantiles[5],
            "quantiles": [{"q": q, "value": v} for q, v in zip((0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95), quantiles)],
            "thresholds": [{"at_least": a, "probability": p} for a, p in thresholds]}


def player_rows(pid, p=0.9, cmin=30.0, pts=15.0, as_of=AS_OF, kickoff=KICK, model="M"):
    base = {"game_id": GAME, "player_id": pid, "as_of": as_of, "kickoff": kickoff, "x_team_id": TID,
            "model_version": model, "participation_probability": p, "x_slot": "pretip"}
    mq = [cmin * f for f in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.25)]
    pq = [pts * f for f in (0.4, 0.5, 0.75, 1.0, 1.25, 1.5, 1.7)]
    pth = [(10.0, 0.8), (15.0, 0.5), (20.0, 0.25), (25.0, 0.1)]
    mth = [(10.0, 0.99), (20.0, 0.9), (30.0, 0.5), (35.0, 0.2)]
    rows = []
    for cond in (True, False):
        k = 1.0 if cond else p
        rows.append(dict(base, conditional_on_playing=cond, statistic="minutes",
                         projection=proj(cmin * k, mq, [(a, pr * k) for a, pr in mth])))
        rows.append(dict(base, conditional_on_playing=cond, statistic="points",
                         projection=proj(pts * k, pq, [(a, pr * k) for a, pr in pth])))
    return rows


def team_rows(**kw):
    return [r for pid in ROSTER for r in player_rows(pid, **kw)]


# ---------------------------------------------------------------------------- status resolution
def test_official_out_is_suppressed():
    idx = AvailabilityIndex(snapshot(overrides={ROSTER[0]: "OUT"}))
    st = idx.status(GAME, TEAM, ROSTER[0], AS_OF)
    assert (st.status, st.source) == ("out", "official")
    new, dec = apply_overlay(team_rows(), idx, TRI)
    assert dec[(GAME, ROSTER[0])].suppressed
    assert not [r for r in new if r["player_id"] == ROSTER[0]]


def test_record_captured_after_as_of_is_ignored():
    """Strict point-in-time: an OUT report published after the projection's as_of must not be used."""
    late = snapshot(t="2026-11-09T23:30:00Z", overrides={ROSTER[0]: "OUT"})
    idx = AvailabilityIndex(snapshot() + late)
    assert idx.status(GAME, TEAM, ROSTER[0], AS_OF).status == "unlisted"
    _, dec = apply_overlay(team_rows(), idx, TRI)
    assert not dec[(GAME, ROSTER[0])].suppressed
    # ...and it is only visible to the replay's after-the-fact late-scratch label
    assert idx.first_out_after(GAME, TEAM, ROSTER[0], AS_OF, KICK) == "2026-11-09T23:30:00Z"


def test_latest_snapshot_wins():
    idx = AvailabilityIndex(snapshot(t="2026-11-09T18:00:00Z", overrides={ROSTER[0]: "OUT"})
                            + snapshot(t="2026-11-09T22:00:00Z", overrides={ROSTER[0]: "ACTIVE"}))
    assert idx.status(GAME, TEAM, ROSTER[0], AS_OF).status == "available"


def test_player_missing_from_covered_roster_is_not_on_roster():
    idx = AvailabilityIndex(snapshot(omit=(ROSTER[1],)))
    st = idx.status(GAME, TEAM, ROSTER[1], AS_OF)
    assert (st.status, st.source) == ("not_on_roster", "official_roster")
    _, dec = apply_overlay(team_rows(), idx, TRI)
    assert dec[(GAME, ROSTER[1])].suppressed


def test_incomplete_team_snapshot_does_not_imply_roster_absence():
    idx = AvailabilityIndex(snapshot()[:5])  # 5 < MIN_ROSTER_SNAPSHOT
    assert idx.status(GAME, TEAM, ROSTER[9], AS_OF).status == "unknown"


def test_espn_fallback_only_without_official_team_coverage():
    espn = [rec(ROSTER[2], status="OUT", certainty="PROJECTED", source="espn_injuries")]
    idx = AvailabilityIndex(espn)
    assert (idx.status(GAME, TEAM, ROSTER[2], AS_OF).status, idx.status(GAME, TEAM, ROSTER[2], AS_OF).source) == ("out", "espn")
    _, dec = apply_overlay(team_rows(), idx, TRI)
    d = dec[(GAME, ROSTER[2])]
    assert not d.suppressed and d.p_new == pytest.approx(PI_W2["questionable"])  # unverified: thinned, never zeroed
    covered = AvailabilityIndex(espn + snapshot())
    assert covered.status(GAME, TEAM, ROSTER[2], AS_OF).status == "unlisted"


def test_no_information_leaves_baseline_untouched():
    rows = team_rows()
    new, dec = apply_overlay(rows, AvailabilityIndex([]), TRI)
    assert all(d.status.status == "unknown" and not d.suppressed for d in dec.values())
    assert [r["projection"] for r in new] == [r["projection"] for r in rows]


# ---------------------------------------------------------------------------- participation caps
@pytest.mark.parametrize("status,p,expected", [("QUESTIONABLE", 0.9, PI_W2["questionable"]),
                                               ("QUESTIONABLE", 0.3, 0.3),
                                               ("PROBABLE", 0.99, PI_W2["probable"]),
                                               ("DOUBTFUL", 0.9, 0.0)])
def test_w2_caps_lower_but_never_raise(status, p, expected):
    idx = AvailabilityIndex(snapshot(overrides={ROSTER[3]: status}))
    rows = [r for pid in ROSTER for r in player_rows(pid, p=p)]
    new, dec = apply_overlay(rows, idx, TRI)
    assert dec[(GAME, ROSTER[3])].p_new == pytest.approx(expected)
    if expected > 0:
        u = next(r for r in new if r["player_id"] == ROSTER[3] and not r["conditional_on_playing"] and r["statistic"] == "points")
        c = next(r for r in new if r["player_id"] == ROSTER[3] and r["conditional_on_playing"] and r["statistic"] == "points")
        assert u["participation_probability"] == pytest.approx(round(expected, 4))
        assert u["projection"]["mean"] == pytest.approx(expected * c["projection"]["mean"], rel=1e-3)
        assert all(t["probability"] <= expected + 1e-9 for t in u["projection"]["thresholds"])


def test_default_overlay_keeps_teammates_conditional_rows_identical():
    rows = team_rows()
    idx = AvailabilityIndex(snapshot(overrides={ROSTER[0]: "OUT"}))
    new, _ = apply_overlay(rows, idx, TRI)
    before = {(r["player_id"], r["conditional_on_playing"], r["statistic"]): r["projection"] for r in rows}
    for r in new:
        assert r["projection"] == before[(r["player_id"], r["conditional_on_playing"], r["statistic"])]
        assert r["model_version"].endswith("+pit-availability-overlay-v1")


def test_projection_at_or_after_kickoff_is_refused():
    rows = team_rows(as_of=KICK)
    with pytest.raises(ValueError):
        apply_overlay(rows, AvailabilityIndex(snapshot()), TRI)


# ---------------------------------------------------------------------------- optional redistribution
def _uncond_minutes(rows):
    return sum(r["projection"]["mean"] for r in rows if not r["conditional_on_playing"] and r["statistic"] == "minutes")


def test_redistribution_conserves_regular_minutes_and_caps():
    rows = team_rows(p=0.9, cmin=24.0)
    idx = AvailabilityIndex(snapshot(overrides={ROSTER[0]: "OUT"}))
    new, dec = apply_overlay(rows, idx, TRI, redistribute=True)
    assert _uncond_minutes(new) == pytest.approx(_uncond_minutes(rows), abs=0.05)
    k = dec[(GAME, ROSTER[1])].k
    assert k > 1.0
    c_pts = next(r for r in new if r["player_id"] == ROSTER[1] and r["conditional_on_playing"] and r["statistic"] == "points")
    assert c_pts["projection"]["mean"] == pytest.approx(15.0 * k, rel=1e-3)
    assert all(d.cond_minutes_new <= MAX_MINUTES + 1e-9 for d in dec.values())


def test_minutes_of_already_absent_players_are_not_redistributed():
    rows = [r for pid in ROSTER for r in player_rows(pid, p=0.3 if pid == ROSTER[0] else 0.9)]
    idx = AvailabilityIndex(snapshot(overrides={ROSTER[0]: "OUT"}))
    _, dec = apply_overlay(rows, idx, TRI, redistribute=True)
    assert all(d.k == 1.0 for d in dec.values())
    _, dec_all = apply_overlay(rows, idx, TRI, redistribute=True, regular_p=0.0)
    assert dec_all[(GAME, ROSTER[1])].k > 1.0


# ---------------------------------------------------------------------------- distribution scaling
def test_scale_projection_identity_and_monotone():
    p = player_rows(ROSTER[0])[1]["projection"]
    assert scale_projection(p, 1.0) is p
    s = scale_projection(p, 1.2)
    probs = [t["probability"] for t in s["thresholds"]]
    assert probs == sorted(probs, reverse=True)
    assert all(a >= b for a, b in zip(probs, [t["probability"] for t in p["thresholds"]]))
    knots = _survival_knots(p)
    assert s["thresholds"][1]["probability"] == pytest.approx(survival(knots, 15.0 / 1.2), abs=1e-4)
    assert s["mean"] == pytest.approx(p["mean"] * 1.2)


# ---------------------------------------------------------------------------- replay metrics + end to end
def test_quantile_score_and_calibration_slope():
    qs = [{"q": 0.5, "value": 10.0}]
    assert quantile_score(qs, 10.0) == 0.0
    assert quantile_score(qs, 14.0) == pytest.approx(2 * 0.5 * 4.0)
    import numpy as np

    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.95, 20000)
    y = (rng.uniform(size=p.size) < p).astype(float)
    a, b = calibration_slope(p, y)
    assert abs(a) < 0.1 and abs(b - 1.0) < 0.1


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def test_replay_end_to_end_improves_participation_and_counts_suppression(tmp_path):
    shadow, pdata = tmp_path / "shadow", tmp_path / "pdata"
    rows = team_rows()
    for arm in ("sim_rotation", "ewm5"):
        for cond in ("conditional", "unconditional"):
            _write(shadow / f"projections/{arm}/{cond}/dt=2026-11-09/p.jsonl.gz",
                   [dict(r, model_version=arm) for r in rows if r["conditional_on_playing"] == (cond == "conditional")])
    gate = []
    for pid in ROSTER[2:]:  # ROSTER[0] OUT and ROSTER[1] not on roster: neither appears in the box
        gate += [{"game_id": GAME, "player_id": pid, "statistic": "minutes", "actual": 24.0, "played": True,
                  "observed_at": "2026-11-10T03:00:00Z"},
                 {"game_id": GAME, "player_id": pid, "statistic": "points", "actual": 12.0, "played": True,
                  "observed_at": "2026-11-10T03:00:00Z"}]
    _write(shadow / "outcomes/gate/dt=2026-11-10/g.jsonl.gz", gate)
    _write(pdata / "availability/nba/2026-11-09/a.jsonl.gz", snapshot(overrides={ROSTER[0]: "OUT"}, omit=(ROSTER[1],)))
    teams = tmp_path / "teams.csv"
    teams.write_text(f"team_id,tricode\n{TID},{TEAM}\n")
    rep = evaluate(str(shadow), str(pdata), str(teams), arms=("sim_rotation",))
    res = rep["arms"]["sim_rotation"]["all"]
    pre = res["by_slot"]["pretip"]
    assert pre["variants"]["overlay"]["participation"]["brier"] < pre["variants"]["baseline"]["participation"]["brier"]
    assert pre["deltas"]["overlay-baseline:prop_brier"]["delta"] == 0.0  # played players' conditional rows untouched
    assert res["absent_player_games"]["total"] == 2
    assert res["absent_player_games"]["suppressed"] == 2
    assert pre["prop_rungs"]["suppressed_but_played"] == 0
    assert pre["prop_rungs"]["issued_for_non_players_overlay"] == 0
