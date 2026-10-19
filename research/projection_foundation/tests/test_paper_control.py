import gzip
import json
import sys
from pathlib import Path

PF = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PF))
from nba.paper import control  # noqa: E402


def test_control_is_read_only_and_reports_no_data_when_absent(tmp_path):
    assert control.latest(None)["status"] == "NO_DATA"
    assert control.latest(str(tmp_path))["status"] == "NO_DATA"


def test_control_reads_the_newest_value_scorecard(tmp_path):
    d = tmp_path / "scorecards/value/dt=2026-10-17"
    d.mkdir(parents=True)
    rec = {"evaluated_at": "2026-10-17T08:00:00Z", "evaluations": {control.PRIMARY_ARM: {
        "arm": "sim_rotation", "capture_window": "pretip", "n_decisions": 12, "n_games": 5, "verdict": "INSUFFICIENT_SAMPLE",
        "verdict_reasons": ["n_decisions 12 < preregistered min_decisions 200"], "eligible_for_independent_value_verdict": True,
        "report": {"preregistration": {"sha256": "abc"}, "verdict": {"thresholds": {"min_decisions": 200, "min_games": 40}}}}}}
    with gzip.open(d / "scorecards_value_x.jsonl.gz", "wt") as f:
        f.write(json.dumps(rec) + "\n")
    before = sorted(p.name for p in tmp_path.rglob("*"))
    out = control.latest(str(tmp_path))
    assert out["status"] == "OK" and out["verdict"] == "INSUFFICIENT_SAMPLE" and out["thresholds"]["min_decisions"] == 200
    assert sorted(p.name for p in tmp_path.rglob("*")) == before
