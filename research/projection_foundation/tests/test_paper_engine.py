"""Paper engine chain: market layer, probabilities, decisions, settlement, replay, idempotence, archive integrity.

REAL data: tests/fixtures/paper/market_archive is a mini capture archive (checkpoint + hash-verifiable deltas) holding the real Kalshi boards of
the three 2026-10-21 opening-night games as captured on 2026-10-20 (build_fixtures.py). Forecasts are SYNTHETIC but built from the repo's own
pmf families (pf_core.dists negbin / discretized normal); they are not model output and make no claim about edges. Horizon tests shift the
real game's tip to 2026-10-20T19:00Z (the board ticks end 18:24Z) with `game_date_et` kept at the Kalshi event date 2026-10-21."""
import copy
import gzip
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
PF = HERE.parent
sys.path.insert(0, str(PF))
from pf_core import dists, prospective as pr  # noqa: E402
from nba.live import ops_guard  # noqa: E402
from nba.paper import config as CFG, engine as EN, markets as MK, probability as PR, run as RUN, schema as S, settle as ST, store  # noqa: E402
from nba_edge.archive.delta import canonical_board  # noqa: E402

FIXARCH = HERE / "fixtures" / "paper" / "market_archive"
UTC = timezone.utc


def utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


GAME = {"game_id": "espn:401909088", "start_utc": "2026-10-20T19:00:00Z", "home": "DET", "away": "BOS", "game_date_et": "2026-10-20"}
GAME2 = {"game_id": "espn:401909089", "start_utc": "2026-10-20T23:00:00Z", "home": "NYK", "away": "PHI", "game_date_et": "2026-10-20"}


@pytest.fixture(scope="module")
def cfg():
    return CFG.load()


@pytest.fixture(scope="module")
def real_board():
    r = MK.ChainReader(str(FIXARCH), "markets")
    dt, b = r.board_at(utc("2026-10-20T18:30:00Z"))
    return dt, b


def gi_for(*games):
    return MK.GameIndex([MK.Game.from_dict(g) for g in games])


def snaps_for(board, dt, game=GAME, horizon="LIVE", target=None):
    g = MK.Game.from_dict(game)
    rows, cov = MK.snapshot_rows(board, gi_for(game), g, horizon, target or utc("2026-10-20T18:30:00Z"), dt)
    return rows, cov


def synth_forecasts(rows, game, gen="2026-10-20T15:00:00Z", p_play=0.93, scale=1.0, seed=3, role="challenger"):
    """Synthetic challenger forecasts for every player seen in the market rows, from real pmf families (negbin)."""
    rng = np.random.default_rng(seed)
    seen = sorted({(r["team"], r["player_name"]) for r in rows if r["scope"] == "player" and r["player_name"]})
    recs = []
    for i, (team, name) in enumerate(seen):
        eid = f"espn:{9000 + i}"
        base = dict(sport="NBA", model_role=role, model_version="pf-test", game_id=game["game_id"], game_start_utc=game["start_utc"], entity_id=eid,
                    entity_name=name, team=team, generated_utc=gen, data_asof_utc=gen, gate_status="PASS", readiness="SHADOW VALIDATION",
                    participation={"status": "LIKELY_ACTIVE"})
        recs.append({**base, "family": "participation", "model_id": "pf-nba-participation", "mean": p_play, "lo": 0, "probs": [1 - p_play, p_play]})
        for stat, mean in (("points", 17.0), ("rebounds", 6.0), ("assists", 4.0), ("threes", 1.8), ("pra", 28.0)):
            d = dists.negbin(np.array([mean * scale * rng.uniform(0.7, 1.3)]), 0.12, 90)
            recs.append({**base, "family": stat, "model_id": f"pf-nba-{stat}", "mean": float(d.mean[0]), "lo": int(d.lo), "probs": [float(x) for x in d.P[0]]})
    return recs


def synth_game_forecast(game, gen="2026-10-20T15:00:00Z", mu_home=112.0, mu_away=109.0, sd=11.5, rho=0.2):
    ts = []
    for team, mu in ((game["home"], mu_home), (game["away"], mu_away)):
        d = dists.discretized_normal(np.array([mu]), np.array([sd]), 60, 130, None)
        ts.append({"team": team, "mean": float(d.mean[0]), "lo": int(d.lo), "probs": [float(x) for x in d.P[0]]})
    return {"schema": S.GAME_FORECAST_SCHEMA, "game_id": game["game_id"], "game_start_utc": game["start_utc"], "home": game["home"], "away": game["away"],
            "generated_utc": gen, "data_asof_utc": gen, "model_id": "pf-nba-team_points", "model_version": "pf-test", "teams": ts, "rho": rho,
            "game_forecast_id": S.sha(["gf", game["game_id"], gen]), "archived_utc": gen}


def seed_archive(root: Path, games=(GAME,), gen="2026-10-20T15:00:00Z", archived="2026-10-20T15:01:00Z", **kw):
    """projection-data archive (git repo) with synthetic challenger forecasts and game forecasts for `games`, built from the real board."""
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-q", "--allow-empty", "-m", "init"], check=True)
    dt, board = MK.ChainReader(str(FIXARCH), "markets").board_at(utc("2026-10-20T18:30:00Z"))
    for g in games:
        rows, _ = snaps_for(board, dt, g)
        recs = synth_forecasts(rows, g, gen=gen, **kw)
        res = pr.archive_forecasts(recs, str(root), archived)
        assert res["written"] == len(recs) and not res["late_rejected"]
        gf = synth_game_forecast(g, gen=gen)
        gf["archived_utc"] = archived
        store.write_new(str(root), "game_forecasts", MK.parse_ts(g["start_utc"]).strftime("%Y-%m-%d"), [gf], "game_forecast_id", utc(archived))


def write_chain(root: Path, boards, run_id="t"):
    sys.path.insert(0, str(HERE / "fixtures" / "paper"))
    import build_fixtures
    build_fixtures.write_chain(root, [(t, canonical_board(rows.values() if isinstance(rows, dict) else rows)) for t, rows in boards], run_id)


# ------------------------------------------------------------------------------------------------------------------ market layer
def test_real_fixture_chain_verifies_and_is_strictly_as_of(real_board):
    r = MK.ChainReader(str(FIXARCH), "markets")
    ts = r.ticks()
    assert len(ts) == 7 and ts[0] == utc("2026-10-20T13:03:59Z") and ts[-1] == utc("2026-10-20T18:24:36Z")
    dt, b = real_board
    assert dt == utc("2026-10-20T18:24:36Z") and len(b) == 1371
    assert r.board_at(utc("2026-10-20T13:00:00Z"), lookback=timedelta(hours=1)) is None       # nothing at/before: never a later board
    got = r.board_at(utc("2026-10-20T17:30:00Z"))
    assert got[0] == utc("2026-10-20T17:24:36Z")


