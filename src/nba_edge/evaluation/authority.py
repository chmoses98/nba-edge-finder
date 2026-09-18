"""Authority ledger: how much a model family has EARNED the right to influence money.

Stages (``nba_edge.schemas.prediction.Authority``) are assigned per family from prospective evidence only:

* RESEARCH  - default. Nothing has been proven.
* SHADOW    - at least ``SHADOW_MIN_N`` (100) pregame predictions have settled. Still zero money.
* LIMITED   - at least ``LIMITED_MIN_N`` (300) settled AND Brier skill vs the market > 0 AND mean CLV > 0
              AND ECE < ``MAX_ECE`` (0.05).
* TRUSTED   - at least ``TRUSTED_MIN_N`` (1000) settled AND the LIMITED conditions AND the lower bound of a
              95% bootstrap CI on Brier skill vs market is > 0.

These thresholds are CONSERVATIVE PLACEHOLDERS. They are to be tuned only by prospective evidence gathered
by running the model live in SHADOW/LIMITED against real closing lines and real settlements. They must never be
tuned on, or satisfied by, backtests: a backtest can be re-run until it passes, a prospective ledger cannot.
Only rows with ``pregame=True`` count; in-game predictions are excluded from every statistic here.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import numpy as np

from nba_edge.evaluation.metrics import brier, brier_skill_score, ece, log_loss
from nba_edge.schemas.core import Strict
from nba_edge.schemas.prediction import Authority

SHADOW_MIN_N = 100
LIMITED_MIN_N = 300
TRUSTED_MIN_N = 1000
MAX_ECE = 0.05
BOOTSTRAP_ALPHA = 0.05


class EvaluationRow(Strict):
    """One settled prediction joined with its outcome, market baseline and CLV."""

    family: str
    ticker: str
    p: float  # our pregame probability of YES
    y: int  # realized outcome, 1 = YES, 0 = NO (VOID/PUSH/UNSETTLEABLE rows must not be added)
    p_market: float | None = None  # market implied probability at prediction time (same instant as p)
    clv: float | None = None  # closing-line value in probability units, signed for the side we favoured
    pregame: bool = True


def bootstrap_ci(
    stat: Callable[..., float],
    *arrays: np.ndarray,
    n_boot: int = 1000,
    alpha: float = BOOTSTRAP_ALPHA,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap CI for ``stat(*arrays)`` resampling rows jointly. Returns ``(lo, hi)``."""
    arrs = [np.asarray(a) for a in arrays]
    n = arrs[0].shape[0]
    if any(a.shape[0] != n for a in arrs):
        raise ValueError("all arrays must share the first dimension")
    if n == 0:
        raise ValueError("empty input")
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        vals[i] = stat(*(a[idx] for a in arrs))
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))


def _finite_or_none(x: float | None) -> float | None:
    return None if x is None or not np.isfinite(x) else float(x)


class AuthorityLedger:
    """Accumulates ``EvaluationRow`` records and reports per-family evidence plus the earned stage."""

    def __init__(self, rows: Iterable[EvaluationRow] = (), n_boot: int = 1000, seed: int = 0):
        self._rows: list[EvaluationRow] = []
        self.n_boot = n_boot
        self.seed = seed
        self.extend(rows)

    def add(self, row: EvaluationRow) -> None:
        if row.pregame:
            self._rows.append(row)

    def extend(self, rows: Iterable[EvaluationRow]) -> None:
        for r in rows:
            self.add(r)

    @property
    def families(self) -> list[str]:
        return sorted({r.family for r in self._rows})

    def rows_for(self, family: str) -> list[EvaluationRow]:
        return [r for r in self._rows if r.family == family]

    # ---- evidence ------------------------------------------------------------------------------

    def evidence(self, family: str) -> dict[str, Any]:
        """JSON-serializable evidence for one family, including the assigned ``stage``."""
        rows = self.rows_for(family)
        ev: dict[str, Any] = {
            "family": family,
            "n_settled_predictions": len(rows),
            "brier": None,
            "log_loss": None,
            "ece": None,
            "n_with_market": 0,
            "brier_market": None,
            "brier_skill_vs_market": None,
            "brier_skill_ci95": None,
            "n_with_clv": 0,
            "clv_mean": None,
        }
        if rows:
            p = np.array([r.p for r in rows])
            y = np.array([r.y for r in rows])
            ev["brier"], ev["log_loss"], ev["ece"] = brier(p, y), log_loss(p, y), ece(p, y)
            self._market_evidence(rows, ev)
            clvs = np.array([r.clv for r in rows if r.clv is not None], dtype=float)
            ev["n_with_clv"] = int(clvs.size)
            ev["clv_mean"] = float(clvs.mean()) if clvs.size else None
        ev["stage"] = self._stage(ev).value
        return ev

    def _market_evidence(self, rows: list[EvaluationRow], ev: dict[str, Any]) -> None:
        mkt = [r for r in rows if r.p_market is not None]
        ev["n_with_market"] = len(mkt)
        if not mkt:
            return
        p = np.array([r.p for r in mkt])
        pm = np.array([r.p_market for r in mkt])
        y = np.array([r.y for r in mkt])
        ev["brier_market"] = brier(pm, y)
        ev["brier_skill_vs_market"] = _finite_or_none(brier_skill_score(p, y, pm))
        if len(mkt) >= LIMITED_MIN_N:
            lo, hi = bootstrap_ci(brier_skill_score, p, y, pm, n_boot=self.n_boot, seed=self.seed)
            ev["brier_skill_ci95"] = [_finite_or_none(lo), _finite_or_none(hi)]

    @staticmethod
    def _stage(ev: dict[str, Any]) -> Authority:
        n = ev["n_settled_predictions"]
        if n < SHADOW_MIN_N:
            return Authority.RESEARCH
        skill, clv, e = ev["brier_skill_vs_market"], ev["clv_mean"], ev["ece"]
        limited_ok = (
            n >= LIMITED_MIN_N and skill is not None and skill > 0 and clv is not None and clv > 0 and e is not None and e < MAX_ECE
        )
        if not limited_ok:
            return Authority.SHADOW
        ci = ev.get("brier_skill_ci95")
        if n >= TRUSTED_MIN_N and ci is not None and ci[0] is not None and ci[0] > 0:
            return Authority.TRUSTED
        return Authority.LIMITED

    def report(self) -> dict[str, dict[str, Any]]:
        """Evidence for every family seen, keyed by family name."""
        return {f: self.evidence(f) for f in self.families}

    def stage(self, family: str) -> Authority:
        return Authority(self.evidence(family)["stage"])
