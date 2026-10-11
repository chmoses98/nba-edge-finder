# W1-C step 1: where `p_rotation` is consumed, and which scorecards predate it

Verified against `main` at `4800ab3` (2026-10-10). File:line references are to that commit.

## The single consumption path (production and every research script)

```
workflows/simulate.py:236      build_game_params(game_in, tg, pg, cutoff, inj_map, rosters, BuildConfig())
  features/build.py:237-241      rot_series = team-aligned minutes over the last rotation_window (20) team games,
                                 0 for every game not played  ->  estimate_profile(...)
  features/build.py:266          PlayerParams(..., p_rotation=rot.p_rotation, rot_min_mean=..., rot_min_sd=...)
  features/build.py:219-220      no-prior-game players: deep-bench prior p_rotation=0.08, rot_min_mean=12, rot_min_sd=5
workflows/simulate.py:240      simulate(gp, n_sims, seed)            (fixed --sims)
  or sim/convergence.py:59     simulate_batch(gp, batch, rng)        (default: simulate_until_converged)
sim/engine.py:239              minutes = draw_minutes_auto(rng, team.players, played, 240)
sim/minutes.py:99-114          draw_minutes_auto:
  sim/minutes.py:86-96           has_rotation_profiles(players) -- ALL-or-nothing: every player needs
                                 p_rotation, rot_min_mean, rot_min_sd, else legacy water-fill (minutes.py:102)
  sim/minutes.py:105-112         RotationProfile(p_rotation=float(pl.p_rotation), ..., role=classify_role(...))
  sim/minutes.py:114             draw_rotation_minutes(rng, profiles, played, caps, total_minutes)
sim/rotation.py:130            p_rot = [p.p_rotation ...]
sim/rotation.py:146            _calibrate_logits(p_rot, played, mean target size)  (log-odds offset, rotation.py:80-109)
sim/rotation.py:147-152        Gumbel-top-k membership with size drawn from ROTATION_SIZE_PMF (rotation.py:47)
sim/rotation.py:159            promotion-under-pressure order = argsort(-p_rot)
```

Because `build_game_params` sets all three rotation fields on **every** `PlayerParams` it creates
(both the normal branch, build.py:266, and the no-history branch, build.py:219-220), the
all-or-nothing check in `has_rotation_profiles` is always true on real inputs. **The rotation mixture
is therefore the only path production and every research script currently run.** The legacy
water-fill (`draw_minutes`, minutes.py:74-83) is reachable only when params are built by hand
(tests) or when profiles are deliberately stripped (`scripts/minutes_validation.py:39-45`, and the
`sim_waterfill` diagnostic arm of this lane).

Research callers that go through the same path today: `research/prop_walk_forward.py:84,87`,
`research/market_vs_model.py:136,140`, `research/walk_forward.py:81,84`,
`scripts/minutes_validation.py:67,70` (NEW arm) and `:71` (OLD arm, profiles stripped).

Note the production call passes the injury map and rosters; every research path (including this
lane) passes `{h: {}, a: {}}` and `None`, because no point-in-time injury history is committed. The
research `p_play` is therefore the participation proxy at build.py:205-214.

## Which numbers predate Phase 3/4 (rotation mixture landed 2026-09-23 11:22 UTC, `f49e4f4`)

| artifact | committed | minutes model it measured | population | still quoted as current? |
|---|---|---|---|---|
| `prop_walk_forward{,_v2,_v3}.json`, RESEARCH_NOTES §4c, HANDOFF "Brier 0.201 → 0.165" | 2026-09-18 | **water-fill** | 100 market-listed games, **7,666 ladder rungs pooled** | yes — the Wave 1 audit quotes "v3 Brier 0.165" |
| `PROP_BIAS_DIAGNOSIS.md` ("13.56 vs 10.07 players ≥5 min", "13–25% low", "efficiency is fine") | 2026-09-18 | **water-fill** | ladder-bracketed player-games (market-selected) and "all who played" (outcome-selected) | yes — Wave 1 audit item 2; AUDIT_FOLLOWUPS R4 "RESOLVED … minutes, not efficiency" |
| `ALL_FAMILIES_MODEL_VS_MARKET.md` | 2026-09-18 | **water-fill** | settled markets | kept as the "old" column of AFTER_REPAIRS |
| `INJURY_IMPACT.md` / `impact_validation.json` | 2026-09-23 11:28 | n/a (team-level APM) | team-games | correctly current (rejection stands) |
| `MINUTES_MODEL.md` / `minutes_validation.json` | 2026-09-23 12:22 | **both** (old vs new, same features) | last 150 home games of 2025-26, roster players | current; its "~20% low, rotation closes 6–8%" frame is explicitly called selection-biased by the doc itself |
| `AFTER_REPAIRS.md` | 2026-09-23 12:42 | **rotation** + rating_scale 1.9 | settled markets, de-laddered table included | current |

So yes: the two headline figures carried forward into Wave 1 — *"v3 historical props Brier 0.165"*
and *"13.56 players ≥5 min vs 10.07"* — were measured on the pre-rotation water-fill simulator, on
market-listed populations, with ladder rungs pooled in the Brier. `AUDIT_FOLLOWUPS.md` R4's
"efficiency is fine" conclusion was later qualified by `MINUTES_MODEL.md` (points per minute 0.95
of actual, conditioned on playing). None of these are restated here as current; the matched
scorecard in `MATCHED_DECOMPOSITION.md` replaces them for the questions Wave 1 asks, and keeps the
water-fill arm alongside so the old/new difference is measured on identical rows rather than
inferred across documents.