def test_tampered_or_missing_delta_breaks_the_chain_from_that_tick(tmp_path):
    for k in ("tamper", "missing"):
        d = tmp_path / k
        shutil.copytree(FIXARCH, d)
        fs = sorted((d / "kalshi" / "markets_delta" / "dt=2026-10-20").glob("*.json.gz"))
        victim = fs[2]                                                     # 17:24:36, the 4th board of 7
        if k == "missing":
            victim.unlink()
        else:
            raw = json.loads(gzip.decompress(victim.read_bytes()))
            tk = next(iter(raw["changed"] or raw["added"]))
            (raw["changed"] if raw["changed"] else raw["added"])[tk] = {**(raw["changed"] or raw["added"])[tk], "yes_bid_dollars": "0.9999"}
            victim.write_bytes(gzip.compress((json.dumps(raw, sort_keys=True) + "\n").encode()))
        out = list(MK.ChainReader(str(d), "markets").walk(utc("2026-10-20T13:00:00Z"), utc("2026-10-20T19:00:00Z")))
        good = [dt for dt, b in out if b is not None]
        bad = [dt for dt, b in out if b is None]
        assert utc("2026-10-20T17:03:59Z") in good and bad, k
        assert all(x >= utc("2026-10-20T17:24:36Z") for x in bad), k
        assert utc("2026-10-20T18:24:36Z") in bad                         # nothing after a broken link is guessed
        assert MK.ChainReader(str(d), "markets").board_at(utc("2026-10-20T18:30:00Z"))[1] is None


def test_real_contract_parsing_and_support_states(real_board):
    dt, b = real_board
    gi = gi_for(GAME, GAME2)
    c = MK.contract_from_row(b["KXNBAPTS-26OCT20BOSDET-DETCCUNNINGHAM2-25"] if "KXNBAPTS-26OCT20BOSDET-DETCCUNNINGHAM2-25" in b
                             else next(r for r in b.values() if r["ticker"].startswith("KXNBAPTS-26OCT20BOSDET-DET")), gi)
    assert c["scope"] == "player" and c["stat"] == "points" and c["support"] == "MODELED" and c["team"] == "DET" and c["comparator"] == "gt"
    assert c["k"] == int(c["threshold"]) + 1 and c["player_name"]
    sp = next(r for r in b.values() if r["ticker"].startswith("KXNBASPREAD-26OCT20BOSDET-") and r["ticker"].split("-")[-1].startswith("DET"))
    c = MK.contract_from_row(sp, gi)
    assert c["family"] == "game_spread" and c["side_team"] == "DET" and c["threshold"] == sp["floor_strike"]
    tt = next(r for r in b.values() if r["ticker"].startswith("KXNBATEAMTOTAL-26OCT20BOSDET-BOS"))
    assert MK.contract_from_row(tt, gi)["stat"] == "team_total"
    per = next(r for r in b.values() if r["ticker"].startswith("KXNBA1HSPREAD-26OCT20BOSDET"))
    assert MK.contract_from_row(per, gi)["support"] == "NO_PERIOD_MODEL"
    stl = next(r for r in b.values() if r["ticker"].startswith("KXNBASTL-26OCT20BOSDET"))
    assert MK.contract_from_row(stl, gi)["support"] == "UNSUPPORTED_SERIES"
    assert MK.contract_from_row(sp, gi_for(GAME2)) is None                    # not one of our games


def test_snapshot_rows_count_unsupported_series_and_skip_them(real_board):
    dt, b = real_board
    rows, cov = snaps_for(b, dt)
    assert rows and not any(r["series"] in ("KXNBASTL", "KXNBABLK", "KXNBAWINMARGIN") for r in rows)
    assert cov["UNSUPPORTED_SERIES:KXNBASTL"] > 0 and cov["quote:TWO_SIDED"] > 300
    assert {r["support"] for r in rows} == {"MODELED", "NO_PERIOD_MODEL"}
    for r in rows:
        if r["quote_class"] == "TWO_SIDED":
            assert abs(r["no_ask"] - (1 - r["yes_bid"])) < 1e-9 and abs(r["no_bid"] - (1 - r["yes_ask"])) < 1e-9 and r["yes_bid"] <= r["yes_ask"]


@pytest.mark.parametrize("bid,ask,cls", [("0.4400", "0.4700", "TWO_SIDED"), ("0.0000", "1.0000", "NO_QUOTE"), ("0.0100", "0.9900", "PLACEHOLDER"),
                                         ("0.5000", "0.4000", "INVALID"), ("0.0000", "0.3000", "ONE_SIDED"), ("0.5000", "1.2000", "INVALID")])
def test_quote_classification_never_treats_placeholders_or_crossed_books_as_prices(real_board, bid, ask, cls):
    dt, b = real_board
    row = copy.deepcopy(next(r for r in b.values() if r["ticker"].startswith("KXNBATOTAL-26OCT20BOSDET")))
    row["yes_bid_dollars"], row["yes_ask_dollars"] = bid, ask
    assert MK.classify_quote(row) == cls
    q = MK.quote(row)
    if cls in ("INVALID", "NO_QUOTE", "PLACEHOLDER"):
        assert q["yes_bid"] is None and q["yes_ask"] is None and q["no_ask"] is None


def test_depth_from_orderbook_levels():
    book = {"yes": [[2, 25.0], [1, 3050.0]], "no": [[89, 1.0], [88, 26.0], [87, 164.0], [83, 47.0]]}
    assert MK.depth(book, "YES", 12) == 1 + 26               # buy YES at 12c <=> hit NO bids priced >= 88c
    assert MK.depth(book, "YES", 13) == 1 + 26 + 164         # >= 87c
    assert MK.depth(book, "NO", 98) == 25.0                  # buy NO at 98c <=> hit YES bids priced >= 2c
    assert MK.depth(None, "YES", 50) is None


def test_player_identity_never_guesses():
    fc = [{"entity_id": "espn:1", "entity_name": "Jayson Tatum", "team": "BOS"}, {"entity_id": "espn:2", "entity_name": "Jalen Williams", "team": "OKC"},
          {"entity_id": "espn:3", "entity_name": "Jaylin Williams", "team": "OKC"}, {"entity_id": "espn:4", "entity_name": "Jalen Williams", "team": "CHI"}]
    p = MK.PlayerIndex(fc)
    assert p.resolve("BOS", "Jayson Tatum") == ("espn:1", "team_name")
    assert p.resolve("OKC", "J. Williams")[0] is None and p.resolve("BOS", "Nobody Here")[0] is None
    assert p.resolve(None, "Jayson Tatum")[0] == "espn:1" and p.resolve(None, "Jalen Williams")[0] is None      # ambiguous league-wide


def test_choose_ticks_missed_stale_and_missing_causes():
    ticks = [utc(f"2026-10-20T{h}Z") for h in ("13:03:59", "16:48:59", "17:03:59", "17:24:36", "17:54:36", "18:09:36", "18:24:36")]
    tip = utc("2026-10-20T19:00:00Z")
    ch = MK.choose_ticks(ticks, tip, utc("2026-10-20T19:10:00Z"))
    assert ch["T-90"]["board_dt"] == utc("2026-10-20T17:24:36Z") and ch["T-60"]["board_dt"] == utc("2026-10-20T17:54:36Z")
    assert ch["T-10"]["board_dt"] == utc("2026-10-20T18:24:36Z") and ch["T-10"]["gap_s"] == 25 * 60 + 24
    assert ch["LAST_VALID"]["board_dt"] == utc("2026-10-20T18:24:36Z") and not MK.is_closing_line(ch["LAST_VALID"]["board_dt"], tip)
    ch = MK.choose_ticks(ticks, utc("2026-10-20T15:00:00Z"), utc("2026-10-20T15:10:00Z"))                     # only tick before 14:30 is 13:03:59
    assert ch["T-90"]["board_dt"] == ticks[0] and ch["T-60"]["cause"] == "GAP_TOO_LARGE" and ch["T-30"]["board_dt"] is None and ch["T-30"]["gap_s"] > 1800
    ch = MK.choose_ticks(ticks, utc("2026-10-20T09:00:00Z"), utc("2026-10-20T09:10:00Z"))
    assert ch["T-60"]["cause"] == "NO_BOARD" and ch["LAST_VALID"]["cause"] == "NO_BOARD"
    assert set(MK.choose_ticks(ticks, utc("2026-10-20T23:00:00Z"), utc("2026-10-20T19:10:00Z"))) == set()        # nothing due yet


