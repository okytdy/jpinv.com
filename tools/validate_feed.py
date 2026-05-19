"""
JII Compounders - Capital-Allocation Inflection Feed - JSON validator.

Validates the on-disk JSON the feed-refresh / feed-backfill workflows
produce against the row shape and invariants described by:
    3 Pipeline/5 Assets/Website/jpinv.com/compounders/feed/_SPEC.md
    Section 4 (Storage shape), Section 6 (Search behaviour).

Stdlib-only by design -- this is meant to run anywhere the workflows run
without pulling in dependencies. Loads:
    compounders/feed/data/feed.json
    compounders/feed/data/index.json
    compounders/feed/data/_meta.json
    compounders/feed/data/by-ticker/*.json

Exits 0 if every invariant holds, 1 otherwise. A human-readable summary
(counts, first ~50 issues per file, totals) is written to stdout either
way so the failure log is self-contained.

Usage:
    python tools/validate_feed.py
    python tools/validate_feed.py --data-dir path/to/data    (optional)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Constants - mirror _SPEC.md Section 4
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "compounders" / "feed" / "data"

FEED_ROW_CAP = 5_000

VALID_CLASSES = {"COC", "BUYBACK", "CANCEL", "DIV", "CROSS", "MBO",
                 "COMP", "GOV"}
VALID_SOURCES = {"EDINET", "TDnet"}

# Tickers in the JPX master are 4-char alphanumeric (e.g. 4776, 409A).
TICKER_RE = re.compile(r"^[0-9A-Z]{4}$")

REQUIRED_ROW_KEYS = {
    "id", "ts", "ticker", "name_en", "name_jp", "class", "tag",
    "summary_en", "summary_jp", "source", "doc_url", "profile_url",
}

REQUIRED_META_KEYS = {
    "last_refresh_iso", "last_edinet_doc_id", "run_count", "error_log",
}

MAX_ISSUES_PER_FILE = 50  # cap stdout noise on a catastrophically broken run


# ---------------------------------------------------------------------------
# Issue accumulator
# ---------------------------------------------------------------------------


class Report:
    """Buckets validation issues by file so the final summary stays
    readable even when one file is dominantly broken."""

    def __init__(self) -> None:
        self._issues: dict[str, list[str]] = {}
        self._counts: dict[str, int] = {}

    def add(self, scope: str, message: str) -> None:
        bucket = self._issues.setdefault(scope, [])
        self._counts[scope] = self._counts.get(scope, 0) + 1
        if len(bucket) < MAX_ISSUES_PER_FILE:
            bucket.append(message)

    @property
    def ok(self) -> bool:
        return not self._issues

    def render(self) -> str:
        if self.ok:
            return "PASS: every checked file conforms to _SPEC.md Section 4."
        lines = ["FAIL: validation issues found."]
        total = 0
        for scope, msgs in self._issues.items():
            count = self._counts[scope]
            total += count
            lines.append("")
            lines.append(f"[{scope}] {count} issue(s):")
            for m in msgs:
                lines.append(f"  - {m}")
            if count > len(msgs):
                lines.append(f"  ... and {count - len(msgs)} more (truncated)")
        lines.append("")
        lines.append(f"Total issues: {total}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Primitive validators
# ---------------------------------------------------------------------------


def _is_iso8601(value: Any) -> bool:
    """Parseable as ISO-8601. Accepts the trailing-Z form and offsets."""
    if not isinstance(value, str) or not value:
        return False
    candidate = value
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        _dt.datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def _load_json(path: Path, report: Report, scope: str) -> Any:
    if not path.exists():
        report.add(scope, f"file missing: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        report.add(scope, f"could not parse JSON: {exc}")
        return None


# ---------------------------------------------------------------------------
# Per-file validators
# ---------------------------------------------------------------------------


def _validate_row(row: Any, scope: str, idx: int, report: Report) -> None:
    if not isinstance(row, dict):
        report.add(scope, f"row[{idx}] is not an object (got {type(row).__name__})")
        return
    missing = REQUIRED_ROW_KEYS - set(row.keys())
    if missing:
        report.add(scope, f"row[{idx}] id={row.get('id')!r} missing keys: "
                          f"{sorted(missing)}")
    cls = row.get("class")
    if cls not in VALID_CLASSES:
        report.add(scope, f"row[{idx}] id={row.get('id')!r} class={cls!r} "
                          f"not in {sorted(VALID_CLASSES)}")
    src = row.get("source")
    if src not in VALID_SOURCES:
        report.add(scope, f"row[{idx}] id={row.get('id')!r} source={src!r} "
                          f"not in {sorted(VALID_SOURCES)}")
    ts = row.get("ts")
    if not _is_iso8601(ts):
        report.add(scope, f"row[{idx}] id={row.get('id')!r} ts={ts!r} not "
                          f"ISO-8601 parseable")
    tk = row.get("ticker")
    if not (isinstance(tk, str) and TICKER_RE.match(tk)):
        report.add(scope, f"row[{idx}] id={row.get('id')!r} ticker={tk!r} "
                          f"does not match {TICKER_RE.pattern}")
    rid = row.get("id")
    if not isinstance(rid, str) or not rid:
        report.add(scope, f"row[{idx}] id={rid!r} not a non-empty string")
    for k in ("name_en", "name_jp", "tag", "summary_en", "summary_jp",
              "doc_url"):
        v = row.get(k)
        if not isinstance(v, str):
            report.add(scope, f"row[{idx}] id={row.get('id')!r} {k}={v!r} "
                              f"not a string")
    # profile_url is allowed to be null when no JII profile exists (sample
    # data convention; spec shows string form for matched profiles).
    pu = row.get("profile_url")
    if pu is not None and not isinstance(pu, str):
        report.add(scope, f"row[{idx}] id={row.get('id')!r} profile_url={pu!r} "
                          f"not a string or null")


def _validate_feed_json(data: Any, report: Report) -> list[dict]:
    scope = "feed.json"
    if data is None:
        return []
    if not isinstance(data, list):
        report.add(scope, f"top-level must be an array (got {type(data).__name__})")
        return []
    if len(data) > FEED_ROW_CAP:
        report.add(scope, f"row count {len(data)} exceeds cap {FEED_ROW_CAP}")
    seen_ids: set[str] = set()
    prev_ts: str | None = None
    for i, row in enumerate(data):
        _validate_row(row, scope, i, report)
        if isinstance(row, dict):
            rid = row.get("id")
            if isinstance(rid, str):
                if rid in seen_ids:
                    report.add(scope, f"duplicate id at row[{i}]: {rid!r}")
                else:
                    seen_ids.add(rid)
            ts = row.get("ts")
            if isinstance(ts, str) and prev_ts is not None and ts > prev_ts:
                report.add(scope, f"sort order broken at row[{i}]: ts={ts!r} "
                                  f"is newer than prev ts={prev_ts!r} "
                                  f"(expected newest-first)")
            if isinstance(ts, str):
                prev_ts = ts
    return [r for r in data if isinstance(r, dict)]


def _validate_index_json(data: Any, report: Report) -> None:
    scope = "index.json"
    if data is None:
        return
    if not isinstance(data, dict):
        report.add(scope, f"top-level must be an object (got {type(data).__name__})")
        return
    for tk, entry in data.items():
        if not TICKER_RE.match(tk):
            report.add(scope, f"key {tk!r} does not match {TICKER_RE.pattern}")
        if not isinstance(entry, dict):
            report.add(scope, f"value for {tk!r} is not an object "
                              f"(got {type(entry).__name__})")
            continue
        mc = entry.get("match_count")
        if not isinstance(mc, int) or isinstance(mc, bool) or mc < 1:
            report.add(scope, f"{tk!r}.match_count={mc!r} not an int >= 1")
        lmi = entry.get("last_match_iso")
        if not _is_iso8601(lmi):
            report.add(scope, f"{tk!r}.last_match_iso={lmi!r} not ISO-8601")


def _validate_meta_json(data: Any, report: Report) -> None:
    scope = "_meta.json"
    if data is None:
        return
    if not isinstance(data, dict):
        report.add(scope, f"top-level must be an object (got {type(data).__name__})")
        return
    missing = REQUIRED_META_KEYS - set(data.keys())
    if missing:
        report.add(scope, f"missing keys: {sorted(missing)}")
    rc = data.get("run_count")
    if rc is not None and (not isinstance(rc, int) or isinstance(rc, bool)):
        report.add(scope, f"run_count={rc!r} not an int")
    lri = data.get("last_refresh_iso")
    if lri is not None and not _is_iso8601(lri):
        report.add(scope, f"last_refresh_iso={lri!r} not ISO-8601")
    el = data.get("error_log")
    if el is not None and not isinstance(el, list):
        report.add(scope, f"error_log must be a list (got {type(el).__name__})")


def _validate_by_ticker(data_dir: Path, report: Report) -> int:
    by_ticker_dir = data_dir / "by-ticker"
    if not by_ticker_dir.exists():
        # Per spec, the directory only exists when at least one ticker
        # has a match. Absence is not a failure on its own.
        return 0
    count = 0
    for path in sorted(by_ticker_dir.glob("*.json")):
        count += 1
        expected_ticker = path.stem
        scope = f"by-ticker/{expected_ticker}.json"
        if not TICKER_RE.match(expected_ticker):
            report.add(scope, f"filename ticker {expected_ticker!r} does not "
                              f"match {TICKER_RE.pattern}")
        rows = _load_json(path, report, scope)
        if rows is None:
            continue
        if not isinstance(rows, list):
            report.add(scope, f"top-level must be an array (got "
                              f"{type(rows).__name__})")
            continue
        for i, row in enumerate(rows):
            _validate_row(row, scope, i, report)
            if isinstance(row, dict):
                tk = row.get("ticker")
                if tk != expected_ticker:
                    report.add(scope, f"row[{i}] id={row.get('id')!r} "
                                      f"ticker={tk!r} does not match filename "
                                      f"{expected_ticker!r}")
    return count


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help="Override data directory (defaults to compounders/feed/data/ "
             "relative to repo root).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    data_dir = Path(args.data_dir).resolve()

    report = Report()

    print(f"validate_feed: data_dir = {data_dir}")

    feed_data = _load_json(data_dir / "feed.json", report, "feed.json")
    feed_rows = _validate_feed_json(feed_data, report)

    index_data = _load_json(data_dir / "index.json", report, "index.json")
    _validate_index_json(index_data, report)

    meta_data = _load_json(data_dir / "_meta.json", report, "_meta.json")
    _validate_meta_json(meta_data, report)

    by_ticker_count = _validate_by_ticker(data_dir, report)

    print(f"  feed.json rows checked:        {len(feed_rows)}")
    print(f"  index.json keys checked:       "
          f"{len(index_data) if isinstance(index_data, dict) else 0}")
    print(f"  by-ticker/*.json files checked: {by_ticker_count}")
    print()
    print(report.render())

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
