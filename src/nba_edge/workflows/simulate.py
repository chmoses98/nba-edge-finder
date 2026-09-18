"""``nba simulate``: the RUN NBA job.

For every not-started game on the target ET date (from the latest archived schedule snapshot):
  1. assemble point-in-time inputs (history parquet + archived box scores, injuries, rosters) with a strict cutoff;
  2. build simulation parameters (features/build.py) and simulate to convergence;
  3. map every archived Kalshi market for that game to a Contract, resolve identities, price it from the same draws;
  4. compute executable economics from the latest market snapshot, gates (NO_EDGE vs CANNOT_TRUST_INPUTS), theses;
  5. freeze ContractPrediction + Contract rows in the ledger (append-only) and write slate.json / slate.md / packet.json.

Model views: DATA_ONLY (simulator), MARKET_BASELINE (Kalshi mid), HYBRID (logit blend with a *prior* weight — the
weight is a placeholder until prospective evidence exists; the value used is recorded on every row).
Authority is RESEARCH for every family tonight: p_production is emitted for evaluation only.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from nba_edge import MODEL_VERSION
from nba_edge.archive.ledger import Ledger, entry_observed_at
from nba_edge.execution.economics import EconomicsConfig, compute_economics, market_implied_probability
from nba_edge.execution.expression import PricedContract, group_by_thesis, select_portfolio
from nba_edge.features.build import FEATURE_VERSION, BuildConfig, build_game_params, rest_days_for
from nba_edge.identity.normalize import normalize_name
from nba_edge.identity.teams import registry
from nba_edge.kalshi.contracts import build_contract
from nba_edge.kalshi.fees import DEFAULT_SCHEDULE
from nba_edge.kalshi.ontology import Ontology
from nba_edge.kalshi.ticker import parse_ticker
from nba_edge.log import get_logger, kv
from nba_edge.pricing.contracts import price_contract
from nba_edge.pricing.ladder import audit_ladders
from nba_edge.schemas.core import InjuryStatus
from nba_edge.schemas.market import Contract
from nba_edge.schemas.prediction import Authority, ContractPrediction, Gate
from nba_edge.sim.convergence import simulate_until_converged
from nba_edge.sim.engine import SIM_VERSION
from nba_edge.timeutil import ET, iso, parse_iso, utcnow

log = get_logger(__name__)
HYBRID_MARKET_WEIGHT = 0.70  # prior; NOT learned. Recorded on every prediction row.
STALE_MARKET_MIN = 45.0
STALE_INJURY_MIN = 6 * 60.0


def _read_kind(ledger: Ledger, kind: str, latest_only: bool = True) -> list[dict[str, Any]]:
    if latest_only:
        e = ledger.latest(kind)
        if not e:
            return []
        with gzip.open(ledger.root / e.path, "rt") as f:
            return [json.loads(line) for line in f if line.strip()]
    return list(ledger.iter_rows(kind))


def load_history(data_root: Path, archive: Ledger) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Historical ESPN parquet + current-season box scores archived by the settle job."""
    from nba_edge.data.history import load_player_games, load_team_games, parse_player_rows, parse_team_rows
    from nba_edge.settlement.boxscore import FinalBoxScore

    hist = data_root / "history"
    seasons = sorted({p.stem.split("_")[-1] for p in (hist / "espn").glob("team_games_*.parquet")}) if (hist / "espn").exists() else []
    tg = load_team_games(hist, seasons) if seasons else pd.DataFrame()
    pg = load_player_games(hist, seasons) if seasons else pd.DataFrame()
    extra_t, extra_p = [], []
    seen = set(tg["game_id"]) if not tg.empty else set()
    for row in archive.iter_rows("boxscores"):
        try:
            box = FinalBoxScore(**{k: v for k, v in row.items() if not k.startswith("_")})
        except Exception:  # noqa: BLE001
            continue
        if box.game_id in seen or not box.is_final:
            continue
        seen.add(box.game_id)
        meta = {"game_id": box.game_id, "game_date_et": (box.actual_tip_utc or box.fetched_at_utc).astimezone(ET).date().isoformat(), "season": row.get("_season", ""), "season_type": row.get("_season_type", "regular"), "home_team_id": box.home_team_id, "away_team_id": box.away_team_id}
        extra_p.extend(parse_player_rows(box, meta))
        extra_t.extend(parse_team_rows(box, meta))
    if extra_t:
        tg = pd.concat([tg, pd.DataFrame(extra_t)], ignore_index=True) if not tg.empty else pd.DataFrame(extra_t)
        pg = pd.concat([pg, pd.DataFrame(extra_p)], ignore_index=True) if not pg.empty else pd.DataFrame(extra_p)
    return tg, pg