# ------------------------------------------------------------------------------------------------------------------ probabilities
def test_ladder_probabilities_monotone_and_participation_aware_ev_and_complements(cfg):
    d = dists.negbin(np.array([20.0]), 0.12, 90)
    rec = {"lo": int(d.lo), "probs": [float(x) for x in d.P[0]]}
    ps = [PR.p_ge(rec, k) for k in range(5, 40, 3)]
    assert all(a >= b - 1e-12 for a, b in zip(ps, ps[1:])) and abs(PR.p_ge(rec, 0) - 1.0) < 1e-9 and PR.p_ge(rec, 500) == 0.0
    assert PR.p_ge(rec, 20, 1.1) > PR.p_ge(rec, 20) > PR.p_ge(rec, 20, 0.9)                                  # scaling the mean moves the tail
    pr_ = {"p_yes_cond": 0.62, "p_yes_sd": 0.05, "p_play": 0.8, "dnp_exposed": True}
    yes, no = PR.side_probabilities(pr_, "YES", 0.55), PR.side_probabilities(pr_, "NO", 0.55)
    assert abs(yes["p_cond"] + no["p_cond"] - 1) < 1e-12 and abs(yes["p_model"] + no["p_model"] - 1) < 1e-12        # complements incl. the DNP leg
    assert abs(yes["p_model"] - (0.8 * 0.62 + 0.2 * 0.55)) < 1e-12
    g = PR.side_probabilities({**pr_, "dnp_exposed": False, "p_play": 1.0}, "NO", None)
    assert abs(g["p_model"] - 0.38) < 1e-12 and g["p_model_sd"] == 0.05


def test_game_probabilities_are_deterministic_symmetric_and_respect_rho(cfg):
    gf = synth_game_forecast(GAME, mu_home=110.0, mu_away=110.0)
    js = PR.JointSim(gf, cfg)
    assert abs(js.p_winner("DET") + js.p_winner("BOS") - 1) < 1e-9 and abs(js.p_winner("DET") - 0.5) < 0.01
    assert js.p_total(219.5) > js.p_total(230.5) and js.p_spread("DET", 2.5) > js.p_spread("DET", 8.5)
    assert PR.JointSim(gf, cfg).p_total(220.5) == js.p_total(220.5)                                         # fixed seed
    hi = PR.JointSim(dict(gf, rho=0.6), cfg)
    lo = PR.JointSim(dict(gf, rho=0.0), cfg)
    tot_sd = lambda j: float(np.std(j.pts["DET"] + j.pts["BOS"]))                                            # noqa: E731
    mar_sd = lambda j: float(np.std(j.pts["DET"] - j.pts["BOS"]))                                            # noqa: E731
    assert tot_sd(hi) > tot_sd(lo) and mar_sd(hi) < mar_sd(lo)
    strong = PR.JointSim(synth_game_forecast(GAME, mu_home=118.0, mu_away=106.0), cfg)
    assert strong.p_winner("DET") > 0.75 and strong.p_spread("DET", 5.5) > 0.5


def test_late_and_unarchived_forecasts_are_ignored(tmp_path):
    root = tmp_path / "arch"
    seed_archive(root, gen="2026-10-20T17:00:00Z", archived="2026-10-20T17:01:00Z")
    recs = pr._read(str(root), "forecasts", "NBA")
    assert PR.Forecasts(recs, utc("2026-10-20T16:59:00Z")).records() == []                                    # generated later than as_of
    assert PR.Forecasts(recs, utc("2026-10-20T17:00:30Z")).records() == []                                    # generated but not yet archived
    f = PR.Forecasts(recs, utc("2026-10-20T17:02:00Z"))
    assert f.records() and f.ignored_late == 0
    later = [dict(r, generated_utc="2026-10-20T17:30:00Z", archived_utc="2026-10-20T17:31:00Z", mean=99.0) for r in recs if r["family"] == "points"]
    f2 = PR.Forecasts(recs + later, utc("2026-10-20T17:10:00Z"))
    assert f2.ignored_late == len(later) and all(r["mean"] != 99.0 for r in f2.records())                       # the as-of version is kept
    assert any(r["mean"] == 99.0 for r in PR.Forecasts(recs + later, utc("2026-10-20T18:00:00Z")).records())    # and the newer one once it is due


# ------------------------------------------------------------------------------------------------------------------ engine on the real board
@pytest.fixture(scope="module")
def decided(real_board, tmp_path_factory, cfg):
    root = tmp_path_factory.mktemp("arch") / "arch"
    seed_archive(root, games=(GAME, GAME2))
    dt, board = real_board
    rows = []
    for g in (GAME, GAME2):
        r, _ = snaps_for(board, dt, g)
        rows += r
    recs = pr._read(str(root), "forecasts", "NBA")
    gf = store.read(str(root), "game_forecasts")
    now = utc("2026-10-20T18:30:00Z")
    fc, gfc, players = PR.Forecasts(recs, now), PR.GameForecasts(gf, now), MK.PlayerIndex(recs)
    res = EN.decide(rows, fc, gfc, players, as_of=now, decided=now, mode="contemporaneous", cfg=cfg)
    return {"rows": rows, "res": res, "cfg": cfg, "now": now, "fc": fc, "gfc": gfc, "players": players}


def test_every_evaluable_contract_has_both_sides_and_unevaluable_ones_a_both_pass(decided):
    c = decided["res"]["candidates"]
    by = {}
    for r in c:
        by.setdefault(r["snapshot_id"], []).append(r)
    sides = {sid: sorted(x["side"] for x in rs) for sid, rs in by.items()}
    assert set(map(tuple, sides.values())) == {("NO", "YES"), ("BOTH",)}
    both = [r for r in c if r["side"] == "BOTH"]
    assert {r["reason"] for r in both} == {"NO_PERIOD_MODEL"}                  # in this fixture every player has a forecast, only period markets are unevaluable
    assert all(r["decision"] == "PASS" and r["simulated_contracts"] == 0 and not r["quality"]["passed"] for r in both)
    for sid, rs in by.items():
        if len(rs) == 2:
            y, n = sorted(rs, key=lambda r: r["side"], reverse=True)
            assert y["side"] == "YES"
            assert abs(y["p_cond"] + n["p_cond"] - 1) < 1e-12 and abs(y["p_model"] + n["p_model"] - 1) < 1e-9
            if y["price"] is not None:
                assert abs(y["price"] - (1 - n["bid"])) < 1e-9 and abs(n["price"] - (1 - y["bid"])) < 1e-9     # no_ask = 1 - yes_bid
                assert abs(y["spread"] - n["spread"]) < 1e-9


