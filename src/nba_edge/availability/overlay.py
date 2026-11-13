"""Point-in-time availability overlay for ``pure_forecast.v1`` player projections (RESEARCH_ONLY).

The frozen shadow arms (``sim_rotation``, ``ewm5``) take participation from the team's recent games and
never read an injury report (``PARTICIPATION_SOURCE = proxy_recent_team_games_no_injury_report``). This
module post-processes their rows with the official NBA injury report as it stood at the projection's own
``as_of``. It never edits the frozen arms; it emits new rows under a separate model version.

Rules (all inputs strictly ``effective_utc <= as_of``):

1. Resolve each player's status from the LATEST official-report snapshot for (game, team):
   an explicit status (OUT / DOUBTFUL / QUESTIONABLE / PROBABLE / ACTIVE), or ``unlisted`` when the
   player is on the report's implied roster (ESPN team rosters fetched at capture) but not listed. A player
   missing from a covered team's snapshot is suppressed as ``not_on_roster`` ONLY with positive roster
   evidence (:meth:`AvailabilityIndex.roster_evidence`): he appears on another team's roster, or he was on this
   team's roster earlier and has been dropped. On the opponent's roster for the same game (stale projection
   team) -> ``team_mismatch``; never on any roster -> ``roster_unconfirmed``; both keep the baseline.
   Every record is usable only from :func:`effective_utc` (the later of its capture and its snapshot write).
2. Teams without an official snapshot yet fall back to the latest ESPN injury capture (OUT, QUESTIONABLE);
   otherwise the status is ``unknown`` and the baseline is untouched. ESPN statuses are unverified (as in the
   live path, PR #101): an ESPN-only OUT is never suppressed, it is capped like an official QUESTIONABLE
   (16% of ESPN-only OUT players in the 2026-27 replay played).
3. Participation: ``out`` / ``not_on_roster`` / ``doubtful`` -> 0; ``questionable`` / ``probable`` capped at
   the W2 DEV-fitted appearance rates (``docs/research/w2_nba_participation/pi_dev_fit.json``, fitted on
   2025-26 only, so out-of-sample for 2026-27). Everything else keeps the baseline probability.
4. OPTIONAL (``redistribute=True``, off by default): freed expected minutes ``(p - p') * E[min | play]`` of
   recent regulars (baseline p >= ``REGULAR_P``) are handed to the team's remaining players in proportion to
   their expected minutes (W2 ``pit_prop``), capped at 48 conditional minutes. The 2026-27 replay
   (``docs/research/AVAILABILITY_OVERLAY_REPLAY.md``) found no conditional-accuracy gain from it, so the
   default leaves teammates' conditional distributions untouched. A recipient's
   conditional stat distributions are scaled by its minutes ratio ``k`` (per-minute rates unchanged).

Rows for players with ``p' == 0`` are suppressed (no prop forecast should be priced for them); they are
returned in the audit, never silently dropped.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

OVERLAY_VERSION = "pit-availability-overlay-v1"
MAX_MINUTES = 48.0
MIN_ROSTER_SNAPSHOT = 8  # a team snapshot with fewer players is treated as incomplete (not covered)
# Only minutes freed by a recent regular (baseline P(play) >= REGULAR_P, i.e. newly ruled out) are handed on.
# A low baseline P(play) means the player has already been missing from recent team games, so teammates'
# recent-history projections already absorb his minutes; redistributing them again double-counts. Chosen on
# the replay's DEV window (games before 2026-11-01) and held fixed for the later holdout games.
REGULAR_P = 0.8

# W2 DEV fit (2025-26, T-60), docs/research/w2_nba_participation/pi_dev_fit.json. Not refitted here.
PI_W2 = {"doubtful": 0.0, "questionable": 0.5881, "probable": 0.9327}
REMOVED = ("out", "not_on_roster", "doubtful")
OFFICIAL = "nba_official_injury_report"
ESPN = "espn_injuries"


def espn_pid(entity_id: str) -> str:
    """``espn:4431767`` -> the shadow store's player id ``-4431767``."""
    return "-" + str(entity_id).split(":", 1)[-1].lstrip("-")


@dataclass(frozen=True)
class Status:
    status: str  # out | not_on_roster | doubtful | questionable | probable | available | unlisted | team_mismatch
    #              | roster_unconfirmed | unknown
    source: str  # official | official_roster | roster_moved | roster_dropped | espn | none
    captured_utc: str | None = None


def effective_utc(r: dict[str, Any]) -> str:
    """When a record became usable: its own ``captured_utc``, or the time its snapshot file was written if later.

    The availability producer stamps implicit-roster rows with the official report's fetch time, but builds them
    from rosters fetched at capture time; when it reuses an older report (PIT fallback) the roster evidence would
    otherwise appear hours before it existed. ``x_available_utc`` is the snapshot write time (set by the loader)."""
    t = r["captured_utc"]
    w = r.get("x_available_utc")
    return w if w and w > t else t


