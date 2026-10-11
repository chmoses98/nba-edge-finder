"""Runtime non-leakage proof for the W1-C PURE path, with a negative control that has power.

The PURE forecasts are RE-RUN end to end (feature build -> simulation -> EWM-5 baseline -> sidecar)
three times on the same sports snapshot, cutoffs and seeds:

    normal       data/history/kalshi as committed
    removed      data/history/kalshi deleted from the data root
    randomized   every price / strike / result field in every committed Kalshi file replaced by noise

and the model-owned sidecar bytes must be identical (sha256), which the kit gate's ``mutation``
command must also confirm. A test that cannot fail proves nothing, so the same mutation is applied to
a NEGATIVE CONTROL: the production HYBRID formula (``workflows.simulate._hybrid``, market weight 0.70)
applied to the PURE points ladder with the listed contract's last price. It reads the market, so it
MUST change under both mutations; if it does not, the harness is broken and the run fails.

    python scripts/nba_pure_mutation_test.py --games 20 --sims 600 --work $SCRATCH/nba/mutation \
        --kit $KIT/scripts/prop_projection_gate.py --json docs/research/pure_mutation_test.json
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

PRICE_KEYS = ("price", "bid", "ask", "strike", "result", "settlement", "volume", "liquidity", "interest", "close", "open", "high", "low", "mean")


def _runner():
    spec = importlib.util.spec_from_file_location("nba_matched_decomposition", ROOT / "scripts" / "nba_matched_decomposition.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["nba_matched_decomposition"] = mod
    spec.loader.exec_module(mod)
    return mod


def _noise(v, rng: random.Random):
    if isinstance(v, bool):
        return rng.random() < 0.5
    if isinstance(v, (int, float)):
        return round(rng.uniform(0, 60), 2)
    if isinstance(v, str):
        try:
            float(v)
            return f"{rng.uniform(0.01, 0.99):.4f}"
        except ValueError:
            return rng.choice(["yes", "no"]) if v in ("yes", "no") else v
    return v


def _mutate_obj(o, rng: random.Random):
    if isinstance(o, dict):
        return {k: (_noise(v, rng) if any(p in k.lower() for p in PRICE_KEYS) and not isinstance(v, (dict, list)) else _mutate_obj(v, rng)) for k, v in o.items()}
    if isinstance(o, list):
        return [_mutate_obj(v, rng) for v in o]
    return o


def make_roots(work: Path, src_data: Path, seed: int = 99, only: set[str] | None = None) -> dict[str, Path]:
    """Three data roots sharing the SAME sports snapshot (symlinked), differing only in market files."""
    if work.exists():
        shutil.rmtree(work)
    roots = {}
    for name in ("normal", "removed", "randomized"):
        r = work / name / "data"
        (r / "history").mkdir(parents=True)
        os.symlink((src_data / "history" / "espn").resolve(), r / "history" / "espn")
        if name == "normal":
            os.symlink((src_data / "history" / "kalshi").resolve(), r / "history" / "kalshi")
        elif name == "randomized":
            rng = random.Random(seed)
            kd = r / "history" / "kalshi"
            kd.mkdir()
            for fp in sorted((src_data / "history" / "kalshi").iterdir()):
                if fp.name.endswith(".jsonl.gz") and (only is None or fp.name in only):
                    with gzip.open(fp, "rt") as fi, gzip.open(kd / fp.name, "wt") as fo:
                        for line in fi:
                            fo.write(json.dumps(_mutate_obj(json.loads(line), rng)) + "\n")
                else:
                    shutil.copy(fp, kd / fp.name)
        roots[name] = r
    return roots


def last_prices(data_root: Path, keys: set[tuple[str, int]], market_file: Path | None = None) -> dict[tuple[str, int, float], float]:
    """(game_id, player_id, at_least) -> last price, for the NEGATIVE CONTROL only."""
    from nba_edge.data.history import load_team_games
    from nba_edge.identity.players import PlayerRegistry
    from nba_edge.identity.teams import registry
    from nba_edge.kalshi.ticker import parse_ticker

    fp = market_file or data_root / "history" / "kalshi" / "markets_KXNBAPTS.jsonl.gz"
    if not fp.exists():
        return {}
    reg = registry()
    uuid_to_id = {r.aliases["kalshi_uuid"]: r.nba_id for r in PlayerRegistry.load().records.values() if "kalshi_uuid" in r.aliases}
    tg = load_team_games(data_root / "history", ["2025-26"])
    home = tg[tg["home"] == True]  # noqa: E712
    gid = {(str(r.game_date_et), reg.by_id(int(r.team_id)).tricode, reg.by_id(int(r.opp_team_id)).tricode): str(r.game_id) for r in home.itertuples(index=False)}
    out = {}
    with gzip.open(fp, "rt") as fh:
        for line in fh:
            m = json.loads(line)
            pt = parse_ticker(m.get("ticker", ""), reg.tricodes)
            if not pt.game_date or not pt.home_tricode:
                continue
            g = gid.get((pt.game_date.isoformat(), pt.home_tricode, pt.away_tricode))
            pid = uuid_to_id.get(((m.get("custom_strike") or {}).get("basketball_player")) or "")
            if g is None or pid is None or (g, int(pid)) not in keys:
                continue
            try:
                strike = float(m["floor_strike"]) + 0.5
                px = float(m["last_price_dollars"])
            except (KeyError, TypeError, ValueError):
                continue
            out[(g, int(pid), strike)] = px
    return out


def leaky_control(sidecar: Path, data_root: Path, dest: Path, market_file: Path | None = None) -> Path:
    """NEGATIVE CONTROL: production HYBRID blend of the PURE points ladder with listed last prices."""
    from nba_edge.workflows.simulate import _hybrid

    rows = [json.loads(x) for x in gzip.open(sidecar, "rt")]
    keys = {(r["game_id"], int(r["player_id"])) for r in rows if r["statistic"] == "points"}
    px = last_prices(data_root, keys, market_file)
    buf = []
    for r in rows:
        if r["statistic"] == "points":
            ths = r["projection"]["thresholds"]
            for t in ths:
                q = px.get((r["game_id"], int(r["player_id"]), float(t["at_least"])))
                if q is not None:
                    t["probability"] = round(float(_hybrid(t["probability"], q)), 4)
            for j in range(1, len(ths)):
                ths[j]["probability"] = min(ths[j]["probability"], ths[j - 1]["probability"])
        buf.append(json.dumps(r, sort_keys=True) + "\n")
    dest.write_bytes(gzip.compress("".join(buf).encode("utf-8"), mtime=0))
    return dest


def sha(p: Path) -> str:
    return hashlib.sha256(gzip.open(p, "rb").read()).hexdigest()


def gate_mutation(kit: Path | None, before: Path, after: Path, work: Path) -> dict | None:
    if not kit:
        return None
    b, a = work / (before.name + ".plain.jsonl"), work / (after.parent.name + "_" + after.name + ".plain.jsonl")
    b.write_bytes(gzip.open(before, "rb").read())
    a.write_bytes(gzip.open(after, "rb").read())
    p = subprocess.run([sys.executable, "-I", str(kit), "mutation", "--before", str(b), "--after", str(a)], capture_output=True, text=True)
    res = json.loads(p.stdout) if p.stdout.strip() else {"stderr": p.stderr}
    return {"exit_code": p.returncode, "passed": res.get("passed"), "base_rows": res.get("base_rows"),
            "n_changed_model_outputs_listed": len(res.get("changed_model_outputs", []))}


def run(work: Path, n_games: int, n_sims: int, kit: Path | None, src_data: Path = ROOT / "data", only: set[str] | None = None) -> dict:
    """``only`` limits which market files are randomized (unit-test speed); None randomizes all of them."""
    runner = _runner()
    roots = make_roots(work, src_data, only=only)
    side: dict[str, dict[str, Path]] = {}
    for name, root in roots.items():
        out = work / name / "out"
        runner.collect(root, "holdout", out, n_sims, n_games)
        paths = runner.write_sidecars(out, "holdout", out / "sidecars")
        side[name] = {k: Path(v["path"]) for k, v in paths.items()}
        side[name]["leaky"] = leaky_control(side[name]["sim_rotation_unc"], root, out / "sidecars" / "leaky_hybrid_points.jsonl.gz")
    res: dict = {"n_games": n_games, "n_sims": n_sims, "randomized_files": sorted(only) if only else "all", "pure": {}, "negative_control": {}}
    for mut in ("removed", "randomized"):
        res["pure"][mut] = {k: sha(side["normal"][k]) == sha(side[mut][k]) for k in side["normal"] if k != "leaky"}
        res["negative_control"][mut] = {"identical": sha(side["normal"]["leaky"]) == sha(side[mut]["leaky"])}
        res["pure"][mut]["gate_sim_rotation_unc"] = gate_mutation(kit, side["normal"]["sim_rotation_unc"], side[mut]["sim_rotation_unc"], work)
        res["negative_control"][mut]["gate"] = gate_mutation(kit, side["normal"]["leaky"], side[mut]["leaky"], work)
    res["normal_leaky_differs_from_pure"] = sha(side["normal"]["leaky"]) != sha(side["normal"]["sim_rotation_unc"])
    res["sha256_sim_rotation_unc"] = sha(side["normal"]["sim_rotation_unc"])
    pure_ok = all(v is True for m in res["pure"].values() for k, v in m.items() if not k.startswith("gate"))
    control_ok = all(not v["identical"] for v in res["negative_control"].values()) and res["normal_leaky_differs_from_pure"]
    res["passed"] = bool(pure_ok and control_ok)
    res["pure_identical_under_all_mutations"] = pure_ok
    res["negative_control_changed_under_all_mutations"] = control_ok
    return res


def randomize_gz_jsonl(src: Path, dst: Path, seed: int) -> None:
    """Format-preserving randomizer (for the shared gate's ``randomizer_cmd``)."""
    rng = random.Random(seed)
    lines = [json.dumps(_mutate_obj(json.loads(x), rng)) + "\n" for x in gzip.open(src, "rt")]
    dst.write_bytes(gzip.compress("".join(lines).encode("utf-8"), mtime=0))


def model_cmd(out: Path, games: int, sims: int, market_file: Path | None, control: bool) -> int:
    """Entry for ``pure_gate.py rerun``. The PURE path receives ``--market-file`` and never opens it;
    the control (``--control``) is the same run followed by the HYBRID blend that reads it."""
    runner = _runner()
    runner.collect(ROOT / "data", "holdout", out / "run", sims, games)
    paths = runner.write_sidecars(out / "run", "holdout", out / "run" / "sidecars")
    src = Path(paths["sim_rotation_unc"]["path"])
    if control:
        leaky_control(src, ROOT / "data", out / "forecast.jsonl.gz", market_file if market_file and market_file.exists() else Path("/nonexistent"))
    else:
        shutil.copy(src, out / "forecast.jsonl.gz")
    shutil.copy(paths["ewm5_unc"]["path"], out / "baseline.jsonl.gz")
    shutil.rmtree(out / "run")
    return 0


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "randomize":
        randomize_gz_jsonl(Path(argv[1]), Path(argv[2]), int(argv[3]))
        return 0
    if argv and argv[0] in ("model", "control"):
        mp = argparse.ArgumentParser()
        mp.add_argument("--out", type=Path, required=True)
        mp.add_argument("--market-file", type=Path)
        mp.add_argument("--games", type=int, default=3)
        mp.add_argument("--sims", type=int, default=300)
        b = mp.parse_args(argv[1:])
        return model_cmd(b.out, b.games, b.sims, b.market_file, argv[0] == "control")
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--sims", type=int, default=600)
    ap.add_argument("--kit", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    res = run(a.work, a.games, a.sims, a.kit)
    txt = json.dumps(res, indent=1)
    if a.json:
        a.json.write_text(txt + "\n")
    print(txt)
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