def test_only_enumerated_reasons_and_rows_validate(decided):
    ok = set(EN.REASONS)
    for r in decided["res"]["decisions"]:
        assert not EN.validate_row(r)
        base = r["reason"].split(":")[0]
        assert base in ok | {"QUALITY_GATE", "EXPOSURE_CAP"}, r["reason"]
        if r["reason"].startswith("QUALITY_GATE:"):
            assert r["reason"].split(":")[1] in EN.QUALITY_CODES
        if r["reason"].startswith("EXPOSURE_CAP:"):
            assert r["reason"].split(":")[1] in EN.CAP_CODES


def test_no_trade_on_placeholder_wide_or_extreme_quotes_and_one_trade_per_thesis(decided):
    dec = decided["res"]["decisions"]
    cand = {r["candidate_id"]: r for r in decided["res"]["candidates"]}
    trades = [r for r in dec if r["decision"] == "TRADE"]
    assert trades, "synthetic forecasts differ from the market, so some trades are expected"
    for t in trades:
        c = cand[t["candidate_id"]]
        assert c["quality"]["passed"] and not c["quality"]["failures"] and t["ev_net"] >= decided["cfg"]["strategies"][t["strategy_id"]]["min_ev_net"] - 1e-12
        assert t["simulated_contracts"] == 1 and t["price"] is not None and t["effective_entry"] <= 0.99
    for strat in ("PF_EDGE_V1", "PF_EDGE_STRICT_V1"):
        th = [t["thesis_id"] for t in trades if t["strategy_id"] == strat]
        assert len(th) == len(set(th)), "a ladder / YES-NO pair on one thesis must collapse to one trade"
    # whenever a thesis had several qualifying contracts, the traded one is the highest net EV, not the cheapest
    qual = [r for r in dec if r["strategy_id"] == "PF_EDGE_V1" and r["reason"] in ("EV_ABOVE_THRESHOLD", "NOT_BEST_IN_THESIS")]
    for t in [x for x in qual if x["decision"] == "TRADE"]:
        rivals = [x for x in qual if x["thesis_id"] == t["thesis_id"] and x["decision"] == "PASS"]
        assert all(x["ev_net"] <= t["ev_net"] + 1e-12 for x in rivals)
    assert any(r["reason"] == "NOT_BEST_IN_THESIS" for r in dec)               # ladders really were collapsed
    # every pass row of the edge strategies is preserved and points at its full candidate
    comp = [r for r in dec if r["strategy_id"] != "PF_ALL_CANDIDATES_V1" and r["decision"] == "PASS"]
    assert comp and all(r["compact"] and r["candidate_id"] in cand for r in comp)


def test_strict_strategy_horizon_protocol_and_gate_filters(decided, cfg):
    dec = decided["res"]["decisions"]
    strict = [r for r in dec if r["strategy_id"] == "PF_EDGE_STRICT_V1"]
    one = [r for r in strict if r["game_id"] == GAME["game_id"]]
    two = [r for r in strict if r["game_id"] == GAME2["game_id"]]
    assert one and "OUTSIDE_PROTOCOL_HORIZON" not in {r["reason"] for r in one}                # LIVE at 30 min to tip is inside [30, 90]
    assert {r["reason"] for r in two} == {"OUTSIDE_PROTOCOL_HORIZON"}                          # the 23:00Z game is 270 min away
    far = {"horizon": "LIVE", "minutes_to_tip": 400.0}
    assert not EN._horizon_allowed(cfg["strategies"]["PF_EDGE_STRICT_V1"], far) and EN._horizon_allowed(cfg["strategies"]["PF_EDGE_V1"], far)
    assert not EN._horizon_allowed(cfg["strategies"]["PF_EDGE_STRICT_V1"], {"horizon": "OPEN", "minutes_to_tip": 3000.0})
    # the same board at a T-60 horizon label is inside the protocol
    rows = [dict(r, horizon="T-60") for r in decided["rows"] if r["game_id"] == GAME["game_id"]]
    res = EN.decide(rows, decided["fc"], decided["gfc"], decided["players"], as_of=utc("2026-10-20T18:30:00Z"), decided=decided["now"],
                    mode="asof_replay", cfg=cfg)
    strict = [r for r in res["decisions"] if r["strategy_id"] == "PF_EDGE_STRICT_V1"]
    assert {r["reason"] for r in strict} - {"OUTSIDE_PROTOCOL_HORIZON"}
    assert any(r["reason"].startswith("QUALITY_GATE:SPREAD_WIDE") or r["reason"] == "EV_BELOW_THRESHOLD" for r in strict)
    for r in strict:
        if r["decision"] == "TRADE":
            assert r["ev_net"] >= 0.06 and r["p_play"] >= 0.85 and r["spread"] <= 0.06 + 1e-9 and r["gate"]["status"] == "PASS"


def test_exposure_caps_are_enforced_and_reported(decided, cfg):
    tight = copy.deepcopy(cfg)
    tight["exposure"].update({"max_trades_per_player_game": 1, "max_trades_per_team_game": 2, "max_trades_per_game": 3, "max_notional_per_day": 1.2})
    res = EN.decide([r for r in decided["rows"]], decided["fc"], decided["gfc"], decided["players"], as_of=decided["now"], decided=decided["now"],
                    mode="contemporaneous", cfg=tight)
    tr = [r for r in res["decisions"] if r["strategy_id"] == "PF_EDGE_V1" and r["decision"] == "TRADE"]
    per_game, per_unit, per_team = {}, {}, {}
    for r in tr:
        per_game[r["game_id"]] = per_game.get(r["game_id"], 0) + 1
        if r["family"].startswith("player_"):
            per_unit[r["unit_id"]] = per_unit.get(r["unit_id"], 0) + 1
        if r["team"]:
            per_team[(r["game_id"], r["team"])] = per_team.get((r["game_id"], r["team"]), 0) + 1
    assert all(v <= 3 for v in per_game.values()) and all(v <= 1 for v in per_unit.values()) and all(v <= 2 for v in per_team.values())
    assert sum(r["effective_entry"] for r in tr) <= 1.2 + 1e-9
    caps = {r["reason"] for r in res["decisions"] if r["reason"].startswith("EXPOSURE_CAP:")}
    assert caps and caps <= {"EXPOSURE_CAP:" + c for c in EN.CAP_CODES}


def test_dnp_leg_is_valued_at_the_mid_in_ev(decided, cfg):
    cand = next(r for r in decided["res"]["candidates"] if r["side"] == "YES" and r["family"] == "player_points" and r["price"] is not None
                and r["quality"]["passed"])
    mult = cand["fee_assumption"]["multiplier"]
    eff = cand["effective_entry"]
    m = cand["m_side_used_for_dnp"]
    exp = cand["p_play"] * cand["p_cond"] + (1 - cand["p_play"]) * m - eff - mult * eff * (1 - eff)
    assert abs(cand["ev_net"] - exp) < 1e-9 and abs(cand["ev_conditional"] - (cand["p_cond"] - eff - mult * eff * (1 - eff))) < 1e-9
    assert cand["p_model_sd"] > 0 and cand["uncertainty_method"] == "mean_scale_sensitivity"


