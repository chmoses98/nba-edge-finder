import gzip
import json

import pytest

from nba_edge.archive.ledger import ImmutabilityError, Ledger
from nba_edge.timeutil import parse_iso


def test_append_and_read_roundtrip(tmp_path):
    led = Ledger(tmp_path, run_id="r1")
    ts = parse_iso("2026-10-21T23:00:00Z")
    e = led.append_rows("kalshi/markets", [{"ticker": "A", "yes_bid": 40}, {"ticker": "B"}], observed_at=ts)
    assert e.rows == 2
    rows = list(led.iter_rows("kalshi/markets"))
    assert [r["ticker"] for r in rows] == ["A", "B"]
    assert rows[0]["_observed_at_utc"] == "2026-10-21T23:00:00Z"
    assert rows[0]["_run_id"] == "r1"
    assert led.verify() == []


def test_refuses_overwrite(tmp_path):
    led = Ledger(tmp_path, run_id="r1")
    ts = parse_iso("2026-10-21T23:00:00Z")
    led.append_rows("k", [{"x": 1}], observed_at=ts)
    with pytest.raises(ImmutabilityError):
        led.append_rows("k", [{"x": 2}], observed_at=ts)


def test_verify_detects_tampering(tmp_path):
    led = Ledger(tmp_path, run_id="r1")
    e = led.append_rows("k", [{"x": 1}], observed_at=parse_iso("2026-10-21T23:00:00Z"))
    p = tmp_path / e.path
    with gzip.open(p, "wt") as f:
        f.write(json.dumps({"x": 999}) + "\n")
    problems = led.verify()
    assert any("hash mismatch" in s for s in problems)


def test_partition_by_date_filters(tmp_path):
    led = Ledger(tmp_path, run_id="r1")
    led.append_rows("k", [{"d": 1}], observed_at=parse_iso("2026-10-21T23:00:00Z"))
    led.append_rows("k", [{"d": 2}], observed_at=parse_iso("2026-10-22T01:00:00Z"))
    assert [r["d"] for r in led.iter_rows("k", dt_from="2026-10-22")] == [2]
    assert led.latest("k").rows == 1
