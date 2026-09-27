"""Archive-level reconstruction: checkpoint policy, point-in-time discipline, fail-closed recovery.

The single most important test here is
``test_a_reconstructed_board_equals_the_captured_one_field_for_field``. Everything else in this file
guards a way of getting that wrong.
"""

from __future__ import annotations

import gzip
import json
from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.archive.delta import DeltaChainError, board_sha256, canonical_board
from nba_edge.archive.ledger import Ledger
from nba_edge.archive.reconstruct import (
    DEFAULT_CHECKPOINT_EVERY,
    chain_tip,
    reconstruct_at,
    verify_archive,
    write_board,
)

T0 = datetime(2026, 10, 3, 18, 0, tzinfo=UTC)


def board(n=5, tweak=None, wide=False):
    """A synthetic board. ``wide`` gives each row distinct content.

    That matters for any size assertion: 400 near-identical rows gzip down to ~1 KB, so a test built
    on them measures gzip's ability to collapse repetition rather than the delta's ability to avoid
    rewriting unchanged markets. Real boards are heterogeneous.
    """
    rows = []
    for i in range(n):
        r = {"ticker": f"T{i}", "yes_bid_dollars": "0.50", "yes_ask_dollars": "0.52", "status": "active"}
        if wide:
            r.update(
                title=f"Will outcome {i} happen in game {i * 7 % 31}?",
                subtitle=f"market {i} / series {i % 13} / strike {i * 3.5:.2f}",
                event_ticker=f"KXNBA-{i:05d}-{(i * 17) % 997}",
                rules=f"Resolves YES if condition {i} holds at settlement time {i * 13 % 1440}.",
                open_interest_fp=str(i * 1013),
                volume_fp=str(i * 37),
            )
        rows.append(r)
    if tweak:
        tweak(rows)
    return rows


def led(tmp_path, run="r1"):
    return Ledger(tmp_path, run_id=run)


# -- checkpoint policy --------------------------------------------------------------------------


def test_the_first_board_is_written_as_a_full_checkpoint(tmp_path):
    res = write_board(led(tmp_path), board(), observed_at=T0)
    assert res["encoding"] == "checkpoint"
    assert "no checkpoint" in res["reason"]


def test_the_next_board_is_written_as_a_delta(tmp_path):
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    res = write_board(lg, board(tweak=lambda r: r[0].update(yes_bid_dollars="0.60")),
                      observed_at=T0 + timedelta(minutes=10))
    assert res["encoding"] == "delta"
    assert res["seq"] == 1
    assert res["n_changed"] == 1


def test_a_delta_is_far_smaller_than_the_checkpoint_it_follows(tmp_path):
    lg = led(tmp_path)
    ck = write_board(lg, board(n=400, wide=True), observed_at=T0)
    d = write_board(lg, board(n=400, wide=True, tweak=lambda r: r[0].update(yes_bid_dollars="0.60")),
                    observed_at=T0 + timedelta(minutes=10))
    ratio = d["bytes"] / ck["bytes"]
    assert ratio < 0.05, f"delta {d['bytes']}b is {ratio:.1%} of checkpoint {ck['bytes']}b"


def test_the_chain_restarts_with_a_checkpoint_at_the_configured_limit(tmp_path):
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    encodings = []
    for i in range(1, 6):
        res = write_board(lg, board(tweak=lambda r, i=i: r[0].update(yes_bid_dollars=f"0.6{i}")),
                          observed_at=T0 + timedelta(minutes=10 * i), checkpoint_every=3)
        encodings.append(res["encoding"])
    assert encodings == ["delta", "delta", "delta", "checkpoint", "delta"], encodings


def test_a_new_utc_day_forces_a_checkpoint_so_day_partitions_stay_self_contained(tmp_path):
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    res = write_board(lg, board(), observed_at=T0 + timedelta(days=1))
    assert res["encoding"] == "checkpoint"
    assert "day rolled over" in res["reason"]


def test_a_broken_chain_degrades_to_a_checkpoint_rather_than_stacking_on_it(tmp_path):
    """Never build a delta on a chain that cannot be proved; that would compound the damage."""
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    write_board(lg, board(tweak=lambda r: r[0].update(status="closed")), observed_at=T0 + timedelta(minutes=10))
    _ck, deltas = chain_tip(lg)
    (tmp_path / deltas[0].path).write_bytes(gzip.compress(b'{"schema":"kalshi.board.delta/1"}'))

    res = write_board(lg, board(), observed_at=T0 + timedelta(minutes=20))
    assert res["encoding"] == "checkpoint"
    assert "unusable" in res["reason"]


# -- reconstruction -----------------------------------------------------------------------------


def test_an_archive_of_only_full_snapshots_still_reconstructs(tmp_path):
    """Existing evidence must keep working: a pre-delta archive is just a chain of length zero."""
    lg = led(tmp_path)
    rows = board()
    lg.append_rows("kalshi/markets", rows, observed_at=T0, meta={})
    r = reconstruct_at(tmp_path, T0)
    assert r.source == "snapshot"
    assert r.n_deltas_applied == 0
    assert canonical_board(r.rows) == canonical_board(rows)


