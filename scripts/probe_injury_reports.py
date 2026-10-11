"""Probe the point-in-time injury/availability sources from a GitHub-hosted runner (read-only).

* official.nba.com season index page -> the list of archived official injury-report PDFs (the report
  timestamp is in each filename), and a few PDFs' extracted text so the parser is written against
  the real layout.
* ESPN ``/injuries`` -> the per-injury fields, in particular whether an entry carries its own
  update ``date`` (the only point-in-time hint ESPN gives).

    python scripts/probe_injury_reports.py
"""

from __future__ import annotations

import io
import json
import re
from collections import Counter

import httpx

from nba_edge.data.http import BROWSER_HEADERS, PLAIN_HEADERS_OK

INDEX_URLS = [
    "https://official.nba.com/nba-injury-report-2025-26-season/",
    "https://official.nba.com/nba-injury-report-2024-25-season/",
]
PDF_RE = re.compile(r"https?://ak-static\.cms\.nba\.com/referee/injury/Injury-Report_[0-9A-Za-z_\-]+\.pdf")
ESPN_INJ = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries"


def main() -> int:
    with httpx.Client(timeout=40.0, follow_redirects=True) as c:
        links: list[str] = []
        for url in INDEX_URLS:
            for label, h in (("BROWSER", BROWSER_HEADERS), ("PLAIN", PLAIN_HEADERS_OK)):
                try:
                    r = c.get(url, headers=h)
                except Exception as e:  # noqa: BLE001
                    print(url, label, type(e).__name__, str(e)[:150])
                    continue
                found = sorted(set(PDF_RE.findall(r.text)))
                print(url, label, r.status_code, len(r.text), "pdf links:", len(found))
                if found:
                    print("  first:", found[:3])
                    print("  last:", found[-3:])
                    suffix = Counter(re.sub(r".*Injury-Report_\d{4}-\d{2}-\d{2}_", "", f) for f in found)
                    print("  time-suffix mix (top 30):", suffix.most_common(30))
                    if "2025-26" in url:
                        links = found
                    break
        for u in ([links[len(links) // 2], links[-1]] if links else []) + [
            "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-01-15_05_30PM.pdf",
            "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-01-15_05PM.pdf",
        ]:
            try:
                r = c.get(u, headers=PLAIN_HEADERS_OK)
            except Exception as e:  # noqa: BLE001
                print(u, type(e).__name__)
                continue
            print("\nPDF", u, r.status_code, len(r.content), r.headers.get("last-modified"))
            if r.status_code == 200:
                from pypdf import PdfReader

                rd = PdfReader(io.BytesIO(r.content))
                txt = "\n".join((p.extract_text() or "") for p in rd.pages)
                print("pages", len(rd.pages), "chars", len(txt))
                print(txt[:3500])
                try:
                    lay = rd.pages[0].extract_text(extraction_mode="layout")
                    print("--- layout mode ---")
                    print(lay[:3500])
                except Exception as e:  # noqa: BLE001
                    print("layout mode failed", e)
        try:
            r = c.get(ESPN_INJ, headers=PLAIN_HEADERS_OK)
            d = r.json()
            print("\nESPN injuries", r.status_code, "top keys", list(d.keys()))
            t0 = (d.get("injuries") or [{}])[0]
            print("team keys", list(t0.keys()))
            print("injury sample", json.dumps((t0.get("injuries") or [])[:2])[:2500])
        except Exception as e:  # noqa: BLE001
            print("ESPN injuries failed", type(e).__name__, str(e)[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