class NameIndex:
    """Identity resolution for contracts: durable aliases first (data/identity/players.jsonl: Kalshi uuid -> id),
    then unique normalised-name match within the game's rosters; ambiguous -> None (never guessed)."""

    def __init__(self, rosters: list[dict[str, Any]], player_games: pd.DataFrame, registry_path: Path | None = None):
        self.by_team: dict[int, dict[str, set[int]]] = {}
        self.names: dict[int, str] = {}
        self.by_kalshi_uuid: dict[str, int] = {}
        reg = registry()
        try:
            from nba_edge.identity.players import PLAYERS_JSONL, PlayerRegistry

            preg = PlayerRegistry.load(registry_path or PLAYERS_JSONL)
            for rec in preg.records.values():
                if "kalshi_uuid" in rec.aliases:
                    self.by_kalshi_uuid[rec.aliases["kalshi_uuid"]] = rec.nba_id
                    self.names.setdefault(rec.nba_id, rec.full_name)
        except Exception as e:  # noqa: BLE001 - registry is optional; name matching still applies
            log.warning(kv(event="player_registry_unavailable", err=str(e)[:120]))
        for r in rosters:
            try:
                tid = reg.by_tricode(r.get("team_abbreviation", "")).team_id
                pid = -int(r["espn_athlete_id"])
            except Exception:  # noqa: BLE001
                continue
            self._add(tid, pid, r.get("full_name") or "")
        if not player_games.empty:
            last = player_games.sort_values("game_date_et").groupby("nba_id").tail(1)
            for _, r in last.iterrows():
                self._add(int(r["team_id"]), int(r["nba_id"]), str(r["player_name"]))

    def _add(self, tid: int, pid: int, name: str) -> None:
        self.names[pid] = name
        self.by_team.setdefault(tid, {}).setdefault(normalize_name(name), set()).add(pid)

    def roster(self, tid: int) -> list[int]:
        return sorted({pid for s in self.by_team.get(tid, {}).values() for pid in s})

    def find_in_text(self, text: str, team_ids: list[int]) -> tuple[int | None, str]:
        t = normalize_name(text)
        hits: set[int] = set()
        for tid in team_ids:
            for nm, pids in self.by_team.get(tid, {}).items():
                if nm and len(nm.split()) >= 2 and nm in t:
                    hits |= pids
        if len(hits) == 1:
            return hits.pop(), "unique_name_in_text"
        return None, ("ambiguous" if hits else "no_match")

    def resolve_name(self, name: str, tid: int) -> int | None:
        pids = self.by_team.get(tid, {}).get(normalize_name(name), set())
        return next(iter(pids)) if len(pids) == 1 else None


def injuries_by_team(inj_rows: list[dict[str, Any]], names: NameIndex) -> tuple[dict[int, dict[int, InjuryStatus]], dict[str, Any]]:
    out: dict[int, dict[int, InjuryStatus]] = {}
    unresolved = []
    official = [r for r in inj_rows if r.get("source") == "nba_official_pdf"]
    rows = official or inj_rows  # prefer the official report when present
    for r in rows:
        tid = int(r["team_id"])
        pid = names.resolve_name(r.get("player_name_raw", ""), tid)
        if pid is None:
            unresolved.append(f"{r.get('player_name_raw')}@{tid}")
            continue
        out.setdefault(tid, {})[pid] = InjuryStatus(r.get("status", "unknown"))
    return out, {"source": "official" if official else ("espn" if inj_rows else "none"), "n": len(rows), "unresolved": unresolved[:50]}


def _pred_id(ticker: str, ts: str, model: str) -> str:
    return hashlib.sha256(f"{ticker}|{ts}|{model}".encode()).hexdigest()[:32]


