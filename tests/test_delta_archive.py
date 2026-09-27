"""Delta encoding: round trips, and every way a chain can be wrong.

The reconstruction path is the one place in this project where a silent bug produces *plausible but
false history* -- a price that never existed, attributed to a minute that did. So the negative cases
here matter more than the happy path, and each is named for the corruption it forbids.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from nba_edge.archive.delta import (
    Delta,
    DeltaChainError,
    apply_delta,
    board_sha256,
    build_delta,
    canonical_board,
    dedupe_and_order,
    diff_boards,
    restamp,
    verify_chain,
)

T0 = datetime(2026, 10, 3, 18, 0, tzinfo=UTC)


def row(ticker, **kw):
    base = {"ticker": ticker, "yes_bid_dollars": "0.50", "yes_ask_dollars": "0.52", "status": "active"}
    base.update(kw)
    return base


def mkdelta(before, after, seq=1, at=None):
    return build_delta(
        before, after, captured_at=at or (T0 + timedelta(minutes=10 * seq)), run_id="r1", seq=seq,
        base_path="kalshi/markets/dt=2026-10-03/ck.jsonl.gz", base_sha256="ckhash",
        base_captured_at="2026-10-03T18:00:00Z",
    )


# -- canonical board ---------------------------------------------------------------------------


def test_ledger_stamps_are_excluded_so_they_cannot_mark_every_market_changed():
    """The stamps differ on every snapshot; diffing them would make all markets look changed."""
    a = canonical_board([row("A", _observed_at_utc="2026-10-03T18:00:00Z", _run_id="1")])
    b = canonical_board([row("A", _observed_at_utc="2026-10-03T18:10:00Z", _run_id="2")])
    assert a == b
    assert board_sha256(a) == board_sha256(b)
    assert "_observed_at_utc" not in a["A"]


def test_rows_without_a_ticker_are_dropped_not_merged_under_none():
    board = canonical_board([row("A"), {"yes_bid_dollars": "0.1"}])
    assert set(board) == {"A"}


def test_board_hash_is_independent_of_row_order():
    one = canonical_board([row("A"), row("B")])
    two = canonical_board([row("B"), row("A")])
    assert board_sha256(one) == board_sha256(two)


def test_board_hash_changes_when_any_field_changes():
    a = canonical_board([row("A")])
    b = canonical_board([row("A", yes_bid_dollars="0.51")])
    assert board_sha256(a) != board_sha256(b)


# -- the four change categories -----------------------------------------------------------------


def test_a_newly_discovered_market_is_carried_as_an_addition():
    before = canonical_board([row("A")])
    after = canonical_board([row("A"), row("NEW")])
    d = mkdelta(before, after)
    assert set(d.added) == {"NEW"}
    assert apply_delta(before, d) == after


def test_a_delisted_market_is_carried_as_a_removal():
    before = canonical_board([row("A"), row("GONE")])
    after = canonical_board([row("A")])
    d = mkdelta(before, after)
    assert d.removed == ["GONE"]
    assert apply_delta(before, d) == after


def test_a_quote_change_carries_only_the_changed_fields():
    before = canonical_board([row("A")])
    after = canonical_board([row("A", yes_bid_dollars="0.60")])
    d = mkdelta(before, after)
    assert d.changed == {"A": {"yes_bid_dollars": "0.60"}}, "unchanged fields must not be carried"
    assert apply_delta(before, d) == after


def test_a_market_status_change_is_carried():
    before = canonical_board([row("A", status="active")])
    after = canonical_board([row("A", status="closed")])
    d = mkdelta(before, after)
    assert d.changed == {"A": {"status": "closed"}}
    assert apply_delta(before, d) == after


def test_a_field_that_disappears_is_cleared_rather_than_left_stale():
    """Without `cleared`, a vanished field would keep its old value forever on reconstruction."""
    before = canonical_board([row("A", extra="present")])
    after = canonical_board([row("A")])
    d = mkdelta(before, after)
    assert d.cleared == {"A": ["extra"]}
    assert apply_delta(before, d) == after
    assert "extra" not in apply_delta(before, d)["A"]


def test_orderbook_depth_changes_round_trip():
    """Order books are keyed rows too, so the same machinery carries depth changes."""
    before = canonical_board([{"ticker": "A", "yes": [[50, 10]], "no": [[48, 5]]}])
    after = canonical_board([{"ticker": "A", "yes": [[50, 12], [49, 3]], "no": [[48, 5]]}])
    d = mkdelta(before, after)
    assert "A" in d.changed
    assert apply_delta(before, d) == after


def test_apply_never_mutates_the_input_board():
    before = canonical_board([row("A")])
    snapshot = json.loads(json.dumps(before))
    apply_delta(before, mkdelta(before, canonical_board([row("A", status="closed")])))
    assert before == snapshot


# -- chain verification: the fail-closed cases --------------------------------------------------


def _chain(n=3):
    boards = [canonical_board([row("A"), row("B")])]
    deltas = []
    for i in range(1, n + 1):
        nxt = canonical_board([row("A", yes_bid_dollars=f"0.5{i}"), row("B")])
        deltas.append(mkdelta(boards[-1], nxt, seq=i))
        boards.append(nxt)
    return boards, deltas


def test_a_complete_chain_reconstructs_the_final_board():
    boards, deltas = _chain(3)
    assert verify_chain(boards[0], deltas) == boards[-1]


def test_a_chain_with_a_missing_delta_fails_closed():
    boards, deltas = _chain(3)
    with pytest.raises(DeltaChainError, match="gap"):
        verify_chain(boards[0], [deltas[0], deltas[2]])


def test_a_chain_that_does_not_start_at_one_fails_closed():
    boards, deltas = _chain(3)
    with pytest.raises(DeltaChainError, match="gap"):
        verify_chain(boards[0], deltas[1:])


def test_a_delta_applied_to_the_wrong_checkpoint_fails_closed():
    _boards, deltas = _chain(2)
    other = canonical_board([row("A", yes_bid_dollars="9.99"), row("B")])
    with pytest.raises(DeltaChainError, match="expects parent board"):
        verify_chain(other, deltas)


def test_a_tampered_field_value_fails_closed_on_the_recorded_hash():
    """The decisive integrity check: altered content must not reproduce its recorded board hash."""
    boards, deltas = _chain(1)
    tampered = replace(deltas[0], changed={"A": {"yes_bid_dollars": "0.99"}})
    with pytest.raises(DeltaChainError, match="is corrupt"):
        verify_chain(boards[0], [tampered])


def test_a_tampered_board_hash_fails_closed():
    boards, deltas = _chain(1)
    tampered = replace(deltas[0], board_sha256="0" * 64)
    with pytest.raises(DeltaChainError, match="is corrupt"):
        verify_chain(boards[0], [tampered])


def test_a_wrong_market_count_fails_closed():
    boards, deltas = _chain(1)
    with pytest.raises(DeltaChainError, match="records"):
        verify_chain(boards[0], [replace(deltas[0], n_markets_after=999)])


def test_an_unknown_schema_fails_closed():
    boards, deltas = _chain(1)
    with pytest.raises(DeltaChainError, match="schema"):
        verify_chain(boards[0], [replace(deltas[0], schema="something/2")])


def test_a_checkpoint_that_does_not_hash_as_expected_fails_closed():
    boards, deltas = _chain(1)
    with pytest.raises(DeltaChainError, match="checkpoint board hashes"):
        verify_chain(boards[0], deltas, base_sha256="f" * 64)


# -- duplicates and ordering --------------------------------------------------------------------


def test_an_identical_duplicate_delta_is_collapsed_not_rejected():
    """A retried push can legitimately land the same delta twice; that is harmless."""
    boards, deltas = _chain(2)
    doubled = [deltas[0], deltas[0], deltas[1], deltas[1]]
    assert len(dedupe_and_order(doubled)) == 2
    assert verify_chain(boards[0], doubled) == boards[-1]


def test_two_different_deltas_claiming_one_seq_fail_closed():
    """A forked chain: there is no way to know which branch history actually took."""
    boards, deltas = _chain(1)
    other = mkdelta(boards[0], canonical_board([row("A", yes_bid_dollars="0.77"), row("B")]), seq=1)
    with pytest.raises(DeltaChainError, match="forked"):
        dedupe_and_order([deltas[0], other])


def test_out_of_order_input_is_sorted_by_seq_not_trusted_as_given():
    boards, deltas = _chain(3)
    assert verify_chain(boards[0], list(reversed(deltas))) == boards[-1]


def test_a_delta_stamped_before_its_predecessor_fails_closed():
    """Contiguous seq is not enough: the capture instants must strictly increase too."""
    boards, deltas = _chain(2)
    backwards = replace(deltas[1], captured_at_utc="2026-10-03T17:00:00Z")
    with pytest.raises(DeltaChainError, match="strictly increase"):
        verify_chain(boards[0], [deltas[0], backwards])


def test_a_delta_stamped_identically_to_its_predecessor_fails_closed():
    boards, deltas = _chain(2)
    same = replace(deltas[1], captured_at_utc=deltas[0].captured_at_utc)
    with pytest.raises(DeltaChainError, match="strictly increase"):
        verify_chain(boards[0], [deltas[0], same])


def test_changing_a_ticker_absent_from_the_board_fails_closed():
    before = canonical_board([row("A")])
    d = replace(mkdelta(before, canonical_board([row("A", status="closed")])),
                changed={"MISSING": {"status": "closed"}})
    with pytest.raises(DeltaChainError, match="not on the board"):
        apply_delta(before, d)


# -- serialisation and provenance ---------------------------------------------------------------


def test_a_delta_round_trips_through_its_serialised_form():
    _boards, deltas = _chain(1)
    assert Delta.from_bytes(deltas[0].to_bytes()) == deltas[0]
    assert Delta.from_bytes(gzip.compress(deltas[0].to_bytes())) == deltas[0]


def test_a_truncated_delta_payload_fails_closed():
    _boards, deltas = _chain(1)
    partial = json.dumps({"schema": "kalshi.board.delta/1", "seq": 1}).encode()
    with pytest.raises(DeltaChainError, match="missing required fields"):
        Delta.from_bytes(partial)


def test_restamp_restores_the_exact_capture_instant_and_run_id():
    """This is what makes a reconstructed snapshot equal to a real one field for field."""
    board = canonical_board([row("A"), row("B")])
    rows = restamp(board, "2026-10-03T18:10:00Z", "run-9")
    assert all(r["_observed_at_utc"] == "2026-10-03T18:10:00Z" for r in rows)
    assert all(r["_run_id"] == "run-9" for r in rows)
    assert [r["ticker"] for r in rows] == ["A", "B"], "deterministic ticker order"


def test_diff_of_identical_boards_is_empty():
    b = canonical_board([row("A"), row("B")])
    parts = diff_boards(b, b)
    assert parts == {"added": {}, "removed": [], "changed": {}, "cleared": {}}
