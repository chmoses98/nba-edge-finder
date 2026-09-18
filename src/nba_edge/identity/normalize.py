"""Name normalization used ONLY to build/lookup durable mappings, never as a production fallback by itself."""

from __future__ import annotations

import re
import unicodedata

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalize_name(name: str) -> str:
    """Lowercase, accent-free, punctuation-free, suffix-free key. 'Jaren Jackson Jr.' -> 'jaren jackson'.
    Not unique in general (duplicate names exist) — that is why it is only a key into an explicit registry."""
    s = strip_accents(name or "").lower()
    s = s.replace("'", "").replace("’", "").replace(".", "")
    s = re.sub(r"[^a-z0-9\s-]", " ", s)
    s = s.replace("-", " ")
    parts = [p for p in s.split() if p and p not in SUFFIXES]
    return " ".join(parts)


def name_variants(name: str) -> set[str]:
    """Reasonable spellings a source might use for the same player."""
    base = normalize_name(name)
    out = {base}
    parts = base.split()
    if len(parts) >= 2:
        out.add(f"{parts[0][0]} {parts[-1]}")  # 'l james'
        out.add(parts[-1])  # surname only (never sufficient alone; used for candidate generation)
    return out