def _hybrid(p_data: float | None, p_mkt: float | None, w: float = HYBRID_MARKET_WEIGHT) -> float | None:
    if p_data is None or p_mkt is None:
        return None
    lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))  # noqa: E731
    z = w * lg(p_mkt) + (1 - w) * lg(p_data)
    return float(1 / (1 + np.exp(-z)))


def markets_for_game(markets: list[dict[str, Any]], game: dict[str, Any]) -> list[dict[str, Any]]:
    reg = registry()
    out = []
    date = game["game_date_et"]
    home, away = game["home_tricode"], game["away_tricode"]
    for m in markets:
        pt = parse_ticker(m.get("ticker", ""), reg.tricodes)
        if pt.game_date and pt.game_date.isoformat() == date and pt.home_tricode == home and pt.away_tricode == away:
            out.append(m)
    return out


def run_simulate(out_root: Path, data_root: Path, date: str | None = None, n_sims: int = 0, seed: int | None = None, now=None) -> int:
    now = now or utcnow()
    archive = Ledger(out_root)
    onto = Ontology.load()
    target = date or now.astimezone(ET).date().isoformat()
    sched = _read_kind(archive, "context/schedule")
    games = [g for g in sched if g.get("game_date_et") == target and parse_iso(g["start_time_utc"]) > now and g.get("status") in ("scheduled", None)]
    games = {g["game_id"]: g for g in games}.values()
    status: dict[str, Any] = {"simulated_at_utc": iso(now), "date": target, "n_games": len(games), "games": []}
    if not games:
        log.info(kv(event="simulate_no_games", date=target))
        (out_root / "STATUS_simulate.json").write_text(json.dumps(status, indent=1))
        return 0
    tg, pg = load_history(data_root, archive)
    rosters = _read_kind(archive, "context/rosters")
    names = NameIndex(rosters, pg)
    inj_entry = archive.latest("context/injuries")
    inj_rows = _read_kind(archive, "context/injuries")
    inj_age_min = (now - entry_observed_at(inj_entry)).total_seconds() / 60 if inj_entry else None
    inj_map, inj_prov = injuries_by_team(inj_rows, names)
    mkt_entry = archive.latest("kalshi/markets")
    markets = _read_kind(archive, "kalshi/markets")
    mkt_age_min = (now - entry_observed_at(mkt_entry)).total_seconds() / 60 if mkt_entry else None
    seed = seed if seed is not None else int(hashlib.sha256(f"{target}{MODEL_VERSION}".encode()).hexdigest()[:8], 16)

    slate_games, slate_contracts, pred_rows, contract_rows, packet_games = [], [], [], [], []
    all_priced: list[PricedContract] = []
    coverage: Counter[str] = Counter()
    for g in games:
        gid = g["game_id"]
        cutoff = g["game_date_et"]
        home_id, away_id = int(g["home_team_id"]), int(g["away_team_id"])
        game_in = dict(g)
        for side, tid in (("home", home_id), ("away", away_id)):
            rd = rest_days_for(tid, cutoff, tg) if not tg.empty else None
            game_in[f"{side}_rest_days"] = rd if rd is not None else 2
            game_in[f"{side}_b2b"] = rd == 1
        rosters_map = {home_id: names.roster(home_id) or None, away_id: names.roster(away_id) or None}
        gp, rep = build_game_params(game_in, tg, pg, cutoff, inj_map, {k: v for k, v in rosters_map.items() if v}, BuildConfig())
        if n_sims > 0:
            from nba_edge.sim.engine import simulate

            sim = simulate(gp, n_sims, seed)
            conv = None
        else:
            sim, conv = simulate_until_converged(gp, seed)
        # input-quality gates
        reasons: list[str] = []
        if inj_age_min is None or inj_age_min > STALE_INJURY_MIN:
            reasons.append(f"injury snapshot missing/stale ({None if inj_age_min is None else round(inj_age_min)} min)")
        if inj_prov.get("source") != "official":
            reasons.append(f"injury source is {inj_prov.get('source')} not official report")
        if mkt_age_min is None or mkt_age_min > STALE_MARKET_MIN:
            reasons.append(f"market snapshot missing/stale ({None if mkt_age_min is None else round(mkt_age_min)} min)")
        if rep.team_games_used.get(home_id, 0) < 5 or rep.team_games_used.get(away_id, 0) < 5:
            reasons.append("fewer than 5 prior games for a team (priors dominate)")
        reasons.extend(w for w in rep.warnings if "CANNOT_TRUST" in w)
        if g.get("season_type") == "preseason":
            reasons.append("preseason game: rotations/minutes are not representative (systems-validation only)")
        trust = not reasons
        gsum = {
            "game_id": gid, "tip_utc": g["start_time_utc"], "home": g["home_tricode"], "away": g["away_tricode"], "p_home_win": float((sim.margin > 0).mean()),
            "margin_mean": float(sim.margin.mean()), "margin_sd": float(sim.margin.std()), "total_mean": float(sim.total.mean()), "total_sd": float(sim.total.std()),
            "home_pts_mean": float(sim.home_pts.mean()), "away_pts_mean": float(sim.away_pts.mean()), "ot_rate": float((sim.n_ot > 0).mean()), "n_sims": sim.n_sims, "seed": seed,
            "converged": None if conv is None else conv.converged, "max_mc_se": None if conv is None else conv.max_se, "inputs_trusted": trust, "input_reasons": reasons,
            "home_params": {"pace": gp.home.pace, "off_ppp": gp.home.off_ppp, "def_ppp": gp.home.def_ppp, "rest_days": gp.home.rest_days, "b2b": gp.home.b2b, "games_used": rep.team_games_used.get(home_id)},
            "away_params": {"pace": gp.away.pace, "off_ppp": gp.away.off_ppp, "def_ppp": gp.away.def_ppp, "rest_days": gp.away.rest_days, "b2b": gp.away.b2b, "games_used": rep.team_games_used.get(away_id)},
        }
        slate_games.append(gsum)
        # contracts
        gms = markets_for_game(markets, g)
        contracts: list[Contract] = []
        probs: dict[str, float] = {}
        game_contracts_out = []
        for m in gms:
            c = build_contract(m, onto)
            c = c.model_copy(update={"game_id": gid})
            if c.scope == "player" and c.nba_id is None:
                pid, how = (names.by_kalshi_uuid.get(c.kalshi_entity_uuid), "kalshi_uuid_alias") if c.kalshi_entity_uuid in names.by_kalshi_uuid else (None, "")
                if pid is None:
                    pid, how = names.find_in_text(f"{m.get('yes_sub_title','')} {m.get('title','')}", [home_id, away_id])
                if pid is not None:
                    c = c.model_copy(update={"nba_id": pid, "notes": c.notes + [f"player resolved via {how}"]})
                elif c.support in ("PRICED", "BUILDABLE"):
                    c = c.model_copy(update={"support": "UNRESOLVED", "semantics_confidence": "low", "notes": c.notes + [f"player identity {how}"]})
                else:
                    c = c.model_copy(update={"notes": c.notes + [f"player identity {how}"]})
            pr = price_contract(c, sim)
            coverage[c.support if pr.supported else (c.support if c.support not in ("PRICED", "BUILDABLE") else "UNRESOLVED")] += 1
            snap = {k: m.get(k) for k in ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price", "volume", "open_interest", "liquidity")} | {"observed_at_utc": m.get("_observed_at_utc")}
            mi = market_implied_probability(snap)
            p_mkt = mi.p_mid
            p_data = pr.p if pr.supported else None
            p_h = _hybrid(p_data, p_mkt)
            econ = compute_economics(snap, p_h if p_h is not None else (p_data or 0.5), pr.se or 0.0, schedule=DEFAULT_SCHEDULE, config=EconomicsConfig(max_age_min=STALE_MARKET_MIN), observed_at=parse_iso(m["_observed_at_utc"]) if m.get("_observed_at_utc") else None, now=now) if (p_h is not None or p_data is not None) else None
            if not pr.supported:
                gate, greasons = Gate.UNSUPPORTED, [pr.reason]
            elif not trust:
                gate, greasons = Gate.CANNOT_TRUST_INPUTS, reasons
            elif econ is None or econ.best_side is None:
                gate, greasons = Gate.NO_EDGE, (econ.reasons if econ else ["no market quote"])
            else:
                gate, greasons = Gate.OK, []
            ts = iso(now)
            pred = ContractPrediction(
                prediction_id=_pred_id(m["ticker"], ts, MODEL_VERSION), ticker=m["ticker"], game_id=gid, family=c.family, predicted_at_utc=now,
                data_cutoff_utc=parse_iso(f"{cutoff}T00:00:00-04:00"), model_version=MODEL_VERSION, sim_version=SIM_VERSION, feature_version=FEATURE_VERSION, n_sims=sim.n_sims,
                p_data_only=p_data, p_market=p_mkt, p_hybrid=p_h, p_production=p_h, p_data_only_se=pr.se if pr.supported else None,
                market_observed_at_utc=parse_iso(m["_observed_at_utc"]) if m.get("_observed_at_utc") else None, market_yes_bid=m.get("yes_bid"), market_yes_ask=m.get("yes_ask"),
                market_no_bid=m.get("no_bid"), market_no_ask=m.get("no_ask"), gate=gate, gate_reasons=[str(x) for x in greasons][:8], authority=Authority.RESEARCH, support=c.support,
                pregame=True, thesis_group=None, input_snapshot_ids={"markets": mkt_entry.path if mkt_entry else "", "injuries": inj_entry.path if inj_entry else "", "hybrid_market_weight": str(HYBRID_MARKET_WEIGHT)},
            )
            pred_rows.append(pred.model_dump(mode="json"))
            contract_rows.append(c.model_dump(mode="json"))
            contracts.append(c)
            if pr.supported:
                probs[m["ticker"]] = pr.p
            row = {
                "ticker": m["ticker"], "game_id": gid, "title": m.get("title"), "family": c.family, "stat": c.stat, "period": c.period, "team_id": c.team_id, "nba_id": c.nba_id,
                "player": names.names.get(c.nba_id) if c.nba_id else None, "threshold": c.threshold, "comparator": c.comparator, "support": c.support, "semantics": c.semantics_confidence,
                "yes_bid": m.get("yes_bid"), "yes_ask": m.get("yes_ask"), "no_bid": m.get("no_bid"), "no_ask": m.get("no_ask"), "p_market": p_mkt, "p_data_only": p_data, "p_hybrid": p_h,
                "p_production": p_h, "mc_se": pr.se if pr.supported else None, "gate": str(gate), "gate_reasons": [str(x) for x in greasons][:4], "authority": "RESEARCH",
                "best_side": econ.best_side if econ else None, "ev_yes": econ.yes.ev_per_contract if econ else None, "ev_no": econ.no.ev_per_contract if econ else None,
                "bet_up_to_yes": econ.yes.bet_up_to_cents if econ else None, "bet_up_to_no": econ.no.bet_up_to_cents if econ else None, "spread_cents": econ.spread_cents if econ else None,
                "flags": (econ.reasons if econ else []) + pr.notes, "market_ts": m.get("_observed_at_utc"), "model_ts": ts, "prediction_id": pred.prediction_id,
            }
            slate_contracts.append(row)
            game_contracts_out.append(row)
            if pr.supported and econ is not None and gate == Gate.OK:
                all_priced.append(PricedContract(ticker=m["ticker"], game_id=gid, family=c.family, stat=c.stat, period=c.period, team_id=c.team_id, nba_id=c.nba_id, threshold=c.threshold, comparator=c.comparator, p_fair=p_h if p_h is not None else pr.p, se=pr.se or 0.0, economics=econ, yes_indicator=pr.indicator, home_team_id=home_id))
        viol = audit_ladders(contracts, probs)
        gsum["ladder_violations"] = [asdict(v) for v in viol]
        gsum["n_markets"] = len(gms)
        packet_games.append(_packet_game(g, gp, rep, sim, names, game_contracts_out, inj_rows, home_id, away_id))
        status["games"].append({"game_id": gid, "n_markets": len(gms), "n_sims": sim.n_sims, "trusted": trust})
        log.info(kv(event="game_simulated", game=gid, markets=len(gms), n_sims=sim.n_sims, p_home=round(gsum["p_home_win"], 3), trusted=trust))

    groups = group_by_thesis(all_priced)
    portfolio = select_portfolio(groups)
    theses = [{"thesis": gr.thesis, "game_id": gr.game_id, "best": gr.best.ticker, "best_side": gr.best.best_side, "best_ev": gr.best.economics.best.ev_per_contract if gr.best.economics.best else None,
               "alternatives": [{"ticker": a.ticker, "corr_with_best": corr} for a, corr in gr.alternatives][:8], "warning": gr.warning} for gr in groups]
    for t in theses:
        for row in slate_contracts:
            if row["ticker"] == t["best"] or any(row["ticker"] == a["ticker"] for a in t["alternatives"]):
                row["thesis"] = t["thesis"]
    slate = {
        "generated_at_utc": iso(now), "date_et": target, "model_version": MODEL_VERSION, "sim_version": SIM_VERSION, "feature_version": FEATURE_VERSION,
        "hybrid_market_weight_prior": HYBRID_MARKET_WEIGHT, "authority_note": "All families are RESEARCH: no betting authority. Numbers are for prospective evaluation.",
        "market_snapshot": mkt_entry.path if mkt_entry else None, "market_snapshot_age_min": mkt_age_min, "injury_snapshot": inj_entry.path if inj_entry else None, "injury_snapshot_age_min": inj_age_min, "injury_provenance": inj_prov,
        "coverage": dict(coverage), "games": slate_games, "contracts": slate_contracts, "theses": theses, "portfolio": [p.ticker for p in portfolio],
    }
    if pred_rows:
        archive.append_rows("predictions", pred_rows, observed_at=now, meta={"date": target, "n": len(pred_rows)})
        archive.append_rows("contracts", contract_rows, observed_at=now, meta={"date": target})
    sd = out_root / "slates" / f"dt={target}" / now.strftime("%Y%m%dT%H%M%SZ")
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "slate.json").write_text(json.dumps(slate, indent=1, default=str))
    (sd / "slate.md").write_text(slate_markdown(slate))
    (sd / "packet.json").write_text(json.dumps({"slate": slate, "games": packet_games}, indent=1, default=str))
    latest = out_root / "slates" / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    for f in ("slate.json", "slate.md", "packet.json"):
        (latest / f).write_text((sd / f).read_text())
    status["slate_dir"] = str(sd)
    status["coverage"] = dict(coverage)
    (out_root / "STATUS_simulate.json").write_text(json.dumps(status, indent=1, default=str))
    print(slate_markdown(slate))
    return 0


