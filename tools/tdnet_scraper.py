"""
JII Compounders - Capital-Allocation Inflection Feed - TDnet scraper.

Scrapes the TSE TDnet "open-list" pages per:
    3 Pipeline/5 Assets/Website/jpinv.com/compounders/feed/_SPEC.md
    Section 3 (Data sources), Section 7 (Backfill), Section 8 (Update loop).

Public API:
    TdnetScraper(rate_limit_sec=1.0, user_agent=...)
        .iter_disclosures(start, end) -> Iterator[dict]
            yields disclosure dicts in the shape `classifier.classify()`
            expects (see tools/classifier.py).

Politeness:
    * 1.0s spacing between requests (configurable).
    * Polite User-Agent.
    * Exponential backoff on 429/503 (max 3 attempts).
    * 404 means the day has no disclosures or page-index is past the end
      of the day's pagination -> stop the inner loop, no retry.

TDnet HTML structure (as of 2026-05):
    Page URL: https://www.release.tdnet.info/inbs/I_list_{NNN}_{YYYYMMDD}.html
    100 rows per page, paginated NNN=001..NNN.
    Each row is a <tr> inside <table id="main-list-table"> with TDs:
        .kjTime    HH:MM  (JST)
        .kjCode    5-digit ticker (last char is 0 padding)
        .kjName    company name (JP, fixed-width padded)
        .kjTitle   contains <a href="...pdf"> with disclosure title
        .kjXbrl    optional <a href="...zip"> XBRL link
        .kjPlace   listing venue (東 / 名 / 札 / etc.)
        .kjHistroy [sic] revision history marker
"""
from __future__ import annotations

import datetime as _dt
import logging
import re
import time
from typing import Iterator, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

LOG = logging.getLogger(__name__)
if not LOG.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TDNET_BASE_URL = "https://www.release.tdnet.info/inbs/"
TDNET_PAGE_URL = TDNET_BASE_URL + "I_list_{page:03d}_{date}.html"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; JII-Compounders-Feed/1.0; "
    "+https://jpinv.com/compounders/feed/)"
)

_MAX_PAGES_PER_DAY = 999  # spec says "pages 001-999 if needed, walk until empty"
_HTTP_TIMEOUT_SEC = 30.0
_MAX_RETRIES = 3
_BACKOFF_BASE_SEC = 2.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_ticker(raw: str) -> str:
    """TDnet emits 5-char codes (last char is 0). Strip to 4 chars if
    alphanumeric. Leave anything else alone."""
    s = (raw or "").strip()
    if len(s) == 5 and s[-1] == "0" and s[:4].isalnum():
        return s[:4]
    return s


def _iter_dates(start: _dt.date, end: _dt.date) -> Iterator[_dt.date]:
    if start > end:
        return
    cur = start
    one_day = _dt.timedelta(days=1)
    while cur <= end:
        yield cur
        cur += one_day


