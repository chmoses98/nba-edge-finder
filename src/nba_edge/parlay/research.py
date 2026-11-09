"""High-payout parlay research (issue #95). RESEARCH_ONLY: paper tickets only, no orders, no RFQ submission.

Rules enforced here:
* a combined price is NEVER invented: ``rfq_price_cents`` is an observed Kalshi Combo/RFQ quote or ``None``. Tickets without
  one are tracked for hit-calibration only and have no P&L; the leg-product price is stored as a labelled reference.
* same-game legs are never multiplied independently: the joint comes from a Gaussian copula with an explicit correlation
  matrix (unknown same-game correlation defaults to a conservative positive value and the ticket says so).
* tickets are frozen append-only before tip with exact legs, quotes, predicted joint probability and a content hash.
* void/push/unsettled legs make a ticket UNRESOLVED, never a loss.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np

from nba_edge.kalshi.fees import taker_fee_cents

DEFAULT_SAME_GAME_RHO = 0.15  # conservative placeholder; replaced by estimated residual correlation when available
TARGET_PAYOUT_USD = 8000.0
_N = NormalDist()


@dataclass(frozen=True)
class Leg:
    ticker: str
    game_id: str
    side: str  # "yes" | "no"
    ask_cents: float
    p_model: float  # probability that THIS SIDE wins
    p_market: float | None = None  # market-implied probability of this side (mid, de-vigged not assumed)
    family: str = ""


@dataclass
class Ticket:
    ticket_id: str
    slate_date_et: str
    frozen_at_utc: str
    first_tip_utc: str
    legs: list[Leg]
    stake_usd: float
    p_joint_model: float
    p_joint_market: float | None
    joint_method: str
    same_game_rho: float | None
    rfq_price_cents: float | None  # observed combo quote per $1 payout contract, in cents; None = no real quote
    rfq_observed_at_utc: str | None
    reference_leg_product_cents: float  # ref only; NOT an executable price
    payout_if_hit_usd: float | None
    breakeven_prob: float | None
    strategy: str = "selective"
    notes: list[str] = field(default_factory=list)

    def content_hash(self) -> str:
        d = asdict(self)
        d.pop("ticket_id")
        return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()


# ---- joint probability with dependence --------------------------------------------------------------


def corr_matrix(legs: list[Leg], rho_same_game: float = DEFAULT_SAME_GAME_RHO, pair_rho: dict[tuple[str, str], float] | None = None) -> np.ndarray:
    """Latent-Gaussian correlation: 0 across games, ``pair_rho[(fam_i, fam_j)]`` (else ``rho_same_game``) within a game.

    The latent correlation is for the *win indicators of the chosen sides*; callers flip the sign of a pair's rho when
    legs are on opposite sides of a positively associated pair.
    """
    n = len(legs)
    m = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            if legs[i].game_id == legs[j].game_id:
                r = rho_same_game
                if pair_rho:
                    r = pair_rho.get((legs[i].family, legs[j].family), pair_rho.get((legs[j].family, legs[i].family), r))
                m[i, j] = m[j, i] = r
    return m


def _nearest_psd(m: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eigh(m)
    w = np.clip(w, 1e-6, None)
    a = v @ np.diag(w) @ v.T
    d = np.sqrt(np.diag(a))
    return a / np.outer(d, d)


def joint_probability(p: list[float], corr: np.ndarray, n_sims: int = 400_000, seed: int = 11) -> float:
    """P(all legs win) under a Gaussian copula. Independent blocks reduce to the exact product; dependent legs are simulated."""
    p = [min(max(x, 1e-9), 1 - 1e-9) for x in p]
    if np.allclose(corr, np.eye(len(p))):
        return float(np.prod(p))
    c = _nearest_psd(corr)
    z = np.random.default_rng(seed).multivariate_normal(np.zeros(len(p)), c, size=n_sims)
    thr = np.array([_N.inv_cdf(x) for x in p])
    return float(np.mean(np.all(z < thr, axis=1)))


def frechet_bounds(p: list[float]) -> tuple[float, float]:
    """Model-free bounds on P(all legs win): [max(0, sum p - (n-1)), min p]."""
    return max(0.0, sum(p) - (len(p) - 1)), min(p)


# ---- economics --------------------------------------------------------------------------------------


def fee_per_contract(price_cents: float) -> float:
    return taker_fee_cents(int(round(price_cents)), 100) / 10000.0


def breakeven_from_price(price_cents: float) -> float:
    """Win probability at which buying at ``price_cents`` (cents per $1 payout) breaks even after one fee."""
    return price_cents / 100.0 + fee_per_contract(price_cents)


def stake_for_payout(price_cents: float, payout_usd: float = TARGET_PAYOUT_USD) -> float:
    return payout_usd * price_cents / 100.0


def tickets_needed(p_true: float, breakeven: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Independent tickets needed for a one-sided test that the ticket win rate exceeds ``breakeven`` with the given power
    if the true rate is ``p_true`` (normal approximation to the binomial). Illustrates why longshot edges are hard to prove."""
    if p_true <= breakeven:
        return math.inf  # type: ignore[return-value]
    za, zb = _N.inv_cdf(1 - alpha), _N.inv_cdf(power)
    num = (za * math.sqrt(breakeven * (1 - breakeven)) + zb * math.sqrt(p_true * (1 - p_true))) ** 2
    return math.ceil(num / (p_true - breakeven) ** 2)


def p_at_least_one_hit(p: float, n: int) -> float:
    return 1.0 - (1.0 - p) ** n


# ---- building, freezing, settling -------------------------------------------------------------------


