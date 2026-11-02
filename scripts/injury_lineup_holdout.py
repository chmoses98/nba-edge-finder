"""Frozen-season paired test of lineup effects vs the same team-only forecast.

Fit ONLY 2024-25 certified stints. Evaluate 2025-26 games with a trailing
team rating. Uses actual current-game minutes as an *oracle upper bound*, NOT
pregame-available information. Candidate must beat baseline even with this
advantage before any model authority can be considered.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nba_edge.availability.identity import PlayerIndex
from nba_edge.config import REPO_ROOT
from nba_edge.research.lineup_impact import fit_lineup_impact
from nba_edge.sim.params import LEAGUE


def _trailing(vals: np.ndarray, half_life: float = 25.0) -> float:
    if len(vals) == 0:
        return LEAGUE["ppp"]
    weights = 0.5 ** (np.arange(len(vals) - 1, -1, -1) / half_life)
    return float((weights @ vals + 4.0 * LEAGUE["ppp"]) / (sum(weights) + 4.0))


def _numbers(err: list[float]) -> dict:
    a = np.array(err, dtype=float)
    return {"n": len(a), "mae": float(np.mean(np.abs(a))), "rmse": float(np.sqrt(np.mean(a ** 2)))}



def _paired_game_bootstrap_ci(rows: list[dict], candidate_key: str, *, affected_only: bool = False,
                              draws: int = 1000, seed: int = 811) -> list[float]:
    """95% paired RMSE-gain interval, resampling games not correlated team rows."""
    df = pd.DataFrame(rows)
    if df.empty or candidate_key not in df:
        return [float("nan"), float("nan")]
    if affected_only:
        df = df[df["pit_affected"] == True]  # noqa: E712
    df = df.dropna(subset=["baseline_error", candidate_key])
    if df["game_id"].nunique() < 20:
        return [float("nan"), float("nan")]
    df["sq0"] = df["baseline_error"] ** 2
    df["sq1"] = df[candidate_key] ** 2
    sums = df.groupby("game_id")[["sq0", "sq1"]].sum().to_numpy()
    counts = df.groupby("game_id").size().to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(sums), size=(draws, len(sums)))
    totals = sums[idx].sum(axis=1)
    n = counts[idx].sum(axis=1)
    gain = np.sqrt(totals[:, 0] / n) - np.sqrt(totals[:, 1] / n)
    return [float(x) for x in np.quantile(gain, [0.025, 0.975])]


def _pit_minutes_delta(
    prior: pd.DataFrame, recent_games: list[str], known_out: set[int], model,
) -> tuple[float, float, float]:
    """Expected offence/defence changes using only pregame box minutes + T-60 OUT.

    The trailing team efficiency rating already incorporates the trailing roster,
    so apply only the DIFFERENCE from that roster. Freed minutes go to existing
    rotation players (capped at 42); no actual game minutes enter this function.
    """
    if not recent_games:
        return 0.0, 0.0, 0.0
    x = prior[prior["game_id"].astype(str).isin(recent_games)]
    avg = x.groupby("nba_id")["minutes"].sum() / len(recent_games)
    if avg.sum() < 180:
        return 0.0, 0.0, 0.0
    # A full-season retrospective name->ID lookup is not proof of a PIT roster.
    # Only a player with an observed prior game is eligible for this replay.
    removed = avg.index.intersection(list(known_out))
    lost = float(avg.reindex(removed).sum())
    if lost < 0.01:
        return 0.0, 0.0, 0.0
    expected = avg.copy()
    expected.loc[removed] = 0.0
    # Redistribution is deterministic, conservative and preserves the 240-min
    # budget whenever existing rotation players have sufficient capacity.
    remaining = lost
    for _ in range(8):
        eligible = expected[(expected > 0) & (expected < 42 - 1e-6)]
        if eligible.empty or remaining <= 1e-6:
            break
        weight = eligible / eligible.sum()
        add = np.minimum(weight * remaining, 42.0 - eligible)
        expected.loc[eligible.index] += add
        remaining -= float(add.sum())
    delta = expected - avg
    do = sum(float(v) * model.offensive_absence_ppp(int(pid)) for pid, v in delta.items()) / 48.0
    dd = sum(float(v) * model.defensive_absence_ppp(int(pid)) for pid, v in delta.items()) / 48.0
    return float(do), float(dd), lost


def _official_t60_out(history: Path) -> tuple[dict[str, list[tuple[int, str]]], set[str]]:
    """Read the verified official report published before tip-minus-60 only."""
    root = history / "injury_reports"
    snaps = pd.read_parquet(root / "game_snapshots_2025-26.parquet")
    reports = pd.read_parquet(root / "report_rows_2025-26.parquet")
    good = snaps[
        snaps["t_minus_60_pit_ok"].fillna(False).astype(bool)
        & snaps["t_minus_60_before_cutoff"].fillna(False).astype(bool)
        & (snaps["t_minus_60_teams_listed"] == 2)
    ][["game_id", "t_minus_60_slot_et"]].copy()
    good["game_id"] = good["game_id"].astype(str)
    good = good.rename(columns={"t_minus_60_slot_et": "slot_et"})
    eligible = set(good["game_id"])
    reports["game_id"] = reports["game_id"].astype(str)
    official = reports.merge(good, on=["game_id", "slot_et"], how="inner")
    official = official[official["status"].astype(str).str.lower().isin(["out", "doubtful"])]
    official = official.dropna(subset=["team_id", "player_name_raw"])
    # Ignore the backfill's retrospective nba_id entirely. It was joined to
    # the full-season box (including the game itself), which leaks identity.
    # Resolve raw official names below against only PRIOR game box rows.
    out: dict[str, list[tuple[int, str]]] = {}
    for r in official.itertuples(index=False):
        out.setdefault(str(r.game_id), []).append((int(r.team_id), str(r.player_name_raw)))
    return out, eligible


def run(history: Path, *, max_games: int = 1300) -> dict:
    train = pd.read_parquet(history / "espn" / "team_games_2024-25.parquet")
    test = pd.read_parquet(history / "espn" / "team_games_2025-26.parquet")
    stints = pd.read_parquet(history / "espn_pbp" / "stints_2024-25.parquet")
    model = fit_lineup_impact(stints, train, "2025-07-01")
    if model.n_players < 20 or model.n_games < 100:
        raise RuntimeError("certified-stint fit lacks coverage")
    rows = pd.concat([train, test], ignore_index=True)
    rows = rows[rows["season_type"] == "regular"].sort_values(["game_date_et", "game_id"])
    train_players = pd.read_parquet(history / "espn" / "player_games_2024-25.parquet")
    test_players = pd.read_parquet(history / "espn" / "player_games_2025-26.parquet")
    players = pd.concat([train_players, test_players], ignore_index=True)
    players = players[players["season_type"] == "regular"].copy()
    players["minutes"] = pd.to_numeric(players["minutes"], errors="coerce").fillna(0).clip(lower=0, upper=48)
    players["o"] = players["nba_id"].map(model.offense).fillna(0) * players["minutes"] / 48.0
    players["d"] = players["nba_id"].map(model.defense).fillna(0) * players["minutes"] / 48.0
    q = players.groupby(["game_id", "team_id"])[["o", "d"]].sum()
    # Per-game actual playing time is retrospective oracle data. NEVER pass it as pretip evidence.
    minutes = players.groupby(["game_id", "team_id", "nba_id"])["minutes"].max()
    official_out, official_eligible = _official_t60_out(history)
    by_player_team = {int(t): p for t, p in players.groupby("team_id")}
    home = test[(test["home"] == True) & (test["season_type"] == "regular")]  # noqa: E712
    home = home.sort_values(["game_date_et", "game_id"]).tail(max_games)
    by_team = {int(t): d.sort_values(["game_date_et", "game_id"])
               for t, d in rows.groupby("team_id")}
    base_errors, candidate_errors, depleted_base, depleted_candidate = [], [], [], []
    pit_base, pit_candidate, pit_affected_base, pit_affected_candidate = [], [], [], []
    pit_offense_only, pit_defense_only = [], []
    pit_affected_offense_only, pit_affected_defense_only = [], []
    recs = []
    for g in home.itertuples(index=False):
        date, home_id, away_id, gid = str(g.game_date_et), int(g.team_id), int(g.opp_team_id), str(g.game_id)
        historical = {}
        for tid in (home_id, away_id):
            h = by_team[tid]
            h = h[h["game_date_et"] < date].tail(25)
            if len(h) < 15:
                break
            historical[tid] = h
        if len(historical) != 2:
            continue
        predicted = {}
        pit_effects = {}
        official_by_team: dict[int, set[int]] = {}
        if gid in official_eligible:
            # Resolve the official report's raw names using only previously
            # played games. Never use the backfill's full-season ID join.
            prior_index = PlayerIndex.from_player_games(players[players["game_date_et"] < date])
            for team_id, raw_name in official_out.get(gid, []):
                pid, _ = prior_index.resolve(team_id, raw_name)
                if pid is not None:
                    official_by_team.setdefault(team_id, set()).add(pid)
        depleted = False
        for tid, opp, at_home in ((home_id, away_id, True), (away_id, home_id, False)):
            h, o = historical[tid], historical[opp]
            own_ppp = _trailing((h["pts"] / h["possessions"]).to_numpy(dtype=float))
            opp_def_ppp = _trailing((o["opp_pts"] / o["possessions"]).to_numpy(dtype=float))
            pred = own_ppp + opp_def_ppp - LEAGUE["ppp"]
            pred += (1 if at_home else -1) * LEAGUE["home_ppp_edge"] / 2
            now = q.loc[(gid, tid)] if (gid, tid) in q.index else pd.Series({"o": 0., "d": 0.})
            other = q.loc[(gid, opp)] if (gid, opp) in q.index else pd.Series({"o": 0., "d": 0.})
            historical_q = q.reindex([(str(x), tid) for x in h["game_id"]]).fillna(0)
            historical_opp_q = q.reindex([(str(x), opp) for x in o["game_id"]]).fillna(0)
            delta = (float(now["o"]) - float(historical_q["o"].mean())) - (
                float(other["d"]) - float(historical_opp_q["d"].mean())
            )
            predicted[tid] = (pred, pred + delta)
            if gid in official_eligible:
                # Official status and player identity are usable only when a
                # historical player row existed before this game date.
                prior = by_player_team.get(tid, players.iloc[:0])
                prior = prior[prior["game_date_et"] < date]
                prior_games = [str(x) for x in h.tail(10)["game_id"]]
                pit_effects[tid] = _pit_minutes_delta(
                    prior, prior_games, official_by_team.get(tid, set()), model
                )
            # Meaningful depletion: a usual 24+ minute player from the last 15 games is absent.
            recent = h.tail(15)
            previous = players[(players["game_id"].isin(recent["game_id"])) & (players["team_id"] == tid)]
            avg = previous.groupby("nba_id")["minutes"].sum() / len(recent)
            stars = avg[avg >= 24.0].index
            if any(float(minutes.get((gid, tid, pid), 0.0)) < 8 for pid in stars):
                depleted = True
        for tid in (home_id, away_id):
            game_row = test[(test["game_id"] == gid) & (test["team_id"] == tid)]
            if len(game_row) != 1:
                continue
            r = game_row.iloc[0]
            actual = float(r["pts"]) / float(r["possessions"])
            e0 = predicted[tid][0] - actual
            e1 = predicted[tid][1] - actual
            base_errors.append(e0)
            candidate_errors.append(e1)
            if depleted:
                depleted_base.append(e0)
                depleted_candidate.append(e1)
            row = {"game_id": gid, "team_id": tid, "depleted": depleted,
                   "baseline_error": e0, "lineup_error": e1}
            if len(pit_effects) == 2:
                own, other = pit_effects[tid], pit_effects[away_id if tid == home_id else home_id]
                # Diagnostic ablations isolate which fitted component contributes to
                # the candidate's held-out error. These are post-hoc diagnostics,
                # NOT independently selected/promotable betting models.
                off_delta, def_delta = own[0], -other[1]
                pit_delta = off_delta + def_delta
                pe = e0 + pit_delta
                oe, de = e0 + off_delta, e0 + def_delta
                pit_base.append(e0)
                pit_candidate.append(pe)
                pit_offense_only.append(oe)
                pit_defense_only.append(de)
                affected = own[2] >= 8 or other[2] >= 8
                if affected:
                    pit_affected_base.append(e0)
                    pit_affected_candidate.append(pe)
                    pit_affected_offense_only.append(oe)
                    pit_affected_defense_only.append(de)
                row.update({"pit_error": pe, "pit_delta_ppp": pit_delta,
                            "pit_offense_only_error": oe, "pit_defense_only_error": de,
                            "pit_offense_delta_ppp": off_delta, "pit_defense_delta_ppp": def_delta,
                            "pit_affected": affected, "pit_removed_minutes": own[2]})
            recs.append(row)
    b, c = _numbers(base_errors), _numbers(candidate_errors)
    db, dc = _numbers(depleted_base), _numbers(depleted_candidate)
    pb, pc = _numbers(pit_base), _numbers(pit_candidate)
    ab, ac = _numbers(pit_affected_base), _numbers(pit_affected_candidate)
    pit_ci = _paired_game_bootstrap_ci(recs, "pit_error")
    affected_ci = _paired_game_bootstrap_ci(recs, "pit_error", affected_only=True)
    diagnostic_ablations = {}
    for name, full, affected, key in (
        ("offense_only", pit_offense_only, pit_affected_offense_only, "pit_offense_only_error"),
        ("defense_only", pit_defense_only, pit_affected_defense_only, "pit_defense_only_error"),
    ):
        diagnostic_ablations[name] = {
            "all": _numbers(full), "affected": _numbers(affected),
            "rmse_gain_vs_baseline": pb["rmse"] - _numbers(full)["rmse"],
            "affected_rmse_gain_vs_baseline": ab["rmse"] - _numbers(affected)["rmse"],
            "gain_ci95_game_clustered": _paired_game_bootstrap_ci(recs, key),
            "affected_gain_ci95_game_clustered": _paired_game_bootstrap_ci(recs, key, affected_only=True),
            "selection_status": "DIAGNOSTIC_ONLY_NOT_PROMOTABLE",
        }
    pit_valid = (pb["n"] > 0 and ab["n"] >= 20
                 and pc["rmse"] < pb["rmse"] and ac["rmse"] < ab["rmse"]
                 and pit_ci[0] > 0 and affected_ci[0] > 0)
    return {
        "training": "2024-25 certified stints only", "holdout": "2025-26 regular season",
        "oracle_minutes_warning": "Actual game minutes are NOT available pregame. This is an upper-bound test.",
        "n_fit_games": model.n_games, "n_fit_stints": model.n_stints,
        "n_fit_players": model.n_players, "baseline": b, "lineup": c,
        "depleted_baseline": db, "depleted_lineup": dc,
        "rmse_gain": b["rmse"] - c["rmse"],
        "t60_pit": {"baseline": pb, "candidate": pc, "affected_baseline": ab, "affected_candidate": ac,
                    "overall_rmse_gain": pb["rmse"] - pc["rmse"],
                    "component_ablations": diagnostic_ablations,
                    "overall_gain_ci95_game_clustered": pit_ci,
                    "affected_rmse_gain": ab["rmse"] - ac["rmse"],
                    "affected_gain_ci95_game_clustered": affected_ci,
                    "status": "RESEARCH_PASS" if pit_valid else "REJECT_OR_INSUFFICIENT",
                    "asof": "latest certified official NBA injury report strictly before tip-minus-60",
                    "identity": "raw official names resolved exclusively against strictly earlier box scores; retrospective backfill IDs ignored",
                    "minutes": "trailing 10 team games, OUT/DOUBTFUL zeroed, minutes redistributed; no actual current minutes"},
        "depleted_rmse_gain": db["rmse"] - dc["rmse"],
        "decision": ("CANDIDATE_FOR_PROSPECTIVE_TEST" if pit_valid and
                     c["rmse"] < b["rmse"] and dc["rmse"] < db["rmse"] else "REJECT_FOR_PRODUCTION"),
        "rows": recs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", type=Path, default=REPO_ROOT / "data" / "history")
    ap.add_argument("--out", type=Path, default=Path("/tmp/nba_injury_lineup_holdout.json"))
    ap.add_argument("--max-games", type=int, default=1300)
    a = ap.parse_args()
    report = run(a.history, max_games=a.max_games)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