def test_missing_forecast_and_unresolved_player_are_explicit_passes(real_board, cfg):
    dt, board = real_board
    rows, _ = snaps_for(board, dt)
    now = utc("2026-10-20T18:30:00Z")
    empty = EN.decide(rows, PR.Forecasts([], now), PR.GameForecasts([], now), MK.PlayerIndex([]), as_of=now, decided=now, mode="contemporaneous", cfg=cfg)
    reasons = {r["reason"] for r in empty["decisions"]}
    assert reasons == {"NO_PERIOD_MODEL", "UNRESOLVED_PLAYER", "NO_FORECAST"} and not any(r["decision"] == "TRADE" for r in empty["decisions"])
    assert all(r["side"] == "BOTH" for r in empty["decisions"])


# ------------------------------------------------------------------------------------------------------------------ stages: idempotence, integrity
def test_stage_paper_is_idempotent_and_archive_guard_clean(tmp_path):
    root = tmp_path / "arch"
    seed_archive(root)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-q", "-m", "seed"], check=True)
    now = utc("2026-10-20T18:30:00Z")
    st = RUN.stage_paper(str(root), str(FIXARCH), now)
    assert st["status"] == "ok" and st["board_observed_utc"] == "2026-10-20T18:24:36Z" and st["games"] == 1
    assert st["snapshots"]["written"] > 300 and st["decisions"]["written"] > 1000 and st["counts"]["PF_EDGE_V1:TRADE"] > 0
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-q", "-m", "run1"], check=True)
    again = RUN.stage_paper(str(root), str(FIXARCH), now)
    assert again["snapshots"]["written"] == 0 and again["decisions"]["written"] == 0 and again["decisions"]["duplicates"] == st["decisions"]["written"]
    assert subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).strip() == ""        # nothing new on disk
    assert ops_guard.violations(str(root)) == []
    # rewriting an archived decision file is a violation
    f = next((root / "paper" / "nba" / "decisions").rglob("*.jsonl.gz"))
    f.write_bytes(gzip.compress(b"{}\n"))
    assert ops_guard.violations(str(root))


def test_stage_paper_reports_missing_board_and_no_games(tmp_path):
    root = tmp_path / "arch"
    seed_archive(root)
    assert RUN.stage_paper(str(root), str(tmp_path / "no_market_archive"), utc("2026-10-20T18:30:00Z"))["status"] == "NO_BOARD"
    assert RUN.stage_paper(str(root), str(FIXARCH), utc("2026-10-20T20:00:00Z"))["status"] == "NO_GAMES_WITH_FORECASTS"      # game already started
    empty = tmp_path / "empty"
    empty.mkdir()
    assert RUN.stage_paper(str(empty), str(FIXARCH), utc("2026-10-20T18:30:00Z"))["status"] == "NO_GAMES_WITH_FORECASTS"


def test_replay_archives_each_due_horizon_with_gaps_and_causes_and_is_idempotent(tmp_path):
    root = tmp_path / "arch"
    seed_archive(root)
    now = utc("2026-10-20T19:10:00Z")
    st = RUN.stage_paper_replay(str(root), str(FIXARCH), now)
    assert st["status"] == "ok" and st["games_due"] == 1
    assert {"T-90", "T-60", "T-30", "T-10", "LAST_VALID", "OPEN"} <= set(st["horizons_archived"])
    snaps = store.read(str(root), "market_snapshots")
    by_h = {}
    for r in snaps:
        by_h.setdefault(r["horizon"], []).append(r)
    assert {r["board_observed_utc"] for r in by_h["T-60"]} == {"2026-10-20T17:54:36Z"} and {r["snapshot_gap_s"] for r in by_h["T-60"]} == {324.0}
    assert {r["board_observed_utc"] for r in by_h["LAST_VALID"]} == {"2026-10-20T18:24:36Z"}
    assert all(utc(r["board_observed_utc"]) <= utc(r["horizon_target_utc"]) for h, rs in by_h.items() for r in rs if h != "LAST_VALID")
    dec = store.read(str(root), "decisions")
    assert {d["decision_mode"] for d in dec} == {"asof_replay"} and {d["horizon"] for d in dec} >= {"T-90", "T-60", "T-30", "T-10"}
    for d in dec:
        assert utc(d["board_observed_utc"]) <= utc(d["as_of_utc"]) <= utc(d["game_start_utc"])
    tr = [d for d in dec if d["decision"] == "TRADE"]
    assert tr and all(utc(d["forecast_generated_utc"]) <= utc(d["as_of_utc"]) for d in tr)
    again = RUN.stage_paper_replay(str(root), str(FIXARCH), now)
    assert again["snapshots"]["written"] == 0 and again["decisions"]["written"] == 0
    # a game no board can serve: MISSING rows with causes
    root2 = tmp_path / "arch2"
    g_old = dict(GAME, game_id="espn:1", start_utc="2026-10-20T15:00:00Z")
    seed_archive(root2, games=(g_old,), gen="2026-10-20T12:00:00Z", archived="2026-10-20T12:01:00Z")
    st2 = RUN.stage_paper_replay(str(root2), str(FIXARCH), utc("2026-10-20T15:10:00Z"))
    miss = [r for r in store.read(str(root2), "market_snapshots") if r["quote_class"] == "MISSING"]
    assert {r["missing_cause"] for r in miss} == {"GAP_TOO_LARGE"} and {r["horizon"] for r in miss} == {"T-60", "T-30", "T-10"}
    assert st2["missing"]["GAP_TOO_LARGE"] == 3 and not any(r["decision"] == "TRADE" for r in store.read(str(root2), "decisions") if r["horizon"] in ("T-30", "T-10"))


# ------------------------------------------------------------------------------------------------------------------ settlement
def test_fee_rounding_and_payoffs():
    assert ST.fee_paid(0.50, 1, 0.07) == 0.02                      # ceil(1.75c)
    assert ST.fee_paid(0.20, 1, 0.07) == 0.02                      # ceil(1.12c)
    assert ST.fee_paid(0.50, 10, 0.07) == 0.18                     # ceil(17.5c) over the whole order, not 10 x 2c
    assert ST.fee_paid(0.99, 1, 0.07) == 0.01
    assert ST.payoff_for_side("YES", 0.3) == 0.3 and abs(ST.payoff_for_side("NO", 0.3) - 0.7) < 1e-12


def _decision(side="YES", eff=0.41, price=0.40, k=20, family="player_points", entity="espn:9000", tip="2026-10-20T19:00:00Z"):
    return {"decision_id": S.sha(["d", side, eff, k, entity]), "strategy_id": "PF_EDGE_V1", "game_id": GAME["game_id"], "game_start_utc": tip,
            "ticker": f"KXNBAPTS-26OCT20BOSDET-X-{k}", "side": side, "family": family, "horizon": "T-60", "thesis_id": "t", "unit_id": "u", "cluster_id": "c",
            "decision": "TRADE", "price": price, "effective_entry": eff, "simulated_contracts": 1, "fee_assumption": {"multiplier": 0.07},
            "entity_id": entity, "k": k, "replay": False, "compact": False}