def build_ticket(legs: list[Leg], slate_date_et: str, frozen_at: datetime, first_tip: datetime, stake_usd: float, *, rfq_price_cents: float | None = None,
                 rfq_observed_at: datetime | None = None, pair_rho: dict[tuple[str, str], float] | None = None, strategy: str = "selective") -> Ticket:
    if frozen_at >= first_tip:
        raise ValueError("a ticket must be frozen strictly before the first tip")
    if rfq_observed_at is not None and rfq_observed_at >= first_tip:
        raise ValueError("RFQ quote is not pre-tip")
    corr = corr_matrix(legs, pair_rho=pair_rho)
    same_game = bool(np.any(corr - np.eye(len(legs))))
    pm = [leg.p_model for leg in legs]
    p_joint = joint_probability(pm, corr)
    mk = [leg.p_market for leg in legs]
    p_mkt = joint_probability([float(x) for x in mk], corr) if all(x is not None for x in mk) else None
    ref = float(np.prod([leg.ask_cents / 100.0 for leg in legs])) * 100.0
    notes = ["reference price is the leg-ask product, NOT an executable combo quote"]
    if rfq_price_cents is None:
        notes.append("NO_RFQ: ticket is calibration-only; no P&L is computed")
    if same_game:
        notes.append("same-game legs: joint from Gaussian copula, not an independent product")
    be = breakeven_from_price(rfq_price_cents) if rfq_price_cents else None
    payout = stake_usd * 100.0 / rfq_price_cents if rfq_price_cents else None
    t = Ticket("", slate_date_et, frozen_at.strftime("%Y-%m-%dT%H:%M:%SZ"), first_tip.strftime("%Y-%m-%dT%H:%M:%SZ"), legs, stake_usd, p_joint, p_mkt,
               "independent_product" if not same_game else "gaussian_copula", DEFAULT_SAME_GAME_RHO if same_game else None, rfq_price_cents,
               rfq_observed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if rfq_observed_at else None, ref, payout, be, strategy, notes)
    t.ticket_id = t.content_hash()[:16]
    return t


def freeze(path: Path, tickets: list[Ticket]) -> Path:
    """Append-only JSONL: refuses to overwrite and refuses to re-freeze an existing ticket id."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite frozen ticket file {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    with open(path, "x") as f:
        for t in tickets:
            if t.ticket_id in seen:
                raise ValueError(f"duplicate ticket {t.ticket_id}")
            seen.add(t.ticket_id)
            f.write(json.dumps({**asdict(t), "content_sha256": t.content_hash()}, sort_keys=True, default=str) + "\n")
    return path


def settle_ticket(t: Ticket, outcomes: dict[str, str]) -> dict[str, Any]:
    """Outcome per ticker is "YES"/"NO"/other. Any non-YES/NO leg (void, push, unsettleable, missing) -> UNRESOLVED."""
    res = []
    for leg in t.legs:
        o = outcomes.get(leg.ticker)
        if o not in ("YES", "NO"):
            return {"ticket_id": t.ticket_id, "status": "UNRESOLVED", "reason": f"leg {leg.ticker} outcome={o}"}
        res.append((o == "YES") == (leg.side == "yes"))
    hit = all(res)
    pnl = None
    if t.rfq_price_cents is not None:
        stake = t.stake_usd + t.stake_usd * fee_per_contract(t.rfq_price_cents) / (t.rfq_price_cents / 100.0)
        pnl = (t.payout_if_hit_usd if hit else 0.0) - stake
    return {"ticket_id": t.ticket_id, "status": "HIT" if hit else "MISS", "legs_won": int(sum(res)), "n_legs": len(res), "net_pnl_usd": pnl}


def evaluate_tickets(tickets: list[Ticket], outcomes: dict[str, str]) -> dict[str, Any]:
    """Totals, hit frequency and calibration of the predicted joint probability, by strategy, with explicit denominators."""
    by: dict[str, dict[str, Any]] = {}
    for t in tickets:
        s = settle_ticket(t, outcomes)
        a = by.setdefault(t.strategy, {"tickets": 0, "resolved": 0, "unresolved": 0, "hits": 0, "priced_by_rfq": 0, "stake_usd": 0.0, "payout_usd": 0.0,
                                       "net_pnl_usd": 0.0, "sum_p_joint": 0.0, "brier_joint": 0.0, "sum_p_joint_market": 0.0, "n_market": 0})
        a["tickets"] += 1
        if s["status"] == "UNRESOLVED":
            a["unresolved"] += 1
            continue
        y = 1.0 if s["status"] == "HIT" else 0.0
        a["resolved"] += 1
        a["hits"] += int(y)
        a["sum_p_joint"] += t.p_joint_model
        a["brier_joint"] += (t.p_joint_model - y) ** 2
        if t.p_joint_market is not None:
            a["sum_p_joint_market"] += t.p_joint_market
            a["n_market"] += 1
        if s["net_pnl_usd"] is not None:
            a["priced_by_rfq"] += 1
            a["stake_usd"] += t.stake_usd
            a["payout_usd"] += t.payout_if_hit_usd if y else 0.0
            a["net_pnl_usd"] += s["net_pnl_usd"]
    for a in by.values():
        n = a["resolved"]
        a["hit_rate"] = a["hits"] / n if n else None
        a["expected_hits_model"] = a["sum_p_joint"]
        a["expected_hits_market_joint"] = a["sum_p_joint_market"] if a["n_market"] else None
        a["verdict"] = "INSUFFICIENT_EVIDENCE" if (n < 200 or a["hits"] < 5) else "DESCRIPTIVE_ONLY"  # never PROFITABLE from tickets alone
    return by
