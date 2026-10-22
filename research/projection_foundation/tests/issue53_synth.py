"""Deterministic SYNTHETIC mini-world for the Issue #53 tests (importable: `from issue53_synth import build_world`).

Every decision row is produced by the REAL paper engine (`engine.candidates_for` + `apply_strategies`) from synthetic market snapshots and synthetic
forecasts (pf_core pmf families), so side-specific asks / sizes / spreads / fees and the strict strategy are the production code paths. Settlements
are produced by the real `settle.build_settlement`. Nothing here is real data; teams are real tricodes, ids are `espn:7xxx`. Planted truths are
explicit so tests can assert them.

World (all in one archive root):
  G1  tip 2026-10-20T19:00Z   RETROSPECTIVE   horizons T-90 / T-60 / T-30 (+ LAST_VALID closing snapshot)
  G2  tip 2026-10-23T00:00Z   PROSPECTIVE     horizons T-90 / T-60 / T-30
  G3  tip 2026-10-23T02:00Z   PROSPECTIVE     T-60 snapshot MISSING (GAP_TOO_LARGE) -> a NO_TRADE game
  per game: 4 players x ladder rungs 10 / 20 points; the model prices the NO side cheap (planted edge on NO)
  minutes-shadow-archive: one eligible v2-uniform snapshot per game (feed = the forecast feed) + one ineligible jrm_v2 file
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

PF = Path(__file__).resolve().parent.parent
if str(PF) not in sys.path:
    sys.path.insert(0, str(PF))

from nba.paper import config as CFG, engine as EN, markets as MK, probability as PR, schema as S, settle as SE, store  # noqa: E402
from pf_core import dists, prospective as pr  # noqa: E402

UTC = timezone.utc
V2_FREEZE = "f000f3c18b670ab94e3b71e403dda03bc0e5188a"
GAMES = [
    {"game_id": "espn:7001", "start_utc": "2026-10-20T19:00:00Z", "home": "DET", "away": "BOS", "game_date_et": "2026-10-20"},
    {"game_id": "espn:7002", "start_utc": "2026-10-23T00:00:00Z", "home": "NYK", "away": "PHI", "game_date_et": "2026-10-22"},
    {"game_id": "espn:7003", "start_utc": "2026-10-23T02:00:00Z", "home": "OKC", "away": "SAS", "game_date_et": "2026-10-22"},
]
HORIZONS = {"T-90": 90, "T-60": 60, "T-30": 30}


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(d: datetime) -> str:
    return d.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def players_of(game: dict) -> list[tuple[str, str, str, float]]:
    out = []
    for ti, team in enumerate((game["home"], game["away"])):
        for j in range(2):
            n = int(game["game_id"][-4:]) * 10 + ti * 2 + j
            out.append((f"espn:{n}", f"P{n}", team, 30.0 - 6 * j))        # entity, name, team, frozen conditional minutes
    return out


def forecasts_for(game: dict, gen: datetime, p_play: float = 0.95, mean_pts: float = 14.0) -> list[dict]:
    recs = []
    for eid, name, team, minutes in players_of(game):
        base = dict(sport="NBA", model_role="challenger", model_version="pf-synth", game_id=game["game_id"], game_start_utc=game["start_utc"], entity_id=eid,
                    entity_name=name, team=team, generated_utc=iso(gen), data_asof_utc=iso(gen), gate_status="PASS", readiness="SHADOW VALIDATION",
                    participation={"status": "LIKELY_ACTIVE"})
        recs.append({**base, "family": "participation", "model_id": "pf-nba-participation", "mean": p_play, "lo": 0, "probs": [1 - p_play, p_play]})
        d = dists.negbin(np.array([mean_pts]), 0.12, 90)
        recs.append({**base, "family": "points", "model_id": "pf-nba-points", "mean": float(d.mean[0]), "lo": int(d.lo), "probs": [float(x) for x in d.P[0]]})
        recs.append({**base, "family": "minutes", "model_id": "pf-nba-minutes", "mean": minutes, "lo": 0, "probs": [1.0 / 61] * 61})
    return recs


def snapshot(game: dict, horizon: str, board: datetime, target: datetime, ticker: str, name: str, team: str, opp: str, k: int, yb: float, ya: float,
             ybs: float, yas: float, tip: datetime) -> dict:
    return {"schema": S.SNAPSHOT_SCHEMA, "snapshot_id": S.snapshot_id(iso(board), ticker, horizon), "board_observed_utc": iso(board), "horizon": horizon,
            "horizon_target_utc": iso(target), "snapshot_gap_s": (target - board).total_seconds(), "game_id": game["game_id"], "game_start_utc": game["start_utc"],
            "ticker": ticker, "event_ticker": ticker.rsplit("-", 2)[0], "series": "KXNBAPTS", "family": "player_points", "scope": "player", "stat": "points",
            "period": "FULL", "player_id": None, "player_name": name, "team": team, "opponent": opp, "threshold": k - 0.5, "k": k, "comparator": "ge",
            "status": "active", "yes_bid": yb, "yes_ask": ya, "no_bid": round(1 - ya, 4), "no_ask": round(1 - yb, 4), "yes_bid_size": ybs, "yes_ask_size": yas,
            "depth_yes_ask": None, "depth_no_ask": None, "depth_source": "top_of_book_only", "volume": 100.0, "open_interest": 100.0, "last_price": ya,
            "quote_class": "TWO_SIDED", "missing_cause": None, "replay": False, "source_run_id": None, "support": "MODELED", "side_team": None,
            "authority": "research_only", "fee_multiplier_row": None}


def quotes(game: dict, k: int, j: int) -> tuple[float, float, float, float]:
    """(yes_bid, yes_ask, yes_bid_size, yes_ask_size). Model P(X>=10) ~ .78, P(X>=20) ~ .15 for mean 14: the k=10 rung is priced at the model, the NO side
    of the 20 rung is cheap vs the model (planted edge). Player j=1 has a thin NO book (bid size 0.5 < 1 contract) to plant INSUFFICIENT_DEPTH on the NO side only."""
    if k == 20:
        return (0.46, 0.48, 0.5 if j == 1 else 40.0, 80.0)         # NO ask = 0.54 (model P(NO) ~ .85)
    return (0.76, 0.78, 60.0, 60.0)                                 # k=10: priced at the model: no edge on either side


def build_world(root: Path, msa: Path | None = None, *, ratio: float = 1.0, p_play_jrm: float | None = None, replay_lag_min: int = 20) -> dict:
    """Write the archive. Returns facts: games, decisions (all rows), cfg."""
    root = Path(root)
    cfg = CFG.load()
    facts: dict = {"games": GAMES, "decisions": [], "settlements": [], "forecast_gen": {}, "tickers": {}}
    all_dec, all_set, all_snap = [], [], []
    for game in GAMES:
        tip = utc(game["start_utc"])
        gen = tip - timedelta(hours=4)
        arch = gen + timedelta(minutes=1)
        recs = forecasts_for(game, gen)
        pr.archive_forecasts(recs, str(root), iso(arch))
        gf = {"schema": S.GAME_FORECAST_SCHEMA, "game_id": game["game_id"], "game_start_utc": game["start_utc"], "home": game["home"], "away": game["away"],
              "generated_utc": iso(gen), "data_asof_utc": iso(gen), "model_id": "pf-nba-team_points", "model_version": "pf-synth", "rho": 0.2,
              "teams": [{"team": t, "mean": 110.0, "lo": 60, "probs": [float(x) for x in dists.discretized_normal(np.array([110.0]), np.array([11.5]), 60, 130, None).P[0]]}
                        for t in (game["home"], game["away"])],
              "game_forecast_id": S.sha(["gf", game["game_id"]]), "archived_utc": iso(arch)}
        store.write_new(str(root), "game_forecasts", tip.strftime("%Y-%m-%d"), [gf], "game_forecast_id", arch)
        frec = pr._read(str(root), "forecasts", "NBA")
        facts["forecast_gen"][game["game_id"]] = iso(gen)
        players = MK.PlayerIndex(frec)
        for h, mins in HORIZONS.items():
            target = tip - timedelta(minutes=mins)
            if game["game_id"] == "espn:7003" and h == "T-60":
                all_snap.append(MK.missing_row(MK.Game.from_dict(game), h, target, "GAP_TOO_LARGE", 2400.0))
                continue
            board = target - timedelta(minutes=2)
            snaps = []
            for eid, name, team, minutes in players_of(game):
                j = int(eid[-1]) % 2
                opp = game["away"] if team == game["home"] else game["home"]
                for k in (10, 20):
                    yb, ya, ybs, yas = quotes(game, k, j)
                    tk = f"KXNBAPTS-{game['game_id'][-4:]}-{eid[-3:]}-{k}"
                    snaps.append(snapshot(game, h, board, target, tk, name, team, opp, k, yb, ya, ybs, yas, tip))
            fc, gfc = PR.Forecasts(frec, board), PR.GameForecasts(store.read(str(root), "game_forecasts"), board)
            decided = board + timedelta(minutes=replay_lag_min)
            cands = EN.candidates_for(snaps, fc, gfc, players, as_of=board, decided=decided, mode="asof_replay", cfg=cfg)
            strat = EN.apply_strategies(cands, cfg)
            all_dec += cands + strat
            all_snap += snaps
            if h == "T-30":                                   # LAST_VALID closing snapshot (valid: two-sided, <= 15 min before tip)
                lv = tip - timedelta(minutes=5)
                for s in snaps:
                    all_snap.append({**s, "horizon": "LAST_VALID", "board_observed_utc": iso(lv), "snapshot_id": S.snapshot_id(iso(lv), s["ticker"], "LAST_VALID"),
                                     "horizon_target_utc": iso(tip), "snapshot_gap_s": 300.0})
    by_day: dict[str, list] = {}
    for r in all_dec:
        by_day.setdefault(MK.parse_ts(r["game_start_utc"]).strftime("%Y-%m-%d"), []).append(r)
    for day, rows in by_day.items():
        store.write_once(str(root), "decisions", day, rows, utc(day + "T00:00:00Z") + timedelta(hours=1))
    sn_day: dict[str, list] = {}
    for r in all_snap:
        sn_day.setdefault(MK.parse_ts(r["game_start_utc"]).strftime("%Y-%m-%d"), []).append(r)
    for day, rows in sn_day.items():
        store.write_once(str(root), "market_snapshots", day, rows, utc(day + "T00:00:00Z") + timedelta(hours=1))
    # ---- settlements: every row of a started game; outcome: the player with index digit 0 scores 8, the others 22 (NO k=20 wins for digit 0 only)
    lastv = {(s["game_id"], s["ticker"]): s for s in all_snap if s.get("horizon") == "LAST_VALID"}
    for r in all_dec:
        if r["side"] not in S.SIDES or r.get("compact"):
            continue
        if r["game_id"] == "espn:7003" or r.get("price") is None:
            continue
        tip = utc(r["game_start_utc"])
        eid = r["entity_id"]
        actual = 8.0 if int(eid[-1]) == 0 else 22.0
        yes = actual >= r["k"]
        d = r
        if d.get("effective_entry") is None:
            continue
        lv = lastv.get((r["game_id"], r["ticker"]))
        closing = SE.closing_for(lv, tip)
        row, _ = SE.build_settlement(d, auth={"result": "yes" if yes else "no", "value": 1.0 if yes else 0.0}, outcome={"actual": actual, "participated": True},
                                     closing=closing, now=tip + timedelta(hours=4))
        if row:
            all_set.append(row)
    set_day: dict[str, list] = {}
    for r in all_set:
        set_day.setdefault(MK.parse_ts(r["game_start_utc"]).strftime("%Y-%m-%d"), []).append(r)
    for day, rows in set_day.items():
        store.write_once(str(root), "settlements", day, rows, utc(day + "T00:00:00Z") + timedelta(hours=12))
    facts["decisions"], facts["settlements"] = all_dec, all_set
    if msa is not None:
        build_msa(Path(msa), facts, ratio=ratio, p_play_jrm=p_play_jrm)
    return facts


# ---------------------------------------------------------------------------------------------------------------- minutes-shadow-archive
def jrm_doc(game_ids: list[str], feed: str, archived: str, ratio: float, p_play_jrm: float | None, *, version="v2", alloc="uniform (validated configuration)",
            frozen="f000f3c18b670ab94e3b71e403dda03bc0e5188a") -> dict:
    rows = []
    for gid in game_ids:
        game = next(g for g in GAMES if g["game_id"] == gid)
        for eid, name, team, minutes in players_of(game):
            rows.append({"availability": {"designation": "ACTIVE", "status": "LIKELY_ACTIVE"}, "eligible_prob": 0.99, "expected_minutes_unconditional_jrm": 0.95 * minutes * ratio,
                         "frozen_published": {"minutes_given_play_after_gate": minutes, "minutes_given_play_before_gate": minutes, "p_play": 0.95}, "game_id": gid,
                         "minutes_given_play_jrm": round(minutes * ratio, 2), "minutes_p10": minutes * ratio - 6, "minutes_p90": minutes * ratio + 6, "name": name,
                         "opponent": "X", "p_play_jrm": p_play_jrm if p_play_jrm is not None else 0.95, "player_id": eid, "pregame": True,
                         "start_utc": next(g for g in GAMES if g["game_id"] == gid)["start_utc"], "team": team})
    return {"allocation": alloc, "archived_utc": archived, "code_commit": "c" * 40, "design_frozen_at": frozen, "feed_data_asof_utc": feed, "feed_generated_utc": feed,
            "frozen_model_version": "pf-synth", "games": game_ids, "model": "pf-nba-jrm-0.1", "n_rows": len(rows), "rows": rows, "scenarios": 400, "schema": "jrm.shadow.v1",
            "version": version}


def build_msa(msa: Path, facts: dict, *, ratio: float, p_play_jrm: float | None) -> None:
    (msa / "eligibility").mkdir(parents=True, exist_ok=True)
    reg = []
    files = []
    for game in GAMES[:2]:                               # G3 has no JRM snapshot
        gid = game["game_id"]
        feed = facts["forecast_gen"][gid]
        tip = utc(game["start_utc"])
        archived = iso(utc(feed) + timedelta(minutes=10))
        files.append(("jrm_v2_uniform", f"{archived.replace('-', '').replace(':', '')}_jrm_v2.json.gz", jrm_doc([gid], feed, archived, ratio, p_play_jrm), True, archived, tip))
    # an ineligible variance-weighted file and a late (archived after T-60 of G1) eligible-looking file
    files.append(("jrm_v2", "20261020T120000Z_jrm_v2.json.gz", jrm_doc(["espn:7001"], facts["forecast_gen"]["espn:7001"], "2026-10-20T12:00:00Z", 1.3, None, alloc=None), False,
                  "2026-10-20T12:00:00Z", utc(GAMES[0]["start_utc"])))
    for sub, fn, doc, eligible, archived, tip in files:
        (msa / sub).mkdir(exist_ok=True)
        raw = json.dumps(doc, sort_keys=True).encode()
        data = gzip.compress(raw, mtime=0)
        (msa / sub / fn).write_bytes(data)
        reg.append({"archived_utc": archived, "audited_utc": archived, "branch_commit_utc": archived, "code_commit": "c" * 40, "eligible_for_prospective_scoring": eligible,
                    "file": f"{sub}/{fn}", "games_eligible": doc["games"] if eligible else [], "reasons": ["all rules satisfied"] if eligible else ["F1 allocation not recorded"],
                    "rows_eligible": doc["n_rows"] if eligible else 0, "rows_in_file": doc["n_rows"], "sha256": hashlib.sha256(data).hexdigest()})
    (msa / "eligibility" / "REGISTER.jsonl").write_text("\n".join(json.dumps(r, sort_keys=True) for r in reg) + "\n")
    (msa / "README.md").write_text("synthetic")


def tamper(msa: Path, rel: str) -> None:
    """Edit a registered file after the fact (changed bytes -> SHA_MISMATCH)."""
    p = msa / rel
    doc = json.loads(gzip.decompress(p.read_bytes()))
    doc["rows"][0]["minutes_given_play_jrm"] += 5
    p.write_bytes(gzip.compress(json.dumps(doc, sort_keys=True).encode(), mtime=0))


__all__ = ["build_world", "GAMES", "utc", "iso", "tamper", "jrm_doc", "build_msa", "snapshot", "players_of", "os"]