class AvailabilityIndex:
    """``sift.availability.v1`` records indexed for point-in-time lookups (on :func:`effective_utc`)."""

    def __init__(self, records: Iterable[dict[str, Any]]):
        # (event, team) -> {effective_utc: {pid: record}}
        self._off: dict[tuple[str, str], dict[str, dict[str, dict]]] = defaultdict(lambda: defaultdict(dict))
        self._espn: dict[str, dict[str, dict[str, dict]]] = defaultdict(lambda: defaultdict(dict))
        # pid -> [(effective_utc, team)] from every official roster snapshot (implicit or explicit rows)
        self._roster_hist: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._event_teams: dict[str, set[str]] = defaultdict(set)
        for r in records:
            if r.get("kind", "injury") != "injury":
                continue
            t = effective_utc(r)
            matched = str(r["entity_id"]).startswith("espn:")
            pid = espn_pid(r["entity_id"])
            if r.get("source") == OFFICIAL:
                self._off[(r["event_id"], r["team"])][t][pid] = r
                self._event_teams[r["event_id"]].add(r["team"])
                if matched:
                    self._roster_hist[pid].append((t, r["team"]))
            elif r.get("source") == ESPN:
                self._espn[r["event_id"]][t][pid] = r
        self._off_times = {k: sorted(v) for k, v in self._off.items()}
        self._espn_times = {k: sorted(v) for k, v in self._espn.items()}
        for v in self._roster_hist.values():
            v.sort()

    @staticmethod
    def _latest(times: list[str] | None, as_of: str) -> str | None:
        best = None
        for t in times or ():
            if t <= as_of:
                best = t
            else:
                break
        return best

    def team_snapshot(self, event_id: str, team: str, as_of: str) -> tuple[str, dict[str, dict]] | None:
        t = self._latest(self._off_times.get((event_id, team)), as_of)
        if t is None:
            return None
        snap = self._off[(event_id, team)][t]
        return (t, snap) if len(snap) >= MIN_ROSTER_SNAPSHOT else None

    def roster_evidence(self, event_id: str, team: str, player_id: str, as_of: str) -> str:
        """Why a player is missing from his projected team's latest snapshot, from roster snapshots <= as_of only.

        opponent    on the OTHER team's snapshot for this very game: the projection has a stale team; he is in the game
        moved       his latest roster appearance anywhere is with another team (trade, signing elsewhere)
        dropped     he was on this team's roster earlier and is no longer (waived, assignment, released)
        unconfirmed never seen on any roster snapshot: no positive evidence either way (e.g. ESPN roster lag)"""
        for opp in self._event_teams.get(event_id, ()):
            if opp != team:
                snap = self.team_snapshot(event_id, opp, as_of)
                if snap is not None and player_id in snap[1]:
                    return "opponent"
        hist = [(t, tm) for t, tm in self._roster_hist.get(player_id, ()) if t <= as_of]
        if not hist:
            return "unconfirmed"
        return "moved" if hist[-1][1] != team else "dropped"

    def status(self, event_id: str, team: str, player_id: str, as_of: str) -> Status:
        snap = self.team_snapshot(event_id, team, as_of)
        if snap is not None:
            t, rows = snap
            r = rows.get(player_id)
            if r is None:
                ev = self.roster_evidence(event_id, team, player_id, as_of)
                if ev in ("moved", "dropped"):
                    return Status("not_on_roster", f"roster_{ev}", t)
                return Status("team_mismatch" if ev == "opponent" else "roster_unconfirmed", "official_roster", t)
            if r.get("certainty") != "REPORTED":
                return Status("unlisted", "official", t)
            s = str(r["status"]).lower()
            return Status("available" if s == "active" else s, "official", t)
        t = self._latest(self._espn_times.get(event_id), as_of)
        if t is not None:
            r = self._espn[event_id][t].get(player_id)
            if r is not None and str(r["status"]).upper() in ("OUT", "QUESTIONABLE"):
                return Status(str(r["status"]).lower(), "espn", t)
        return Status("unknown", "none", None)

    def first_out_after(self, event_id: str, team: str, player_id: str, after: str, until: str) -> str | None:
        """First official capture in (after, until] that lists the player OUT/DOUBTFUL or shows positive roster
        evidence of his absence: used only by the replay to label late scratches. Never used to build a forecast."""
        for t in self._off_times.get((event_id, team), ()):
            if after < t <= until:
                snap = self._off[(event_id, team)][t]
                if len(snap) < MIN_ROSTER_SNAPSHOT:
                    continue
                r = snap.get(player_id)
                if r is None:
                    if self.roster_evidence(event_id, team, player_id, t) in ("moved", "dropped"):
                        return t
                elif r.get("certainty") == "REPORTED" and str(r["status"]).upper() in ("OUT", "DOUBTFUL"):
                    return t
        return None


