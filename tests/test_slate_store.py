"""Slate pass storage: compressed for new passes, readable alongside the old plain format, deterministic, never serves a stale packet."""

import gzip
import json

from nba_edge.archive.slate_store import dumps_compact, gz_bytes, read_json_any, write_json_gz, write_pass

SLATE = {"date_et": "2026-10-24", "contracts": [{"ticker": f"T{i}", "p": i / 1000} for i in range(500)], "x": None}
PACKET = {"slate": SLATE, "games": [{"id": "g", "players": [{"n": j, "sim": {"pts": {"q50": j}}} for j in range(40)]}]}


def test_roundtrip_gz_and_deterministic_bytes(tmp_path):
    a, b = tmp_path / "a.json.gz", tmp_path / "b.json.gz"
    write_json_gz(a, PACKET)
    write_json_gz(b, PACKET)
    assert a.read_bytes() == b.read_bytes()  # mtime/filename pinned: stable sha256
    assert json.loads(gzip.decompress(a.read_bytes())) == PACKET
    assert a.stat().st_size < len(json.dumps(PACKET, indent=1)) / 4


def test_read_json_any_accepts_old_plain_and_new_gz_and_prefers_gz(tmp_path):
    p = tmp_path / "packet.json"
    assert read_json_any(p) is None
    p.write_text(json.dumps({"v": "old"}))
    assert read_json_any(p) == {"v": "old"}  # historical plain files stay readable
    write_json_gz(tmp_path / "packet.json.gz", {"v": "new"})
    assert read_json_any(p) == {"v": "new"}


def test_read_json_any_returns_none_on_corrupt_content(tmp_path):
    (tmp_path / "packet.json.gz").write_bytes(gz_bytes(b"{not json")[:-4])
    assert read_json_any(tmp_path / "packet.json") is None


def test_write_pass_layout_sizes_and_latest_refresh_removes_stale_plain_packet(tmp_path):
    latest = tmp_path / "slates" / "latest"
    latest.mkdir(parents=True)
    (latest / "packet.json").write_text(json.dumps({"v": "stale-old-format"}))
    sd = tmp_path / "slates" / "dt=2026-10-24" / "20261024T120000Z"
    sizes = write_pass(sd, latest, SLATE, PACKET, "# md\n")
    assert sorted(p.name for p in sd.iterdir()) == ["packet.json.gz", "slate.json.gz", "slate.md"]
    assert sorted(p.name for p in latest.iterdir()) == ["packet.json.gz", "slate.json", "slate.md"]
    assert set(sizes) == {"slate.json.gz", "packet.json.gz"}
    assert read_json_any(latest / "packet.json") == json.loads(dumps_compact(PACKET))
    assert json.loads((latest / "slate.json").read_text()) == SLATE  # app export reads this plain file live
    assert read_json_any(sd / "slate.json") == json.loads(dumps_compact(SLATE))
