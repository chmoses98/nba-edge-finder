"""Write-once archive I/O for the paper system (same discipline as pf_core.prospective: content-hashed files, additions only)."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Iterable

from .schema import KIND_DIR


def _dump(r: dict) -> str:
    return json.dumps(r, sort_keys=True, default=lambda o: o.item() if hasattr(o, "item") else str(o))


def write_once(root: str, kind: str, day: str, rows: Iterable[dict[str, Any]], now: datetime) -> str | None:
    """Write `rows` as one gz-jsonl file under <root>/<KIND_DIR[kind]>/<day>/. Identical content already present -> that path, no write."""
    rows = list(rows)
    if not rows:
        return None
    payload = "\n".join(_dump(r) for r in rows).encode()
    h = hashlib.sha256(payload).hexdigest()[:12]
    d = os.path.join(root, KIND_DIR[kind], day)
    os.makedirs(d, exist_ok=True)
    for fn in os.listdir(d):
        if fn.endswith(f"_{h}.jsonl.gz"):
            return os.path.join(d, fn)
    path = os.path.join(d, f"{now.strftime('%H%M%S')}Z_{h}.jsonl.gz")
    with gzip.open(path, "xb") as f:
        f.write(payload)
    return path


def days(root: str, kind: str) -> list[str]:
    base = os.path.join(root, KIND_DIR[kind])
    return sorted(os.listdir(base)) if os.path.isdir(base) else []


def read(root: str, kind: str, days_: Iterable[str] | None = None) -> list[dict[str, Any]]:
    base = os.path.join(root, KIND_DIR[kind])
    out: list[dict[str, Any]] = []
    if not os.path.isdir(base):
        return out
    for day in (sorted(days_) if days_ is not None else sorted(os.listdir(base))):
        d = os.path.join(base, day)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".jsonl.gz"):
                    with gzip.open(os.path.join(d, fn), "rt") as f:
                        out += [json.loads(x) for x in f if x.strip()]
    return out


def existing_ids(root: str, kind: str, id_field: str, days_: Iterable[str] | None = None) -> set[str]:
    return {r[id_field] for r in read(root, kind, days_) if id_field in r}


def write_new(root: str, kind: str, day: str, rows: Iterable[dict[str, Any]], id_field: str, now: datetime) -> dict[str, Any]:
    """Idempotent append: rows whose `id_field` is already archived for that day are skipped (counted), the rest are written once."""
    rows = list(rows)
    have = existing_ids(root, kind, id_field, [day])
    new, seen = [], set()
    for r in rows:
        i = r[id_field]
        if i in have or i in seen:
            continue
        seen.add(i)
        new.append(r)
    path = write_once(root, kind, day, new, now)
    return {"written": len(new), "duplicates": len(rows) - len(new), "path": path}
