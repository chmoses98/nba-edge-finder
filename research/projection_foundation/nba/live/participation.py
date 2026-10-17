"""Resolve availability observations into the participation published with every projection, plus P(play).

Combines the per-source observations as of the cut-off (never after the event start, never after the run time):

  official explicit designation (REPORTED)  >  newer ESPN OUT/DOUBTFUL (PROJECTED)  >  ESPN designation  >
  official implicit "not listed" (PROJECTED)  >  nothing -> UNVERIFIED.

Conflicts are never resolved silently toward "active": an ESPN OUT that the official report that covers the game does not
list (and that is not newer than the report) becomes UNCERTAIN with the reason spelled out. A PROJECTED OUT is LIKELY_OUT,
not CONFIRMED_OUT (pf_core reserves CONFIRMED_OUT for CONFIRMED/REPORTED exclusions).

P(play) is the frozen LightGBM hurdle recalibrated with the official designation exactly as the study did on 2025-26
(logistic regression on logit(hurdle) + status dummies; Brier 0.132 -> 0.087 on the held-out second half). The coefficients
are fitted once by `fit_participation.py` and frozen in `participation_calibration.json`. When there is no observation the
raw hurdle is published and the row is labelled UNVERIFIED; a CONFIRMED starter is published at 0.995.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Iterable

import numpy as np

from pf_core import availability as av

from .availability import SRC_ESPN_INJ, SRC_OFFICIAL, SRC_STARTERS
from .sources import iso, parse_ts

CALIB_PATH = os.path.join(os.path.dirname(__file__), "participation_calibration.json")
CLASSES = ("OUT", "DOUBTFUL", "QUESTIONABLE", "PROBABLE", "AVAILABLE")
CONFIRMED_STARTER_P = 0.995


def load_calibration(path: str = CALIB_PATH) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def calibrated_p_play(p_hurdle, cls: list[str | None], calib: dict) -> np.ndarray:
    """Vectorised: report-aware P(play). Rows whose class is None keep the raw hurdle probability."""
    p = np.clip(np.asarray(p_hurdle, float), 0.01, 0.99)
    z = np.log(p / (1 - p)) * calib["coef"]["logit"] + calib["intercept"]
    for k in CLASSES:
        z = z + calib["coef"][k] * np.array([c == k for c in cls], float)
    out = 1.0 / (1.0 + np.exp(-z))
    cl = np.array([c is None for c in cls])
    out[cl] = np.asarray(p_hurdle, float)[cl]
    conf = np.array([c == "STARTER_CONFIRMED" for c in cls])
    out[conf] = CONFIRMED_STARTER_P
    return out


def _latest_by(rows: Iterable[dict], cutoff: str, event_id: str, pred) -> dict[tuple, dict]:
    return av.asof([r for r in rows if pred(r)], cutoff, event_id)


def resolve_event(rows: list[dict], event_id: str, start_utc: str, entities: Iterable[str], now: datetime,
                  stale_minutes: float = 24 * 60) -> dict[str, dict]:
    """Participation for every entity of one event as of min(now, start). `rows` = availability rows (dicts)."""
    cutoff = iso(min(now, parse_ts(start_utc)))
    ev_rows = [r for r in rows if r["event_id"] == event_id]
    off = _latest_by(ev_rows, cutoff, event_id, lambda r: r["source"] == SRC_OFFICIAL and r["kind"] == "injury"
                     and not (r.get("detail") or {}).get("implicit"))
    imp = _latest_by(ev_rows, cutoff, event_id, lambda r: r["source"] == SRC_OFFICIAL and r["kind"] == "injury"
                     and (r.get("detail") or {}).get("implicit"))
    esp = _latest_by(ev_rows, cutoff, event_id, lambda r: r["source"] == SRC_ESPN_INJ and r["kind"] == "injury")
    stt = _latest_by(ev_rows, cutoff, event_id, lambda r: r["kind"] == "starter")
    res = _latest_by(ev_rows, cutoff, event_id, lambda r: r["kind"] == "restriction")
    out: dict[str, dict] = {}
    for ent in entities:
        O, I, E = off.get((event_id, ent, "injury")), imp.get((event_id, ent, "injury")), esp.get((event_id, ent, "injury"))
        S, R = stt.get((event_id, ent, "starter")), res.get((event_id, ent, "restriction"))
        notes: list[str] = []
        chosen = None
        upd = lambda r: parse_ts(r.get("source_updated_utc") or r["captured_utc"])  # noqa: E731
        if O:
            chosen = O
            if E and E["status"] in ("OUT", "DOUBTFUL") and O["status"] not in ("OUT", "DOUBTFUL") and \
                    E.get("source_updated_utc") and upd(E) > upd(O):
                chosen = E
                notes.append(f"ESPN reports {E['status']} after the official report ({O['status']}); newer news wins")
        elif E:
            chosen = E
            if I and E["status"] in ("OUT", "DOUBTFUL") and not (E.get("source_updated_utc") and upd(E) > upd(I)):
                chosen = dict(E, status="QUESTIONABLE", detail=dict(E.get("detail") or {}, conflict=True))
                notes.append(f"conflict: ESPN lists {E['status']} (entry {E.get('source_updated_utc')}) but the official report "
                             "covering the game does not list the player; treated as uncertain")
        elif I:
            chosen = I
        latest: dict[tuple, dict] = {}
        if chosen:
            latest[(event_id, ent, "injury")] = chosen
        if S:
            latest[(event_id, ent, "starter")] = S
        part = av.resolve_participation(latest, event_id, ent, cutoff, stale_minutes=stale_minutes)
        if chosen and chosen["status"] == "OUT" and chosen["certainty"] == "PROJECTED":
            part = av.Participation(av.LIKELY_OUT, "PROJECTED", chosen["source"], chosen["captured_utc"], part.age_minutes,
                                    [f"{chosen['source']}: OUT (aggregator report, not the official designation)"])
        cls = None
        if part.status == av.CONFIRMED_ACTIVE:
            cls = "STARTER_CONFIRMED"
        elif chosen:
            cls = {"ACTIVE": "AVAILABLE"}.get(chosen["status"], chosen["status"])
            if cls not in CLASSES:
                cls = None
        implicit = bool(chosen and (chosen.get("detail") or {}).get("implicit"))
        reasons = notes + list(part.reasons)
        if implicit:
            reasons.append("not listed on the official injury report that covers the game (treated as available, PROJECTED)")
        if S and S["status"] == "STARTING":
            reasons.append(f"{S['source']}: listed as a starter ({S['certainty'].lower()})")
        d = {"status": part.status, "certainty": part.certainty, "source": part.source, "captured_utc": part.captured_utc,
             "age_minutes": None if part.age_minutes is None else round(part.age_minutes, 1), "reasons": reasons,
             "designation": chosen["status"] if chosen else None, "implicit": implicit, "_class": cls,
             "gate_injury_status": part.gate_injury_status()}
        if R:
            d["restriction"] = {"minutes_cap": (R.get("detail") or {}).get("minutes_cap"), "source": R["source"],
                                "certainty": R["certainty"], "text": (R.get("detail") or {}).get("text")}
        out[ent] = d
    return out