CLOSING_OK = {"ticker": "t", "valid": True, "cause": None, "board_observed_utc": "2026-10-20T18:50:00Z", "yes_bid": 0.4, "yes_ask": 0.5, "mid_yes": 0.45, "age_s": 600}


def test_settlement_yes_no_scalar_dnp_void_and_fee():
    now = utc("2026-10-21T06:00:00Z")
    row, why = ST.build_settlement(_decision("YES"), auth={"result": "yes", "value": 1.0}, outcome=None, closing=CLOSING_OK, now=now)
    assert row["won"] is True and row["gross_payoff"] == 1.0 and row["fee_paid"] == 0.02 and abs(row["net_pnl"] - (1 - 0.41 - 0.02)) < 1e-9
    assert abs(row["clv_cents"] - (0.45 - 0.40) * 100) < 1e-9 and row["outcome_source"] == "kalshi_result"
    row, _ = ST.build_settlement(_decision("NO", eff=0.62, price=0.61), auth={"result": "yes", "value": 1.0}, outcome=None, closing=CLOSING_OK, now=now)
    assert row["won"] is False and row["gross_payoff"] == 0.0 and row["net_pnl"] < -0.62 and abs(row["clv_cents"] - ((1 - 0.45) - 0.61) * 100) < 1e-9
    # scalar (DNP): neither NO nor a fee-free void; pays the pre-game fair value, fee not refunded
    row, _ = ST.build_settlement(_decision("YES"), auth={"result": "scalar", "value": 0.93}, outcome={"actual": 0.0, "participated": False}, closing=CLOSING_OK, now=now)
    assert row["dnp"] and row["won"] is None and row["gross_payoff"] == 0.93 and row["dnp_value_source"] == "authoritative"
    assert abs(row["net_pnl"] - (0.93 - 0.41 - 0.02)) < 1e-9 and row["net_pnl_if_conditional_void"] is None
    row, _ = ST.build_settlement(_decision("NO", eff=0.62), auth={"result": "scalar", "value": 0.93}, outcome={"actual": 0.0, "participated": False}, closing=CLOSING_OK, now=now)
    assert abs(row["gross_payoff"] - 0.07) < 1e-9
    # void: refunded at the entry price, fee kept
    row, _ = ST.build_settlement(_decision("YES"), auth={"result": "void", "value": None}, outcome=None, closing=CLOSING_OK, now=now)
    assert abs(row["net_pnl"] + 0.02) < 1e-9
    # box-derived, played: threshold semantics X >= k
    d = _decision("YES", k=20)
    row, _ = ST.build_settlement(d, auth=None, outcome={"actual": 20.0, "participated": True}, closing=CLOSING_OK, now=now)
    assert row["won"] is True and row["outcome_source"] == "box_score_derived"
    row, _ = ST.build_settlement(d, auth=None, outcome={"actual": 19.0, "participated": True}, closing=CLOSING_OK, now=now)
    assert row["won"] is False
    # box-derived DNP: modeled at the LAST_VALID mid, flagged; without a valid closing quote it stays pending
    row, _ = ST.build_settlement(d, auth=None, outcome={"actual": 0.0, "participated": False}, closing=CLOSING_OK, now=now)
    assert row["dnp"] and row["dnp_value_source"] == "modeled_last_valid_mid" and abs(row["gross_payoff"] - 0.45) < 1e-9
    none, why = ST.build_settlement(d, auth=None, outcome={"actual": 0.0, "participated": False}, closing=ST.closing_for(None, utc("2026-10-20T19:00:00Z")), now=now)
    assert none is None and why == "DNP_NO_VALID_LAST_VALID_MID"
    none, why = ST.build_settlement(_decision(family="game_total"), auth=None, outcome=None, closing=CLOSING_OK, now=now)
    assert none is None and why == "NO_AUTHORITATIVE_RESULT"                # game markets are never box-derived
    none, why = ST.build_settlement(d, auth={"result": "weird", "value": None}, outcome=None, closing=CLOSING_OK, now=now)
    assert none is None and why.startswith("UNKNOWN_RESULT")


def test_closing_line_validity_stale_and_one_sided():
    tip = utc("2026-10-20T19:00:00Z")
    ok = ST.closing_for({"ticker": "t", "board_observed_utc": "2026-10-20T18:50:00Z", "quote_class": "TWO_SIDED", "yes_bid": 0.4, "yes_ask": 0.5}, tip)
    assert ok["valid"] and abs(ok["mid_yes"] - 0.45) < 1e-12
    stale = ST.closing_for({"ticker": "t", "board_observed_utc": "2026-10-20T18:24:36Z", "quote_class": "TWO_SIDED", "yes_bid": 0.4, "yes_ask": 0.5}, tip)
    assert not stale["valid"] and stale["cause"] == "STALE_LAST_VALID"                      # a stale snapshot is never called a closing line
    one = ST.closing_for({"ticker": "t", "board_observed_utc": "2026-10-20T18:55:00Z", "quote_class": "ONE_SIDED", "yes_bid": None, "yes_ask": 0.5}, tip)
    assert not one["valid"] and one["mid_yes"] is None


def _board_with_results(rows_by_ticker, results):
    out = []
    for tk, r in rows_by_ticker.items():
        r = dict(r)
        if tk in results:
            r["result"], r["settlement_value_dollars"], r["status"] = results[tk][0], f"{results[tk][1]:.4f}", "finalized"
        out.append(r)
    return out


