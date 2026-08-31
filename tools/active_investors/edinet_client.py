"""
Active Investors in Japan — EDINET ingestion + large-shareholding parser.

Production data source: the official FSA EDINET API v2.
  list:     GET https://api.edinet-fsa.go.jp/api/v2/documents.json?date=YYYY-MM-DD&type=2&Subscription-Key=KEY
  download: GET https://api.edinet-fsa.go.jp/api/v2/documents/{docID}?type=5&Subscription-Key=KEY   (CSV ZIP)

Requires EDINET_API_KEY (free; https://api.edinet-fsa.go.jp). All v2 endpoints
need the Subscription-Key, including the metadata listing.

We pull docTypeCode 350 (大量保有報告書 / initial) and 360 (変更報告書 / change),
then parse the CSV to extract the holding ratio, the prior ratio and the issuer.
Parsing is defensive: filings are NOT clean. We try element IDs first, then the
Japanese item-name (項目名) as a fallback, normalize full/half-width digits, and
fail soft — a row we cannot parse confidently still records filer/issuer/date
with the ratio left null and confidence 'low' (it lands in the audit set, not
the public feed).

This module returns RAW filing dicts (percent ratios). refresh.py attributes
them to investors via common.attribute_investor and hands them to build_data.
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import re
import time
import unicodedata
import zipfile
from typing import Iterator, Optional

import urllib.request
import urllib.parse
import urllib.error

API_BASE = "https://api.edinet-fsa.go.jp/api/v2"
DOC_TYPES_LARGE_HOLDING = {"350", "360"}  # initial, change
# Public, stable clickable source: the filer's holdings list on kabutan, keyed by
# EDINET code. We also store the EDINET docID so a switch to the official viewer
# is a one-line change later.
KABUTAN_HOLDER = "https://kabutan.jp/holder/lists/?edicode={code}"
EDINET_VIEW = "https://disclosure2.edinet-fsa.go.jp/WEEK0010.aspx"  # portal (docID stored separately)


class EdinetApiError(RuntimeError):
    """A response from EDINET that must stop the refresh.

    EDINET returns authentication, throttling and service failures as JSON in
    an HTTP-200 response, so callers cannot rely on urllib raising HTTPError.
    """

    def __init__(self, status: str, message: str, *, operation: str):
        self.status = str(status or "unknown")
        self.operation = operation
        self.api_message = (message or "EDINET returned an error").strip()
        super().__init__(f"EDINET {operation} failed (status {self.status}): {self.api_message}")


def _nikkei(doc_id, submit_date):
    d = (submit_date or "").replace("-", "")
    return ("https://www.nikkei.com/nkd/disclosure/ednr/" + d + doc_id + "/") if (doc_id and len(d) == 8) else ""


class EdinetClient:
    def __init__(self, api_key: str, *, timeout: int = 30, pause: float = 0.3):
        if not api_key:
            raise ValueError("EDINET_API_KEY is required for live ingestion.")
        self.api_key = api_key
        self.timeout = timeout
        self.pause = pause

    def _get(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "jpinv-active-investors/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            # Do not let urllib's exception string expose Subscription-Key from
            # the query string in public CI logs.
            raise EdinetApiError(str(exc.code), "HTTP request rejected",
                                 operation="transport") from None
        except urllib.error.URLError as exc:
            raise EdinetApiError("transport_error", str(exc.reason),
                                 operation="transport") from None

    def list_documents(self, date: str) -> list[dict]:
        """All documents submitted on `date` (YYYY-MM-DD) with metadata."""
        q = urllib.parse.urlencode({"date": date, "type": 2,
                                    "Subscription-Key": self.api_key})
        raw = self._get(f"{API_BASE}/documents.json?{q}")
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EdinetApiError("malformed_response", str(exc), operation=f"list {date}") from exc
        if not isinstance(data, dict):
            raise EdinetApiError("malformed_response", "top-level JSON is not an object",
                                 operation=f"list {date}")
        status = str(((data or {}).get("metadata") or {}).get("status") or
                     (data or {}).get("StatusCode") or "")
        if status and status != "200":
            message = (data.get("message") or
                       ((data.get("metadata") or {}).get("message")) or
                       "EDINET rejected the request")
            raise EdinetApiError(status, message, operation=f"list {date}")
        results = data.get("results")
        if results is None:
            # Successful no-document days are represented by an empty results
            # array. Missing results on a nominally successful response is not
            # safe to treat as a quiet filing day.
            raise EdinetApiError(status or "malformed_response", "missing results array",
                                 operation=f"list {date}")
        if not isinstance(results, list):
            raise EdinetApiError(status or "malformed_response", "results is not an array",
                                 operation=f"list {date}")
        return results

    def fetch_document_csv(self, doc_id: str) -> Optional[bytes]:
        """Download the CSV ZIP for a document; return the concatenated CSV bytes."""
        q = urllib.parse.urlencode({"type": 5, "Subscription-Key": self.api_key})
        blob = self._get(f"{API_BASE}/documents/{doc_id}?{q}")
        # Authentication and quota errors are JSON bodies with HTTP 200.
        if blob.lstrip().startswith(b"{"):
            try:
                data = json.loads(blob.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                data = None
            if isinstance(data, dict):
                status = str(((data.get("metadata") or {}).get("status")) or
                             data.get("StatusCode") or "")
                if status != "200":
                    raise EdinetApiError(status or "malformed_response",
                                         data.get("message") or "EDINET returned JSON instead of a CSV ZIP",
                                         operation=f"download {doc_id}")
        try:
            zf = zipfile.ZipFile(io.BytesIO(blob))
        except zipfile.BadZipFile:
            return None
        # Large-holding CSVs are named like jplvh*.csv; take the first CSV.
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            return None
        return zf.read(sorted(names)[0])

    def iter_large_holding(self, start: str, end: str) -> Iterator[dict]:
        """Yield raw large-holding filing dicts for the inclusive date window."""
        for date in _daterange(start, end):
            docs = self.list_documents(date)
            for d in docs:
                if str(d.get("docTypeCode")) not in DOC_TYPES_LARGE_HOLDING:
                    continue
                row = self._raw_from_meta(d)
                csv_bytes = self.fetch_document_csv(d.get("docID", ""))
                if csv_bytes:
                    parsed = parse_large_holding_csv(csv_bytes)
                    row.update({k: v for k, v in parsed.items() if v is not None})
                _finalize_row(row)
                yield row
                time.sleep(self.pause)

    @staticmethod
    def _raw_from_meta(d: dict) -> dict:
        filer_code = (d.get("edinetCode") or "").strip()
        return {
            "edinet_doc_id": d.get("docID", ""),
            "filer_raw_name": d.get("filerName", ""),
            "filer_edinet_code": filer_code,
            "issuer_name": d.get("issuerName") or "",
            "issuer_code": _sec_code(d.get("secCode")),
            "issuer_edinet_code": d.get("subjectEdinetCode") or d.get("issuerEdinetCode") or "",
            "filing_date": _submit_date(d.get("submitDateTime")),
            # 特例対象株券等 CHANGE reports are filed under docTypeCode 350 (not 360),
            # so the description, not the type code, decides initial-vs-change.
            "is_change_report": (str(d.get("docTypeCode")) == "360"
                                 or "変更" in (d.get("docDescription") or "")
                                 or "訂正" in (d.get("docDescription") or "")),
            "japanese_title": d.get("docDescription") or "",
            "source_url": (_nikkei(d.get("docID", ""), _submit_date(d.get("submitDateTime")))
                           or (KABUTAN_HOLDER.format(code=filer_code) if filer_code else EDINET_VIEW)),
            "current_pct": None,
            "previous_pct": None,
            "change_pp": None,
            "confidence": None,
        }


# ---------------------------------------------------------------------------
# CSV parsing (defensive)
# ---------------------------------------------------------------------------

# Element-id substrings (taxonomy-version agnostic). Order = priority.
_CUR_ELEM = ("HoldingRatioOfShareCertificatesEtc",)
_PREV_ELEM = ("HoldingRatioOfShareCertificatesEtcOfLastReport",
              "HoldingRatioOfShareCertificatesEtcInLastReport")
_ISSUER_ELEM = ("NameOfIssuer", "IssuerName")
_REASON_ELEM = ("ReasonForChange", "ReasonForSubmission")
# Japanese 項目名 fallbacks.
_CUR_ITEM = ("保有割合",)
_PREV_ITEM = ("直前の", "前回")
_ISSUER_ITEM = ("発行者", "発行会社")
_REASON_ITEM = ("変更の理由", "提出事由")
_CODE_ELEM = ("SecurityCodeOfIssuer", "SecuritiesCodeOfIssuer", "CodeNumberOfIssuer")
_CODE_ITEM = ("証券コード", "コード番号")
_PURPOSE_ELEM = ("PurposeOfHolding",)
_PURPOSE_ITEM = ("保有目的",)
_SHARES_ELEM = ("TotalNumberOfStocksEtcHeld",)
_SHARES_ITEM = ("保有株券等の数（総数）",)


def parse_large_holding_csv(csv_bytes: bytes) -> dict:
    """Parse an EDINET large-holding CSV (UTF-16 TSV) into percent ratios.
    ``current_pct`` is the reporting holder's own ratio. When a filing has
    joint holders, EDINET also emits a root-context aggregate; that is returned
    separately as ``group_current_pct`` so downstream screens can use the
    economic voting bloc without overwriting the member-level figure.
    """
    if not csv_bytes:
        return {}
    text = _decode_edinet_csv(csv_bytes)
    rows = [ln.split("\t") for ln in text.splitlines() if ln.strip()]
    if not rows:
        return {}
    header = rows[0]
    # Locate columns; EDINET CSV header is 要素ID 項目名 ... 値.
    def col(*names, default=None):
        for i, h in enumerate(header):
            for n in names:
                if n in h:
                    return i
        return default
    c_elem = col("要素ID", "ElementId", default=0)
    c_item = col("項目名", "ItemName", default=1)
    c_ctx = col("コンテキストID", "ContextId", "Context ID", default=2)
    c_val = col("値", "Value", default=len(header) - 1)

    cur_member = prev_member = None
    cur_group = prev_group = None
    issuer_name = reason = purpose = None
    shares = None
    code_strong = code_weak = None
    for r in rows[1:]:
        if len(r) <= c_val:
            continue
        elem = r[c_elem] if c_elem < len(r) else ""
        item = r[c_item] if c_item < len(r) else ""
        ctx = r[c_ctx] if c_ctx < len(r) else ""
        val = (r[c_val] or "").strip().strip('"')
        is_member_ctx = "FilerLargeVolumeHolder" in ctx and "Member" in ctx
        is_cur = ((_any_in(elem, _CUR_ELEM) or _any_in(item, _CUR_ITEM))
                  and not _any_in(item, _PREV_ITEM) and not _any_in(elem, _PREV_ELEM))
        is_prev = _any_in(elem, _PREV_ELEM) or _any_in(item, _PREV_ITEM)
        if is_cur:
            parsed = _to_pct(val)
            if is_member_ctx and cur_member is None:
                cur_member = parsed
            elif not is_member_ctx and cur_group is None:
                cur_group = parsed
        if is_prev:
            parsed = _to_pct(val)
            if is_member_ctx and prev_member is None:
                prev_member = parsed
            elif not is_member_ctx and prev_group is None:
                prev_group = parsed
        if issuer_name is None and (_any_in(elem, _ISSUER_ELEM) or _any_in(item, _ISSUER_ITEM)):
            if val and not val.replace(".", "").isdigit():
                issuer_name = unicodedata.normalize("NFKC", val)
        if reason is None and (_any_in(elem, _REASON_ELEM) or _any_in(item, _REASON_ITEM)):
            if val:
                reason = unicodedata.normalize("NFKC", val)
        if purpose is None and (_any_in(elem, _PURPOSE_ELEM) or _any_in(item, _PURPOSE_ITEM)):
            if val and not val.replace(".", "").replace("-", "").isdigit():
                purpose = unicodedata.normalize("NFKC", val)
        if shares is None and (_any_in(elem, _SHARES_ELEM) or _any_in(item, _SHARES_ITEM)):
            sv = unicodedata.normalize("NFKC", val).replace(",", "").strip()
            if sv.isdigit():
                shares = int(sv)
        if code_strong is None and _any_in(elem, _CODE_ELEM):
            cc = _sec_code(unicodedata.normalize("NFKC", val))
            if cc and any(ch.isdigit() for ch in cc):
                code_strong = cc      # 発行者の証券コード (issuer) — authoritative
        elif (code_weak is None and _any_in(item, _CODE_ITEM)
              and "DEI" not in (item or "") and "dei" not in (elem or "").lower()
              and not _any_in(item, _PREV_ITEM)):
            cc = _sec_code(unicodedata.normalize("NFKC", val))
            if cc and any(ch.isdigit() for ch in cc):
                code_weak = cc        # generic 証券コード fallback, excluding filer DEI
    code = code_strong or code_weak
    cur = cur_member if cur_member is not None else cur_group
    prev = prev_member if prev_member is not None else prev_group
    out = {}
    if cur is not None:
        out["current_pct"] = cur
    if prev is not None:
        out["previous_pct"] = prev
    if cur_group is not None:
        out["group_current_pct"] = cur_group
    if prev_group is not None:
        out["group_previous_pct"] = prev_group
    if issuer_name:
        out["issuer_name"] = issuer_name
    if code:
        out["issuer_code"] = code
    if reason:
        out["reason_ja"] = reason
    if purpose:
        out["purpose_ja"] = purpose
    if shares is not None:
        out["shares_held"] = shares
    return out


def _finalize_row(row: dict) -> None:
    """Compute change_pp + confidence from whatever parsing produced."""
    cur, prev = row.get("current_pct"), row.get("previous_pct")
    if row.get("change_pp") is None and cur is not None and prev is not None:
        row["change_pp"] = round(cur - prev, 2)
    if cur is None:
        row["confidence"] = "low"
        row.setdefault("caveats", []).append(
            "Holding ratio could not be parsed from the filing; review manually.")
    elif row.get("is_change_report") and prev is None:
        row["confidence"] = row.get("confidence") or "medium"
        row.setdefault("caveats", []).append("Prior holding ratio not found in the filing.")
    else:
        row["confidence"] = row.get("confidence") or "high"


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _any_in(hay: str, needles) -> bool:
    return any(n in (hay or "") for n in needles)


def _decode_edinet_csv(b: bytes) -> str:
    for enc in ("utf-16", "utf-16-le", "utf-8-sig", "cp932", "utf-8"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", errors="replace")


def _to_pct(val: str) -> Optional[float]:
    """Parse a holding ratio cell to PERCENT. EDINET reports either a fraction
    (0.0822) or a percent (8.22); disambiguate by magnitude."""
    if not val:
        return None
    v = unicodedata.normalize("NFKC", val).replace("%", "").replace(",", "").strip()
    try:
        f = float(v)
    except ValueError:
        return None
    if f <= 1.0:          # stored as fraction
        return round(f * 100, 2)
    return round(f, 2)    # already percent


def _sec_code(code) -> str:
    """EDINET secCode is 5 digits (e.g. 18610); the市場 ticker is the first 4
    (1861). Alphanumeric new codes (e.g. 131A0) keep their 4-char prefix."""
    if not code:
        return ""
    s = str(code).strip()
    if len(s) == 5:
        return s[:4]
    return s


def _submit_date(dt: str) -> str:
    if not dt:
        return ""
    return dt[:10]  # 'YYYY-MM-DD HH:MM' -> 'YYYY-MM-DD'


def _daterange(start: str, end: str):
    s = _dt.date.fromisoformat(start)
    e = _dt.date.fromisoformat(end)
    cur = s
    while cur <= e:
        yield cur.isoformat()
        cur += _dt.timedelta(days=1)


# ---------------------------------------------------------------------------
# offline self-test of the parser (no API key needed)
# ---------------------------------------------------------------------------

def _selftest() -> None:
    sample = (
        "要素ID\t項目名\tコンテキストID\t相対年度\t連結・個別\t期間・時点\tユニットID\t単位\t値\n"
        "jplvh_cor:NameOfIssuer\t発行者の名称\tFilingDateInstant\t-\t-\t時点\t-\t-\t株式会社テスト\n"
        "jplvh_cor:HoldingRatioOfShareCertificatesEtc\t保有割合\tFilingDateInstant_FilerLargeVolumeHolder1Member\t-\t-\t時点\tPure\t純額\t0.0822\n"
        "jplvh_cor:HoldingRatioOfShareCertificatesEtcOfLastReport\t直前の保有割合\tFilingDateInstant_FilerLargeVolumeHolder1Member\t-\t-\t時点\tPure\t純額\t0.0715\n"
        "jplvh_cor:HoldingRatioOfShareCertificatesEtc\t保有割合\tFilingDateInstant\t-\t-\t時点\tPure\t純額\t0.2874\n"
        "jplvh_cor:HoldingRatioOfShareCertificatesEtcOfLastReport\t直前の保有割合\tFilingDateInstant\t-\t-\t時点\tPure\t純額\t0.2843\n"
        "jplvh_cor:ReasonForChange\t変更の理由\tFilingDateInstant\t-\t-\t時点\t-\t-\t保有割合が1％以上増加\n"
    )
    b = ("﻿" + sample).encode("utf-16")
    out = parse_large_holding_csv(b)
    assert out.get("current_pct") == 8.22, out
    assert out.get("previous_pct") == 7.15, out
    assert out.get("group_current_pct") == 28.74, out
    assert out.get("group_previous_pct") == 28.43, out
    assert out.get("issuer_name") == "株式会社テスト", out
    assert "保有割合" in out.get("reason_ja", ""), out
    print("edinet_client parser self-test OK:", out)


if __name__ == "__main__":
    _selftest()
