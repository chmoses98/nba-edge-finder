"""Paper settlement: authoritative Kalshi result first, box-score-derived second; DNP scalar semantics; fees; closing line and CLV.

Authority order for one decision (docs/research/PAPER_ENGINE_SPEC.md sections 4-5):
  1. `kalshi_result`  a captured market row of the ticker with `result` in yes | no | scalar | void after the game. YES pays 1 on `yes`, 0 on
     `no`, `settlement_value_dollars` on `scalar` (NO pays 1 - that). Real examples (data/history/kalshi, 2025-26): KXNBAPTS 23,562 settled
     markets = 14,074 no, 8,483 yes, 1,005 scalar (player never entered; `rules_secondary`: "If a player is active but never takes the
     court, the market settles to the last fair market price before game start."); KXNBAGAME 6 scalar of 2,898; KXNBATOTAL 33 of 14,787.
     `void` has not been observed; if it appears the position is refunded at the entry price and the fee is NOT refunded (conservative).
  2. `box_score_derived`  player props only, from archived outcomes (`outcomes/nba`): played => YES iff actual >= k; did not play => the DNP
     leg is valued at the LAST_VALID mid of the ticker (`dnp_value_source: modeled_last_valid_mid`), pending when no valid closing quote
     was archived. Game markets (winner, spread, total, team total) are box-derived from the archived `team_outcomes` (final team points
     incl. overtime) when the Kalshi result is not in the archive yet; the authoritative result later supersedes via a correction row.
A settlement is written ONCE per decision_id. When a later authoritative result differs from a box-derived / modeled settlement, an
append-only `sift.paper_correction.v1` row is written; the original is never touched.

Fees at settlement use the whole-order, cent-rounded taker fee of nba_edge.kalshi.fees for the simulated order (1 contract), so P&L is
`payoff - effective_entry - fee_paid`; the slippage assumed at decision time is already inside `effective_entry`.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from pf_core import prospective as pr

from . import config as CFG
from . import markets as MK
from . import schema as S
from . import store

PROP_FAMILY = {"player_points": "points", "player_rebounds": "rebounds", "player_assists": "assists", "player_threes": "threes",
               "player_pra": "pra"}


GAME_FAMILY = {"game_winner", "game_spread", "game_total", "team_total"}


def game_yes(d: dict, team: dict | None) -> bool | None:
    """YES truth of a game-level contract from the subject team's final facts `team` = {pts, opp_pts} (None when not derivable)."""
    if team is None or team.get("pts") is None or team.get("opp_pts") is None:
        return None
    pts, opp = float(team["pts"]), float(team["opp_pts"])
    fam, thr = d["family"], d.get("threshold")
    if fam == "game_winner":
        return pts > opp
    if thr is None:
        return None
    ge = d.get("comparator") == "ge"
    cmp = (lambda x: x >= float(thr)) if ge else (lambda x: x > float(thr))
    if fam == "game_spread":
        return cmp(pts - opp)
    if fam == "game_total":
        return cmp(pts + opp)
    if fam == "team_total":
        return cmp(pts)
    return None


def fee_paid(eff: float, contracts: int, mult: float) -> float:
    from nba_edge.kalshi.fees import FeeSchedule, taker_fee_cents
    return taker_fee_cents(int(round(eff * 100)), contracts, FeeSchedule(taker_multiplier=mult)) / 100.0


def payoff_for_side(side: str, value: float) -> float:
    return value if side == "YES" else 1.0 - value


