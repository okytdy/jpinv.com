"""
JII Compounders - Capital-Allocation Inflection Feed - EDINET client.

Implements the EDINET (FSA) data source per:
    3 Pipeline/5 Assets/Website/jpinv.com/compounders/feed/_SPEC.md
    Section 3 (Data sources), Section 7 (Backfill), Section 8 (Update loop).

Public API:
    EdinetClient(api_key: str | None, rate_limit_sec: float = 3.5)
        .list_documents(date)        -> list[dict]   raw API rows
        .get_document_metadata(doc_id) -> dict        raw API row for one doc
        .iter_disclosures(start, end)  -> Iterator[dict]
            yields disclosure dicts in the shape `classifier.classify()`
            expects (see tools/classifier.py).

Stub-mode: if `api_key` is None or empty, the client logs a warning and
yields nothing. The GitHub Actions cron will still run green; the feed
just doesn't grow until the key is supplied. This is the agreed bottleneck.
"""
from __future__ import annotations

import datetime as _dt
import logging
import time
from typing import Iterator, Optional

import requests

LOG = logging.getLogger(__name__)
if not LOG.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EDINET_DOCUMENTS_URL = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
EDINET_DOCUMENT_URL = "https://api.edinet-fsa.go.jp/api/v2/documents/{doc_id}"
EDINET_DOC_VIEWER_URL = (
    "https://disclosure2.edinet-fsa.go.jp/WEEK0010.aspx?"
    "submitDateMode=2&BSpb008=&BSpb009={doc_id}"
)

# docTypeCode values where Principle-6 events live (spec Section 2 maps to
# titles inside these envelopes; the classifier rejects the rest).
PRINCIPLE6_DOC_TYPES: frozenset[str] = frozenset({
    "120",  # 有価証券報告書
    "130",  # 半期報告書
    "140",  # 四半期報告書
    "160",  # 訂正
    "180",  # 臨時報告書 (most BUYBACK/CANCEL/DIV/MBO live here)
    "350",  # コーポレートガバナンス報告書
})

