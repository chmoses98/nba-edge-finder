"""Issue #53: server-timestamped, additions-only publication of the sealed ledger (nba.paper.ledger_remote) against an in-memory fake of the GitHub Git Data API.

The real API path cannot be exercised before merge (the workflow runs from the default branch); these tests pin the protocol it relies on: no client-supplied dates, fast-forward-only
ref updates, additions only, write-once paths, bootstrap of a missing branch, retry on a lost race, durability and deadline checks."""
import base64
import hashlib
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from nba.paper import ledger_remote as LR  # noqa: E402


class FakeApi:
    """Just enough of the Git Data API. `clock` is the SERVER clock: commits are stamped with it and the request body's dates (if any) are ignored but recorded."""

    def __init__(self, clock="2026-10-24T18:20:00Z"):
        self.clock, self.blobs, self.trees, self.commits, self.refs, self.log = clock, {}, {}, {}, {}, []
        self.race = 0                                    # number of upcoming ref updates that lose a race

    def _sha(self, *parts):
        return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()

    def __call__(self, method, ep, body=None):
        self.log.append((method, ep, body))
        ep = ep.split("?")[0]
        parts = ep.split("/")                           # repos/o/n/git/<kind>/...
        if ep.endswith("/git/blobs") and method == "POST":
            data = base64.b64decode(body["content"])
            sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            self.blobs[sha] = data
            return {"sha": sha}
        if ep.endswith("/git/trees") and method == "POST":
            base = dict(self.trees[body["base_tree"]]) if body.get("base_tree") else {}
            for e in body["tree"]:
                assert e.get("sha") and e["mode"] == "100644", "only additions / replacements of blobs: a deletion would be sha null"
                base[e["path"]] = e["sha"]
            sha = self._sha("tree", sorted(base.items()))
            self.trees[sha] = base
            return {"sha": sha}
        if "/git/trees/" in ep and method == "GET":
            return {"tree": [{"path": p, "sha": s, "type": "blob"} for p, s in self.trees[parts[-1]].items()]}
        if ep.endswith("/git/commits") and method == "POST":
            assert "author" not in body and "committer" not in body, "client must not supply dates"
            sha = self._sha("commit", body["tree"], body["parents"], self.clock, len(self.commits))
            self.commits[sha] = {"sha": sha, "tree": {"sha": body["tree"]}, "parents": body["parents"], "committer": {"date": self.clock}, "author": {"date": self.clock}}
            return {k: self.commits[sha][k] for k in ("sha", "committer", "author")}
        if "/git/commits/" in ep and method == "GET":
            return self.commits[parts[-1]]
        if "/git/ref/heads/" in ep and method == "GET":
            b = ep.split("/git/ref/heads/")[1]
            if b not in self.refs:
                raise LR.ApiError(404)
            return {"object": {"sha": self.refs[b]}}
        if ep.endswith("/git/refs") and method == "POST":
            b = body["ref"].replace("refs/heads/", "")
            if b in self.refs:
                raise LR.ApiError(422, "Reference already exists")
            self.refs[b] = body["sha"]
            return {}
        if "/git/refs/heads/" in ep and method == "DELETE":
            b = ep.split("/git/refs/heads/")[1]
            if b not in self.refs:
                raise LR.ApiError(422, "Reference does not exist")
            del self.refs[b]
            return {}
        if "/git/refs/heads/" in ep and method == "PATCH":
            b = ep.split("/git/refs/heads/")[1]
            assert body["force"] is False, "fast-forward only"
            if self.race:
                self.race -= 1
                self._concurrent(b)
            if not self._is_ancestor(self.refs[b], body["sha"]):
                raise LR.ApiError(422, "Update is not a fast forward")
            self.refs[b] = body["sha"]
            return {}
        if "/compare/" in ep:
            a, b = parts[-1].split("...")
            return {"status": "identical" if a == b else "ahead" if self._is_ancestor(a, b) else "diverged"}
        raise AssertionError((method, ep))

    def _is_ancestor(self, a, b):
        while True:
            if a == b:
                return True
            ps = self.commits[b]["parents"]
            if not ps:
                return False
            b = ps[0]

    def _concurrent(self, branch):                       # somebody else commits first
        cur = self.refs[branch]
        tree = dict(self.trees[self.commits[cur]["tree"]["sha"]])
        tree["seals/other.json"] = self("POST", "repos/o/n/git/blobs", {"content": base64.b64encode(b"x").decode(), "encoding": "base64"})["sha"]
        t = self("POST", "repos/o/n/git/trees", {"tree": [{"path": "seals/other.json", "mode": "100644", "type": "blob", "sha": tree["seals/other.json"]}], "base_tree": self.commits[cur]["tree"]["sha"]})
        c = self("POST", "repos/o/n/git/commits", {"message": "other", "tree": t["sha"], "parents": [cur]})
        self.refs[branch] = c["sha"]


