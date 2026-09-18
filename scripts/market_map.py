"""Generate docs/KALSHI_MARKET_MAP.md from the discovery summary + ontology (coverage invariant report)."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from nba_edge.config import REPO_ROOT
from nba_edge.kalshi.ontology import Ontology


def main(out: Path = REPO_ROOT / "docs" / "KALSHI_MARKET_MAP.md") -> int:
    s = json.loads((REPO_ROOT / "data" / "catalog" / "discovery_summary.json").read_text())
    onto = Ontology.load()
    fam_series: dict[str, list[dict]] = defaultdict(list)
    unmapped = []
    support_markets: Counter[str] = Counter()
    support_series: Counter[str] = Counter()
    for r in s["nba_series"]:
        fam = onto.family_for_series(r["ticker"])
        n = sum(r["counts_by_status"].values())
        if fam is None:
            unmapped.append(r["ticker"])
            support_markets["UNRESOLVED"] += n
            support_series["UNRESOLVED"] += 1
            continue
        spec = onto.families[fam]
        fam_series[fam].append(r | {"n": n})
        support_markets[str(spec.support)] += n
        support_series[str(spec.support)] += 1
    L = ["# Kalshi NBA market map", "", f"Discovery run: `{s['discovered_at']}` · ontology `{onto.version}` · {s['n_series_total']} series enumerated on Kalshi · {len(s['nba_series'])} NBA-related series · {s['total_markets']} NBA markets scanned (all lifecycle statuses, live API).", "",
         "Off-season caveat: game/player series had 0 live markets on the discovery date (season starts 2026-10-20; last season's markets are archived to the historical API). Market counts for those families come from the summer-league analogues and from `data/history/kalshi` once the historical pull lands.", "",
         "## Coverage invariant", "", "| support | series | markets (live scan) |", "|---|---:|---:|"]
    for k in ("MODELABLE", "BUILDABLE", "RESEARCH", "UNMODELABLE", "UNRESOLVED"):
        L.append(f"| {k} | {support_series.get(k, 0)} | {support_markets.get(k, 0)} |")
    L += ["", "## Families", ""]
    for support in ("MODELABLE", "BUILDABLE", "RESEARCH", "UNMODELABLE"):
        L += [f"### {support}", ""]
        for fam, spec in onto.families.items():
            if str(spec.support) != support:
                continue
            ser = fam_series.get(fam, [])
            L.append(f"**{fam}** — scope `{spec.scope}`, stat `{spec.stat}`, period `{spec.period}`. {spec.description}")
            if spec.settlement_notes:
                L.append(f"  - settlement: {spec.settlement_notes}")
            if spec.series_patterns:
                L.append(f"  - patterns: `{'`, `'.join(spec.series_patterns)}`")
            if ser:
                L.append("  - series observed: " + ", ".join(f"`{r['ticker']}` ({r['n']})" for r in sorted(ser, key=lambda x: -x['n'])))
            else:
                L.append("  - series observed: none yet (ontology entry ahead of the board)")
            L.append("")
    if unmapped:
        L += ["## UNRESOLVED series (need ontology entries)", ""] + [f"- `{t}`" for t in unmapped]
    L += ["", "## Ticker anatomy (observed)", "", "- Game markets: `KXNBAGAME-26OCT20OKCSAS-SAS` = series, `YYMMMDD` + AWAY + HOME, then the YES team.",
          "- Spreads: `KXNBASPREAD-<event>-DEN16` with `strike_type=greater`, `floor_strike='15.5'` (YES iff team margin > 15.5).",
          "- Totals: `KXNBATOTAL-<event>-200` with `floor_strike='199.5'` (YES iff total > 199.5).",
          "- Season wins: `KXNBAWINS-27UTA-60` with `strike_type=greater_or_equal`, `floor_strike='60'`.",
          "- Entities: `custom_strike.basketball_team` / `basketball_player` carry stable Kalshi UUIDs (mapped in `data/history/kalshi/kalshi_team_uuids.json`).",
          "- `close_time` is not the tip time (observed 3 days after the game); the schedule is authoritative for pregame labelling."]
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out}: {dict(support_markets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
