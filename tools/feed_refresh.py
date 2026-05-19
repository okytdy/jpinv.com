"""
JII Compounders - Capital-Allocation Inflection Feed - refresh entry point.

Entry point for the GitHub Actions cron defined by:
    3 Pipeline/5 Assets/Website/jpinv.com/compounders/feed/_SPEC.md
    Section 4 (Storage shape), Section 7 (Backfill), Section 8 (Update loop).

Reads `EDINET_API_KEY` from env. Two modes via `FEED_MODE` env var:
    incremental  (default)  - pulls today and yesterday only
    backfill                 - walks today-730d through today

The backfill window can be overridden via `FEED_BACKFILL_LOOKBACK_DAYS`
(bounded to 30..1095 inclusive). Out-of-range or non-integer values fall
back to the 730-day default with a warning.

Outputs (relative to repo root, computed from __file__):
    compounders/feed/data/feed.json
    compounders/feed/data/index.json
    compounders/feed/data/_meta.json
    compounders/feed/data/by-ticker/{ticker}.json   (per ticker w/ >=1 match)

Idempotency: matches are keyed by `id`. Existing feed.json is loaded and
the id-set used to skip already-classified docs before they hit the
classifier, then to dedupe new rows before append.

JSON write convention: sort_keys=True, indent=2, ensure_ascii=False,
trailing newline.
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, Iterator, Optional

# Make sibling modules importable when invoked as `python tools/feed_refresh.py`.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from classifier import classify  # noqa: E402
from edinet_client import EdinetClient  # noqa: E402
from tdnet_scraper import TdnetScraper  # noqa: E402

LOG = logging.getLogger("feed_refresh")
if not LOG.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

JST = _dt.timezone(_dt.timedelta(hours=9))

REPO_ROOT = Path(__file__).resolve().parent.parent
FEED_DIR = REPO_ROOT / "compounders" / "feed" / "data"
FEED_JSON = FEED_DIR / "feed.json"
INDEX_JSON = FEED_DIR / "index.json"
META_JSON = FEED_DIR / "_meta.json"
BY_TICKER_DIR = FEED_DIR / "by-ticker"
ARCHIVE_DIR = FEED_DIR / "archive"

FEED_ROW_CAP = 5_000  # spec Section 4

INCREMENTAL_LOOKBACK_DAYS = 1     # today and yesterday
BACKFILL_LOOKBACK_DAYS = 730      # 2 years (default; override via env)
BACKFILL_LOOKBACK_MIN = 30
BACKFILL_LOOKBACK_MAX = 1095      # 3 years - hard ceiling


def _resolve_backfill_lookback() -> int:
    """Return the backfill window length in days, honouring the
    `FEED_BACKFILL_LOOKBACK_DAYS` env var when present and in range.
    Out-of-range or non-integer values fall back to the default with a
    warning so the run still completes."""
    raw = os.environ.get("FEED_BACKFILL_LOOKBACK_DAYS")
    if raw is None or raw.strip() == "":
        return BACKFILL_LOOKBACK_DAYS
    try:
        n = int(raw.strip())
    except ValueError:
        LOG.warning(
            "FEED_BACKFILL_LOOKBACK_DAYS=%r is not an integer; using default %d.",
            raw, BACKFILL_LOOKBACK_DAYS,
        )
        return BACKFILL_LOOKBACK_DAYS
    if n < BACKFILL_LOOKBACK_MIN or n > BACKFILL_LOOKBACK_MAX:
        LOG.warning(
            "FEED_BACKFILL_LOOKBACK_DAYS=%d outside [%d..%d]; using default %d.",
            n, BACKFILL_LOOKBACK_MIN, BACKFILL_LOOKBACK_MAX,
            BACKFILL_LOOKBACK_DAYS,
        )
        return BACKFILL_LOOKBACK_DAYS
    LOG.info("Backfill lookback overridden via env: %d days.", n)
    return n


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        LOG.warning("Could not read %s (%s); using default.", path, exc)
        return default


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
    if not text.endswith("\n"):
        text += "\n"
    with path.open("w", encoding="utf-8") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# Date-window resolution
# ---------------------------------------------------------------------------


def _resolve_window(mode: str) -> tuple[_dt.date, _dt.date]:
    today_jst = _dt.datetime.now(JST).date()
    if mode == "backfill":
        lookback = _resolve_backfill_lookback()
        return today_jst - _dt.timedelta(days=lookback), today_jst
    # default: incremental
    return today_jst - _dt.timedelta(days=INCREMENTAL_LOOKBACK_DAYS), today_jst


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


def _gather_disclosures(
    start: _dt.date,
    end: _dt.date,
    edinet: EdinetClient,
    tdnet: TdnetScraper,
) -> Iterator[dict]:
    """Yield raw disclosure dicts from both sources, EDINET first, then
    TDnet. Errors propagate."""
    for d in edinet.iter_disclosures(start, end):
        yield d
    for d in tdnet.iter_disclosures(start, end):
        yield d


def _classify_new(
    disclosures: Iterable[dict],
    seen_ids: set[str],
) -> Iterator[dict]:
    """Run each disclosure through the classifier, skipping those whose
    composed id is already in the seen-set. Yields classified feed rows
    (not the raw disclosure)."""
    for disc in disclosures:
        composed_id = f"{disc.get('source', 'EDINET')}-{disc.get('doc_id', '')}"
        if composed_id in seen_ids:
            continue
        row = classify(disc)
        if row is None:
            continue
        seen_ids.add(row["id"])
        yield row


def _sort_feed_rows(rows: list[dict]) -> list[dict]:
    """Reverse-chronological by `ts`, with `id` as deterministic tiebreaker."""
    return sorted(rows, key=lambda r: (r.get("ts", ""), r.get("id", "")),
                  reverse=True)


def _split_cap(rows: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    """Cap feed at FEED_ROW_CAP rows. Overflow gets bucketed by year for
    archive files. Returns (kept_rows, year -> overflow_rows)."""
    if len(rows) <= FEED_ROW_CAP:
        return rows, {}
    kept = rows[:FEED_ROW_CAP]
    overflow = rows[FEED_ROW_CAP:]
    by_year: dict[str, list[dict]] = {}
    for r in overflow:
        ts = r.get("ts", "")
        year = ts[:4] if len(ts) >= 4 and ts[:4].isdigit() else "unknown"
        by_year.setdefault(year, []).append(r)
    return kept, by_year


def _rebuild_index(rows: list[dict]) -> dict[str, dict]:
    """{ticker: {match_count, last_match_iso}} - spec Section 4/6."""
    index: dict[str, dict] = {}
    for r in rows:
        tk = (r.get("ticker") or "").strip()
        if not tk:
            continue
        bucket = index.setdefault(tk, {"match_count": 0, "last_match_iso": ""})
        bucket["match_count"] += 1
        ts = r.get("ts", "")
        if ts > bucket["last_match_iso"]:
            bucket["last_match_iso"] = ts
    return index


def _rebuild_by_ticker(rows: list[dict], tickers: set[str]) -> None:
    """For each ticker in the affected set, rewrite by-ticker/{ticker}.json
    with that ticker's full back-catalogue from `rows`. Tickers not in the
    set are left untouched (their files remain authoritative)."""
    if not tickers:
        return
    BY_TICKER_DIR.mkdir(parents=True, exist_ok=True)
    bucket: dict[str, list[dict]] = {tk: [] for tk in tickers}
    for r in rows:
        tk = (r.get("ticker") or "").strip()
        if tk in bucket:
            bucket[tk].append(r)
    for tk, tk_rows in bucket.items():
        tk_rows_sorted = _sort_feed_rows(tk_rows)
        _write_json(BY_TICKER_DIR / f"{tk}.json", tk_rows_sorted)


def _update_meta(
    meta: dict,
    new_count: int,
    last_iso: str,
    last_edinet_doc_id: Optional[str],
    run_iso: str,
    error: Optional[str],
) -> dict:
    meta = dict(meta) if meta else {}
    meta["last_refresh_iso"] = run_iso
    meta["run_count"] = int(meta.get("run_count") or 0) + 1
    if last_iso:
        meta["last_match_iso"] = last_iso
    if last_edinet_doc_id:
        meta["last_edinet_doc_id"] = last_edinet_doc_id
    meta["last_append_count"] = new_count
    err_log = meta.get("error_log") or []
    if not isinstance(err_log, list):
        err_log = []
    if error:
        err_log.append({"ts": run_iso, "error": error})
        # Keep last 50 only.
        err_log = err_log[-50:]
    meta["error_log"] = err_log
    return meta


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    mode = (os.environ.get("FEED_MODE") or "incremental").strip().lower()
    if mode not in ("incremental", "backfill"):
        LOG.warning("Unknown FEED_MODE=%s; defaulting to incremental.", mode)
        mode = "incremental"

    api_key = os.environ.get("EDINET_API_KEY", "")
    edinet = EdinetClient(api_key=api_key)
    tdnet = TdnetScraper()

    start, end = _resolve_window(mode)
    LOG.info("feed_refresh mode=%s window=%s..%s", mode, start, end)

    existing_feed: list[dict] = _read_json(FEED_JSON, default=[])
    if not isinstance(existing_feed, list):
        LOG.warning("feed.json was not a list; resetting.")
        existing_feed = []
    seen_ids: set[str] = {
        r["id"] for r in existing_feed
        if isinstance(r, dict) and isinstance(r.get("id"), str)
    }

    new_rows: list[dict] = []
    last_edinet_doc_id: Optional[str] = None
    last_match_iso: str = ""

    # Streamed pipeline: gather -> dedupe-by-id -> classify -> collect.
    for raw in _gather_disclosures(start, end, edinet, tdnet):
        composed_id = f"{raw.get('source', 'EDINET')}-{raw.get('doc_id', '')}"
        if composed_id in seen_ids:
            continue
        row = classify(raw)
        if row is None:
            continue
        seen_ids.add(row["id"])
        new_rows.append(row)
        if raw.get("source") == "EDINET":
            last_edinet_doc_id = raw.get("doc_id") or last_edinet_doc_id
        ts = row.get("ts", "")
        if ts > last_match_iso:
            last_match_iso = ts

    combined = _sort_feed_rows(existing_feed + new_rows)
    kept, overflow_by_year = _split_cap(combined)

    # Identify which by-ticker files need rebuilding.
    affected_tickers = {
        (r.get("ticker") or "").strip()
        for r in new_rows
        if (r.get("ticker") or "").strip()
    }

    _write_json(FEED_JSON, kept)
    _write_json(INDEX_JSON, _rebuild_index(kept))
    _rebuild_by_ticker(kept, affected_tickers)
    for year, year_rows in overflow_by_year.items():
        existing_year = _read_json(ARCHIVE_DIR / f"{year}.json", default=[])
        if not isinstance(existing_year, list):
            existing_year = []
        # Dedupe archive too.
        archive_ids = {
            r["id"] for r in existing_year
            if isinstance(r, dict) and isinstance(r.get("id"), str)
        }
        merged_year = list(existing_year) + [
            r for r in year_rows if r.get("id") not in archive_ids
        ]
        _write_json(
            ARCHIVE_DIR / f"{year}.json",
            _sort_feed_rows(merged_year),
        )

    run_iso = _dt.datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    meta = _read_json(META_JSON, default={}) or {}
    meta = _update_meta(
        meta=meta,
        new_count=len(new_rows),
        last_iso=last_match_iso or (kept[0]["ts"] if kept else ""),
        last_edinet_doc_id=last_edinet_doc_id,
        run_iso=run_iso,
        error=None,
    )
    _write_json(META_JSON, meta)

    latest_iso = kept[0]["ts"] if kept else ""
    print(f"Appended {len(new_rows)} new matches. Latest: {latest_iso}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
