"""Activation readiness of the NBA projection families, judged from the live archive (read-only).

    python -m nba.live.activation_check --archive <projection-data checkout> [--now ISO] [--json OUT] [--strict] [--roster-audit AUDIT.json]

SIFT shows the improved NBA engines (minutes, points, rebounds, assists, threes, PRA, FGA) as its one projection only after the
official NBA injury report has been verified on a REAL slate. This module turns that requirement into checks over the artifacts the
live pipeline already archives, so the answer is evidence, not an opinion, and so a replay or a rehearsal can never stand in for it:

  A  the official report         fetched live from the league host, with its own timestamps; fresh; and carrying PLAYER-LEVEL
                                 designations for a game that has not started (not only "NOT YET SUBMITTED" team rows)
  B  identity                    teams map to the game, report names map to rostered players (no possible identity miss)
  C  status vocabulary           OUT / DOUBTFUL / QUESTIONABLE / PROBABLE / AVAILABLE and unlisted-but-covered are distinguished;
                                 an unreadable status is uncertain (never available) and is reported
  D  availability reaches model  the published rows carry the resolved participation, report-aware P(play) and the report-aware
                                 minutes model; ruled-out players are BLOCK; uncertain / unverified players are REVIEW; eligible
                                 players are not blocked
  E  archive                     the pregame forecasts exist for every game in the window, written before the start, after the
                                 availability they used

Verdicts: READY (every required check PASS), PENDING (no check FAILED but evidence is still missing: waiting on data), BLOCKED
(evidence is present and wrong). Nothing here changes a projection, a gate or a promotion: the promotion is a SIFT decision
(`projectionApprovals.ts`) taken by a person after this reads READY and SIFT's own production-path verification
(`scripts/verify-nba-activation.ts`) agrees.

Thresholds are explicit constants below; they are proposals for the owner to adjust, not statistical results.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

SCHEMA = "sift.nba_activation_check.v1"
FAMILIES = ("minutes", "points", "rebounds", "assists", "threes", "pra", "fga")
OFFICIAL_HOST = "ak-static.cms.nba.com"
OFFICIAL_SOURCE = "nba_official_injury_report"
KNOWN_DESIGNATIONS = ("OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "ACTIVE")
# policy constants (owner-adjustable)
MAX_REPORT_AGE_H = 6.0            # the report the run read was published at most this long before the run
MIN_TEAM_SUBMISSION_SHARE = 0.5   # at least this share of the window's teams have submitted player-level rows
MIN_ELIGIBLE_NOT_BLOCKED = 0.95   # share of eligible (confirmed / likely active) rows whose gate is not BLOCK
MIN_ELIGIBLE_PASS = 0.5           # share of eligible rows that are accepted (clean PASS, or the documented REVIEW below, audited)
# The one REVIEW that D5 accepts as its own, separately reported category ("eligible Low-reliability REVIEW"): the team reconciliation's
# early-season roster-uncertainty review, i.e. ONLY a `team_consistency` / `model_assumption` finding about normalising the team's
# minutes (nba/live/reconcile.py: "Roles carried over from previous teams overlapped; early-season roster uncertainty."), within these
# bounds, for an eligible (confirmed / likely active) player, and ONLY while a roster audit of the same feed found no roster, team or
# availability error (nba/live/roster_audit.py). Any other finding, or the same finding without the audit, is "other REVIEW" and is never accepted.
DOCUMENTED_CHECK = "team_consistency"
DOCUMENTED_CATEGORY = "model_assumption"
MAX_DOCUMENTED_NORMALISATION = 0.25   # the team's minutes were scaled by at least 1 - this (the engine's own hard limit is 0.55)
MAX_AUDIT_AGE_H = 6.0                 # the roster audit was run at most this long before / after the feed it vouches for

PASS, FAIL, PENDING, WARN = "PASS", "FAIL", "PENDING", "WARN"


def _ts(x: str | None) -> datetime | None:
    if not x:
        return None
    d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _json(path: str) -> Any:
    with open(path) as f:
        return json.load(f)


def _jsonl_gz(paths: list[str]) -> list[dict]:
    out = []
    for p in paths:
        with gzip.open(p, "rt") as f:
            out += [json.loads(line) for line in f if line.strip()]
    return out


def check(cid: str, title: str, status: str, why: str, evidence: dict | None = None, required: bool = True) -> dict:
    return {"id": cid, "title": title, "status": status, "required": required, "why": why, "evidence": evidence or {}}


# --------------------------------------------------------------------------------------------------- the checks
def check_official_report(run: dict | None, now: datetime) -> list[dict]:
    cap = (run or {}).get("capture") or {}
    off = (cap.get("sources") or {}).get("official") or {}
    cov = cap.get("coverage") or {}
    games = int(cap.get("games") or 0)
    out: list[dict] = []
    if not run or not cap:
        return [check("A1", "A live capture ran", PENDING, "no pregame capture has been archived yet")]
    live = off.get("status") == "ok" and off.get("via") == "nba_official_live"
    out.append(check("A1", "The official report was fetched live from the league", PASS if live else (FAIL if off.get("status") == "ok" else PENDING),
                     "fetched live" if live else f"official source status {off.get('status')!r} via {off.get('via')!r} (a fallback copy or a failed fetch is not live evidence)",
                     {"status": off.get("status"), "via": off.get("via")}))
    url = str(off.get("url") or "")
    prov = {k: off.get(k) for k in ("url", "report_time_utc", "last_modified_utc", "pdf_sha256")}
    ok_prov = OFFICIAL_HOST in url and all(off.get(k) for k in ("report_time_utc", "last_modified_utc", "pdf_sha256"))
    out.append(check("A2", "Source provenance is recorded (league host, report time, last-modified, content hash)", PASS if ok_prov else (PENDING if not live else FAIL),
                     "league host with report time, last-modified and sha256" if ok_prov else "missing or foreign provenance", prov))
    lm, rt = _ts(off.get("last_modified_utc")), _ts(off.get("report_time_utc"))
    captured = _ts(cap.get("captured_utc"))
    if lm and rt and captured:
        age_h = (captured - lm).total_seconds() / 3600
        fresh = -0.1 <= age_h <= MAX_REPORT_AGE_H and rt <= captured
        out.append(check("A3", f"The report is fresh (published within {MAX_REPORT_AGE_H:g} h of the capture, not from the future)", PASS if fresh else FAIL,
                         f"report published {age_h:.1f} h before the capture", {"age_hours": round(age_h, 2), "report_time_utc": off.get("report_time_utc")}))
    else:
        out.append(check("A3", "The report is fresh", PENDING, "no report timestamps to judge"))
    covered, explicit = int(off.get("games_covered") or 0), int(off.get("official_explicit") or 0)
    nys = int(off.get("not_yet_submitted_rows") or 0)
    teams_missing = int(off.get("teams_not_yet_submitted") or 0)
    n_teams = 2 * games
    submitted_share = (1 - teams_missing / n_teams) if n_teams else 0.0
    covers = games > 0 and covered >= games
    out.append(check("A4", "The report covers every game in the window", PASS if covers else (PENDING if games else PENDING),
                     f"{covered} of {games} games appear on the report" if games else "no game starts inside the window",
                     {"games": games, "games_covered": covered}))
    has_players = explicit > 0 and submitted_share >= MIN_TEAM_SUBMISSION_SHARE
    out.append(check("A5", "Teams have submitted PLAYER-LEVEL designations for games that have not started",
                     PASS if has_players else PENDING,
                     f"{explicit} explicit player designations; {teams_missing} of {n_teams} teams still 'NOT YET SUBMITTED' ({nys} such rows)" if games else "no game in the window",
                     {"explicit_designations": explicit, "teams_not_yet_submitted": teams_missing, "teams_in_window": n_teams,
                      "implicit_available": int(off.get("official_implicit") or 0), "submitted_share": round(submitted_share, 3)}))
    share = cov.get("official_report_game_share")
    out.append(check("A6", "Official coverage of the players being projected", PASS if (share or 0) > 0 and has_players else PENDING,
                     f"{share} of games covered by the official report", {"official_report_game_share": share, "mean_coverage": cov.get("mean_coverage")}, required=False))
    return out


def check_identity(run: dict | None) -> list[dict]:
    off = (((run or {}).get("capture") or {}).get("sources") or {}).get("official") or {}
    if not off.get("official_explicit"):
        return [check("B1", "Report names map to rostered players (no possible identity miss)", PENDING, "no player-level rows to match yet"),
                check("B2", "Report teams map to the game they are listed under", PENDING, "no player-level rows to match yet")]
    misses = int(off.get("possible_identity_misses") or 0)
    unmatched = int(off.get("rows_unmatched_player") or 0)
    explicit = int(off.get("official_explicit") or 0)
    wrong_team = int(off.get("rows_team_not_in_game") or 0)
    return [
        check("B1", "Report names map to rostered players (no possible identity miss)", PASS if misses == 0 else FAIL,
              f"{unmatched} of {explicit + unmatched} designated players are not on the ESPN rosters (expected: two-way / inactive); {misses} share a surname with a rostered teammate"
              + (f": {off.get('possible_identity_miss_names')}" if misses else ""),
              {"explicit": explicit, "unmatched": unmatched, "possible_identity_misses": misses, "names": off.get("possible_identity_miss_names")}),
        check("B2", "Report teams map to the game they are listed under", PASS if wrong_team == 0 else FAIL,
              f"{wrong_team} rows name a team that is not in their game", {"rows_team_not_in_game": wrong_team}),
    ]


def check_vocabulary(run: dict | None) -> list[dict]:
    off = (((run or {}).get("capture") or {}).get("sources") or {}).get("official") or {}
    if not off.get("official_explicit"):
        return [check("C1", "Designations are distinguished: OUT, DOUBTFUL, QUESTIONABLE, PROBABLE, AVAILABLE, unlisted", PENDING, "no player-level rows yet"),
                check("C2", "An unreadable status is uncertain, never available", PENDING, "no player-level rows yet")]
    seen = {k: int(off.get(f"status_{k}") or 0) for k in KNOWN_DESIGNATIONS}
    unknown = int(off.get("rows_unknown_status") or 0)
    return [
        check("C1", "Designations are distinguished: OUT, DOUBTFUL, QUESTIONABLE, PROBABLE, AVAILABLE, unlisted", PASS,
              "observed on this report: " + ", ".join(f"{k} {v}" for k, v in seen.items()) + f"; unlisted-but-covered (implicit available) {int(off.get('official_implicit') or 0)}", seen),
        check("C2", "An unreadable status is uncertain, never available", WARN if unknown else PASS,
              f"{unknown} rows carried a status word the parser does not know; each was read as QUESTIONABLE (REPORTED) and reported" if unknown else "no unreadable status on this report",
              {"rows_unknown_status": unknown}, required=False),
    ]


def _documented_review(p: dict, recon: dict[tuple, dict]) -> bool:
    """Is this REVIEW row's ONLY finding the documented early-season roster-uncertainty review, within bounds? (Pure; no audit here.)"""
    fs = [f for f in p["gate"].get("findings", []) if f.get("severity") != "INFO"]
    if not fs or any(f.get("check") != DOCUMENTED_CHECK or f.get("severity") != "REVIEW" or f.get("category") != DOCUMENTED_CATEGORY
                     or "normalised to the team" not in (f.get("what") or "") for f in fs):
        return False
    r = recon.get((str(p.get("game_id")).replace("espn:", ""), p.get("team")))
    if not r or r.get("status") != "REVIEW":
        return False
    lo = 1 - MAX_DOCUMENTED_NORMALISATION
    return float(r.get("minutes_scale") or 1.0) >= lo and lo <= float(r.get("usage_scale") or 1.0) <= 1 + MAX_DOCUMENTED_NORMALISATION


