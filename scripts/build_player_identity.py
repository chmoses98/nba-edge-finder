"""Build the Kalshi player identity map from historical prop markets and link it to ESPN roster ids.

Inputs : data/history/kalshi/markets_KXNBA{PTS,REB,AST,3PT}.jsonl.gz (custom_strike.basketball_player uuid + title name
         + basketball_team uuid + ticker suffix tricode), data/history/kalshi/kalshi_team_uuids.json,
         data/history/espn/player_games_*.parquet (ESPN athlete ids as negative nba_id + names + team ids),
         optionally the latest context/rosters snapshot from the archive (passed as a JSONL.gz path).
Outputs: data/identity/kalshi_players.json  (uuid -> {name, team_tricodes, n_markets, first/last seen})
         data/identity/players.jsonl        (PlayerRegistry rows: espn id as provisional nba_id, aliases kalshi/espn)
         docs/identity_report.md            (coverage + ambiguities)
Resolution rule: a Kalshi name maps to an ESPN player only when the normalised name is unique within the same team
(by tricode) in the ESPN data; otherwise it is left unresolved and listed for review. No fuzzy matching.
"""

from __future__ import annotations

import ast
import gzip
import json
import sys
from collections import Counter, defaultdict

import pandas as pd

from nba_edge.config import REPO_ROOT
from nba_edge.identity.normalize import normalize_name
from nba_edge.identity.players import PlayerRecord, PlayerRegistry
from nba_edge.identity.teams import registry
from nba_edge.kalshi.contracts import player_name_from_title
from nba_edge.kalshi.ticker import parse_ticker


def main(rosters_jsonl_gz: str | None = None) -> int:
    reg = registry()
    kdir = REPO_ROOT / "data" / "history" / "kalshi"
    players: dict[str, dict] = {}
    for series in ("KXNBAPTS", "KXNBAREB", "KXNBAAST", "KXNBA3PT", "KXNBAPRA"):
        fp = kdir / f"markets_{series}.jsonl.gz"
        if not fp.exists():
            continue
        with gzip.open(fp, "rt") as f:
            for line in f:
                m = json.loads(line)
                cs = m.get("custom_strike")
                if isinstance(cs, str):
                    try:
                        cs = ast.literal_eval(cs)
                    except (ValueError, SyntaxError):
                        cs = {}
                uuid = (cs or {}).get("basketball_player")
                name = player_name_from_title(m.get("title", ""), m.get("yes_sub_title", ""))
                if not uuid or not name:
                    continue
                pt = parse_ticker(m["ticker"], reg.tricodes)
                suffix = pt.market_suffix.upper()
                tri = next((c for c in (pt.away_tricode, pt.home_tricode) if c and suffix.startswith(c)), None)
                rec = players.setdefault(uuid, {"names": Counter(), "tricodes": Counter(), "team_uuids": Counter(), "n_markets": 0, "first_seen": pt.game_date.isoformat() if pt.game_date else None, "last_seen": None})
                rec["names"][name] += 1
                if tri:
                    rec["tricodes"][tri] += 1
                if (cs or {}).get("basketball_team"):
                    rec["team_uuids"][cs["basketball_team"]] += 1
                rec["n_markets"] += 1
                if pt.game_date:
                    d = pt.game_date.isoformat()
                    rec["first_seen"] = min(rec["first_seen"] or d, d)
                    rec["last_seen"] = max(rec["last_seen"] or d, d)
    kalshi_players = {u: {"name": r["names"].most_common(1)[0][0], "name_variants": [n for n, _ in r["names"].most_common(5)], "team_tricodes": [t for t, _ in r["tricodes"].most_common(3)], "team_uuids": [t for t, _ in r["team_uuids"].most_common(2)], "n_markets": r["n_markets"], "first_seen": r["first_seen"], "last_seen": r["last_seen"]} for u, r in players.items()}

    # ESPN side: (team tricode, normalised name) -> set(espn negative ids)
    hist = REPO_ROOT / "data" / "history" / "espn"
    frames = [pd.read_parquet(p) for p in sorted(hist.glob("player_games_*.parquet"))]
    espn_index: dict[tuple[str, str], set[int]] = defaultdict(set)
    espn_names: dict[int, str] = {}
    if frames:
        pg = pd.concat(frames, ignore_index=True)
        last = pg.sort_values("game_date_et").groupby(["nba_id", "team_id"]).tail(1)
        for _, r in last.iterrows():
            try:
                tri = reg.by_id(int(r["team_id"])).tricode
            except KeyError:
                continue
            espn_index[(tri, normalize_name(str(r["player_name"])))].add(int(r["nba_id"]))
            espn_names[int(r["nba_id"])] = str(r["player_name"])
    if rosters_jsonl_gz:
        with gzip.open(rosters_jsonl_gz, "rt") as f:
            for line in f:
                r = json.loads(line)
                try:
                    tri = reg.by_tricode(r.get("team_abbreviation", "")).tricode
                    pid = -int(r["espn_athlete_id"])
                except Exception:  # noqa: BLE001
                    continue
                espn_index[(tri, normalize_name(r.get("full_name") or ""))].add(pid)
                espn_names[pid] = r.get("full_name") or ""

    # link
    registry_rows: list[PlayerRecord] = []
    resolved, ambiguous, unmatched = 0, [], []
    for uuid, kp in kalshi_players.items():
        cands: set[int] = set()
        for tri in kp["team_tricodes"] or [None]:
            for nm in kp["name_variants"]:
                cands |= espn_index.get((tri, normalize_name(nm)), set()) if tri else set()
        if not cands:  # try any team (traded players)
            for nm in kp["name_variants"]:
                for (_tri, n2), ids in espn_index.items():
                    if n2 == normalize_name(nm):
                        cands |= ids
        if len(cands) == 1:
            pid = cands.pop()
            resolved += 1
            registry_rows.append(PlayerRecord(nba_id=pid, full_name=espn_names.get(pid, kp["name"]), aliases={"kalshi_uuid": uuid, "kalshi": kp["name"], "espn": str(-pid)}, active=True, first_seen=kp["first_seen"], last_seen=kp["last_seen"]))
        elif len(cands) > 1:
            ambiguous.append((uuid, kp["name"], sorted(cands)))
        else:
            unmatched.append((uuid, kp["name"], kp["team_tricodes"]))
    out_dir = REPO_ROOT / "data" / "identity"
    (out_dir / "kalshi_players.json").write_text(json.dumps(kalshi_players, indent=1, sort_keys=True))
    registry_obj = PlayerRegistry([])
    for r in registry_rows:
        try:
            registry_obj.add(r)
        except Exception as e:  # noqa: BLE001
            ambiguous.append((r.aliases.get("kalshi_uuid"), r.full_name, [str(e)[:80]]))
    registry_obj.save(out_dir / "players.jsonl")
    rep = [
        "# Player identity report", "", f"Kalshi player uuids seen in 2025-26 props: {len(kalshi_players)}",
        f"Resolved to a unique ESPN id: {resolved}", f"Ambiguous: {len(ambiguous)}", f"Unmatched: {len(unmatched)}", "",
        "## Ambiguous (need manual alias)", "", *[f"- `{u}` {n} → {c}" for u, n, c in ambiguous[:50]], "",
        "## Unmatched (top 50 by market count)", "", *[f"- `{u}` {n} ({','.join(t)})" for u, n, t in sorted(unmatched, key=lambda x: -kalshi_players[x[0]]["n_markets"])[:50]],
    ]
    (REPO_ROOT / "docs" / "identity_report.md").write_text("\n".join(rep) + "\n")
    print("\n".join(rep[:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