def test_end_to_end_settlement_correction_and_idempotence(tmp_path, cfg):
    root = tmp_path / "arch"
    seed_archive(root)
    now = utc("2026-10-20T19:10:00Z")
    RUN.stage_paper_replay(str(root), str(FIXARCH), now)                      # decisions + LAST_VALID snapshots from the real board
    dec = [d for d in store.read(str(root), "decisions") if not d.get("compact") and d["side"] in S.SIDES and d["horizon"] == "T-60"]
    props = [d for d in dec if d["family"] == "player_points" and d["strategy_id"] == "PF_ALL_CANDIDATES_V1" and d["price"] is not None]
    gmk = [d for d in dec if d["family"] == "game_total" and d["strategy_id"] == "PF_ALL_CANDIDATES_V1" and d["price"] is not None]
    assert props and gmk
    p_yes = next(d for d in props if d["side"] == "YES")
    g_yes = gmk[0]
    # market archive for settlement: the real fixture chain + a post-game checkpoint carrying results (the capture worker's later boards)
    mk = tmp_path / "mk"
    shutil.copytree(FIXARCH, mk)
    dt, board = MK.ChainReader(str(FIXARCH), "markets").board_at(utc("2026-10-20T18:30:00Z"))
    post = utc("2026-10-21T04:00:00Z")
    results = {g_yes["ticker"]: ("yes", 1.0)}
    write_chain(mk, [(post, _board_with_results(board, results))], run_id="post")        # a new checkpoint (day 2026-10-21)
    st = ST.settle_paper(str(root), str(mk), utc("2026-10-21T06:00:00Z"))
    assert st["decisions_considered"] > 100 and st["settled_written"] >= 1
    sett = {r["decision_id"]: r for r in store.read(str(root), "settlements")}
    gs = sett[g_yes["decision_id"]]
    assert gs["outcome_source"] == "kalshi_result" and gs["kalshi_result"] == "yes" and gs["won"] == (g_yes["side"] == "YES")
    assert p_yes["decision_id"] not in sett and st["pending"]["NO_OUTCOME"] > 0               # props without outcome/result stay pending
    # a player prop settles from the archived box score: played (>= k) ...
    ent = p_yes["entity_id"]
    rows = [{"game_id": GAME["game_id"], "entity_id": ent, "family": "points", "actual": float(p_yes["k"]), "participated": True, "final": True,
             "game_date": "2026-10-20", "source": "t"}]
    pr.archive_outcomes(rows, str(root), "NBA", "2026-10-21T05:00:00Z")
    st2 = ST.settle_paper(str(root), str(mk), utc("2026-10-21T06:00:00Z"))
    sett = {r["decision_id"]: r for r in store.read(str(root), "settlements")}
    s = sett[p_yes["decision_id"]]
    assert s["outcome_source"] == "box_score_derived" and s["won"] is True and s["actual"] == float(p_yes["k"]) and not s["dnp"]
    assert abs(s["net_pnl"] - (1.0 - p_yes["effective_entry"] - ST.fee_paid(p_yes["effective_entry"], 1, p_yes["fee_assumption"]["multiplier"]))) < 1e-9
    assert st2["settled_written"] >= 1
    n_before = len(sett)
    st3 = ST.settle_paper(str(root), str(mk), utc("2026-10-21T06:00:00Z"))               # idempotent
    assert st3["settled_written"] == 0 and st3["corrections_written"] == 0 and len(store.read(str(root), "settlements")) == n_before
    # a DNP with only a STALE LAST_VALID quote (36 min before tip: not a closing line) stays pending: no fair-price estimate is invented
    lv = {r["ticker"]: r for r in store.read(str(root), "market_snapshots") if r["horizon"] == "LAST_VALID" and r["quote_class"] == "TWO_SIDED"}
    other = next(d for d in props if d["entity_id"] != ent and d["side"] == "YES" and d["ticker"] in lv)
    pr.archive_outcomes([{"game_id": GAME["game_id"], "entity_id": other["entity_id"], "family": "points", "actual": 0.0, "participated": False,
                          "final": True, "game_date": "2026-10-20", "source": "t"}], str(root), "NBA", "2026-10-21T05:00:00Z")
    st4 = ST.settle_paper(str(root), str(mk), utc("2026-10-21T06:00:00Z"))
    assert st4["pending"].get("DNP_NO_VALID_LAST_VALID_MID", 0) > 0
    assert other["decision_id"] not in {r["decision_id"] for r in store.read(str(root), "settlements")}
    # a played prop settled from the box (value 0 < k: NO wins), later contradicted by the authoritative result -> an append-only correction
    third = next(d for d in props if d["entity_id"] not in (ent, other["entity_id"]) and d["side"] == "YES")
    pr.archive_outcomes([{"game_id": GAME["game_id"], "entity_id": third["entity_id"], "family": "points", "actual": 0.0, "participated": True,
                          "final": True, "game_date": "2026-10-20", "source": "t"}], str(root), "NBA", "2026-10-21T05:00:00Z")
    ST.settle_paper(str(root), str(mk), utc("2026-10-21T06:00:00Z"))
    so = {r["decision_id"]: r for r in store.read(str(root), "settlements")}[third["decision_id"]]
    assert so["outcome_source"] == "box_score_derived" and so["won"] is False
    mk2 = tmp_path / "mk2"
    shutil.copytree(mk, mk2)
    write_chain(mk2, [(utc("2026-10-21T05:00:00Z"), _board_with_results(board, {third["ticker"]: ("yes", 1.0)}))], run_id="post2")
    st5 = ST.settle_paper(str(root), str(mk2), utc("2026-10-21T07:00:00Z"))
    assert st5["corrections_written"] >= 1
    corr = store.read(str(root), "corrections")
    c = next(x for x in corr if x["decision_id"] == third["decision_id"])
    assert c["previous"]["outcome_source"] == "box_score_derived" and c["new"]["outcome_source"] == "kalshi_result" and c["new"]["won"] is True
    after = {r["decision_id"]: r for r in store.read(str(root), "settlements")}
    assert after[third["decision_id"]] == so                                       # the original settlement is never rewritten
    assert ST.settle_paper(str(root), str(mk2), utc("2026-10-21T07:00:00Z"))["corrections_written"] == 0


# ------------------------------------------------------------------------------------------------------------------ game forecast archive
def test_game_forecast_records_only_unstarted_games_and_are_idempotent(tmp_path):
    g1 = synth_game_forecast(GAME)
    g2 = synth_game_forecast(dict(GAME2, start_utc="2026-10-20T14:00:00Z", game_id="espn:started"))
    res = {"generated_utc": "2026-10-20T15:00:00Z", "game_forecasts": [{k: v for k, v in g.items() if k not in ("game_forecast_id", "archived_utc", "schema")} for g in (g1, g2)]}
    recs = RUN.challenger_game_records(res)
    assert [r["game_id"] for r in recs] == [GAME["game_id"]] and recs[0]["schema"] == S.GAME_FORECAST_SCHEMA and recs[0]["game_forecast_id"]
    root = tmp_path / "a"
    now = utc("2026-10-20T15:01:00Z")
    assert RUN.stage_game_forecasts(res, str(root), now) == {"games": 1, "written": 1, "duplicates": 0}
    assert RUN.stage_game_forecasts(res, str(root), now) == {"games": 1, "written": 0, "duplicates": 1}
    got = store.read(str(root), "game_forecasts")
    assert len(got) == 1 and got[0]["archived_utc"] == "2026-10-20T15:01:00Z" and abs(sum(got[0]["teams"][0]["probs"]) - 1) < 1e-6


def test_project_game_forecast_helper_uses_the_team_pmf_and_only_existing_context():
    import pandas as pd
    from nba import project as P
    tdist = dists.discretized_normal(np.array([110.0, 105.0]), np.array([11.0, 11.0]), 60, 120, None)
    g = pd.DataFrame({"game_id": ["1", "1"], "team": ["DET", "BOS"], "home": [True, False], "mean": [110.0, 105.0], "_tpos": [0, 1],
                      "rest_days": [2.0, 1.0], "b2b": [0.0, 1.0], "exp_pace": [99.5, 99.5]})
    gg = {"game_id": "espn:1", "start_utc": "2026-10-20T19:00:00Z", "home": "DET", "away": "BOS"}
    out = P._game_forecast(gg, g, tdist, "2026-10-20T15:00:00Z", "2026-10-20T14:00:00Z")
    assert [t["team"] for t in out["teams"]] == ["DET", "BOS"] and abs(sum(out["teams"][1]["probs"]) - 1) < 1e-6
    assert out["context"] == {"home_rest_days": 2.0, "home_b2b": 0.0, "home_exp_pace": 99.5, "away_rest_days": 1.0, "away_b2b": 1.0, "away_exp_pace": 99.5}
    assert out["rho"] == CFG.load()["game_model"]["rho"] and "ortg_off" not in json.dumps(out["context"])