def audit_accepts(audit: dict | None, doc: dict) -> tuple[bool, str]:
    """May the documented REVIEW be accepted for this feed? Only with a roster audit of the same slate and teams, run close to the feed, with no error."""
    if not audit:
        return False, "no roster audit supplied (--roster-audit)"
    if audit.get("schema") != "sift.nba_roster_audit.v1":
        return False, "the roster audit is not a sift.nba_roster_audit.v1 document"
    if audit.get("slate") != doc.get("slate_date"):
        return False, f"the roster audit is for slate {audit.get('slate')}, the feed for {doc.get('slate_date')}"
    a, g = _ts(audit.get("feed_generated_utc")), _ts(doc.get("generated_utc"))
    if not a or not g or abs((g - a).total_seconds()) / 3600 > MAX_AUDIT_AGE_H:
        return False, f"the roster audit describes a feed from {audit.get('feed_generated_utc')}, not within {MAX_AUDIT_AGE_H:g} h of {doc.get('generated_utc')}"
    teams = {p["team"] for p in doc.get("players", [])}
    if not teams <= set((audit.get("identity") or {})):
        return False, "the roster audit does not cover every team in the feed"
    if "ok" != (audit.get("sources") or {}).get("espn_rosters"):
        return False, "the roster audit could not read the current rosters"
    if int(audit.get("genuine_roster_errors", 1)) != 0:
        return False, f"the roster audit found {audit.get('genuine_roster_errors')} roster / availability error(s)"
    return True, "a roster audit of this slate found no roster, team or availability error"


