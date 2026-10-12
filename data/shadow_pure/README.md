# PURE shadow collections

The stores themselves live on per-sport append-only data branches, not on main. NBA: branch `nba-shadow-pure`, which the
workflow mounts at `data/shadow_pure/nba` (see `docs/research/SHADOW_PURE_NBA.md`). Files under this directory that exist
on `origin/main` must never be modified or deleted (`tests/test_shadow_pure_immutability.py`).