def test_config_is_hashed_versioned_and_declares_hypotheses(cfg):
    assert len(CFG.config_sha()) == 64 and cfg["version"] and cfg["authority"] == "research_only"
    assert set(cfg["strategies"]) == set(S.STRATEGIES) and S.CONTROL_STRATEGY not in cfg["strategies"]
    assert cfg["hypotheses"] and all(h["declared_utc"] <= cfg["prospective_start_utc"] and h["min_independent_units"] >= 100 for h in cfg["hypotheses"])
    assert cfg["game_model"]["rho_source"] and cfg["control"]["min_decisions"] == 200 and cfg["control"]["min_games"] == 40
    cfg["execution"]["slippage"] = 0.5
    assert CFG.load()["execution"]["slippage"] == 0.01                                 # callers cannot mutate the protocol


def test_new_forecast_on_an_unchanged_board_is_a_new_decision_not_a_duplicate(tmp_path):
    root = tmp_path / "arch"
    seed_archive(root)
    now = utc("2026-10-20T18:30:00Z")
    first = RUN.stage_paper(str(root), str(FIXARCH), now)
    dt, board = MK.ChainReader(str(FIXARCH), "markets").board_at(now)
    rows, _ = snaps_for(board, dt)
    recs = synth_forecasts(rows, GAME, gen="2026-10-20T17:00:00Z", scale=1.3, seed=11)
    assert pr.archive_forecasts(recs, str(root), "2026-10-20T17:01:00Z")["written"] == len(recs)
    second = RUN.stage_paper(str(root), str(FIXARCH), now)
    assert second["snapshots"]["written"] == 0 and second["decisions"]["written"] > 0                  # same board, newer forecast
    assert RUN.stage_paper(str(root), str(FIXARCH), now)["decisions"]["written"] == 0                  # and now idempotent again
    assert first["decisions"]["written"] > 0


def test_game_markets_settle_from_team_outcomes_and_authoritative_result_supersedes(tmp_path):
    base = _decision(side="YES", eff=0.41, price=0.40)
    for fam, thr, team_row, yes in (("game_winner", None, {"pts": 110, "opp_pts": 104}, True),
                                    ("game_spread", 5.5, {"pts": 110, "opp_pts": 104}, True),
                                    ("game_spread", 6.5, {"pts": 110, "opp_pts": 104}, False),
                                    ("game_total", 215.5, {"pts": 110, "opp_pts": 104}, False),
                                    ("game_total", 213.5, {"pts": 110, "opp_pts": 104}, True),
                                    ("team_total", 109.5, {"pts": 110, "opp_pts": 104}, True)):
        d = dict(base, family=fam, threshold=thr, k=None, entity_id=None)
        assert ST.game_yes(d, team_row) is yes
        row, why = ST.build_settlement(d, auth=None, outcome=None, closing=CLOSING_OK, now=utc("2026-10-21T11:00:00Z"), team=team_row)
        assert why is None and row["outcome_source"] == "box_score_derived" and row["won"] is yes
        assert row["net_pnl"] == pytest.approx((1.0 if yes else 0.0) - 0.41 - row["fee_paid"])
    # without team facts the market waits for the authoritative result
    d = dict(base, family="game_total", threshold=213.5, k=None)
    assert ST.build_settlement(d, auth=None, outcome=None, closing=CLOSING_OK, now=utc("2026-10-21T11:00:00Z"))[1] == "NO_AUTHORITATIVE_RESULT"
    assert ST.game_yes(d, {"pts": None, "opp_pts": 1}) is None


# ------------------------------------------------------------------------------------------------------------------ review regressions
def test_nan_numbers_are_missing_data_never_prices_or_sizes():
    assert MK._f(float("nan")) is None and MK._f("nan") is None and MK._f(float("inf")) is None and MK._f("0.41") == 0.41
    q = EN.quality_failures({"quote_class": "TWO_SIDED", "status": "active", "board_observed_utc": "2026-10-20T18:00:00Z", "yes_bid": 0.4, "yes_ask": 0.45,
                             "snapshot_gap_s": 0}, "YES", utc("2026-10-20T18:05:00Z"), CFG.load(), 0.45, float("nan"), "PASS")
    assert "NO_SIZE" in q


def test_replay_gap_makes_a_trade_stale_even_though_as_of_is_the_board_time():
    cfg = CFG.load()
    snap = {"quote_class": "TWO_SIDED", "status": "active", "board_observed_utc": "2026-10-20T17:55:00Z", "yes_bid": 0.4, "yes_ask": 0.45,
            "snapshot_gap_s": 2400.0}
    assert "STALE_QUOTE" in EN.quality_failures(snap, "YES", utc("2026-10-20T17:55:00Z"), cfg, 0.45, 5.0, "PASS")


def test_game_total_settles_from_any_team_outcome_row_of_the_game(tmp_path):
    root = tmp_path / "a"
    seed_archive(root)
    now = utc("2026-10-20T19:10:00Z")
    RUN.stage_paper_replay(str(root), str(FIXARCH), now)
    store.write_new(str(root), "team_outcomes", "2026-10-20", [
        {"schema": "sift.team_outcome.v1", "game_id": GAME["game_id"], "team": t, "pts": p, "opp_pts": q, "final": True, "observed_utc": "2026-10-21T04:00:00Z",
         "outcome_key": t} for t, p, q in (("DET", 112, 106), ("BOS", 106, 112))], "outcome_key", utc("2026-10-21T04:00:00Z"))
    ST.settle_paper(str(root), None, utc("2026-10-21T06:00:00Z"))
    tot = [r for r in store.read(str(root), "settlements") if r["family"] == "game_total"]
    assert tot and all(r["outcome_source"] == "box_score_derived" and r["actual"] == 218.0 for r in tot)


def test_evaluation_applies_the_latest_correction_over_the_original_settlement(tmp_path):
    from nba.paper import evaluate as EV
    root = tmp_path / "a"
    root.mkdir()
    base = {"strategy_id": "PF_EDGE_V1", "game_id": "g", "game_start_utc": "2026-10-20T19:00:00Z", "side": "YES", "ticker": "t", "stat": "points",
            "family": "player_points", "horizon": "T-60", "decision": "TRADE", "price": 0.4, "as_of_utc": "2026-10-20T18:00:00Z", "decision_id": "d1",
            "thesis_id": "x", "ev_net": 0.05, "p_model": 0.6, "bid": 0.39, "ask": 0.4, "replay": False}
    store.write_once(str(root), "decisions", "2026-10-20", [base], utc("2026-10-20T18:00:00Z"))
    first = {"decision_id": "d1", "strategy_id": "PF_EDGE_V1", "won": False, "dnp": False, "net_pnl": -0.41}
    store.write_once(str(root), "settlements", "2026-10-20", [first], utc("2026-10-21T06:00:00Z"))
    store.write_once(str(root), "corrections", "2026-10-20", [{"correction_id": "c", "decision_id": "d1", "corrected_utc": "2026-10-21T08:00:00Z",
                                                                  "new": {**first, "won": True, "net_pnl": 0.55}}], utc("2026-10-21T08:00:00Z"))
    q: dict = {}
    d = EV._load_decisions(str(root), None, lambda s: s.notna(), False, q)
    assert float(d["net_pnl"].iloc[0]) == 0.55 and q["paper_corrections_applied"] == 1