def _q(x: np.ndarray, qs=(0.05, 0.25, 0.5, 0.75, 0.95)) -> dict[str, float]:
    return {f"q{int(q*100)}": float(np.quantile(x, q)) for q in qs}


def _packet_game(g: dict[str, Any], gp, rep, sim, names: NameIndex, contracts: list[dict[str, Any]], inj_rows: list[dict[str, Any]], home_id: int, away_id: int) -> dict[str, Any]:
    def team_block(tp):
        players = []
        for p in tp.players:
            ps = sim.players.get(p.nba_id)
            block = {"nba_id": p.nba_id, "name": p.name, "p_play": p.p_play, "p_start": p.p_start, "minutes_mean": p.min_mean, "minutes_sd": p.min_sd, "fga_per_min": p.fga_per_min,
                     "three_share": p.three_share, "fg2_pct": p.fg2_pct, "fg3_pct": p.fg3_pct, "ft_pct": p.ft_pct, "games_used": rep.player_games_used.get(p.nba_id)}
            if ps is not None and ps.played.any():
                pl = ps.played
                block["sim"] = {k: {"mean": float(ps.stats[k][pl].mean()), **_q(ps.stats[k][pl])} for k in ("min", "pts", "reb", "ast", "fg3m")}
                block["sim"]["pra"] = {"mean": float(ps.stat("pra")[pl].mean()), **_q(ps.stat("pra")[pl])}
            players.append(block)
        return {"team_id": tp.team_id, "tricode": tp.tricode, "pace": tp.pace, "off_ppp": tp.off_ppp, "def_ppp": tp.def_ppp, "rest_days": tp.rest_days, "b2b": tp.b2b, "rating_sd": tp.rating_sd, "players": players}

    return {
        "game": g, "warnings": rep.warnings, "league_rates": rep.league, "home": team_block(gp.home), "away": team_block(gp.away),
        "sim": {"margin": {"mean": float(sim.margin.mean()), **_q(sim.margin)}, "total": {"mean": float(sim.total.mean()), **_q(sim.total)}, "home_pts": _q(sim.home_pts), "away_pts": _q(sim.away_pts),
                "first_half_total": _q(sim.period_total("1H")), "first_quarter_total": _q(sim.period_total("1Q")), "ot_rate": float((sim.n_ot > 0).mean()), "p_home_win": float((sim.margin > 0).mean()),
                "margin_ladder": {str(k): float((sim.margin > k).mean()) for k in np.arange(-15.5, 16, 1.0)}, "total_ladder": {str(k): float((sim.total > k).mean()) for k in np.arange(float(np.floor(sim.total.mean() - 20)) + 0.5, sim.total.mean() + 21, 1.0)}},
        "injury_report_rows": [r for r in inj_rows if int(r.get("team_id", -1)) in (home_id, away_id)],
        "contracts": contracts,
    }