def adjusted_participation(p: float, st: Status, pi: dict[str, float] = PI_W2) -> float:
    if st.source == "espn":
        return min(p, pi["questionable"])
    if st.status in ("out", "not_on_roster"):
        return 0.0
    if st.status in pi:
        return min(p, pi[st.status])
    return p


# ---------------------------------------------------------------------------- distribution helpers
def _survival_knots(proj: dict[str, Any]) -> list[tuple[float, float]]:
    """Monotone (x, P(X >= x)) knots from thresholds, extended with quantiles outside the rung grid."""
    thr = sorted((float(t["at_least"]), float(t["probability"])) for t in proj.get("thresholds", ()))
    qs = sorted((float(q["value"]), 1.0 - float(q["q"])) for q in proj.get("quantiles", ()))
    lo = thr[0][0] if thr else math.inf
    hi = thr[-1][0] if thr else -math.inf
    knots = [(x, s) for x, s in qs if x < lo or x > hi] + thr
    knots.sort()
    out: list[tuple[float, float]] = []
    for x, s in knots:  # enforce non-increasing survival
        if out and x == out[-1][0]:
            out[-1] = (x, min(out[-1][1], s))
            continue
        out.append((x, min(s, out[-1][1]) if out else s))
    return out


def survival(knots: list[tuple[float, float]], x: float) -> float:
    if not knots:
        return float("nan")
    if x <= knots[0][0]:
        x0, s0 = knots[0]
        return s0 if x0 <= 0 else min(1.0, s0 + (1.0 - s0) * (x0 - x) / x0)
    for (x0, s0), (x1, s1) in zip(knots, knots[1:]):
        if x <= x1:
            return s0 + (s1 - s0) * (x - x0) / (x1 - x0)
    return knots[-1][1]


def scale_projection(proj: dict[str, Any], k: float, cap: float | None = None) -> dict[str, Any]:
    """Distribution of ``k * X`` (optionally capped): quantiles scaled, P(kX >= r) = P(X >= r / k)."""
    if k == 1.0:
        return proj
    knots = _survival_knots(proj)
    out = dict(proj)

    def sc(v: float) -> float:
        v = v * k
        return min(v, cap) if cap is not None else v

    out["quantiles"] = [dict(q, value=round(sc(float(q["value"])), 4)) for q in proj.get("quantiles", ())]
    out["thresholds"] = [dict(t, probability=round(survival(knots, float(t["at_least"]) / k)
                                                  if cap is None or float(t["at_least"]) <= cap else 0.0, 4))
                         for t in proj.get("thresholds", ())]
    for key in ("mean", "median", "p10", "p90"):
        if key in proj and proj[key] is not None:
            out[key] = round(sc(float(proj[key])), 4)
    return out


# ---------------------------------------------------------------------------- the overlay
@dataclass
class PlayerDecision:
    game_id: str
    team: str
    player_id: str
    status: Status
    p_base: float
    p_new: float
    cond_minutes_base: float
    cond_minutes_new: float
    as_of: str = ""
    kickoff: str = ""
    k: float = 1.0
    suppressed: bool = False
    notes: list[str] = field(default_factory=list)


