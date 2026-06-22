#!/usr/bin/env python3
"""
Active Investors in Japan — update command (9 curated cards).

Modes
-----
  python refresh.py --seed
      Build the public data from the genuine seed file (config/seed_filings.json).
      Key-free, deterministic template summaries. Run once to populate the page
      before you have an EDINET key.

  python refresh.py --build-only
      Re-emit the public data from the existing filings.json — run after you edit
      investors.json (swap the 9, rename, re-rank) or editorial.json
      (hide / pin / override summary). No network.

  python refresh.py                 (default: live, last 5 days)
  python refresh.py --days 30       (live backfill, last 30 days)
  python refresh.py --date 2026-05-22
      Pull large-shareholding filings from the FSA EDINET API, attribute to the
      configured investors (download CSV only for matches), classify, summarize,
      and merge into the historical record. Needs EDINET_API_KEY. Uses
      ANTHROPIC_API_KEY for the Claude summary tier when present.

Also run tools/active_investors/new5_feed.py for the TSE-wide new-5% feed.

Env: EDINET_API_KEY (live), ANTHROPIC_API_KEY (optional), FEED_MAX_DOWNLOADS.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common as C
import build_data
from build_data import DATA_DIR

SEED_FILE = C.CONFIG_DIR / "seed_filings.json"
CACHE_FILE = Path(__file__).resolve().parent / ".summary_cache.json"
LEDGER_FILE = Path(__file__).resolve().parent / ".llm_ledger.json"


class Budget:
    """Soft monthly USD guard + per-run wall-clock guard for the optional Claude
    summary tier. The wall-clock deadline (default 8 min, well under the 12-min
    CI step timeout) means a slow/overloaded Anthropic API stops the LLM tier and
    falls back to template summaries rather than hanging the whole job."""
    HARD_CAP_USD = float(os.environ.get("ACTIVE_INVESTORS_LLM_CAP_USD", "5"))
    DEADLINE_SEC = float(os.environ.get("ACTIVE_INVESTORS_LLM_DEADLINE_SEC", "480"))
    IN_PER_MTOK = 1.0
    OUT_PER_MTOK = 5.0

    def __init__(self, path=LEDGER_FILE):
        self.path = path
        d = C.read_json(path, {}) or {}
        self.month = _dt.date.today().strftime("%Y-%m")
        self.spent = float(d.get("spent_usd") or 0.0) if d.get("month") == self.month else 0.0
        self._t0 = time.monotonic()

    def can_spend(self):
        return (self.spent < self.HARD_CAP_USD
                and (time.monotonic() - self._t0) < self.DEADLINE_SEC)

    def record(self, usage):
        if not usage:
            return
        it = getattr(usage, "input_tokens", 0) or 0
        ot = getattr(usage, "output_tokens", 0) or 0
        self.spent += it / 1e6 * self.IN_PER_MTOK + ot / 1e6 * self.OUT_PER_MTOK

    def save(self):
        C.write_json(self.path, {"month": self.month, "spent_usd": round(self.spent, 4)})


def _raw_from_normalized(f: dict) -> dict:
    """Reconstruct a build() input from a stored filings.json row."""
    return {
        "investor_id": f["investor_id"],
        "edinet_doc_id": f.get("edinet_doc_id") or "",
        "filing_date": f.get("filing_date", ""),
        "is_change_report": f.get("filing_type") != "new_5pct_report",
        "current_pct": f.get("current_holding_ratio"),
        "previous_pct": f.get("previous_holding_ratio"),
        "change_pp": f.get("change_percentage_points"),
        "filer_raw_name": f.get("filer_raw_name", ""),
        "issuer_name": f.get("issuer_name", ""),
        "issuer_name_en": f.get("issuer_name_en", ""),
        "issuer_code": f.get("issuer_code", ""),
        "reason_ja": f.get("japanese_title", ""),
        "purpose_ja": f.get("purpose_ja", ""),
        "purpose_category": f.get("purpose_category", ""),
        "source_url": f.get("source_url", ""),
        "confidence": f.get("confidence"),
        "caveats": f.get("caveats") or [],
        "seed": f.get("seed", False),
    }


def _resolve_method(force_llm: bool):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if force_llm and not key:
        print("warning: --llm requested but ANTHROPIC_API_KEY unset; using template tier.")
    return ("llm" if key else "template"), key


def run_seed(force_llm=False) -> int:
    cfg = C.load_config()
    seed = C.read_json(SEED_FILE)
    if not seed or "filings" not in seed:
        print(f"seed file missing: {SEED_FILE}", file=sys.stderr); return 2
    raws = []
    for r in seed["filings"]:
        r = dict(r); r["seed"] = True; r["filing_date"] = r.get("base_date", "")
        raws.append(r)
    method, key = _resolve_method(force_llm) if force_llm else ("template", "")
    cache = {}  # seed regenerates summaries deterministically from the data
    budget = Budget()
    meta = build_data.build(raws, cfg, editorial=C.load_editorial(),
                            summarize_method=method, api_key=key, budget=budget, summary_cache=cache)
    C.write_json(CACHE_FILE, cache); budget.save()
    print(f"[seed] {meta['counts']['filings_total']} filings "
          f"({meta['counts']['filings_visible']} visible), {meta['counts']['investors_total']} investors.")
    return 0


def run_build_only() -> int:
    cfg = C.load_config()
    existing = C.read_json(DATA_DIR / "filings.json", []) or []
    raws = [_raw_from_normalized(f) for f in existing]
    cache = C.read_json(CACHE_FILE, {}) or {}
    method, key = _resolve_method(False)
    budget = Budget()
    meta = build_data.build(raws, cfg, editorial=C.load_editorial(),
                            summarize_method=method, api_key=key, budget=budget, summary_cache=cache)
    C.write_json(CACHE_FILE, cache); budget.save()
    print(f"[build-only] re-emitted {meta['counts']['filings_visible']} visible filings.")
    return 0


def run_live(days: int, single_date, force_llm: bool) -> int:
    from edinet_client import (EdinetClient, parse_large_holding_csv, _finalize_row,
                               DOC_TYPES_LARGE_HOLDING)
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        print("error: EDINET_API_KEY not set. See README.", file=sys.stderr); return 2
    cfg = C.load_config()
    alias_index = C.build_alias_index(cfg)
    client = EdinetClient(key)
    max_dl = int(os.environ.get("FEED_MAX_DOWNLOADS", "500"))

    if single_date:
        dates = [single_date]
    else:
        today = _dt.date.today()
        dates = [(today - _dt.timedelta(days=i)).isoformat() for i in range(days + 1)]

    # Start from the historical record so nothing is lost.
    existing = C.read_json(DATA_DIR / "filings.json", []) or []
    raws = [_raw_from_normalized(f) for f in existing]
    seen_docs = {f.get("edinet_doc_id") for f in existing if f.get("edinet_doc_id")}

    unmatched, new_n, downloads = [], 0, 0
    for date in dates:
        try:
            docs = client.list_documents(date)
        except Exception as e:
            print(f"  list {date} failed: {e}"); continue
        for d in docs:
            if str(d.get("docTypeCode")) not in DOC_TYPES_LARGE_HOLDING:
                continue
            # Attribute from metadata BEFORE downloading — only matches cost a fetch.
            iid = C.attribute_investor(alias_index, filer_name=d.get("filerName", ""),
                                       edinet_code=(d.get("edinetCode") or ""))
            if not iid:
                unmatched.append({"filer": d.get("filerName", ""), "doc": d.get("docID", "")})
                continue
            if d.get("docID") in seen_docs:
                continue
            if downloads >= max_dl:
                print(f"  reached FEED_MAX_DOWNLOADS={max_dl}; stopping (rerun to continue)."); break
            row = EdinetClient._raw_from_meta(d)
            row["investor_id"] = iid
            csv = client.fetch_document_csv(row["edinet_doc_id"]); downloads += 1
            if csv:
                row.update({k: v for k, v in parse_large_holding_csv(csv).items() if v is not None})
            _finalize_row(row)
            raws.append(row); new_n += 1
        else:
            continue
        break

    cache = C.read_json(CACHE_FILE, {}) or {}
    method, akey = _resolve_method(force_llm)
    budget = Budget()
    err = [{"reason": "unmatched_filer", **u} for u in unmatched[:50]]
    meta = build_data.build(raws, cfg, editorial=C.load_editorial(),
                            summarize_method=method, api_key=akey, budget=budget,
                            summary_cache=cache, error_log=err)
    C.write_json(CACHE_FILE, cache)
    C.write_json(DATA_DIR / "_unmatched.json", unmatched)
    budget.save()
    print(f"[live {dates[-1]}..{dates[0]}] {new_n} attributed filing(s), {downloads} CSVs fetched; "
          f"{len(unmatched)} unmatched filers logged. Visible total: {meta['counts']['filings_visible']}.")
    return 0


def run_reenrich(force_llm: bool) -> int:
    """Back-fill the high-signal 保有目的 (purpose of holding) for existing live
    rows that lack it, by re-fetching just their CSV. Resumable + bounded by
    FEED_MAX_DOWNLOADS; rows already enriched are skipped."""
    from edinet_client import EdinetClient, parse_large_holding_csv
    key = os.environ.get("EDINET_API_KEY", "").strip()
    if not key:
        print("error: EDINET_API_KEY not set.", file=sys.stderr); return 2
    cfg = C.load_config()
    existing = C.read_json(DATA_DIR / "filings.json", []) or []
    raws = [_raw_from_normalized(f) for f in existing]
    client = EdinetClient(key)
    max_dl = int(os.environ.get("FEED_MAX_DOWNLOADS", "120"))
    fetched = enriched = 0
    for r in raws:
        if r.get("purpose_ja") or not r.get("edinet_doc_id"):
            continue
        if fetched >= max_dl:
            print(f"  reached FEED_MAX_DOWNLOADS={max_dl}; rerun to continue."); break
        csv = client.fetch_document_csv(r["edinet_doc_id"]); fetched += 1
        if not csv:
            continue
        p = parse_large_holding_csv(csv)
        if p.get("purpose_ja"):
            r["purpose_ja"] = p["purpose_ja"]; enriched += 1
        if p.get("reason_ja") and not r.get("reason_ja"):
            r["reason_ja"] = p["reason_ja"]
    cache = C.read_json(CACHE_FILE, {}) or {}
    # purpose changed -> summaries must regenerate; drop cache for enriched rows
    cache = {}
    method, akey = _resolve_method(force_llm)
    budget = Budget()
    meta = build_data.build(raws, cfg, editorial=C.load_editorial(),
                            summarize_method=method, api_key=akey, budget=budget,
                            summary_cache=cache)
    C.write_json(CACHE_FILE, cache); budget.save()
    print(f"[reenrich] fetched {fetched} CSV(s), added purpose to {enriched} row(s). "
          f"Visible: {meta['counts']['filings_visible']}.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Active Investors in Japan — update command")
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--build-only", action="store_true")
    ap.add_argument("--reenrich-purpose", action="store_true")
    ap.add_argument("--days", type=int, default=5)
    ap.add_argument("--date", type=str, default=None)
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    if a.seed:
        return run_seed(force_llm=a.llm)
    if a.build_only:
        return run_build_only()
    if a.reenrich_purpose:
        return run_reenrich(a.llm)
    return run_live(a.days, a.date, a.llm)


if __name__ == "__main__":
    raise SystemExit(main())