def files(**kw):
    return {f"seals/2026-10-24/{k}.json": v.encode() for k, v in kw.items()}


def test_bootstrap_creates_the_orphan_branch_with_a_server_timestamp_and_no_client_dates():
    api = FakeApi()
    res = LR.publish(api, "o/n", "exec-shadow-seals", files(a="1"), "msg")
    assert res["status"] == "PUBLISHED" and res["bootstrapped"] and res["parent"] is None and res["commit_utc"] == "2026-10-24T18:20:00Z"
    tree = api.trees[api.commits[api.refs["exec-shadow-seals"]]["tree"]["sha"]]
    assert set(tree) == {"README.md", "seals/2026-10-24/a.json"}
    assert all(c[2] is None or "author" not in c[2] and "committer" not in c[2] for c in api.log)


def test_second_publish_adds_on_top_and_never_deletes():
    api = FakeApi()
    LR.publish(api, "o/n", "b", files(a="1"), "m")
    api.clock = "2026-10-24T18:30:00Z"
    res = LR.publish(api, "o/n", "b", files(b="2"), "m")
    head = api.refs["b"]
    assert res["parent"] is not None and api.commits[head]["parents"] == [res["parent"]] and res["commit_utc"] == "2026-10-24T18:30:00Z"
    assert {"seals/2026-10-24/a.json", "seals/2026-10-24/b.json"} <= set(api.trees[api.commits[head]["tree"]["sha"]])
    assert LR.verify_durable(api, "o/n", "b", res["commit_sha"]) and LR.verify_durable(api, "o/n", "b", res["parent"])      # an ancestor is durable too


def test_existing_paths_are_write_once_identical_resubmission_is_a_noop_different_content_aborts():
    api = FakeApi()
    LR.publish(api, "o/n", "b", files(a="1"), "m")
    head = api.refs["b"]
    assert LR.publish(api, "o/n", "b", files(a="1"), "m")["status"] == "NOTHING_TO_PUBLISH" and api.refs["b"] == head
    with pytest.raises(LR.Conflict, match="write-once"):
        LR.publish(api, "o/n", "b", files(a="DIFFERENT"), "m")
    assert api.refs["b"] == head


def test_only_the_ledger_layout_is_accepted():
    api = FakeApi()
    for bad in ({"../x.json": b"1"}, {".github/workflows/x.yml": b"1"}, {"seals/../../x": b"1"}, {"other/a.json": b"1"}):
        with pytest.raises(LR.Conflict):
            LR.publish(api, "o/n", "b", bad, "m")
    assert not api.refs


def test_a_lost_race_is_retried_on_the_new_head_and_still_fast_forward():
    api = FakeApi()
    LR.publish(api, "o/n", "b", files(a="1"), "m")
    api.race = 1
    res = LR.publish(api, "o/n", "b", files(b="2"), "m", sleep=lambda s: None)
    tree = api.trees[api.commits[api.refs["b"]]["tree"]["sha"]]
    assert res["status"] == "PUBLISHED" and {"seals/other.json", "seals/2026-10-24/a.json", "seals/2026-10-24/b.json"} <= set(tree)


def test_persistent_failure_raises_instead_of_pretending():
    api = FakeApi()
    LR.publish(api, "o/n", "b", files(a="1"), "m")
    api.race = 99
    with pytest.raises(LR.ApiError):
        LR.publish(api, "o/n", "b", files(b="2"), "m", attempts=2, sleep=lambda s: None)


