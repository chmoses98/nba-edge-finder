"""Research-side shim (NOT model code): rate teams on games with an observed outcome only.

The code branch predates main's `ridge_ratings_observed` (nba/features.py). pf_core.pit.rolling_ridge_ratings fits every row of every earlier weekly block, so a slate row (no outcome yet)
in an earlier block than the block being rated reaches sklearn as NaN ("Input y contains NaN"). That is date-triggered: from the 2026-10-26 / 2026-10-27 block boundary on, a
feed spanning both days crashes. This shim applies main's rule without touching nba/ or pf_core/ (the frozen challenger files stay byte-identical): blocks with an observed game are rated
on the observed rows only (identical to the old computation for fully observed input); a block with no observed game is rated from the observed rows of earlier blocks plus its own rows.
Missing outcomes are excluded, never imputed. Fully observed input is passed through unchanged.
"""
import pandas as pd

def install():
    from pf_core import pit
    if getattr(pit.rolling_ridge_ratings, "_observed_only", False):
        return
    orig = pit.rolling_ridge_ratings

    def patched(games, block_col, off_col, def_col, y_col, **kw):
        obs = games[y_col].notna()
        if obs.all():
            return orig(games, block_col, off_col, def_col, y_col, **kw)
        base = orig(games[obs], block_col, off_col, def_col, y_col, **kw)
        parts = [base]
        for b in sorted(set(games[block_col]) - set(games.loc[obs, block_col])):
            frame = pd.concat([games[obs & (games[block_col] < b)], games[games[block_col] == b]])
            r = orig(frame, block_col, off_col, def_col, y_col, **kw)
            parts.append(r[r[block_col] == b])
        parts = [p for p in parts if len(p)]
        return pd.concat(parts, ignore_index=True) if parts else base
    patched._observed_only = True
    pit.rolling_ridge_ratings = patched