def test_a_reconstructed_board_equals_the_captured_one_field_for_field(tmp_path):
    """The contract. Not "equivalent" -- equal, including the ledger's own stamps."""
    lg = led(tmp_path, run="run-7")
    write_board(lg, board(n=50), observed_at=T0)
    ticks = []
    for i in range(1, 6):
        rows = board(n=50, tweak=lambda r, i=i: (
            r[i].update(yes_bid_dollars=f"0.7{i}", status="closed"),
            r.append({"ticker": f"NEW{i}", "yes_bid_dollars": "0.10"}),
        ))
        at = T0 + timedelta(minutes=10 * i)
        write_board(lg, rows, observed_at=at)
        ticks.append((at, rows))

    for at, rows in ticks:
        r = reconstruct_at(tmp_path, at)
        assert r.source == "checkpoint+deltas"
        # field-for-field, including stamps, which is what makes it usable in place of a snapshot
        want = [{**row, "_observed_at_utc": r.observed_at_utc, "_run_id": "run-7"} for row in rows]
        got = sorted(r.rows, key=lambda x: x["ticker"])
        assert got == sorted(want, key=lambda x: x["ticker"])
        assert r.board_sha256 == board_sha256(canonical_board(rows))


def test_reconstructing_between_ticks_returns_the_tick_at_or_before(tmp_path):
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    write_board(lg, board(tweak=lambda r: r[0].update(yes_bid_dollars="0.60")),
                observed_at=T0 + timedelta(minutes=10))
    r = reconstruct_at(tmp_path, T0 + timedelta(minutes=17))
    assert r.observed_at_utc.startswith("2026-10-03T18:10")


# -- point-in-time discipline -------------------------------------------------------------------


def test_a_later_delta_cannot_leak_into_an_earlier_reconstruction(tmp_path):
    """Compression must not make history depend on current truth."""
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    write_board(lg, board(tweak=lambda r: r[0].update(yes_bid_dollars="0.60")),
                observed_at=T0 + timedelta(minutes=10))
    write_board(lg, board(tweak=lambda r: r[0].update(yes_bid_dollars="0.99")),
                observed_at=T0 + timedelta(minutes=20))

    early = reconstruct_at(tmp_path, T0 + timedelta(minutes=10))
    assert next(r for r in early.rows if r["ticker"] == "T0")["yes_bid_dollars"] == "0.60"
    assert early.n_deltas_applied == 1, "the 18:20 delta must not have been applied"


def test_a_request_before_any_checkpoint_refuses_to_use_a_later_one(tmp_path):
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    with pytest.raises(DeltaChainError, match="no .* checkpoint at or before"):
        reconstruct_at(tmp_path, T0 - timedelta(hours=1))


def test_reconstruction_does_not_modify_the_archive(tmp_path):
    """Immutable evidence: reading history must never write to it."""
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    write_board(lg, board(tweak=lambda r: r[0].update(status="closed")), observed_at=T0 + timedelta(minutes=10))
    before = {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}
    reconstruct_at(tmp_path, T0 + timedelta(minutes=10))
    after = {p: p.read_bytes() for p in sorted(tmp_path.rglob("*")) if p.is_file()}
    assert before == after


# -- failure and recovery -----------------------------------------------------------------------


def test_a_deleted_delta_makes_reconstruction_fail_closed(tmp_path):
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    for i in (1, 2, 3):
        write_board(lg, board(tweak=lambda r, i=i: r[0].update(yes_bid_dollars=f"0.6{i}")),
                    observed_at=T0 + timedelta(minutes=10 * i))
    _ck, deltas = chain_tip(lg)
    (tmp_path / deltas[1].path).unlink()
    with pytest.raises(DeltaChainError, match="missing from disk"):
        reconstruct_at(tmp_path, T0 + timedelta(minutes=30))


def test_a_corrupted_delta_makes_reconstruction_fail_closed(tmp_path):
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    write_board(lg, board(tweak=lambda r: r[0].update(yes_bid_dollars="0.60")),
                observed_at=T0 + timedelta(minutes=10))
    _ck, deltas = chain_tip(lg)
    path = tmp_path / deltas[0].path
    payload = json.loads(gzip.decompress(path.read_bytes()))
    payload["changed"] = {"T0": {"yes_bid_dollars": "6.66"}}
    path.write_bytes(gzip.compress(json.dumps(payload).encode()))
    with pytest.raises(DeltaChainError, match="corrupt"):
        reconstruct_at(tmp_path, T0 + timedelta(minutes=10))


def test_verify_archive_reports_a_broken_chain_without_raising(tmp_path):
    """The daily health check must surface one broken chain alongside the healthy ones."""
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    write_board(lg, board(tweak=lambda r: r[0].update(status="closed")), observed_at=T0 + timedelta(minutes=10))
    assert verify_archive(tmp_path)["n_ok"] == 1

    _ck, deltas = chain_tip(lg)
    (tmp_path / deltas[0].path).unlink()
    rep = verify_archive(tmp_path)
    assert rep["n_broken"] == 1
    assert rep["chains"][0]["ok"] is False
    assert "error" in rep["chains"][0]


def test_a_fresh_checkpoint_after_corruption_restores_reconstructability(tmp_path):
    """Recovery: the damage is bounded to the broken chain, not the whole archive."""
    lg = led(tmp_path)
    write_board(lg, board(), observed_at=T0)
    write_board(lg, board(tweak=lambda r: r[0].update(status="closed")), observed_at=T0 + timedelta(minutes=10))
    _ck, deltas = chain_tip(lg)
    (tmp_path / deltas[0].path).unlink()

    res = write_board(lg, board(n=6), observed_at=T0 + timedelta(minutes=20))
    assert res["encoding"] == "checkpoint"
    r = reconstruct_at(tmp_path, T0 + timedelta(minutes=20))
    assert r.source == "snapshot"
    assert r.n_markets == 6


def test_the_default_checkpoint_interval_is_a_bounded_chain():
    assert 1 < DEFAULT_CHECKPOINT_EVERY <= 48, "an unbounded chain makes reconstruction cost grow forever"