def eligible_breakdown(doc: dict, audit: dict | None) -> dict:
    """The four D5 categories over eligible (confirmed / likely active) rows, counted separately."""
    elig = [p for p in doc["players"] if p["participation"]["status"] in ("CONFIRMED_ACTIVE", "LIKELY_ACTIVE")]
    recon = {(str(r["game_id"]).replace("espn:", ""), r["team"]): r for r in doc.get("reconciliation", [])}
    ok, why = audit_accepts(audit, doc)
    clean = blocked = documented = other = 0
    for p in elig:
        st = p["gate"]["status"]
        if st == "BLOCK":
            blocked += 1
        elif st == "PASS":
            clean += 1
        elif _documented_review(p, recon):
            documented += 1
        else:
            other += 1
    return {"eligible": len(elig), "clean_pass": clean, "documented_review": documented, "other_review": other, "blocked": blocked,
            "audit_accepts": ok, "audit_why": why}


def check_model_inputs(doc: dict | None, avail: list[dict] | None = None, audit: dict | None = None) -> list[dict]:
    if not doc or not doc.get("players"):
        return [check("D1", "Availability reaches the model", PENDING, "no projection document")]
    rows = doc["players"]
    pts = [p for p in rows if p["family"] == "points"]
    c = Counter(p["participation"]["status"] for p in pts)
    official = [p for p in pts if p["participation"].get("source") == OFFICIAL_SOURCE]
    out: list[dict] = []
    # D1 the resolved participation (and the report-aware P(play)) are on the rows
    recal = [p for p in pts if p["participation"].get("p_play_basis") == "report-recalibrated hurdle"]
    out.append(check("D1", "Rows carry the resolved participation and the report-recalibrated P(play)", PASS if official and len(recal) >= len(official) else PENDING,
                     f"{len(official)} players resolved from the official report; {len(recal)} with report-recalibrated P(play); participation {dict(c)}",
                     {"participation": dict(c), "official_resolved": len(official), "recalibrated": len(recal)}))
    # D2 the report-aware minutes model is used exactly where the report covers the player
    has_einj = lambda p: any("Minutes model: E_inj" in a for a in p.get("adjustments", []))  # noqa: E731
    mins = [p for p in rows if p["family"] == "minutes"]
    wrong = [p["player_id"] for p in mins if has_einj(p) != (p["participation"].get("source") == OFFICIAL_SOURCE)]
    n_einj = sum(has_einj(p) for p in mins)
    out.append(check("D2", "Minutes use the report-aware model exactly where the official report covers the player",
                     PASS if (n_einj and not wrong) else (FAIL if wrong else PENDING),
                     f"{n_einj} minutes rows use E_inj; {len(wrong)} disagree with their participation source" if mins else "no minutes rows",
                     {"einj_rows": n_einj, "disagreeing_rows": wrong[:10]}))
    # D3 ruled-out players are withheld (gate BLOCK) in every family
    outp = [p for p in rows if p["participation"]["status"] in ("CONFIRMED_OUT", "LIKELY_OUT")]
    not_blocked = [(p["player_id"], p["family"]) for p in outp if p["gate"]["status"] != "BLOCK"]
    out.append(check("D3", "Ruled-out players are withheld (gate BLOCK in every family)", FAIL if not_blocked else (PASS if outp else PENDING),
                     f"{len(outp)} rows of ruled-out players; {len(not_blocked)} not blocked" if outp else "no ruled-out player on the slate yet (nothing to withhold)",
                     {"ruled_out_rows": len(outp), "not_blocked": not_blocked[:10]}))
    # D4 uncertain / unverified availability lowers reliability: gate REVIEW, never PASS
    unc = [p for p in rows if p["participation"]["status"] in ("UNCERTAIN", "UNVERIFIED")]
    passed = [(p["player_id"], p["family"]) for p in unc if p["gate"]["status"] == "PASS"]
    out.append(check("D4", "Uncertain or unverified availability is REVIEW (SIFT shows it at Low reliability), never PASS", FAIL if passed else (PASS if unc else PENDING),
                     f"{len(unc)} rows uncertain / unverified; {len(passed)} wrongly PASS" if unc else "no uncertain row yet",
                     {"uncertain_rows": len(unc), "wrongly_pass": passed[:10]}))
    # D5 eligible players are projected and not blocked. Four categories, counted and reported separately; PASS keeps its meaning (the
    # gate said PASS), the 50 % bar is unchanged, and the only REVIEW that counts toward it is the documented, audited one.
    b = eligible_breakdown(doc, audit)
    n = b["eligible"]
    if not n:
        out.append(check("D5", "Eligible (confirmed / likely active) players pass the projection-quality gate", PENDING, "no eligible player on the slate yet"))
    else:
        nb = (n - b["blocked"]) / n
        accepted_with = (b["clean_pass"] + b["documented_review"]) / n
        accepted_without = b["clean_pass"] / n
        accepted = accepted_with if b["audit_accepts"] else accepted_without
        ok = nb >= MIN_ELIGIBLE_NOT_BLOCKED and accepted >= MIN_ELIGIBLE_PASS
        would = nb >= MIN_ELIGIBLE_NOT_BLOCKED and accepted_with >= MIN_ELIGIBLE_PASS
        status = PASS if ok else (PENDING if would and not b["audit_accepts"] else FAIL)
        cats = (f"clean PASS {b['clean_pass']} ({b['clean_pass'] / n:.0%}) · eligible REVIEW, documented early-season roster uncertainty "
                f"{b['documented_review']} ({b['documented_review'] / n:.0%}; Low reliability{'' if b['audit_accepts'] else '; NOT accepted: ' + b['audit_why']}) · "
                f"other REVIEW {b['other_review']} ({b['other_review'] / n:.0%}; never accepted) · BLOCKED {b['blocked']} ({b['blocked'] / n:.0%})")
        out.append(check("D5", "Eligible (confirmed / likely active) players pass the projection-quality gate", status,
                         f"{n} eligible rows: {cats}; {nb:.0%} not blocked (need {MIN_ELIGIBLE_NOT_BLOCKED:.0%}); accepted {accepted:.0%} (need {MIN_ELIGIBLE_PASS:.0%})",
                         {"eligible_rows": n, **{k: b[k] for k in ("clean_pass", "documented_review", "other_review", "blocked")},
                          "not_blocked": round(nb, 3), "pass": round(accepted_without, 3), "accepted": round(accepted, 3),
                          "documented_review_accepted": b["audit_accepts"], "audit": b["audit_why"]}))
    # D7 no archived observation was ignored: a row whose game / player has an observation captured at or before the projection's own
    # time (and before the start) must not be published UNVERIFIED. This is the defect of 2026-10-19T18:52Z (the run's own ESPN capture
    # carried the same whole-second stamp as the projection clock and was excluded by the strictly-before cut-off).
    gen = _ts(doc.get("generated_utc"))
    ignored: list[str] = []
    if avail and gen:
        seen = {(o["event_id"], o["entity_id"]) for o in avail
                if o.get("kind") == "injury" and _ts(o.get("captured_utc")) <= gen and _ts(o.get("captured_utc")) < _ts(o.get("event_start_utc"))}
        ignored = sorted({f"{p['player_id']} {p['name']} ({p['team']})" for p in pts
                          if (p["game_id"], p["player_id"]) in seen and p["participation"]["status"] == "UNVERIFIED"})
    out.append(check("D7", "No archived availability observation was ignored by the projection", FAIL if ignored else (PASS if avail else PENDING),
                     f"{len(ignored)} players have an archived observation taken before the projection yet are published UNVERIFIED: {ignored[:6]}" if ignored
                     else ("every archived observation reached its row" if avail else "no observations archived yet"),
                     {"ignored": ignored[:20]}))
    fam = {p["family"] for p in rows}
    missing = [f for f in FAMILIES if f not in fam]
    ready = {f: (doc.get("families", {}).get(f) or {}).get("readiness") for f in FAMILIES}
    out.append(check("D6", "All seven families are published and READY", PASS if not missing and all(v == "READY" for v in ready.values()) else FAIL,
                     f"missing {missing}; readiness {ready}" if missing or any(v != "READY" for v in ready.values()) else "published and READY", {"readiness": ready}))
    return out


