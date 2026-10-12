"""The vendored tools/pure_gate copies must match the sha256 pinned in VENDORED_FROM. Do not edit them."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

GATE = Path(__file__).resolve().parents[1] / "tools" / "pure_gate"
EXPECTED = {
    "pure_gate.py", "schema/pure_forecast.v1.schema.json", "accuracy_scorecard.py", "value_scorecard.py", "SCORECARDS.md",
}


def test_vendored_files_match_their_pins():
    pins = re.findall(r"^path: pure-contract/(\S+) sha256=([0-9a-f]{64})$", (GATE / "VENDORED_FROM").read_text(), re.M)
    assert {rel for rel, _ in pins} == EXPECTED
    for rel, sha in pins:
        assert hashlib.sha256((GATE / rel).read_bytes()).hexdigest() == sha, f"vendored {rel} was edited"


def test_pure_gate_and_schema_are_the_pinned_versions():
    pins = dict(re.findall(r"^path: pure-contract/(\S+) sha256=([0-9a-f]{64})$", (GATE / "VENDORED_FROM").read_text(), re.M))
    assert pins["pure_gate.py"].startswith("36b52d07") and pins["schema/pure_forecast.v1.schema.json"].startswith("7caea6c3")