def apply_overlay(
    rows: list[dict[str, Any]],
    index: AvailabilityIndex,
    team_tricode: dict[int, str],
    pi: dict[str, float] = PI_W2,
    redistribute: bool = False,
    regular_p: float = REGULAR_P,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], PlayerDecision]]:
    """Apply the overlay to one arm's rows for one as_of capture (conditional + unconditional, all stats).

    Returns (new rows without suppressed players, decisions keyed by (game_id, player_id))."""
    by_player: dict[tuple[str, str], dict[tuple[bool, str], dict]] = defaultdict(dict)
    for r in rows:
        by_player[(r["game_id"], str(r["player_id"]))][(bool(r["conditional_on_playing"]), r["statistic"])] = r

    decisions: dict[tuple[str, str], PlayerDecision] = {}
    teams: dict[tuple[str, int], list[tuple[str, str]]] = defaultdict(list)
    for key, d in by_player.items():
        um, cm = d.get((False, "minutes")), d.get((True, "minutes"))
        if um is None or cm is None:
            continue
        gid, pid = key
        tid = int(um["x_team_id"])
        tri = team_tricode.get(tid, "")
        p = float(um.get("participation_probability") or 0.0)
        st = index.status(gid, tri, pid, um["as_of"]) if tri else Status("unknown", "none")
        if um["as_of"] >= um["kickoff"]:
            raise ValueError(f"projection as_of {um['as_of']} is not before kickoff {um['kickoff']}")
        p2 = adjusted_participation(p, st, pi)
        c = float(cm["projection"]["mean"])
        decisions[key] = PlayerDecision(gid, tri, pid, st, p, p2, c, c, as_of=um["as_of"], kickoff=um["kickoff"],
                                        suppressed=p2 <= 0.0)
        teams[(gid, tid)].append(key)

    if redistribute:
        for members in teams.values():
            freed = sum((decisions[m].p_base - decisions[m].p_new) * decisions[m].cond_minutes_base
                        for m in members if decisions[m].p_base >= regular_p)
            for _ in range(5):  # hand out, re-handing what the 48-minute cap clips
                recips = [m for m in members if decisions[m].p_new > 0 and decisions[m].cond_minutes_new < MAX_MINUTES]
                w = {m: decisions[m].p_new * decisions[m].cond_minutes_new for m in recips}
                tot = sum(w.values())
                if freed <= 1e-9 or tot <= 0:
                    break
                left = 0.0
                for m in recips:
                    dec = decisions[m]
                    add_cond = freed * w[m] / tot / dec.p_new
                    new = dec.cond_minutes_new + add_cond
                    if new > MAX_MINUTES:
                        left += (new - MAX_MINUTES) * dec.p_new
                        new = MAX_MINUTES
                    dec.cond_minutes_new = new
                freed = left
            for m in members:
                dec = decisions[m]
                if dec.cond_minutes_base > 0 and dec.p_new > 0:
                    dec.k = dec.cond_minutes_new / dec.cond_minutes_base

    out: list[dict[str, Any]] = []
    for key, d in by_player.items():
        dec = decisions.get(key)
        for (cond, stat), r in d.items():
            if dec is None:
                out.append(r)
                continue
            if dec.suppressed:
                continue
            nr = dict(r)
            proj = scale_projection(r["projection"], dec.k, cap=MAX_MINUTES if stat == "minutes" else None)
            if not cond:
                proj = _unconditional_from(d.get((True, stat)), proj, dec, cap=MAX_MINUTES if stat == "minutes" else None)
                nr["participation_probability"] = round(dec.p_new, 4)
            nr["projection"] = proj
            nr["model_version"] = f"{r['model_version']}+{OVERLAY_VERSION}"
            nr["x_availability"] = {"status": dec.status.status, "source": dec.status.source,
                                    "captured_utc": dec.status.captured_utc, "p_base": round(dec.p_base, 4),
                                    "p_new": round(dec.p_new, 4), "minutes_scale": round(dec.k, 4)}
            out.append(nr)
    return out, decisions


def _unconditional_from(cond_row: dict | None, uproj_scaled: dict, dec: PlayerDecision, cap: float | None) -> dict:
    """Rebuild an unconditional projection as the mixture (1 - p') * 0 + p' * conditional'."""
    if cond_row is None or (dec.p_new == dec.p_base and dec.k == 1.0):
        return uproj_scaled
    cproj = scale_projection(cond_row["projection"], dec.k, cap=cap)
    knots = _survival_knots(cproj)
    p = dec.p_new
    out = dict(uproj_scaled)
    out["mean"] = round(p * float(cproj["mean"]), 4)
    out["thresholds"] = [dict(t, probability=round(p * survival(knots, float(t["at_least"])), 4))
                         for t in uproj_scaled.get("thresholds", ())]
    qs = []
    for q in uproj_scaled.get("quantiles", ()):
        qq = float(q["q"])
        qs.append(dict(q, value=round(_cond_quantile(knots, cproj, (qq - (1 - p)) / p), 4) if qq > 1 - p else 0.0))
    out["quantiles"] = qs
    by_q = {round(float(q["q"]), 4): q["value"] for q in qs}
    for key, qv in (("median", 0.5), ("p10", 0.1), ("p90", 0.9)):
        if key in out and qv in by_q:
            out[key] = by_q[qv]
    return out


def _cond_quantile(knots: list[tuple[float, float]], cproj: dict, u: float) -> float:
    """Quantile of the conditional distribution at level u, interpolated on its own quantile grid."""
    pts = sorted((float(q["q"]), float(q["value"])) for q in cproj.get("quantiles", ()))
    if not pts:
        return float(cproj["mean"])
    if u <= pts[0][0]:
        return pts[0][1]
    for (q0, v0), (q1, v1) in zip(pts, pts[1:]):
        if u <= q1:
            return v0 + (v1 - v0) * (u - q0) / (q1 - q0)
    return pts[-1][1]