def slate_markdown(s: dict[str, Any]) -> str:
    L = [f"# NBA slate {s['date_et']} — generated {s['generated_at_utc']} — {s['model_version']}", "", f"_{s['authority_note']}_", "",
         f"Market snapshot age: {s.get('market_snapshot_age_min') and round(s['market_snapshot_age_min'])} min · injury snapshot age: {s.get('injury_snapshot_age_min') and round(s['injury_snapshot_age_min'])} min ({s.get('injury_provenance', {}).get('source')})", "",
         "## Coverage", "", "| support | contracts |", "|---|---:|"]
    for k, v in sorted(s["coverage"].items()):
        L.append(f"| {k} | {v} |")
    L += ["", "## Games", "", "| game | tip (UTC) | P(home) | margin μ±σ | total μ±σ | OT | sims | inputs |", "|---|---|---:|---|---|---:|---:|---|"]
    for g in s["games"]:
        L.append(f"| {g['away']} @ {g['home']} | {g['tip_utc']} | {g['p_home_win']:.3f} | {g['margin_mean']:+.1f}±{g['margin_sd']:.1f} | {g['total_mean']:.1f}±{g['total_sd']:.1f} | {g['ot_rate']:.3f} | {g['n_sims']} | {'ok' if g['inputs_trusted'] else 'CANNOT_TRUST: ' + '; '.join(g['input_reasons'][:2])} |")
    L += ["", "## Contracts (OK gate, sorted by best EV)", "", "| ticker | title | side | ask | p_mkt | p_data | p_hyb | EV | bet≤ | thesis |", "|---|---|---|---:|---:|---:|---:|---:|---:|---|"]
    ok = [c for c in s["contracts"] if c["gate"] == "OK"]
    ok.sort(key=lambda c: -max(c["ev_yes"] or -9, c["ev_no"] or -9))
    for c in ok[:80]:
        side = c["best_side"]
        ask = c["yes_ask"] if side == "yes" else c["no_ask"]
        ev = c["ev_yes"] if side == "yes" else c["ev_no"]
        bu = c["bet_up_to_yes"] if side == "yes" else c["bet_up_to_no"]
        L.append(f"| {c['ticker']} | {str(c['title'])[:48]} | {side} | {ask} | {c['p_market'] and round(c['p_market'],3)} | {c['p_data_only'] and round(c['p_data_only'],3)} | {c['p_hybrid'] and round(c['p_hybrid'],3)} | {ev and round(ev,3)} | {bu} | {c.get('thesis','')} |")
    other = Counter(c["gate"] for c in s["contracts"] if c["gate"] != "OK")
    L += ["", f"Other gates: {dict(other)}", ""]
    if s["theses"]:
        L += ["## Theses (best expression per thesis)", ""]
        for t in s["theses"][:40]:
            L.append(f"- **{t['thesis']}** ({t['game_id']}): {t['best']} {t['best_side']} EV={t['best_ev'] and round(t['best_ev'],3)}; alternatives: " + ", ".join(f"{a['ticker']}(ρ={a['corr_with_best'] if a['corr_with_best'] is None else round(a['corr_with_best'],2)})" for a in t["alternatives"][:5]) + (f" ⚠ {t['warning']}" if t.get("warning") else ""))
    return "\n".join(L) + "\n"