def _combine_jst(date: _dt.date, hhmm: str) -> str:
    """Combine the page's calendar date with a row's HH:MM string into
    ISO-8601 with +09:00 offset."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", hhmm or "")
    if not m:
        return _dt.datetime(date.year, date.month, date.day).strftime(
            "%Y-%m-%dT00:00:00+09:00"
        )
    hh, mm = int(m.group(1)), int(m.group(2))
    return _dt.datetime(date.year, date.month, date.day, hh, mm).strftime(
        "%Y-%m-%dT%H:%M:00+09:00"
    )


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------


class TdnetScraper:
    """Polite scraper for the TDnet daily disclosure index."""

    def __init__(
        self,
        rate_limit_sec: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.rate_limit_sec: float = float(rate_limit_sec)
        self.user_agent: str = user_agent
        self._session: requests.Session = session or requests.Session()
        self._session.headers.setdefault("User-Agent", self.user_agent)
        self._last_call_ts: float = 0.0

    # -- private ---------------------------------------------------------

    def _sleep_for_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_call_ts
        wait = self.rate_limit_sec - elapsed
        if wait > 0:
            time.sleep(wait)

    def _fetch_page(self, url: str) -> Optional[str]:
        """Return HTML text, or None if the page is 404 (end of pagination
        or holiday). Raises on persistent 5xx/429 after retries."""
        last_exc: Optional[Exception] = None
        for attempt in range(1, _MAX_RETRIES + 1):
            self._sleep_for_rate_limit()
            try:
                resp = self._session.get(url, timeout=_HTTP_TIMEOUT_SEC)
                self._last_call_ts = time.monotonic()
                if resp.status_code == 404:
                    return None
                if resp.status_code in (429, 503):
                    raise requests.HTTPError(
                        f"TDnet {resp.status_code} on attempt {attempt}",
                        response=resp,
                    )
                if 500 <= resp.status_code < 600:
                    raise requests.HTTPError(
                        f"TDnet {resp.status_code} on attempt {attempt}",
                        response=resp,
                    )
                resp.raise_for_status()
                # TDnet pages are Shift_JIS or UTF-8 depending on era;
                # requests' apparent_encoding handles both.
                if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                    resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            except (requests.HTTPError, requests.ConnectionError,
                    requests.Timeout) as exc:
                last_exc = exc
                if attempt >= _MAX_RETRIES:
                    break
                backoff = _BACKOFF_BASE_SEC * (2 ** (attempt - 1))
                LOG.warning(
                    "TDnet GET %s failed (attempt %d/%d): %s. "
                    "Backing off %.1fs.",
                    url, attempt, _MAX_RETRIES, exc, backoff,
                )
                time.sleep(backoff)
        assert last_exc is not None
        raise last_exc

    @staticmethod
    def _parse_rows(html: str, page_url: str, date: _dt.date) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table", id="main-list-table")
        if not table:
            return []
        rows: list[dict] = []
        for tr in table.find_all("tr"):
            time_td = tr.find("td", class_=re.compile(r"\bkjTime\b"))
            code_td = tr.find("td", class_=re.compile(r"\bkjCode\b"))
            name_td = tr.find("td", class_=re.compile(r"\bkjName\b"))
            title_td = tr.find("td", class_=re.compile(r"\bkjTitle\b"))
            if not (time_td and code_td and name_td and title_td):
                continue
            hhmm = time_td.get_text(strip=True)
            ticker = _normalise_ticker(code_td.get_text(strip=True))
            name_jp = name_td.get_text(strip=True)
            title_a = title_td.find("a")
            title_jp = (title_a.get_text(strip=True) if title_a
                        else title_td.get_text(strip=True))
            pdf_href = title_a.get("href", "").strip() if title_a else ""
            doc_url = urljoin(page_url, pdf_href) if pdf_href else ""

            # XBRL is optional - we don't need it for classification but
            # capture it as doc_id source to keep ids deterministic.
            xbrl_td = tr.find("td", class_=re.compile(r"\bkjXbrl\b"))
            xbrl_href = ""
            if xbrl_td:
                x_a = xbrl_td.find("a")
                if x_a:
                    xbrl_href = x_a.get("href", "").strip()

            # Doc-id: prefer the PDF filename stem (e.g. "140120260515538453"),
            # else the XBRL stem. Falls back to a synthetic key built from
            # date+time+ticker+title (still deterministic).
            doc_id = ""
            for href in (pdf_href, xbrl_href):
                if href:
                    stem = href.rsplit("/", 1)[-1]
                    stem = stem.rsplit(".", 1)[0]
                    if stem:
                        doc_id = stem
                        break
            if not doc_id:
                doc_id = (
                    f"{date.strftime('%Y%m%d')}-{hhmm.replace(':', '')}-"
                    f"{ticker}-{abs(hash(title_jp)) & 0xFFFFFFFF:08x}"
                )

            rows.append({
                "source": "TDnet",
                "doc_id": doc_id,
                "submitted_at": _combine_jst(date, hhmm),
                "ticker": ticker,
                "name_jp": name_jp,
                "name_en": "",
                "title_jp": title_jp,
                "doc_url": doc_url,
                "body_jp": None,
                "shares_outstanding": None,
                "market_cap_jpy": None,
            })
        return rows

    # -- public ----------------------------------------------------------

    def iter_disclosures(
        self,
        start_date: _dt.date,
        end_date: _dt.date,
    ) -> Iterator[dict]:
        """Walk every TDnet daily index page in [start_date, end_date] and
        yield disclosure dicts in the classifier's input shape."""
        for date in _iter_dates(start_date, end_date):
            date_str = date.strftime("%Y%m%d")
            page = 1
            yielded_for_day = 0
            while page <= _MAX_PAGES_PER_DAY:
                url = TDNET_PAGE_URL.format(page=page, date=date_str)
                try:
                    html = self._fetch_page(url)
                except Exception as exc:  # noqa: BLE001 - re-raise after log
                    LOG.error("TDnet fetch failed for %s: %s", url, exc)
                    raise
                if html is None:
                    # 404: out of pagination range or holiday.
                    break
                rows = self._parse_rows(html, url, date)
                if not rows:
                    break
                for row in rows:
                    yielded_for_day += 1
                    yield row
                # If page returned fewer than 100 rows we've hit the last
                # page for the day; no need to probe the next one.
                if len(rows) < 100:
                    break
                page += 1
            LOG.info(
                "TDnet %s: %d rows across %d page(s).",
                date_str, yielded_for_day, page,
            )


__all__ = [
    "TdnetScraper",
    "TDNET_PAGE_URL",
    "DEFAULT_USER_AGENT",
]
