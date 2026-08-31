#!/usr/bin/env python3
"""
Active Investors in Japan — GLOBAL "new 5%" live feed.

Separate from the curated investor cards. This collects INITIAL large-shareholding
reports (EDINET docTypeCode 350, 大量保有報告書) from ANY filer — i.e. every new
5%+ shareholder crossing reported to EDINET — and writes a rolling, capped feed:

    compounders/active-investors/data/new5_feed.json

It also writes a four-row new5_home.json for the Compounders front page so
that page does not download the full rolling archive on every visit.

Each row carries the filer, the target company + ticker, the reported holding,
a neutral EN/JA one-line summary, the EDINET doc id and a source link. Filings
by one of the 9 tracked investors are flagged is_tracked=true so the UI can mark
them. Change reports (360) and corrections (訂正) are excluded — this feed is
strictly NEW 5% reports.

Run: EDINET_API_KEY=... python3 new5_feed.py --days 3 [--max-downloads 60]
Merges with the existing feed (dedupe by docID), keeps the most recent
ROWS_CAP rows. Designed to be called by cron; bounded per run by --max-downloads
so a single invocation stays well under tight step timeouts.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from build_data import DATA_DIR
from edinet_client import EdinetClient, parse_large_holding_csv, _finalize_row, KABUTAN_HOLDER, EDINET_VIEW
from summarize import template_summary

NEW5_PATH = DATA_DIR / "new5_feed.json"
NEW5_HOME_PATH = DATA_DIR / "new5_home.json"
ROWS_CAP = 500
HOME_ROWS = 4
KEEP_DAYS = 180


def _is_initial_new5(d: dict) -> bool:
    """docTypeCode 350 initial 大量保有報告書, excluding corrections (訂正)."""
    if str(d.get("docTypeCode")) != "350":
        return False
    desc = d.get("docDescription") or ""
    if "訂正" in desc or "変更" in desc:
        return False
    return "大量保有報告書" in desc or desc == ""


def _clean_filer(name: str) -> str:
    return (name or "").strip()


def _summary_en(row: dict, filer_en: str, issuer_en: str) -> str:
    """Rebuild the one-line English summary from a row + resolved English names.
    Mirrors the sentence built for new rows in build()."""
    code = row.get("issuer_code", "")
    shares = row.get("shares_held")
    shares_str = "{:,}".format(shares) if shares else None
    curs = C.pct(row.get("current_holding_ratio"))
    intent_en = C.INTENT_LABEL.get(row.get("intent", ""), {}).get("en", "")
    te = filer_en + " filed an initial large-shareholding report for " + issuer_en + " (" + code + ")"
    te += (": " + shares_str + " shares" if shares_str else "")
    te += (", " + curs + "% of voting rights." if curs else
           ". The holding ratio requires source review.")
    if intent_en:
        te += " Stated purpose: " + intent_en + "."
    return te


def _reresolve_names(row: dict, inv_by_id: dict) -> bool:
    """Upgrade a cached row's English names in place so the EN feed never shows
    raw Japanese. Runs every build so history self-heals as the vocabulary and
    the romanizer improve. Returns True if anything changed."""
    iid = row.get("investor_id")
    filer_raw = row.get("filer_raw_name", "")
    if iid and iid in inv_by_id:
        filer_en = inv_by_id[iid]["display_name"]
    else:
        filer_en = C.translate_fund_name(filer_raw) or C.tentative_en(filer_raw)[0] or filer_raw
    issuer_en = C.issuer_en(row.get("issuer_code", ""), row.get("issuer_name", ""))[0] \
        or row.get("issuer_name", "")

    changed = False
    if filer_en and row.get("filer_name_en") != filer_en:
        row["filer_name_en"] = filer_en
        changed = True
    if issuer_en and row.get("issuer_name_en") != issuer_en:
        row["issuer_name_en"] = issuer_en
        changed = True
    if changed or C.looks_japanese(row.get("summary_text_en", "")):
        row["summary_text_en"] = _summary_en(row, filer_en, issuer_en)
        changed = True
    return changed


def build(days: int, single_date: str | None, max_downloads: int, force_llm: bool):
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        print("EDINET_API_KEY not set", file=sys.stderr)
        return 2
    cfg = C.load_config()
    idx = C.build_alias_index(cfg)
    inv_by_id = {i["id"]: i for i in cfg["investors"]}
    client = EdinetClient(key)

    if single_date:
        dates = [single_date]
    else:
        today = _dt.date.fromisoformat(C.today_jst())
        dates = [(today - _dt.timedelta(days=i)).isoformat() for i in range(days + 1)]

    existing = C.read_json(NEW5_PATH, {}) or {}
    rows = {r["id"]: r for r in existing.get("rows", [])}
    downloads = 0
    documents_seen = candidates_seen = accepted = already_present = 0
    missing_csv = unparseable_ratio = 0

    for date in dates:
        docs = client.list_documents(date)
        documents_seen += len(docs)
        cands = [d for d in docs if _is_initial_new5(d)]
        candidates_seen += len(cands)
        for d in cands:
            doc_id = d.get("docID", "")
            if not doc_id:
                raise RuntimeError(f"EDINET returned an initial report without a docID on {date}")
            rid = f"edinet-{doc_id}"
            if rid in rows:
                already_present += 1
                continue
            if downloads >= max_downloads:
                raise RuntimeError(
                    f"max-downloads={max_downloads} reached before the requested window completed")
            csv = client.fetch_document_csv(doc_id)
            downloads += 1
            parsed = parse_large_holding_csv(csv) if csv else {}
            member_cur = parsed.get("current_pct")
            group_cur = parsed.get("group_current_pct")
            effective_cur = group_cur if group_cur is not None else member_cur
            # docType 350 + an initial-report description is the authoritative
            # inclusion rule. Do not discard the report merely because its CSV
            # is missing or a member-level ratio is below 5%; joint-holder
            # filings often cross 5% only at the group level.
            if not csv:
                missing_csv += 1
            if effective_cur is None:
                unparseable_ratio += 1
            cur = effective_cur
            filer = _clean_filer(d.get("filerName", ""))
            filer_code = (d.get("edinetCode") or "").strip()
            iid = C.attribute_investor(idx, filer_name=filer, edinet_code=filer_code)
            meta_row = EdinetClient._raw_from_meta(d)
            issuer = parsed.get("issuer_name") or meta_row.get("issuer_name") or ""
            code = parsed.get("issuer_code") or meta_row.get("issuer_code") or ""
            filer_en = inv_by_id[iid]["display_name"] if iid else (
                C.translate_fund_name(filer) or C.tentative_en(filer)[0] or filer)
            filer_ja = inv_by_id[iid].get("display_name_ja", filer) if iid else filer
            row = {
                "investor_id": iid,
                "is_tracked": bool(iid),
                "filer_raw_name": filer,
                "filer_name_en": filer_en,
                "issuer_name": issuer,
                "issuer_name_en": "",
                "issuer_code": code,
                "current_holding_ratio": cur,
                **({"member_current_holding_ratio": member_cur}
                   if group_cur is not None and member_cur is not None else {}),
                **({"group_current_holding_ratio": group_cur} if group_cur is not None else {}),
                "change_percentage_points": None,
                "move_type": "new_5pct",
                "confidence": "high" if effective_cur is not None else "low",
                "caveats": ([] if effective_cur is not None else
                            ["Holding ratio could not be parsed automatically; review the source filing."]),
            }
            row["purpose_ja"] = parsed.get("purpose_ja", "")
            row["reason_ja"] = ""
            row["intent"] = C.classify_intent(row["purpose_ja"])
            disp = inv_by_id[iid] if iid else {"display_name": filer, "display_name_ja": filer}
            s = template_summary(row, disp)
            # English company name (official JPX) + share count for the 2-line summary.
            issuer_en = C.issuer_en(code, issuer)[0] or issuer
            shares = parsed.get("shares_held")
            shares_str = ("{:,}".format(shares)) if shares else None
            intent_en = C.INTENT_LABEL.get(row["intent"], {}).get("en", "")
            intent_ja = C.INTENT_LABEL.get(row["intent"], {}).get("ja", "")
            curs = C.pct(cur)
            te = filer_en + " filed an initial large-shareholding report for " + issuer_en + " (" + code + ")"
            te += (": " + shares_str + " shares" if shares_str else "")
            te += (", " + curs + "% of voting rights." if curs else ". The holding ratio requires source review.")
            if intent_en:
                te += " Stated purpose: " + intent_en + "."
            tj = filer_ja + "は" + issuer + "（" + code + "）について新規の大量保有報告書を提出"
            tj += ("。保有株式数 " + shares_str + " 株" if shares_str else "")
            tj += ("、保有割合 " + curs + "%。" if curs else "。保有割合は原文確認が必要です。")
            if intent_ja:
                tj += "保有目的：" + intent_ja + "。"
            rows[rid] = {
                "id": rid,
                "edinet_doc_id": doc_id,
                "filing_date": (d.get("submitDateTime") or "")[:10],
                "filer_raw_name": filer,
                "filer_name_en": filer_en,
                "investor_id": iid,
                "is_tracked": bool(iid),
                "issuer_name": issuer,
                "issuer_name_en": issuer_en,
                "issuer_code": code,
                "shares_held": shares,
                "current_holding_ratio": cur,
                **({"member_current_holding_ratio": member_cur}
                   if group_cur is not None and member_cur is not None else {}),
                **({"group_current_holding_ratio": group_cur} if group_cur is not None else {}),
                "move_type": "new_5pct",
                "japanese_title": d.get("docDescription") or "大量保有報告書",
                "source_url": (C.edinet_filing_url(doc_id)
                               or (KABUTAN_HOLDER.format(code=filer_code) if filer_code else EDINET_VIEW)),
                "intent": s["intent"],
                "signal": s["signal"],
                "summary_en": s["en"],
                "summary_ja": s["ja"],
                "summary_text_en": te,
                "summary_text_ja": tj,
                "confidence": row["confidence"],
                "caveats": row["caveats"],
            }
            accepted += 1

    if documents_seen == 0 and any(_dt.date.fromisoformat(d).weekday() < 5 for d in dates):
        raise RuntimeError(
            "EDINET returned zero documents for the entire requested window; refusing to mark the feed fresh")

    # Self-heal: re-resolve English names on every cached row so previously
    # untranslated (Japanese) filer / issuer names get a real or tentative
    # English rendering as the vocabulary and romanizer improve.
    healed = 0
    for r in rows.values():
        if _reresolve_names(r, inv_by_id):
            healed += 1
        official_source = C.edinet_filing_url(r.get("edinet_doc_id", ""))
        if official_source:
            r["source_url"] = official_source
    if healed:
        print(f"[new5] re-resolved English names on {healed} existing row(s).")

    # Prune to KEEP_DAYS + cap, newest first.
    today_jst = _dt.date.fromisoformat(C.today_jst())
    cutoff = (today_jst - _dt.timedelta(days=KEEP_DAYS)).isoformat()
    allrows = [r for r in rows.values() if r.get("filing_date", "") >= cutoff]
    allrows.sort(key=lambda r: (r.get("filing_date", ""), r["id"]), reverse=True)
    allrows = allrows[:ROWS_CAP]

    completed_at = C.now_jst_iso()
    out = {
        "meta": {
            "generated_at": completed_at,
            "as_of_date": C.today_jst(),
            "source_status": "ok",
            "last_successful_fetch_at": completed_at,
            "latest_filing_date": allrows[0].get("filing_date", "") if allrows else "",
            "rows_count": len(allrows),
            "tracked_count": sum(1 for r in allrows if r.get("is_tracked")),
            "source": "EDINET API v2 (FSA) docTypeCode 350 initial large-shareholding reports",
            "ingestion": {
                "requested_start": min(dates),
                "requested_end": max(dates),
                "days_requested": len(dates),
                "documents_seen": documents_seen,
                "initial_reports_seen": candidates_seen,
                "already_present": already_present,
                "new_rows_added": accepted,
                "csv_downloads": downloads,
                "missing_csv": missing_csv,
                "unparseable_ratio": unparseable_ratio,
            },
        },
        "rows": allrows,
    }
    C.write_json(NEW5_PATH, out)
    home = {
        "meta": out["meta"],
        "rows": [{
            "filing_date": r.get("filing_date", ""),
            "filer_raw_name": r.get("filer_raw_name", ""),
            "filer_name_en": r.get("filer_name_en", ""),
            "issuer_name": r.get("issuer_name", ""),
            "issuer_name_en": r.get("issuer_name_en", ""),
            "issuer_code": r.get("issuer_code", ""),
            "current_holding_ratio": r.get("current_holding_ratio"),
            "edinet_doc_id": r.get("edinet_doc_id", ""),
            "source_url": r.get("source_url", ""),
            "japanese_title": r.get("japanese_title", ""),
            "summary_en": r.get("summary_en", {}),
            "summary_ja": r.get("summary_ja", {}),
        } for r in allrows if r.get("issuer_code")][:HOME_ROWS],
    }
    C.write_json(NEW5_HOME_PATH, home)
    print(f"[new5] {len(allrows)} rows ({out['meta']['tracked_count']} by tracked funds); "
          f"{accepted} added from {candidates_seen} initial reports, {downloads} CSVs fetched "
          f"-> {NEW5_PATH} + {NEW5_HOME_PATH}")
    return 0


def scan(days: int):
    """Count candidates per day without downloading (fast sizing)."""
    key = os.environ.get("EDINET_API_KEY", "").strip()
    client = EdinetClient(key)
    today = _dt.date.fromisoformat(C.today_jst())
    for i in range(days + 1):
        date = (today - _dt.timedelta(days=i)).isoformat()
        docs = client.list_documents(date)
        n = sum(1 for d in docs if _is_initial_new5(d))
        print(f"  {date}: {n} initial new-5% candidates ({len(docs)} docs total)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--date", type=str, default=None)
    ap.add_argument("--max-downloads", type=int, default=60)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    if a.scan:
        return scan(a.days)
    return build(a.days, a.date, a.max_downloads, a.llm)


if __name__ == "__main__":
    raise SystemExit(main())