MINUTES_BUDGET = 241.5
MINUTES_TOL = 0.03          # |sum_i p_i x E[min_i | play] / 241.5 - 1| a JRM team may deviate: its construction makes the sum exact; a larger gap is a defect
MINUTES_WARN = 0.05         # frozen engine: normalisation beyond this is reported (it is covered by the D5 policy, not required here)


def minutes_integrity(doc: dict) -> dict:
    """Per team-game: sum of p(play) x E[minutes | play] as published, and whether the publisher normalised minutes to get there."""
    sums: dict[tuple, float] = {}
    for p in doc.get("players") or []:
        if p.get("family") != "minutes":
            continue
        pp = (p.get("participation") or {}).get("p_play")
        if pp is None or p.get("mean") is None:
            continue
        k = (p.get("game_id"), p.get("team"))
        sums[k] = sums.get(k, 0.0) + float(pp) * float(p["mean"])
    scaled = {(r.get("game_id"), r.get("team")): r.get("minutes_scale", 1.0) for r in doc.get("reconciliation") or []
              if "minutes" in str(r.get("action", ""))}
    worst = max(((abs(v / MINUTES_BUDGET - 1), k) for k, v in sums.items()), default=(0.0, None))
    return {"engine": (doc.get("model") or {}).get("minutes_engine", "frozen"), "teams": len(sums), "worst_gap": round(worst[0], 4), "worst_team": worst[1],
            "outside_tol": sorted(f"{k[1]} {v / MINUTES_BUDGET - 1:+.1%}" for k, v in sums.items() if abs(v / MINUTES_BUDGET - 1) > MINUTES_TOL),
            "normalised": sorted(f"{k[1]} x{v}" for k, v in scaled.items()), "scale_range": [min(scaled.values()), max(scaled.values())] if scaled else None}


