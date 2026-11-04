"""Capture-gap audit: attribution of gaps between consecutive market ticks to handovers vs in-loop capture failures (synthetic commit logs; no network, no git)."""
from datetime import timedelta

from nba.paper import capture_audit as CA


def L(commit, subject):
    return f"{commit}|{subject}"


def base_log():
    # worker 1: ticks every 15 min 10:00..11:00; its last cycle is committed 11:04, retired 11:07;
    # worker 2 acquires its lease 11:50 (a 43 min runner wait) and ticks from 11:50:06 on.
    lines = [L("2026-10-26T09:57:00Z", "worker: 1 gen 5 acquired lease")]
    for i, tick in enumerate(["10:00:00", "10:15:00", "10:30:00", "10:45:00", "11:00:00"]):
        lines.append(L(f"2026-10-26T{tick}Z", f"capture: 1 at 2026-10-26T{tick}Z"))
    lines += [L("2026-10-26T11:07:00Z", "worker: 1 retired after 5 cycles"), L("2026-10-26T11:50:00Z", "worker: 2 gen 6 acquired lease")]
    for tick in ["11:50:06", "12:05:06"]:
        lines.append(L(f"2026-10-26T{tick}Z", f"capture: 2 at 2026-10-26T{tick}Z"))
    return lines


def ticks_of(lines):
    out = {}
    for ln in lines:
        c, s = ln.split("|", 1)
        if s.startswith("capture: "):
            out[s.split(" at ")[1]] = c
    return out


def test_a_handover_gap_is_attributed_to_the_successor_wait():
    lines = base_log()
    rep = CA.audit(lines, ticks_of(lines), threshold_min=20)
    assert rep["gap_kinds"] == {"HANDOVER": 1} and rep["n_gaps"] == 1
    g = rep["gaps"][0]
    assert g["gap_min"] == 50.1 and g["kind"] == "HANDOVER"
    assert g["components"]["successor_wait_min"] == 43.0 and g["components"]["retire_tail_min"] == 7.0       # last capture commit 11:00 -> retired 11:07
    assert g["dominant"] == "successor_wait_min"


def test_cycles_that_produced_no_market_file_make_an_in_loop_gap():
    lines = [L("2026-10-26T09:57:00Z", "worker: 1 gen 5 acquired lease")]
    ticks = {}
    for tick, ok in (("10:00:00", 1), ("10:15:00", 0), ("10:30:00", 0), ("10:45:00", 0), ("11:00:00", 1)):
        lines.append(L(f"2026-10-26T{tick}Z", f"capture: 1 at 2026-10-26T{tick}Z"))
        if ok:
            ticks[f"2026-10-26T{tick}Z"] = f"2026-10-26T{tick}Z"
    rep = CA.audit(lines, ticks, threshold_min=20)
    assert rep["gap_kinds"] == {"CAPTURE_GAP_IN_LOOP": 1}
    assert rep["gaps"][0]["cycles_without_data"] == 3 and rep["gaps"][0]["gap_min"] == 60.0


def test_commit_lag_and_handover_statistics_and_threshold():
    lines = base_log()
    ticks = {k: (CA._t(k) + timedelta(seconds=200)).isoformat() for k in ticks_of(lines)}
    rep = CA.audit(lines, ticks, threshold_min=60)
    assert rep["n_gaps"] == 0                                                                        # 50 min < the 60 min threshold
    assert rep["commit_lag_s"]["median"] == 200.0 and rep["worker_handover_gap_min"]["n"] == 1
    assert "| from tick |" in CA.markdown(CA.audit(lines, ticks, threshold_min=20))


def test_commit_lag_is_reported_by_regime_and_never_pooled():
    from datetime import datetime, timedelta, timezone
    from nba.paper import capture_audit as C
    t0 = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    ticks = [(t0 + timedelta(minutes=5 * i), t0 + timedelta(minutes=5 * i, seconds=210)) for i in range(30)] + \
            [(t0 + timedelta(minutes=150 + 5 * i), t0 + timedelta(minutes=150 + 5 * i, seconds=40)) for i in range(25)]
    r = C.lag_by_regime(ticks, t0 + timedelta(minutes=150))
    assert r["before"]["n"] == 30 and r["before"]["median"] == 210.0
    assert r["after"]["n"] == 25 and r["after"]["median"] == 40.0
    assert r["comparable"] is True and "never pooled" in r["rule"]
    few = C.lag_by_regime(ticks[:30] + ticks[30:35], t0 + timedelta(minutes=150))
    assert few["after"]["n"] == 5 and few["comparable"] is False        # too few post-cutover ticks to compare


def test_the_sealed_calibration_audit_module_imports_without_running_anything():
    from nba.paper import sealed_calibration_audit as A      # a research CLI: importing it must have no side effects
    assert callable(A.main)
