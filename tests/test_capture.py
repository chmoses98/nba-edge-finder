import json

from nba_edge.archive.capture import _count, snapshot_markets, snapshot_orderbooks
from nba_edge.archive.ledger import Ledger
from nba_edge.kalshi.client import KalshiError
from nba_edge.kalshi.ontology import Ontology

FIX = json.loads(open("data/fixtures/kalshi_sample_markets.json").read())


class FakeClient:
    request_count = 0

    def __init__(self, fail_series=()):
        self.fail = set(fail_series)

    def iter_markets(self, series_ticker=None, status=None, max_pages=None, **kw):
        if series_ticker in self.fail:
            raise KalshiError("boom")
        if series_ticker == "KXNBAGAME" and status == "open":
            yield dict(FIX["KXNBAGAME"])
            yield dict(FIX["KXNBAGAME"])  # duplicate across pages must be dropped
        if series_ticker == "KXNBAWINS" and status == "open":
            yield dict(FIX["KXNBAWINS"])

    def get_orderbook(self, ticker, depth=10):
        if ticker.startswith("KXNBAWINS"):
            raise KalshiError("no book")
        return {"yes": [[60, 100], [59, 50]], "no": [[38, 120]]}


def test_snapshot_markets_dedupes_and_classifies():
    onto = Ontology.load()
    rows = snapshot_markets(FakeClient(fail_series=["KXNBAPTS"]), ["KXNBAGAME", "KXNBAWINS", "KXNBAPTS"], ["open", "unopened"], onto)
    tickers = [r.get("ticker") for r in rows if "ticker" in r]
    assert tickers.count("KXNBAGAME-26OCT20OKCSAS-SAS") == 1
    assert {r["_family"] for r in rows if "_family" in r} == {"game_winner", "season_wins"}
    errs = [r for r in rows if "_error" in r]
    assert len(errs) == 2 and all(e["series_ticker"] == "KXNBAPTS" for e in errs)  # one per status, never silent
    assert _count(rows, "_support") == {"None": 2, "PRICED": 1, "RESEARCH": 1}


def test_orderbooks_prioritise_open_and_record_errors(tmp_path):
    onto = Ontology.load()
    rows = snapshot_markets(FakeClient(), ["KXNBAGAME", "KXNBAWINS"], ["open"], onto)
    books = snapshot_orderbooks(FakeClient(), rows, max_books=5)
    by = {b["ticker"]: b for b in books}
    assert by["KXNBAGAME-26OCT20OKCSAS-SAS"]["yes"][0] == [60, 100]
    assert "_error" in by["KXNBAWINS-27UTA-60"]
    led = Ledger(tmp_path, run_id="t")
    e = led.append_rows("kalshi/orderbooks", books)
    assert e.rows == 2 and led.verify() == []