def check_minutes_integrity(doc: dict | None) -> list[dict]:
    """F1: team minutes add up by construction, not by normalisation. Required when the projection declares the joint rotation model
    (`model.minutes_engine == "jrm"`); for the frozen engine it is reported (WARN when a team needed a normalisation beyond 5%) and not required."""
    title = "Team minutes are structurally coherent: sum of p x E[min | play] = 241.5 per team-game with no minutes normalisation"
    if not doc or not doc.get("players"):
        return [check("F1", title, PENDING, "no projection document", required=False)]
    ev = minutes_integrity(doc)
    if ev["engine"] == "frozen":
        rng = ev["scale_range"]
        warn = bool(rng) and (min(rng) < 1 - MINUTES_WARN or max(rng) > 1 + MINUTES_WARN)
        return [check("F1", title, WARN if warn else PASS,
                      f"frozen engine: {len(ev['normalised'])} team(s) normalised" + (f" (scales {rng[0]:.2f}-{rng[1]:.2f}); allowed by the D5 policy, not by this check" if rng else ""),
                      ev, required=False)]
    bad = ev["outside_tol"] or ev["normalised"]
    return [check("F1", title, FAIL if bad else PASS,
                  (f"{len(ev['outside_tol'])} team(s) outside +-{MINUTES_TOL:.0%} of {MINUTES_BUDGET} and {len(ev['normalised'])} normalised" if bad
                   else f"all {ev['teams']} team-games within +-{MINUTES_TOL:.0%} (worst {ev['worst_gap']:.2%}) and none normalised"), ev, required=True)]


