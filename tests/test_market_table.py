"""Canonical market-observation table: executable prices, horizons, and the never-substitute-a-post-tip rule."""

from __future__ import annotations

import gzip
import json

import pandas as pd
import pytest

from nba_edge.research import market_table as MT

TIP_TS = 1_767_225_600  # 2026-01-01T00:00:00Z
DAY = "2026-01-01"


def _candle(ticker, ts, bid, ask, volume="10.0"):
    return {
        "ticker": ticker, "series_ticker": ticker.split("-")[0], "end_period_ts": ts, "period_interval": 60,
        "yes_bid": {"close": f"{bid/100:.4f}"}, "yes_ask": {"close": f"{ask/100:.4f}"},
        "price": {"close": None}, "volume": volume, "open_interest": "5.0",
    }


def _write(kdir, series, markets, candles):
    with gzip.open(kdir / f"markets_{series}.jsonl.gz", "wt") as f:
        for m in markets:
            f.write(json.dumps(m) + "\n")
    with gzip.open(kdir / f"candles_{series}.jsonl.gz", "wt") as f:
        for c in candles:
            f.write(json.dumps(c) + "\n")


@pytest.fixture
def kdir(tmp_path, monkeypatch):
    d = tmp_path / "kalshi"
    d.mkdir()
    monkeypatch.setattr(MT, "tip_index", lambda _root: {
        (DAY, "BOS", "NYK"): {
            "game_id": "espn:1", "season": "2025-26", "tip_utc": "2026-01-01T00:00:00Z", "tip_ts": TIP_TS,
            "home_team_id": 1610612752, "away_team_id": 1610612738, "home": "NYK", "away": "BOS",
            "game_date_et": DAY,
        }
    })
    return d


def test_cents_handles_dollar_strings_and_cent_ints():
    assert MT._cents("0.5300") == 53 and MT._cents("1.0000") == 100 and MT._cents(57) == 57
    assert MT._cents(None) is None and MT._cents("") is None and MT._cents("junk") is None


def test_horizons_pick_last_candle_at_or_before_each_cutoff_and_never_after_tip(kdir):
    tk = "KXNBAGAME-26JAN01BOSNYK-NYK"
    m = {"ticker": tk, "series_ticker": "KXNBAGAME", "title": "New York wins", "yes_sub_title": "New York",
         "strike_type": "structured", "custom_strike": "{'basketball_team': 'uuid-nyk'}", "result": "yes",
         "rules_primary": "If New York wins the Boston at New York professional basketball game originally "
                          "scheduled for Jan 1, 2026, then the market resolves to Yes."}
    candles = [
        _candle(tk, TIP_TS - 30 * 3600, 40, 42),   # before T-24h
        _candle(tk, TIP_TS - 25 * 3600, 44, 46),   # the T-24h pick
        _candle(tk, TIP_TS - 2 * 3600, 50, 52),    # the T-6h? no: after it. T-90m/T-30m pick
        _candle(tk, TIP_TS - 600, 60, 62),         # final pre-tip pick
        _candle(tk, TIP_TS + 3600, 95, 97),        # POST-TIP: must never be used
    ]
    _write(kdir, "KXNBAGAME", [m], candles)
    df = MT.build_market_table(kdir, kdir)
    by = df.set_index("horizon")
    assert by.loc["T-24h", "yes_ask_cents"] == 46
    assert by.loc["T-90m", "yes_ask_cents"] == 52
    assert by.loc["final", "yes_ask_cents"] == 62
    # the post-tip candle is never selected at any horizon
    assert (df["market_ts"] < TIP_TS).all()
    assert df["seconds_before_tip"].min() > 0


def test_executable_prices_follow_kalshi_convention(kdir):
    tk = "KXNBAGAME-26JAN01BOSNYK-NYK"
    m = {"ticker": tk, "series_ticker": "KXNBAGAME", "title": "New York wins", "yes_sub_title": "New York",
         "strike_type": "structured", "custom_strike": "{'basketball_team': 'u'}", "result": "no",
         "rules_primary": "If New York wins the Boston at New York professional basketball game originally "
                          "scheduled for Jan 1, 2026, then the market resolves to Yes."}
    _write(kdir, "KXNBAGAME", [m], [_candle(tk, TIP_TS - 600, 53, 57)])
    r = MT.build_market_table(kdir, kdir).iloc[0]
    assert r.exec_yes_cents == 57          # buying YES pays the YES ask
    assert r.exec_no_cents == 100 - 53     # buying NO pays 100 - YES bid
    assert r.mid_cents_analysis_only == 55 and r.spread_cents == 4
    assert r.p_market == pytest.approx(0.55) and r.p_market_exec_yes == pytest.approx(0.57)
    assert r.outcome == 0.0 and r.result_raw == "no"