def closing_for(snap: dict | None, tip: datetime) -> dict[str, Any]:
    """Closing-line record from an archived LAST_VALID snapshot (valid only if two-sided and within 15 min of tip)."""
    if not snap or snap.get("board_observed_utc") is None:
        return {"ticker": snap.get("ticker") if snap else None, "valid": False, "cause": "NO_LAST_VALID_SNAPSHOT", "board_observed_utc": None,
                "yes_bid": None, "yes_ask": None, "mid_yes": None, "age_s": None}
    bd = MK.parse_ts(snap["board_observed_utc"])
    two = snap.get("quote_class") == "TWO_SIDED" and snap.get("yes_bid") is not None and snap.get("yes_ask") is not None
    mid = (snap["yes_bid"] + snap["yes_ask"]) / 2 if two else None
    age = (tip - bd).total_seconds()
    valid = two and MK.is_closing_line(bd, tip)
    cause = None if valid else ("QUOTE_NOT_TWO_SIDED" if not two else "STALE_LAST_VALID")
    return {"ticker": snap["ticker"], "valid": bool(valid), "cause": cause, "board_observed_utc": snap["board_observed_utc"],
            "yes_bid": snap.get("yes_bid"), "yes_ask": snap.get("yes_ask"), "mid_yes": mid, "age_s": age}


def build_settlement(d: dict, *, auth: dict | None, outcome: dict | None, closing: dict, now: datetime,
                     team: dict | None = None) -> tuple[dict | None, str | None]:
    """(settlement row | None, pending reason). `auth` = {result, value, observed_utc}; `outcome` = {actual, participated, observed_utc}."""
    side = d["side"]
    eff = d["effective_entry"]
    mult = d["fee_assumption"]["multiplier"]
    contracts = int((d.get("simulated_contracts") or 0)) or 1
    row: dict[str, Any] = {"schema": S.SETTLEMENT_SCHEMA, "decision_id": d["decision_id"], "strategy_id": d["strategy_id"], "game_id": d["game_id"],
                           "game_start_utc": d["game_start_utc"], "ticker": d["ticker"], "side": side, "family": d["family"], "horizon": d["horizon"],
                           "thesis_id": d["thesis_id"], "unit_id": d["unit_id"], "cluster_id": d["cluster_id"], "decision": d["decision"],
                           "price": d["price"], "effective_entry": eff, "settled_utc": MK.iso(now), "closing_line": closing,
                           "replay": d.get("replay"), "authority": "research_only", "paper": True, "participated": None, "actual": None,
                           "dnp": False, "dnp_value": None, "dnp_value_source": None, "won": None, "kalshi_result": None}
    fee = fee_paid(eff, contracts, mult) / contracts
    prop = d["family"] in PROP_FAMILY
    played = None if outcome is None else bool(outcome["participated"])
    if outcome is not None:
        row["actual"], row["participated"] = outcome["actual"], played
    gross: float
    if auth is not None:
        row["kalshi_result"] = auth["result"]
        row["outcome_source"] = "kalshi_result"
        if auth["result"] in ("yes", "no"):
            yes = auth["result"] == "yes"
            gross = payoff_for_side(side, 1.0 if yes else 0.0)
            row["won"] = (yes if side == "YES" else not yes)
        elif auth["result"] == "scalar":
            if auth.get("value") is None:
                return None, "SCALAR_WITHOUT_VALUE"
            v = float(auth["value"])
            gross = payoff_for_side(side, v)
            row["dnp"] = bool(prop and (played is False or played is None))
            row["dnp_value"], row["dnp_value_source"] = v, "authoritative"
            row["settlement_note"] = "scalar settlement: the market settled to the last pre-game fair price (player never entered, or the game was not played)"
        elif auth["result"] == "void":
            gross = eff
            row["settlement_note"] = "void: refunded at entry price; fee NOT refunded (conservative assumption, never observed in history)"
        else:
            return None, "UNKNOWN_RESULT:" + str(auth["result"])
    elif prop and outcome is not None:
        row["outcome_source"] = "box_score_derived"
        if played and outcome.get("actual") is None:
            return None, "NO_OUTCOME"
        if played:
            yes = float(outcome["actual"]) >= d["k"]
            gross = payoff_for_side(side, 1.0 if yes else 0.0)
            row["won"] = (yes if side == "YES" else not yes)
        else:
            if closing.get("mid_yes") is None or not closing.get("valid"):
                return None, "DNP_NO_VALID_LAST_VALID_MID"           # a stale / one-sided closing quote is not a fair-price estimate
            row["dnp"] = True
            row["dnp_value"] = closing["mid_yes"]                      # the YES-side fair value; the side payoff is derived from it
            row["dnp_value_source"] = "modeled_last_valid_mid"
            gross = payoff_for_side(side, closing["mid_yes"])
            row["settlement_note"] = ("player did not play: valued at the LAST_VALID mid (Kalshi settles such markets to the last fair price); "
                                      "authoritative value pending -> a correction is appended if it differs")
    elif d["family"] in GAME_FAMILY and game_yes(d, team) is not None:
        yes = game_yes(d, team)
        row["outcome_source"] = "box_score_derived"
        pts, opp = float(team["pts"]), float(team["opp_pts"])
        row["actual"] = {"game_total": pts + opp, "team_total": pts}.get(d["family"], pts - opp)      # the contract's own quantity
        row["team_pts"], row["opp_pts"] = pts, opp
        gross = payoff_for_side(side, 1.0 if yes else 0.0)
        row["won"] = (yes if side == "YES" else not yes)
        row["settlement_note"] = "derived from the archived final team points (overtime included); the authoritative Kalshi result supersedes via a correction"
    else:
        return None, "NO_AUTHORITATIVE_RESULT" if not prop else "NO_OUTCOME"
    row["gross_payoff"] = round(gross, 6)
    row["fee_paid"] = round(fee, 6)
    row["net_pnl"] = round(gross - eff - fee, 6)
    row["net_pnl_if_conditional_void"] = None if row["dnp"] else row["net_pnl"]
    mid = closing.get("mid_yes")
    if closing["valid"] and mid is not None:
        side_mid = mid if side == "YES" else 1.0 - mid
        row["clv_cents"] = round((side_mid - d["price"]) * 100.0, 3)
    else:
        row["clv_cents"] = None
    return row, None


