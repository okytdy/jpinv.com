#!/usr/bin/env python3
"""
Rank the most active large-shareholding (5%) filers over a window.

Metadata-only: reads EDINET document listings (no CSV downloads), tallies
docTypeCode 350 (initial 大量保有報告書) + 360 (変更報告書) per filer. Resumable —
each run extends a persistent tally (.filer_tally.json) and skips already-scanned
dates, so it can be invoked in chunks under a tight shell timeout.

  EDINET_API_KEY=... python3 rank_filers.py --start 2025-07-01 --end 2026-06-03 --max-seconds 38
  python3 rank_filers.py --report --top 40        # print ranking, no scan
"""
from __future__ import annotations
import argparse, datetime as _dt, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from edinet_client import EdinetClient

TALLY = Path(__file__).resolve().parent / ".filer_tally.json"


def _load():
    d = C.read_json(TALLY, {}) or {}
    d.setdefault("scanned", []); d.setdefault("filers", {})
    return d


def _is_new5(desc): return ("訂正" not in desc) and ("変更" not in desc)


def scan(start, end, max_seconds):
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        print("EDINET_API_KEY not set", file=sys.stderr); return 2
    client = EdinetClient(key)
    d = _load()
    scanned = set(d["scanned"]); filers = d["filers"]
    s = _dt.date.fromisoformat(start); e = _dt.date.fromisoformat(end)
    deadline = time.monotonic() + max_seconds
    dates = []
    cur = s
    while cur <= e:
        if cur.isoformat() not in scanned:
            dates.append(cur.isoformat())
        cur += _dt.timedelta(days=1)
    done = 0
    for date in dates:
        if time.monotonic() >= deadline:
            break
        try:
            docs = client.list_documents(date)
        except Exception:
            continue
        for doc in docs:
            dt = str(doc.get("docTypeCode"))
            if dt not in ("350", "360"):
                continue
            code = (doc.get("edinetCode") or "").strip() or ("name:" + (doc.get("filerName") or ""))
            desc = doc.get("docDescription") or ""
            rec = filers.setdefault(code, {"name": doc.get("filerName", ""), "total": 0,
                                           "new5": 0, "chg": 0, "last": ""})
            rec["name"] = doc.get("filerName", "") or rec["name"]
            rec["total"] += 1
            if dt == "350" and _is_new5(desc):
                rec["new5"] += 1
            else:
                rec["chg"] += 1
            sd = (doc.get("submitDateTime") or "")[:10]
            if sd > rec["last"]:
                rec["last"] = sd
        scanned.add(date); done += 1
    d["scanned"] = sorted(scanned)
    C.write_json(TALLY, d)
    remaining = len(dates) - done
    print(f"scanned {done} new day(s); {len(scanned)} total scanned; ~{remaining} day(s) remain in range.")
    return 0


def report(top):
    d = _load()
    rows = sorted(d["filers"].values(), key=lambda r: r["total"], reverse=True)[:top]
    # attribution to the configured investors (for tagging)
    cfg = C.load_config(); idx = C.build_alias_index(cfg)
    inv = {i["id"]: i for i in cfg["investors"]}
    print(f"{'#':>3} {'total':>6}{'new5':>6}{'chg':>6}  {'last':<11} filer")
    for i, r in enumerate(rows, 1):
        iid = C.attribute_investor(idx, filer_name=r["name"])
        tag = ("=" + inv[iid]["display_name"]) if iid else ""
        print(f"{i:>3} {r['total']:>6}{r['new5']:>6}{r['chg']:>6}  {r['last']:<11} {r['name'][:48]} {tag}")
    print(f"\nscanned days: {len(d['scanned'])}  | distinct filers: {len(d['filers'])}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-07-01")
    ap.add_argument("--end", default=_dt.date.today().isoformat())
    ap.add_argument("--max-seconds", type=int, default=38)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()
    if a.report:
        return report(a.top)
    return scan(a.start, a.end, a.max_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