# HTTP behaviour
_HTTP_TIMEOUT_SEC = 30.0
_MAX_RETRIES = 3
_BACKOFF_BASE_SEC = 2.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_ticker(raw: Optional[str]) -> str:
    """EDINET secCode comes as 5-char (e.g. '47760' or '299A0'). Trim trailing
    '0' if the first 4 chars are alphanumeric (the JPX 5-digit form). Leave
    other strings as-is."""
    if not raw:
        return ""
    s = str(raw).strip()
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


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class EdinetClient:
    """Thin wrapper over the EDINET v2 REST API.

    Rate-limited (default 3.5s spacing per EDINET's published etiquette) and
    retries 5xx with exponential backoff (max 3 attempts).
    """

    def __init__(
        self,
        api_key: Optional[str],
        rate_limit_sec: float = 3.5,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key: str = (api_key or "").strip()
        self.rate_limit_sec: float = float(rate_limit_sec)
        self._session: requests.Session = session or requests.Session()
        self._last_call_ts: float = 0.0
        if not self.api_key:
            LOG.warning(
                "EDINET_API_KEY not set - EdinetClient is in stub mode "
                "and will yield no disclosures."
            )

    # -- private ---------------------------------------------------------

    def _sleep_for_rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_call_ts
        wait = self.rate_limit_sec - elapsed
        if wait > 0:
            time.sleep(wait)

    def _get(self, url: str, params: dict) -> dict:
        params = dict(params)
        params["Subscription-Key"] = self.api_key
        last_exc: Optional[Exception] = None
        for attempt in range(1, _MAX_RETRIES + 1):
            self._sleep_for_rate_limit()
            try:
                resp = self._session.get(
                    url, params=params, timeout=_HTTP_TIMEOUT_SEC
                )
                self._last_call_ts = time.monotonic()
                if 500 <= resp.status_code < 600:
                    raise requests.HTTPError(
                        f"EDINET {resp.status_code} on attempt {attempt}",
                        response=resp,
                    )
                if resp.status_code == 429:
                    raise requests.HTTPError(
                        f"EDINET 429 rate-limit on attempt {attempt}",
                        response=resp,
                    )
                resp.raise_for_status()
                return resp.json()
            except (requests.HTTPError, requests.ConnectionError,
                    requests.Timeout) as exc:
                last_exc = exc
                if attempt >= _MAX_RETRIES:
                    break
                backoff = _BACKOFF_BASE_SEC * (2 ** (attempt - 1))
                LOG.warning(
                    "EDINET GET failed (attempt %d/%d): %s. "
                    "Backing off %.1fs.",
                    attempt, _MAX_RETRIES, exc, backoff,
                )
                time.sleep(backoff)
        assert last_exc is not None
        raise last_exc

    # -- public ----------------------------------------------------------

    def list_documents(self, date: _dt.date) -> list[dict]:
        """Return the raw `results` array from EDINET's documents.json for the
        given JST date. Empty list in stub mode."""
        if not self.api_key:
            return []
        date_str = date.strftime("%Y-%m-%d")
        LOG.info("EDINET list_documents %s", date_str)
        payload = self._get(
            EDINET_DOCUMENTS_URL,
            params={"date": date_str, "type": 2},
        )
        results = payload.get("results") or []
        if not isinstance(results, list):
            LOG.warning("EDINET unexpected payload shape for %s", date_str)
            return []
        # DIAGNOSTIC (temp - remove after EDINET pipeline confirmed working)
        from collections import Counter as _Counter
        _md = payload.get("metadata") or {}
        _type_counts = _Counter(str(r.get("docTypeCode") or "") for r in results)
        _p6_counts = {t: _type_counts.get(t, 0) for t in sorted(PRINCIPLE6_DOC_TYPES)}
        _p6_total = sum(_p6_counts.values())
        LOG.info(
            "EDINET DIAG %s: total=%d md_status=%s p6_filter_passes=%d by_p6_type=%s top5_all_types=%s",
            date_str, len(results), _md.get("status"),
            _p6_total, _p6_counts, _type_counts.most_common(5),
        )
        # Log titles of any 350 (CG report) docs to see actual EDINET docDescription strings
        _three_fifty = [r for r in results if str(r.get("docTypeCode") or "") == "350"]
        for _r in _three_fifty[:5]:
            LOG.info(
                "EDINET DIAG 350-sample: docID=%s secCode=%r filerName=%r docDescription=%r",
                _r.get("docID"), _r.get("secCode"), _r.get("filerName"), _r.get("docDescription"),
            )
        return results

    def get_document_metadata(self, doc_id: str) -> dict:
        """Fetch the metadata envelope for a single docID. Empty dict in stub
        mode."""
        if not self.api_key:
            return {}
        LOG.info("EDINET get_document_metadata %s", doc_id)
        payload = self._get(
            EDINET_DOCUMENT_URL.format(doc_id=doc_id),
            params={"type": 2},
        )
        results = payload.get("results")
        if isinstance(results, dict):
            return results
        if isinstance(results, list) and results:
            return results[0]
        return payload

    def iter_disclosures(
        self,
        start_date: _dt.date,
        end_date: _dt.date,
    ) -> Iterator[dict]:
        """Yield disclosure dicts (classifier input shape) for each EDINET
        filing in the range whose docTypeCode is in PRINCIPLE6_DOC_TYPES.

        Output schema (matches `classifier.classify` expectations):
            source             "EDINET"
            doc_id             str   (EDINET docID, unique)
            submitted_at       str   ISO-8601 with JST offset
            ticker             str   4-char (or 5-char alphanumeric)
            name_jp            str   filerName
            name_en            str   filerNameEn or "" when EDINET omits it
            title_jp           str   docDescription
            doc_url            str   public EDINET viewer URL
            body_jp            None  (kept for classifier compatibility)
            shares_outstanding None
            market_cap_jpy     None
            _doc_type_code     str   raw EDINET docTypeCode (debug only)
        """
        if not self.api_key:
            LOG.warning(
                "EdinetClient.iter_disclosures called in stub mode "
                "(no API key). Yielding nothing."
            )
            return

        # DIAGNOSTIC (temp) - count yields per day
        _yield_counter = {"yielded": 0, "rejected_type": 0, "rejected_no_docid": 0}
        for date in _iter_dates(start_date, end_date):
            try:
                rows = self.list_documents(date)
            except Exception as exc:  # noqa: BLE001 - we re-raise after log
                LOG.error("EDINET fetch failed for %s: %s", date, exc)
                raise
            _per_day_yield = 0
            for row in rows:
                doc_type = str(row.get("docTypeCode") or "").strip()
                if doc_type not in PRINCIPLE6_DOC_TYPES:
                    _yield_counter["rejected_type"] += 1
                    continue
                doc_id = str(row.get("docID") or "").strip()
                if not doc_id:
                    _yield_counter["rejected_no_docid"] += 1
                    continue
                _yield_counter["yielded"] += 1
                _per_day_yield += 1
                submitted_at_raw = (
                    row.get("submitDateTime") or row.get("submitDate") or ""
                )
                submitted_at = _format_submit_dt(submitted_at_raw)
                yield {
                    "source": "EDINET",
                    "doc_id": doc_id,
                    "submitted_at": submitted_at,
                    "ticker": _normalise_ticker(row.get("secCode")),
                    "name_jp": (row.get("filerName") or "").strip(),
                    "name_en": (row.get("filerNameEn") or "").strip(),
                    "title_jp": (row.get("docDescription") or "").strip(),
                    "doc_url": EDINET_DOC_VIEWER_URL.format(doc_id=doc_id),
                    "body_jp": None,
                    "shares_outstanding": None,
                    "market_cap_jpy": None,
                    "_doc_type_code": doc_type,
                }
            LOG.info("EDINET DIAG iter %s: per_day_yielded=%d", date, _per_day_yield)
        LOG.info("EDINET DIAG iter TOTAL: %s", _yield_counter)


# ---------------------------------------------------------------------------
# Date/time normalisation
# ---------------------------------------------------------------------------


def _format_submit_dt(raw: str) -> str:
    """EDINET emits 'YYYY-MM-DD HH:MM' (JST) or sometimes 'YYYY-MM-DD'.
    Always return ISO-8601 with +09:00 offset. Empty input -> "" so the
    classifier falls back to its own normalisation."""
    if not raw:
        return ""
    s = str(raw).strip().replace("T", " ")
    fmts = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    )
    for fmt in fmts:
        try:
            dt = _dt.datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        except ValueError:
            continue
    # Last-resort: return raw and let classifier handle it.
    return s


__all__ = [
    "EdinetClient",
    "PRINCIPLE6_DOC_TYPES",
    "EDINET_DOCUMENTS_URL",
    "EDINET_DOCUMENT_URL",
]