def test_durability_is_checked_through_the_server():
    api = FakeApi()
    res = LR.publish(api, "o/n", "b", files(a="1"), "m")
    api.refs["b"] = "f" * 40
    api.commits["f" * 40] = {"sha": "f" * 40, "tree": {"sha": ""}, "parents": [], "committer": {"date": "x"}, "author": {"date": "x"}}
    assert LR.verify_durable(api, "o/n", "b", res["commit_sha"]) is False        # the branch no longer contains the seal commit


def test_late_games_use_the_server_commit_time_and_ignore_dry_runs():
    rep = {"sealed": [{"game_id": "g1", "deadline_utc": "2026-10-24T18:50:00Z"}, {"game_id": "g2", "deadline_utc": "2026-10-24T20:50:00Z"}]}
    assert LR.late_games(rep, "2026-10-24T18:49:59Z") == []
    assert LR.late_games(rep, "2026-10-24T18:50:01Z") == ["g1"]
    assert LR.late_games({**rep, "dry_run": True}, "2026-10-24T23:00:00Z") == []


def test_collect_additions_refuses_to_publish_a_modified_or_deleted_tracked_seal(tmp_path):
    import subprocess

    def g(*a):
        return subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True, text=True).stdout
    g("init", "-q")
    (tmp_path / "seals/d").mkdir(parents=True)
    (tmp_path / "seals/d/a.json").write_text("1")
    g("add", "-A")
    g("commit", "-q", "-m", "x")
    (tmp_path / "seals/d/new.json").write_text("2")
    (tmp_path / "stray.txt").write_text("not ledger")
    assert set(LR.collect_additions(str(tmp_path))) == {"seals/d/new.json"}           # untracked files outside the layout are ignored
    (tmp_path / "seals/d/a.json").write_text("EDITED")
    with pytest.raises(LR.Conflict):
        LR.collect_additions(str(tmp_path))
    (tmp_path / "seals/d/a.json").unlink()
    with pytest.raises(LR.Conflict):
        LR.collect_additions(str(tmp_path))


def test_export_and_load_dir_round_trip(tmp_path):
    import subprocess
    led = tmp_path / "led"
    led.mkdir()
    subprocess.run(["git", "-C", str(led), "init", "-q"], check=True)
    (led / "seals/d").mkdir(parents=True)
    (led / "seals/d/a.json").write_bytes(b"1")
    (led / "missed").mkdir()
    (led / "missed/g.json").write_bytes(b"2")
    (led / "ENABLED_UTC").write_bytes(b"2026-10-24T18:00:00Z\n")
    out = tmp_path / "out"
    LR.export(str(led), str(out))
    assert LR.load_dir(str(out)) == {"seals/d/a.json": b"1", "missed/g.json": b"2", "ENABLED_UTC": b"2026-10-24T18:00:00Z\n"}


def test_selftest_passes_on_a_faithful_api_and_only_touches_the_throwaway_branch():
    api = FakeApi()
    api.clock = "2026-10-24T18:20:00Z"
    from datetime import datetime, timezone
    res = LR.selftest(api, "o/n", now=lambda: datetime(2026, 10, 24, 18, 20, 0, tzinfo=timezone.utc), sleep=lambda s: None)
    assert res["ok"], res
    assert set(api.refs) == set()                                       # created, exercised and deleted
    wrote = {c[1] for c in api.log if c[0] in ("POST", "PATCH", "DELETE") and "/git/refs" in c[1]}
    assert all("exec-shadow-seals-selftest" in w or w.endswith("/git/refs") for w in wrote)
    with pytest.raises(LR.Conflict):
        LR.selftest(api, "o/n", branch="exec-shadow-seals")


def test_selftest_fails_loudly_when_the_server_accepts_what_it_must_refuse():
    class Lax(FakeApi):
        def __call__(self, method, ep, body=None):
            if method == "PATCH" and "/git/refs/heads/" in ep:           # a server that moves the ref backwards
                self.refs[ep.split("/git/refs/heads/")[1]] = body["sha"]
                return {}
            return super().__call__(method, ep, body)
    from datetime import datetime, timezone
    res = LR.selftest(Lax(), "o/n", now=lambda: datetime(2026, 10, 24, 18, 20, 0, tzinfo=timezone.utc), sleep=lambda s: None)
    assert res["ok"] is False and res["checks"]["non_fast_forward_refused_by_server"] is False
