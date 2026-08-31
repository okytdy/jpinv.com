#!/usr/bin/env python3
"""Fail CI when the public new-5% feed is structurally valid but stale."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

DEFAULT_FEED = (Path(__file__).resolve().parents[2] / "compounders" /
                "active-investors" / "data" / "new5_feed.json")
JST = dt.timezone(dt.timedelta(hours=9))


def business_days_after(earlier: dt.date, later: dt.date) -> int:
    if later <= earlier:
        return 0
    count = 0
    cur = earlier + dt.timedelta(days=1)
    while cur <= later:
        if cur.weekday() < 5:
            count += 1
        cur += dt.timedelta(days=1)
    return count


def validate(feed: dict, *, today: dt.date, max_stale_business_days: int) -> list[str]:
    errors: list[str] = []
    meta = feed.get("meta") if isinstance(feed, dict) else None
    rows = feed.get("rows") if isinstance(feed, dict) else None
    if not isinstance(meta, dict):
        return ["meta is missing or not an object"]
    if not isinstance(rows, list):
        return ["rows is missing or not an array"]
    if meta.get("source_status") != "ok":
        errors.append(f"source_status={meta.get('source_status')!r}, expected 'ok'")
    ingestion = meta.get("ingestion")
    if not isinstance(ingestion, dict):
        errors.append("ingestion diagnostics are missing")
    elif int(ingestion.get("documents_seen") or 0) <= 0:
        errors.append("ingestion.documents_seen is zero")
    if int(meta.get("rows_count") or -1) != len(rows):
        errors.append(f"rows_count={meta.get('rows_count')!r}, actual={len(rows)}")

    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if len(ids) != len(rows) or any(not value for value in ids):
        errors.append("one or more rows have no id")
    if len(set(ids)) != len(ids):
        errors.append("duplicate row ids found")

    dates = [str(r.get("filing_date") or "") for r in rows if isinstance(r, dict)]
    if dates != sorted(dates, reverse=True):
        errors.append("rows are not sorted newest-first")
    newest = max(dates, default="")
    if meta.get("latest_filing_date") != newest:
        errors.append(
            f"latest_filing_date={meta.get('latest_filing_date')!r}, newest row={newest!r}")
    try:
        newest_date = dt.date.fromisoformat(newest)
    except ValueError:
        errors.append(f"newest filing date is invalid: {newest!r}")
    else:
        if newest_date > today:
            errors.append(f"newest filing date is in the future: {newest}")
        age = business_days_after(newest_date, today)
        if age > max_stale_business_days:
            errors.append(
                f"newest filing is {age} business days old ({newest}); "
                f"limit is {max_stale_business_days}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    ap.add_argument("--today", type=dt.date.fromisoformat,
                    default=dt.datetime.now(JST).date())
    ap.add_argument("--max-stale-business-days", type=int, default=3)
    args = ap.parse_args()
    try:
        with args.feed.open("r", encoding="utf-8") as fh:
            feed = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"active-investors validation failed: {exc}", file=sys.stderr)
        return 1
    errors = validate(feed, today=args.today,
                      max_stale_business_days=args.max_stale_business_days)
    if errors:
        print("active-investors validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"active-investors feed OK: {len(feed['rows'])} rows, "
          f"latest {feed['meta']['latest_filing_date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
