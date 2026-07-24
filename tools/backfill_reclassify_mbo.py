"""
JII Compounders - one-time reclassification backfill: MBO -> M_AND_A.

Why this exists
---------------
The feed's classifier used to read EVERY 完全子会社化 ("make wholly owned") as a
take-private. But that word points in two opposite directions. A parent can make
the LISTED FILER wholly owned and delist it (a real take-private), OR the LISTED
FILER can make some OTHER company wholly owned (ordinary outbound M&A, where the
filer is the buyer). The old code labelled both "Take-private", so a listed
company acquiring a private subsidiary - e.g. 6055 Japan Material buying the last
30% of GBS (Singapore) on 2026-07-23 - printed as a take-private.

classifier.py now decides direction and routes the buyer case to a new class,
M_AND_A. But existing rows in feed.json / by-ticker / archive were already
classified and are skipped by the incremental refresh (id-based dedupe), so they
keep the old label until a one-time pass fixes them. That is this script.

What it does, per MBO / M_AND_A row
-----------------------------------
1. If the row still carries its Japanese title, re-run the live classifier on the
   title. That is the authoritative fix (self-take-private stays MBO; outbound
   completion becomes M_AND_A; stale FSA "買集め行為" rows that the classifier no
   longer recognises are dropped).
2. If the title was not stored (older backfilled rows), use the one reliable
   proxy: the stored kind tag "Going-private (parent)" is emitted ONLY by the
   完全子会社化 branch, which is outbound by the new model, so flip those to
   M_AND_A. Every other blank-title kind ("Tender offer", "MBO", "Going-private")
   is left as MBO - outbound tender offers against a listed target were already
   stored as M_AND_A by the old ticker guard, so a surviving "Tender offer" MBO
   is the filer being tendered FOR.
3. For any row whose final class is M_AND_A, strip the wrong leading take-private
   label out of the human tags (tag / tag_en / tag_jp) so the display reads as an
   acquisition, and recompute signal_score.

Safety
------
- A row is DROPPED only when the classifier returns None AND the title is a known
  non-inflection (FSA 買集め行為 / 公開買付けに準ずる行為). Any other None keeps the
  row unchanged, so we never lose a real row to an unexpected parse.
- Idempotent: running twice yields the same result.
- Rewrites feed.json, index.json, every by-ticker/*.json and archive/*.json using
  the feed's JSON convention (sort_keys, indent=2, ensure_ascii=False, trailing
  newline), via atomic temp-file replace.

Usage
-----
    python tools/backfill_reclassify_mbo.py            # repo data dir
    python tools/backfill_reclassify_mbo.py --data-dir /path/to/data --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import classifier  # noqa: E402

REPO_ROOT = _SCRIPT_DIR.parent
DEFAULT_DATA_DIR = REPO_ROOT / "compounders" / "feed" / "data"

# Leading wrong-label token (take-private wording) + a separator. Stripped from
# the human tags of rows that are actually outbound M&A. Also strips a leading
# "M&A"/"Acquisition"/"買収" so it does not duplicate the "M&A / Acquisition" pill.
_LEAD_LABEL = re.compile(
    r"^\s*(?:MBO|Take[-\s]?private|Going[-\s]?private(?:\s*\(parent\))?|"
    r"TOB\s*/\s*MBO|非公開化|M&A|M＆A|Acquisition|買収)\s*[·・:：\-–—]\s*",
    re.IGNORECASE,
)
# A tag that is nothing but a bare wrong label (e.g. "Take-private", "TOB / MBO").
_BARE_LABEL = re.compile(
    r"^\s*(?:MBO|Take[-\s]?private|Going[-\s]?private(?:\s*\(parent\))?|"
    r"TOB\s*/\s*MBO|非公開化)\s*$",
    re.IGNORECASE,
)
_DROP_TITLE = re.compile(r"公開買付け?に準ずる行為|買集め行為")


def _clean_tag(s):
    """Strip a leading take-private / M&A label from a human tag. Return '' if
    nothing meaningful is left (so the display falls back to the class pill)."""
    if not isinstance(s, str) or not s.strip():
        return s
    out = _LEAD_LABEL.sub("", s, count=1).strip()
    if not out or _BARE_LABEL.match(out):
        return ""
    return out


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
    if not text.endswith("\n"):
        text += "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def _reclassify_row(row: dict, stats: dict):
    """Return the transformed row, or None to drop it."""
    if not isinstance(row, dict):
        return row
    cls = row.get("class")
    if cls not in ("MBO", "M_AND_A"):
        return row

    title = (row.get("doc_title_jp") or "").strip()
    old_cls = cls
    new_cls = cls
    new_tag = row.get("tag")

    if title:
        res = classifier.classify({
            "title_jp": title,
            "body_jp": None,
            "ticker": row.get("ticker", ""),
            "submitted_at": row.get("ts", ""),
            "doc_id": (row.get("id", "") or "").split("-", 1)[-1],
            "source": row.get("source", "TDnet"),
        })
        if res is None:
            if _DROP_TITLE.search(title):
                stats["dropped"].append(row.get("id"))
                return None
            stats["kept_unexpected_none"].append(row.get("id"))
            return row
        new_cls = res["class"]
        new_tag = res["tag"]
    else:
        # Blank title: only the 完全子会社化 kind ("Going-private (parent)") is
        # systematically mislabelled. Everything else stays MBO.
        if cls == "MBO" and (row.get("tag") or "") == "Going-private (parent)":
            new_cls = "M_AND_A"
            new_tag = "Subsidiary consolidation"

    flipped = new_cls != old_cls
    if flipped:
        row["class"] = new_cls
        row["tag"] = new_tag

    # For anything that ends up M&A, clean the human tags and fix the score.
    if new_cls == "M_AND_A":
        cleaned_tag = _clean_tag(row.get("tag"))
        if cleaned_tag:
            row["tag"] = cleaned_tag
        row["tag_en"] = _clean_tag(row.get("tag_en"))
        row["tag_jp"] = _clean_tag(row.get("tag_jp"))
        row["signal_score"] = classifier._signal_score(
            "M_AND_A", row.get("key_facts") or {}
        )

    if flipped:
        stats["flipped"].append((old_cls, new_cls, row.get("ticker")))
    elif new_cls == "M_AND_A":
        stats["cleaned_existing"].append(row.get("id"))
    else:
        stats["kept_mbo"].append(row.get("id"))
    return row


def _process_list(rows, stats, drop_ids=None):
    """Transform each row. Also drop any row whose id is in drop_ids -- used so
    that rows dropped from feed.json (stale FSA 買集め行為 filings) are removed
    from the by-ticker / archive copies too, even if a copy stored the row under
    a stale legacy class (e.g. a lone INSIDER_REORG in by-ticker/5038.json)."""
    out = []
    for r in rows:
        if drop_ids and isinstance(r, dict) and r.get("id") in drop_ids:
            stats["dropped"].append(r.get("id"))
            continue
        nr = _reclassify_row(r, stats)
        if nr is not None:
            out.append(nr)
    return out


def _rebuild_index(rows):
    index = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        tk = (r.get("ticker") or "").strip()
        if not tk:
            continue
        bucket = index.setdefault(tk, {"match_count": 0, "last_match_iso": ""})
        bucket["match_count"] += 1
        ts = r.get("ts", "")
        if ts > bucket["last_match_iso"]:
            bucket["last_match_iso"] = ts
    return index


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    ap.add_argument("--dry-run", action="store_true",
                    help="report only; do not write any files")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    feed_json = data_dir / "feed.json"
    index_json = data_dir / "index.json"
    by_ticker_dir = data_dir / "by-ticker"
    archive_dir = data_dir / "archive"

    stats = {"flipped": [], "dropped": [], "cleaned_existing": [],
             "kept_mbo": [], "kept_unexpected_none": []}

    if not feed_json.exists():
        print(f"ERROR: {feed_json} not found", file=sys.stderr)
        return 2

    with feed_json.open(encoding="utf-8") as fh:
        feed = json.load(fh)
    feed = _process_list(feed, stats)
    drop_ids = set(stats["dropped"])

    # by-ticker + archive: apply the same transform, and drop the same ids the
    # feed dropped (keeps every copy of a stale filing consistent).
    side_stats = {k: [] for k in stats}
    by_ticker_files = sorted(by_ticker_dir.glob("*.json")) if by_ticker_dir.exists() else []
    archive_files = sorted(archive_dir.glob("*.json")) if archive_dir.exists() else []
    side_payloads = {}
    for p in by_ticker_files + archive_files:
        with p.open(encoding="utf-8") as fh:
            rows = json.load(fh)
        if isinstance(rows, list):
            side_payloads[p] = _process_list(rows, side_stats, drop_ids=drop_ids)

    # ---- report -----------------------------------------------------------
    from collections import Counter
    print("=== Reclassification backfill report (feed.json) ===")
    print(f"  flipped MBO -> M_AND_A : {len(stats['flipped'])}")
    print(f"  dropped (stale 買集め行為): {len(stats['dropped'])}")
    print(f"  existing M_AND_A cleaned: {len(stats['cleaned_existing'])}")
    print(f"  kept as MBO            : {len(stats['kept_mbo'])}")
    if stats["kept_unexpected_none"]:
        print(f"  WARN kept (unexpected None, NOT dropped): "
              f"{len(stats['kept_unexpected_none'])} -> {stats['kept_unexpected_none'][:10]}")
    print(f"  flip directions        : {Counter(f[:2] for f in stats['flipped'])}")
    print(f"  side files touched     : {len(side_payloads)} "
          f"(by-ticker {len(by_ticker_files)}, archive {len(archive_files)})")
    print(f"  side flips             : {len(side_stats['flipped'])}, "
          f"side drops {len(side_stats['dropped'])}")

    if args.dry_run:
        print("\n(dry-run: no files written)")
        return 0

    _write_json(feed_json, feed)
    _write_json(index_json, _rebuild_index(feed))
    for p, rows in side_payloads.items():
        _write_json(p, rows)

    # Stamp meta so a human can see the pass ran.
    if index_json.parent.joinpath("_meta.json").exists():
        meta_path = index_json.parent / "_meta.json"
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(meta, dict):
                import datetime as _dt
                jst = _dt.timezone(_dt.timedelta(hours=9))
                meta["last_reclassify_backfill_iso"] = _dt.datetime.now(jst).strftime(
                    "%Y-%m-%dT%H:%M:%S+09:00")
                meta["last_reclassify_flips"] = len(stats["flipped"]) + len(side_stats["flipped"])
                _write_json(meta_path, meta)
        except (OSError, json.JSONDecodeError):
            pass

    print("\nWrote feed.json, index.json, and all side files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
