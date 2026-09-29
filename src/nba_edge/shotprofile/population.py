"""Which shot events a study is allowed to see by default.

Preseason basketball is played by different people under different rules of engagement: two-way and camp
contracts take a large share of the minutes, rotations are experiments, and results are meaningless to the
teams playing them. Those shots were nonetheless inside every shot-profile study run before schema
``shotevent/2``, because until then a row carried no way to tell them apart. They are still *stored* -- nothing
is deleted -- but a study now has to ask for them by name.

The filter fails loudly on an unlabelled frame rather than passing it through. A silent pass-through is how
the contamination happened the first time, and "the column was missing" is the one case where defaulting to
permissive reproduces the original bug exactly.
"""

from __future__ import annotations

from typing import Any

from nba_edge.schemas.core import SeasonType

# The default research population: the games that count. Play-in games are included as postseason -- they are
# played by the same rotations under the same stakes as a playoff game, and they settle real markets.
RESEARCH_SEASON_TYPES: tuple[str, ...] = (
    SeasonType.REGULAR.value,
    SeasonType.PLAYIN.value,
    SeasonType.PLAYOFFS.value,
)

# Stored, retained, and excluded unless a caller asks for them explicitly. OTHER is here too: it means the
# authoritative code was missing or unrecognised, which is not a licence to assume the game counted.
EXCLUDED_BY_DEFAULT: tuple[str, ...] = (
    SeasonType.PRESEASON.value,
    SeasonType.ALLSTAR.value,
    SeasonType.OTHER.value,
)


class UnlabelledPopulationError(RuntimeError):
    """Raised when a frame has no usable season_type, so the population cannot be honoured."""


def research_population(
    df: Any, *, season_types: tuple[str, ...] | None = None, include_preseason: bool = False
) -> tuple[Any, dict[str, Any]]:
    """``df`` restricted to the research population, plus a report of what was dropped and why.

    ``season_types`` overrides the default set outright. ``include_preseason`` is the narrow opt-in for a
    study that genuinely wants camp basketball; it widens the default set rather than replacing it.
    """
    wanted = tuple(season_types) if season_types is not None else RESEARCH_SEASON_TYPES
    if include_preseason and SeasonType.PRESEASON.value not in wanted:
        wanted = (*wanted, SeasonType.PRESEASON.value)

    if "season_type" not in df.columns:
        raise UnlabelledPopulationError(
            "shot events carry no season_type column: this frame predates schema shotevent/2. "
            "Run `nba-edge shot-events-migrate` before using it in a study -- filtering cannot be "
            "skipped, because an unfiltered frame is what put preseason inside the earlier results."
        )
    st = df["season_type"].astype("object")
    missing = int((st.isna() | (st == "") | (st == "None")).sum())
    if missing:
        raise UnlabelledPopulationError(
            f"{missing} of {len(df)} shot events carry no season_type value. Re-run the migration; "
            "a partially labelled frame cannot be filtered honestly."
        )

    keep = st.isin(wanted)
    kept = df[keep]
    dropped = df[~keep]
    report = {
        "requested": list(wanted),
        "rows_in": int(len(df)),
        "rows_kept": int(len(kept)),
        "rows_dropped": int(len(dropped)),
        "dropped_by_season_type": {str(k): int(v) for k, v in dropped["season_type"].value_counts().items()},
        "include_preseason": bool(include_preseason),
    }
    return kept.reset_index(drop=True), report
