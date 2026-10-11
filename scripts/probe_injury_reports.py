"""Probe the point-in-time injury/availability sources from a GitHub-hosted runner (read-only).

Round 2 (round 1 found: direct PDFs on the ``_HH_MMAM`` pattern answer 200 with a Last-Modified header;
missing slots answer 403; the official.nba.com index page loads but exposes no static PDF links;
plain ``extract_text`` emits one token per line, ``extraction_mode="layout"`` keeps rows):

* the index page: where (if anywhere) report links live in its HTML;
* publication cadence: HEAD every 15-minute slot of two dates (status + Last-Modified);
* full layout-mode text of two pages, so the parser is written against the real layout.

    python scripts/probe_injury_reports.py
"""

from __future__ import annotations

import io
import re
from datetime import datetime, timedelta

import httpx

from nba_edge.data.http import BROWSER_HEADERS, PLAIN_HEADERS_OK

INDEX_URL = "https://official.nba.com/nba-injury-report-2025-26-season/"
PDF = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{d}_{t}.pdf"


def main() -> int:
    with httpx.Client(timeout=40.0, follow_redirects=True) as c:
        r = c.get(INDEX_URL, headers=BROWSER_HEADERS)
        html = r.text
        print("index", r.status_code, len(html))
        for m in list(re.finditer(r"(?i)injury[-_ ]report|\.pdf|ak-static|referee", html))[:15]:
            print("  ...", html[max(0, m.start() - 150): m.end() + 150].replace("\n", " "))
        for day in ("2026-01-15", "2025-11-29"):
            t = datetime(2000, 1, 1, 0, 0)
            found = []
            for _ in range(96):
                slot = t.strftime("%I_%M%p")
                u = PDF.format(d=day, t=slot)
                h = c.head(u, headers=PLAIN_HEADERS_OK)
                if h.status_code == 200:
                    found.append((slot, h.headers.get("last-modified"), h.headers.get("content-length")))
                t += timedelta(minutes=15)
            print(f"\n{day}: {len(found)} slots exist")
            for f in found:
                print("  ", f)
        u = PDF.format(d="2026-01-15", t="05_30PM")
        r = c.get(u, headers=PLAIN_HEADERS_OK)
        from pypdf import PdfReader

        rd = PdfReader(io.BytesIO(r.content))
        for i in (0, 5, len(rd.pages) - 1):
            print(f"\n--- layout page {i} ---")
            print(rd.pages[i].extract_text(extraction_mode="layout"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