def test_scalar_dnp_and_unsettled_markets_produce_no_outcome_rows(kdir):
    base = {"series_ticker": "KXNBAPTS", "strike_type": "structured", "floor_strike": "19.5",
            "title": "X records 20+ points", "yes_sub_title": "X: 20+",
            "custom_strike": "{'basketball_player': 'pu', 'basketball_team': 'tu'}",
            "rules_primary": "If X records 20+ Points in the Boston at New York professional basketball game "
                             "originally scheduled for Jan 1, 2026, then the market resolves to Yes."}
    ok = {**base, "ticker": "KXNBAPTS-26JAN01BOSNYK-NYKX-20", "result": "yes"}
    dnp = {**base, "ticker": "KXNBAPTS-26JAN01BOSNYK-NYKY-20", "result": "scalar"}
    unsettled = {**base, "ticker": "KXNBAPTS-26JAN01BOSNYK-NYKZ-20", "result": ""}
    cs = [_candle(t["ticker"], TIP_TS - 600, 40, 43) for t in (ok, dnp, unsettled)]
    _write(kdir, "KXNBAPTS", [ok, dnp, unsettled], cs)
    df = MT.build_market_table(kdir, kdir)
    assert set(df.ticker) == {ok["ticker"]}  # only the binary-settled market yields rows
    assert df.iloc[0].threshold == 19.5 and df.iloc[0].family == "player_points"


def test_crossed_degenerate_and_wide_quotes_are_rejected(kdir):
    tk = "KXNBAGAME-26JAN01BOSNYK-NYK"
    m = {"ticker": tk, "series_ticker": "KXNBAGAME", "title": "New York wins", "yes_sub_title": "New York",
         "strike_type": "structured", "custom_strike": "{'basketball_team': 'u'}", "result": "yes",
         "rules_primary": "If New York wins the Boston at New York professional basketball game originally "
                          "scheduled for Jan 1, 2026, then the market resolves to Yes."}
    candles = [
        _candle(tk, TIP_TS - 5000, 60, 55),   # crossed (ask < bid)
        _candle(tk, TIP_TS - 4000, 0, 30),    # no bid
        _candle(tk, TIP_TS - 3000, 30, 100),  # no ask
        _candle(tk, TIP_TS - 2000, 10, 80),   # 70c spread: unusable
    ]
    _write(kdir, "KXNBAGAME", [m], candles)
    assert MT.build_market_table(kdir, kdir).empty
    # a sane quote in the same series does produce a row
    _write(kdir, "KXNBAGAME", [m], [*candles, _candle(tk, TIP_TS - 1000, 45, 48)])
    df = MT.build_market_table(kdir, kdir)
    assert len(df) and set(df.yes_ask_cents) == {48}


def test_missing_tip_drops_the_market_rather_than_guessing(kdir, monkeypatch):
    monkeypatch.setattr(MT, "tip_index", lambda _root: {})
    tk = "KXNBAGAME-26JAN01BOSNYK-NYK"
    m = {"ticker": tk, "series_ticker": "KXNBAGAME", "title": "New York wins", "yes_sub_title": "New York",
         "strike_type": "structured", "custom_strike": "{'basketball_team': 'u'}", "result": "yes"}
    _write(kdir, "KXNBAGAME", [m], [_candle(tk, TIP_TS - 600, 50, 52)])
    assert MT.build_market_table(kdir, kdir).empty


def test_table_schema_and_summary(kdir):
    tk = "KXNBAGAME-26JAN01BOSNYK-NYK"
    m = {"ticker": tk, "series_ticker": "KXNBAGAME", "title": "New York wins", "yes_sub_title": "New York",
         "strike_type": "structured", "custom_strike": "{'basketball_team': 'u'}", "result": "yes",
         "rules_primary": "If New York wins the Boston at New York professional basketball game originally "
                          "scheduled for Jan 1, 2026, then the market resolves to Yes."}
    _write(kdir, "KXNBAGAME", [m], [_candle(tk, TIP_TS - 600, 50, 52)])
    df = MT.build_market_table(kdir, kdir)
    assert list(df.columns) == MT.COLUMNS
    # model columns exist but are unfilled here: this table is a record of the market, not of the model
    assert df.p_data_only.isna().all() and df.p_hybrid.isna().all()
    assert "game_winner" in MT.summarize(df)
    assert MT.summarize(pd.DataFrame()) == "market table is EMPTY"
