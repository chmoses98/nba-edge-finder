"""NBA routed-wager accounting: identity, idempotency, conflicts, orphans, validator, CLI privacy, isolation.

The ledger logic is the vendored contract module (``edge_finder_contract.routed_ledger``); these tests prove the
NBA binding of it -- the spec in ``nba_edge.accounting`` and the three scripts the router invokes -- behaves the
way the router's merge gate relies on.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from edge_finder_contract import routed_ledger as L

from nba_edge.accounting import SPEC

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts" / "accounting"
KEY = "kalshi:0:KXNBAGAME-26OCT07MININD-MIN:order-abc123"
TICKER = "KXNBAGAME-26OCT07MININD-MIN"


def wager_row(**kw) -> dict:
    row = {"source_bet_key": KEY, "import_batch_id": "kalshi-router-v1", "entry_method": "IMPORTED_RECEIPT",
           "game_date": "2026-10-07", "market_ticker": TICKER, "side": "YES", "executed_at": "2026-10-07T22:15:03Z",
           "contracts": 25.0, "execution_price": 0.57, "stake": 14.61, "fees_paid": 0.36, "fees_are_estimated": False,
           "venue": "kalshi"}
    row.update(kw)
    return row


def settlement_row(**kw) -> dict:
    row = {"source_bet_key": KEY, "market_ticker": TICKER, "side": "YES", "settlement_status": "SETTLED",
           "settled_at": "2026-10-08T02:40:00Z", "result": "WON", "gross_return": 25.0, "net_profit_loss": 10.39,
           "refusals": [], "venue": "kalshi", "economics_version": L.ECONOMICS_V2}
    row.update(kw)
    return row


def ledger_bytes(base: Path) -> tuple[bytes, bytes]:
    w, s = SPEC.wagers_path(base), SPEC.settlements_path(base)
    return (w.read_bytes() if w.exists() else b"", s.read_bytes() if s.exists() else b"")


def run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True)


# ------------------------------------------------------------------------------------------------- spec
def test_spec_is_the_nba_binding():
    assert SPEC.sport == "NBA"
    assert SPEC.wager_schema == "nba_accounted_wager.v1"
    assert SPEC.settlement_schema == "nba_wager_settlement.v1"
    assert SPEC.mint_wager_id(KEY).startswith("nbaw-") and len(SPEC.mint_wager_id(KEY)) == len("nbaw-") + 24
    assert SPEC.mint_settlement_id(KEY).startswith("nbas-")
    assert SPEC.mint_wager_id(KEY) == SPEC.mint_wager_id(KEY)  # no clock, no economics
    assert SPEC.wagers_path(Path("/b")) == Path("/b/data/accounting/wagers.jsonl")
    assert SPEC.settlements_path(Path("/b")) == Path("/b/data/accounting/settlements.jsonl")


# ---------------------------------------------------------------------------------------------- wagers
def test_new_then_duplicate_noop_is_byte_identical(tmp_path):
    r1 = L.import_wagers(SPEC, tmp_path, [wager_row()], import_batch_id="kalshi-router-v1")
    assert (r1.written, r1.duplicate, r1.refused) == (1, 0, 0)
    assert r1.rows[0]["status"] == L.NEW and r1.rows[0]["wager_id"] == SPEC.mint_wager_id(KEY)
    before = ledger_bytes(tmp_path)
    r2 = L.import_wagers(SPEC, tmp_path, [wager_row()], import_batch_id="kalshi-router-v1")
    assert (r2.written, r2.duplicate, r2.refused) == (0, 1, 0)
    assert r2.rows[0]["status"] == L.DUPLICATE_NOOP and r2.rows[0]["success"] is True
    assert ledger_bytes(tmp_path) == before
    on_file = L.read_jsonl(SPEC.wagers_path(tmp_path))
    assert len(on_file) == 1 and on_file[0]["schema_version"] == "nba_accounted_wager.v1"


def test_conflict_never_rewrites(tmp_path):
    L.import_wagers(SPEC, tmp_path, [wager_row()], import_batch_id="kalshi-router-v1")
    before = ledger_bytes(tmp_path)
    r = L.import_wagers(SPEC, tmp_path, [wager_row(contracts=30.0, stake=17.46)], import_batch_id="kalshi-router-v1")
    assert (r.written, r.duplicate, r.refused) == (0, 0, 1)
    assert r.rows[0]["status"] == L.CONFLICT and r.conflicted
    assert set(r.rows[0]["conflicting_fields"]) == {"contracts", "stake"}
    assert "17.46" not in r.rows[0]["reason"] and "30" not in r.rows[0]["reason"]
    assert ledger_bytes(tmp_path) == before


@pytest.mark.parametrize("field", ["recommendation_id", "model_probability", "fair_probability", "prediction_id",
                                   "authority", "confidence", "edge", "gate", "model_version"])
def test_provenance_fields_are_refused(tmp_path, field):
    r = L.import_wagers(SPEC, tmp_path, [wager_row(**{field: None})], import_batch_id="kalshi-router-v1")
    assert r.refused == 1 and r.rows[0]["status"] == L.REFUSED
    assert "provenance" in r.rows[0]["reason"] and field in r.rows[0]["reason"]
    assert ledger_bytes(tmp_path) == (b"", b"")


# ----------------------------------------------------------------------------------------- settlements
def test_orphan_settlement_is_refused(tmp_path):
    r = L.import_settlements(SPEC, tmp_path, [settlement_row()])
    assert r.refused == 1 and r.rows[0]["status"] == L.REFUSED and "ORPHAN" in r.rows[0]["reason"]
    assert not SPEC.settlements_path(tmp_path).exists()


def test_settlement_new_then_duplicate_then_conflict(tmp_path):
    L.import_wagers(SPEC, tmp_path, [wager_row()], import_batch_id="kalshi-router-v1")
    r1 = L.import_settlements(SPEC, tmp_path, [settlement_row()])
    assert r1.written == 1 and r1.rows[0]["settlement_id"] == SPEC.mint_settlement_id(KEY)
    before = ledger_bytes(tmp_path)
    r2 = L.import_settlements(SPEC, tmp_path, [settlement_row()])
    assert r2.duplicate == 1 and ledger_bytes(tmp_path) == before
    r3 = L.import_settlements(SPEC, tmp_path, [settlement_row(result="LOST", gross_return=0.0, net_profit_loss=-14.61)])
    assert r3.refused == 1 and r3.rows[0]["status"] == L.CONFLICT and ledger_bytes(tmp_path) == before
    stored = L.read_jsonl(SPEC.settlements_path(tmp_path))
    assert stored[0]["schema_version"] == "nba_wager_settlement.v1"


# ------------------------------------------------------------------------------------------- validator
def test_validator_passes_a_clean_ledger_and_an_empty_one(tmp_path):
    assert L.validate_ledger(SPEC, tmp_path)["ok"] is True
    L.import_wagers(SPEC, tmp_path, [wager_row()], import_batch_id="kalshi-router-v1")
    L.import_settlements(SPEC, tmp_path, [settlement_row()])
    res = L.validate_ledger(SPEC, tmp_path)
    assert res["ok"] is True and res["counts"] == {"wagers": 1, "settlements": 1}


def test_validator_fails_on_orphan_duplicate_and_bad_json(tmp_path):
    L.import_wagers(SPEC, tmp_path, [wager_row()], import_batch_id="kalshi-router-v1")
    L.import_settlements(SPEC, tmp_path, [settlement_row()])
    wp = SPEC.wagers_path(tmp_path)
    wp.write_text(wp.read_text() + wp.read_text().splitlines()[0] + "\nnot json\n")
    orphan = dict(L.build_settlement(SPEC, settlement_row(source_bet_key="kalshi:0:X:order-zzz")))
    sp = SPEC.settlements_path(tmp_path)
    sp.write_text(sp.read_text() + json.dumps(orphan) + "\n")
    res = L.validate_ledger(SPEC, tmp_path)
    assert res["ok"] is False
    text = "\n".join(res["failures"])
    assert "duplicate source_bet_key" in text and "not JSON" in text and "ORPHAN" in text
    assert KEY not in text and TICKER not in text


# ------------------------------------------------------------------------------------------------- CLI
def test_cli_round_trip_with_the_routers_argv_prints_no_ticker_price_or_key(tmp_path):
    payload = tmp_path / "NBA.json"
    payload.write_text(json.dumps({"importBatchId": "kalshi-router-v1", "rows": [wager_row()]}))
    spay = tmp_path / "NBA-settlements.json"
    spay.write_text(json.dumps({"settlements": [settlement_row()]}))
    base = tmp_path / "ledger"
    base.mkdir()
    outs = []
    for script, pay, rec in (("import_routed_wagers.py", payload, "w1.json"), ("import_routed_wagers.py", payload, "w2.json"),
                             ("import_routed_settlements.py", spay, "s1.json"), ("import_routed_settlements.py", spay, "s2.json")):
        p = run_script(script, "--payload", str(pay), "--base-dir", str(base), "--receipts-out", str(tmp_path / rec))
        assert p.returncode == 0, p.stdout + p.stderr
        outs.append(p.stdout + p.stderr)
    v = run_script("validate_routed_ledger.py", "--base-dir", str(base), "--result-out", str(tmp_path / "v.json"))
    assert v.returncode == 0, v.stdout + v.stderr
    outs.append(v.stdout + v.stderr)
    blob = "\n".join(outs)
    for secret in (TICKER, KEY, "14.61", "0.57", "25.0", "10.39", "0.36"):
        assert secret not in blob, f"{secret!r} leaked into a public log"
    w1, w2 = (json.loads((tmp_path / f).read_text()) for f in ("w1.json", "w2.json"))
    s1, s2 = (json.loads((tmp_path / f).read_text()) for f in ("s1.json", "s2.json"))
    assert [r["status"] for r in w1["rows"]] == ["NEW"] and [r["status"] for r in w2["rows"]] == ["DUPLICATE_NOOP"]
    assert [r["status"] for r in s1["rows"]] == ["NEW"] and [r["status"] for r in s2["rows"]] == ["DUPLICATE_NOOP"]
    assert w1["importBatchId"] == "kalshi-router-v1"
    assert w1["rows"][0]["wager_id"] == w2["rows"][0]["wager_id"] == SPEC.mint_wager_id(KEY)
    assert w1["rows"][0]["source_bet_key"] == KEY
    result = json.loads((tmp_path / "v.json").read_text())
    assert result["passed"] is True and result["counts"] == {"wagers": 1, "settlements": 1}


def test_cli_conflict_exits_1_and_unreadable_payload_exits_2(tmp_path):
    base = tmp_path / "ledger"
    base.mkdir()
    payload = tmp_path / "NBA.json"
    payload.write_text(json.dumps({"importBatchId": "kalshi-router-v1", "rows": [wager_row()]}))
    assert run_script("import_routed_wagers.py", "--payload", str(payload), "--base-dir", str(base)).returncode == 0
    before = ledger_bytes(base)
    payload.write_text(json.dumps({"importBatchId": "kalshi-router-v1", "rows": [wager_row(execution_price=0.6, stake=15.36)]}))
    p = run_script("import_routed_wagers.py", "--payload", str(payload), "--base-dir", str(base))
    assert p.returncode == 1 and "CONFLICT" in p.stdout and "execution_price" in p.stdout
    assert "0.6" not in p.stdout and "15.36" not in p.stdout and TICKER not in p.stdout
    assert ledger_bytes(base) == before
    payload.write_text("{not json")
    p = run_script("import_routed_wagers.py", "--payload", str(payload), "--base-dir", str(base))
    assert p.returncode == 2 and ledger_bytes(base) == before
    v = run_script("validate_routed_ledger.py", "--base-dir", str(base))
    assert v.returncode == 0


# ------------------------------------------------------------------------------------------- isolation
def test_accounting_imports_no_model_code():
    code = ("import sys; sys.path.insert(0, 'src'); import nba_edge.accounting; "
            "bad = sorted(m for m in sys.modules if m.startswith('nba_edge.') and m != 'nba_edge.accounting'); print(bad)")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO)
    assert p.returncode == 0, p.stderr
    assert p.stdout.strip() == "[]", p.stdout


def test_model_authority_is_untouched():
    from nba_edge.schemas.prediction import Authority, ContractPrediction

    assert ContractPrediction.model_fields["authority"].default == Authority.RESEARCH