def authoritative_results(reader: MK.ChainReader, tickers_by_tip: dict[str, datetime], until: datetime) -> dict[str, dict]:
    """First captured post-game market row per ticker whose `result` is yes|no|scalar|void."""
    if not tickers_by_tip:
        return {}
    since = min(tickers_by_tip.values())
    remaining = set(tickers_by_tip)
    found: dict[str, dict] = {}
    for dt, board in reader.walk(since, until):
        if board is None:
            continue
        for tk in list(remaining):
            r = board.get(tk)
            if r is None or dt <= tickers_by_tip[tk]:
                continue
            res = (r.get("result") or "").lower()
            if res in ("yes", "no", "scalar", "void"):
                sv = MK._f(r.get("settlement_value_dollars"))
                found[tk] = {"result": res, "value": sv, "observed_utc": MK.iso(dt)}
                remaining.discard(tk)
        if not remaining:
            break
    return found


def _latest_outcomes(root: str) -> dict[tuple[str, str, str], dict]:
    rows = pr._read(root, "outcomes", "NBA")
    out: dict[tuple[str, str, str], dict] = {}
    for r in sorted(rows, key=lambda x: x.get("observed_utc") or ""):
        out[(r["game_id"], r["entity_id"], r["family"])] = r
    return out


def settle_paper(archive: str, market_archive: str | None, now: datetime, *, min_age_hours: float = 2.0, cfg: dict | None = None,
                 reader: MK.ChainReader | None = None) -> dict[str, Any]:
    """Settle every unsettled full decision row of games that started more than `min_age_hours` ago; append corrections where a later
    authoritative result contradicts a box-derived one. Idempotent."""
    cfg = cfg or CFG.load()
    st: dict[str, Any] = {"decisions_considered": 0, "settled_written": 0, "already_settled": 0, "pending": Counter(), "corrections_written": 0,
                          "by_source": Counter()}
    days = store.days(archive, "decisions")
    decisions = [d for d in store.read(archive, "decisions", days) if not d.get("compact") and d.get("side") in S.SIDES
                 and d.get("price") is not None]
    cutoff = now - timedelta(hours=min_age_hours)
    decisions = [d for d in decisions if MK.parse_ts(d["game_start_utc"]) <= cutoff]
    st["decisions_considered"] = len(decisions)
    if not decisions:
        st["pending"], st["by_source"] = {}, {}
        return st
    settled_days = store.days(archive, "settlements")
    done = {r["decision_id"]: r for r in store.read(archive, "settlements", settled_days)}
    st["already_settled"] = sum(1 for d in decisions if d["decision_id"] in done)
    todo = [d for d in decisions if d["decision_id"] not in done or done[d["decision_id"]].get("outcome_source") != "kalshi_result"]
    snaps = {}
    for r in store.read(archive, "market_snapshots", sorted({MK.parse_ts(d["game_start_utc"]).strftime("%Y-%m-%d") for d in decisions})):
        if r.get("horizon") == "LAST_VALID" and r.get("ticker"):
            snaps[r["ticker"]] = r
    auth: dict[str, dict] = {}
    if market_archive and todo:
        reader = reader or MK.ChainReader(market_archive, "markets")
        tips = {d["ticker"]: MK.parse_ts(d["game_start_utc"]) for d in todo}
        auth = authoritative_results(reader, tips, now)
    outs = _latest_outcomes(archive)
    teams: dict[tuple[str, str], dict] = {}
    for r in sorted(store.read(archive, "team_outcomes"), key=lambda x: x.get("observed_utc") or ""):
        teams[(r["game_id"], r["team"])] = r
        teams[(r["game_id"], None)] = r                # any one team row fixes a full-game total (pts + opp_pts)
    new_rows, corr_rows = [], []
    for d in todo:
        tip = MK.parse_ts(d["game_start_utc"])
        key = None
        if d["family"] in PROP_FAMILY and d.get("entity_id"):
            key = (d["game_id"], d["entity_id"], PROP_FAMILY[d["family"]])
        o = outs.get(key) if key else None
        if o is not None and not o.get("participated", True):
            o = {"actual": 0.0, "participated": False, "observed_utc": o.get("observed_utc")}
        elif o is not None:
            o = {"actual": o["actual"], "participated": True, "observed_utc": o.get("observed_utc")}
        # a player who did not play has participated=False on every stat family of the outcome archive (results.outcome_rows)
        closing = closing_for(snaps.get(d["ticker"]), tip)
        row, why = build_settlement(d, auth=auth.get(d["ticker"]), outcome=o, closing=closing, now=now,
                                    team=teams.get((d["game_id"], d.get("team"))) if d["family"] in GAME_FAMILY else None)
        if row is None:
            st["pending"][why] += 1
            continue
        prev = done.get(d["decision_id"])
        if prev is None:
            new_rows.append(row)
            st["by_source"][row["outcome_source"]] += 1
        elif row["outcome_source"] == "kalshi_result" and (abs(prev["net_pnl"] - row["net_pnl"]) > 1e-9 or prev.get("won") != row.get("won")):
            corr_rows.append({"schema": S.CORRECTION_SCHEMA, "correction_id": S.sha(["corr", d["decision_id"], row["net_pnl"], row["outcome_source"]]),
                              "decision_id": d["decision_id"], "game_id": d["game_id"], "strategy_id": d["strategy_id"],
                              "corrected_utc": MK.iso(now), "previous": {k: prev.get(k) for k in ("outcome_source", "net_pnl", "won", "dnp_value",
                                                                                                    "dnp_value_source", "gross_payoff")},
                              "new": row, "reason": "authoritative Kalshi result differs from the earlier box-derived / modeled settlement",
                              "authority": "research_only"})
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in new_rows:
        by_day[MK.parse_ts(r["game_start_utc"]).strftime("%Y-%m-%d")].append(r)
    for day, rows in sorted(by_day.items()):
        res = store.write_new(archive, "settlements", day, rows, "decision_id", now)
        st["settled_written"] += res["written"]
    by_day = defaultdict(list)
    for r in corr_rows:
        by_day[MK.parse_ts(r["new"]["game_start_utc"]).strftime("%Y-%m-%d")].append(r)
    for day, rows in sorted(by_day.items()):
        res = store.write_new(archive, "corrections", day, rows, "correction_id", now)
        st["corrections_written"] += res["written"]
    st["pending"], st["by_source"] = dict(st["pending"]), dict(st["by_source"])
    return st