def check_archive(archive: str, doc: dict | None, run: dict | None, now: datetime) -> list[dict]:
    fc_files = sorted(glob.glob(os.path.join(archive, "forecasts", "nba", "*", "*.jsonl.gz")))
    av_files = sorted(glob.glob(os.path.join(archive, "availability", "nba", "*", "*.jsonl.gz")))
    if not fc_files or not doc:
        return [check("E1", "Pregame forecasts are archived for every game in the window, before the start", PENDING, "no forecast archive yet")]
    fc = _jsonl_gz(fc_files)
    games = {g for g in (p["game_id"] for p in doc.get("players", []))}
    late = [r["forecast_id"] for r in fc if _ts(r.get("generated_utc")) >= _ts(r.get("game_start_utc"))]
    archived_games = {r["game_id"] for r in fc if r.get("model_role") == "challenger"}
    missing = sorted(games - archived_games)
    out = [check("E1", "Pregame forecasts are archived for every game in the window, before the start", FAIL if (late or missing) else PASS,
                 f"{len(games)} games projected; {len(archived_games & games)} archived; {len(late)} written at/after the start",
                 {"games": sorted(games), "missing": missing, "late": late[:5]})]
    avail = _jsonl_gz(av_files)
    used = max((_ts(p["participation"].get("captured_utc")) for p in doc["players"] if p["participation"].get("captured_utc")), default=None)
    gen = _ts(doc.get("generated_utc"))
    ok = bool(avail) and (used is None or (gen is not None and used < gen))
    out.append(check("E2", "The availability used was captured and archived before the forecast", PASS if ok else (PENDING if not avail else FAIL),
                     f"{len(avail)} availability observations archived; newest used {used}; forecast generated {gen}", {"observations": len(avail)}))
    return out


# --------------------------------------------------------------------------------------------------- driver
def evaluate(archive: str, now: datetime | None = None, audit: dict | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    rp, pp = os.path.join(archive, "runs", "nba", "latest.json"), os.path.join(archive, "projections", "nba", "latest.json")
    run = _json(rp) if os.path.exists(rp) else None
    doc = _json(pp) if os.path.exists(pp) else None
    av_files = sorted(glob.glob(os.path.join(archive, "availability", "nba", "*", "*.jsonl.gz")))
    avail = _jsonl_gz(av_files) if av_files else []
    checks = check_official_report(run, now) + check_identity(run) + check_vocabulary(run) + check_model_inputs(doc, avail, audit) + check_minutes_integrity(doc) + check_archive(archive, doc, run, now)
    req = [c for c in checks if c["required"]]
    if any(c["status"] == FAIL for c in req):
        verdict = "BLOCKED"
    elif all(c["status"] == PASS for c in req):
        verdict = "READY"
    else:
        verdict = "PENDING"
    remaining = [f"{c['id']}: {c['title']}: {c['why']}" for c in req if c["status"] in (FAIL, PENDING)]
    return {"schema": SCHEMA, "generated_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "verdict": verdict, "families": list(FAMILIES),
            "run_published_utc": (run or {}).get("published_utc"), "projection_generated_utc": (doc or {}).get("generated_utc"),
            "slate_date": (doc or {}).get("slate_date"), "checks": checks, "remaining": remaining,
            "policy": {"max_report_age_h": MAX_REPORT_AGE_H, "min_team_submission_share": MIN_TEAM_SUBMISSION_SHARE,
                       "min_eligible_not_blocked": MIN_ELIGIBLE_NOT_BLOCKED, "min_eligible_pass": MIN_ELIGIBLE_PASS,
                       "documented_review": {"check": DOCUMENTED_CHECK, "category": DOCUMENTED_CATEGORY, "max_normalisation": MAX_DOCUMENTED_NORMALISATION,
                                             "max_audit_age_h": MAX_AUDIT_AGE_H, "needs": "a roster audit (nba/live/roster_audit.py) of the same slate with no error"}},
            "note": "READY means the live evidence supports promotion; the promotion itself is a person's decision in SIFT (projectionApprovals.ts) after "
                    "scripts/verify-nba-activation.ts agrees. A replay, a rehearsal or a dry run on recorded data is not live evidence."}


def markdown(rep: dict) -> str:
    icon = {PASS: "PASS", FAIL: "FAIL", PENDING: "PENDING", WARN: "WARN"}
    lines = [f"## NBA activation readiness: **{rep['verdict']}**", "",
             f"slate {rep.get('slate_date')} · projection {rep.get('projection_generated_utc')} · checked {rep['generated_utc']}", "",
             "| | check | status | evidence |", "|---|---|---|---|"]
    for c in rep["checks"]:
        lines.append(f"| {c['id']} | {c['title']}{'' if c['required'] else ' (info)'} | {icon[c['status']]} | {c['why']} |")
    if rep["remaining"]:
        lines += ["", "**Remaining before activation**", ""] + [f"- {r}" for r in rep["remaining"]]
    lines += ["", f"_{rep['note']}_"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--now", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--strict", action="store_true", help="exit 1 unless the verdict is READY")
    ap.add_argument("--roster-audit", default=None, help="the JSON written by `python -m nba.live.roster_audit --json` for this feed; without it the documented "
                    "early-season REVIEW is not accepted by D5")
    a = ap.parse_args(argv)
    rep = evaluate(a.archive, _ts(a.now) if a.now else None, _json(a.roster_audit) if a.roster_audit else None)
    md = markdown(rep)
    print(md)
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
        with open(a.json, "w") as f:
            json.dump(rep, f, indent=1)
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        with open(summ, "a") as f:
            f.write(md)
    return 0 if (rep["verdict"] == "READY" or not a.strict) else 1


if __name__ == "__main__":
    sys.exit(main())
