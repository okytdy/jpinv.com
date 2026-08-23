"""
Active Investors in Japan — data builder.

Takes a list of ATTRIBUTED filing dicts (each carrying investor_id + disclosed
numbers) plus the investor config, then writes the public data model under
compounders/active-investors/data/:

    investors.json   — public investor records + computed stats
    filings.json     — every filing (full audit set, incl. sub-1pp amendments)
    summaries.json   — filing_id -> {en, ja, move_type, confidence, caveats}
    feed.json        — denormalized view the page fetches
    _meta.json       — generated_at, window, counts, error log

Seed and live both call build(); identical rules. Seed (date = reference date,
no doc id) and live (date = submission date, real doc id) rows for the SAME
underlying filing are collapsed by content key, preferring the live row.
"""
from __future__ import annotations

from pathlib import Path

import common as C
from summarize import make_summary

REPO_ROOT = Path(__file__).resolve().parents[2]   # .../jpinv.com
DATA_DIR = REPO_ROOT / "compounders" / "active-investors" / "data"


def _filing_type(is_change_report: bool, move_type: str) -> str:
    if not is_change_report:
        return "new_5pct_report"
    if move_type == C.MOVE_OTHER:
        return "amendment"
    return "change_report"


def normalize_filing(raw: dict) -> dict:
    """Attributed raw filing -> canonical record + classification. Ratios percent."""
    is_change = bool(raw.get("is_change_report"))
    cur = raw.get("current_pct")
    chg = raw.get("change_pp")
    prev = raw.get("previous_pct")
    cls = C.classify_move(is_change_report=is_change, current_pct=cur,
                          change_pp=chg, previous_pct=prev)
    date = raw.get("filing_date") or raw.get("base_date") or ""
    doc_id = raw.get("edinet_doc_id") or ""
    iid = raw["investor_id"]
    code = str(raw.get("issuer_code", "")).strip()
    fid = C.filing_id(investor_id=iid, issuer_code=code, date=date,
                      current_pct=cur, edinet_doc_id=doc_id)
    confidence = raw.get("confidence") or cls["confidence_floor"]
    order = {"low": 0, "medium": 1, "high": 2}
    if order.get(confidence, 2) > order.get(cls["confidence_floor"], 2):
        confidence = cls["confidence_floor"]
    now = C.now_jst_iso()
    return {
        "id": fid,
        "investor_id": iid,
        "edinet_doc_id": doc_id or None,
        "filing_date": date,
        "filing_type": _filing_type(is_change, cls["move_type"]),
        # Prefer an explicit doc title (live docDescription); fall back to the
        # Japanese reason text (seed rows carry the reason here).
        "japanese_title": raw.get("japanese_title") or raw.get("reason_ja") or "",
        "filer_raw_name": raw.get("filer_raw_name", ""),
        "issuer_name": raw.get("issuer_name", ""),
        "issuer_name_en": raw.get("issuer_name_en") or C.jpx_name_en(code),
        "issuer_code": code,
        "previous_holding_ratio": cls["previous_pct"],
        "current_holding_ratio": cur,
        "change_percentage_points": cls["change_pp"],
        "move_type": cls["move_type"],
        "qualifying": cls["qualifying"],
        "audit_only": cls["audit_only"],
        "purpose_category": raw.get("purpose_category", ""),
        "purpose_ja": raw.get("purpose_ja", ""),
        "intent": C.intent_from(raw.get("purpose_ja", ""), raw.get("purpose_category", "")),
        "source_url": (C.edinet_filing_url(doc_id) or raw.get("source_url", "")),
        "confidence": confidence,
        "caveats": list(raw.get("caveats") or []),
        "seed": bool(raw.get("seed", False)),
        "created_at": now,
        "updated_at": now,
    }


def _sort_key(f):
    return (f.get("filing_date", ""), f.get("id", ""))


def _content_key(f):
    """Identity of the underlying filing independent of date-field/source, so a
    seed row and the live EDINET row for the same move collapse to one."""
    cur = f.get("current_holding_ratio")
    prev = f.get("previous_holding_ratio")
    return (f["investor_id"], f.get("issuer_code", ""),
            round(cur, 2) if cur is not None else None,
            round(prev, 2) if prev is not None else None,
            f.get("move_type", ""))


def build(raw_filings, cfg, *, editorial=None, summarize_method="template",
          api_key="", budget=None, summary_cache=None, error_log=None):
    editorial = editorial or C.load_editorial()
    error_log = error_log or []
    investors_by_id = {inv["id"]: inv for inv in cfg["investors"]}

    # Normalize + classify, dedupe by id.
    norm = {}
    for raw in raw_filings:
        if raw.get("investor_id") not in investors_by_id:
            error_log.append({"reason": "unknown_investor", "raw": raw.get("filer_raw_name", "")})
            continue
        try:
            f = normalize_filing(raw)
        except Exception as e:  # pragma: no cover
            error_log.append({"reason": "normalize_error", "err": str(e)})
            continue
        norm[f["id"]] = f

    # Collapse seed vs live duplicates by content key (prefer the live row,
    # i.e. the one with a real EDINET doc id + submission date).
    by_content = {}
    for f in norm.values():
        k = _content_key(f)
        cur = by_content.get(k)
        if cur is None:
            by_content[k] = f
        elif f.get("edinet_doc_id") and not cur.get("edinet_doc_id"):
            by_content[k] = f
    filings = sorted(by_content.values(), key=_sort_key, reverse=True)

    hidden = set(editorial.get("hidden_filing_ids", []))
    pinned = set(editorial.get("pinned_filing_ids", []))
    for f in filings:
        f["hidden"] = f["id"] in hidden
        f["pinned"] = f["id"] in pinned

    summaries = {}
    overrides = editorial.get("summary_overrides", {})
    import summarize as _S
    for f in filings:
        inv = investors_by_id[f["investor_id"]]
        s = make_summary(f, inv, method=summarize_method, api_key=api_key,
                         budget=budget, cache=summary_cache)
        if f["id"] in overrides:
            s = {**s, **overrides[f["id"]], "method": "editorial_override"}
        s = {**s, "generated_at": C.now_jst_iso(),
             "claude_model": _S.CLAUDE_MODEL if s.get("method") == "llm" else None}
        summaries[f["id"]] = s

    def visible(f):
        return (not f["audit_only"]) and (not f["hidden"])

    pub_investors = []
    for inv in cfg["investors"]:
        rows = [f for f in filings if f["investor_id"] == inv["id"] and visible(f)]
        rows.sort(key=_sort_key, reverse=True)
        stats = {
            "filing_count": len(rows),
            "qualifying_count": sum(1 for f in rows if f["qualifying"]),
            "new_count": sum(1 for f in rows if f["move_type"] == C.MOVE_NEW),
            "increase_count": sum(1 for f in rows if f["move_type"] == C.MOVE_INCREASE),
            "decrease_count": sum(1 for f in rows if f["move_type"] == C.MOVE_DECREASE),
            "last_filing_date": rows[0]["filing_date"] if rows else "",
            "latest_move_type": rows[0]["move_type"] if rows else "",
        }
        pub_investors.append({
            "id": inv["id"], "display_name": inv.get("display_name", ""),
            "display_name_ja": inv.get("display_name_ja", ""),
            "category": inv.get("category", ""), "country": inv.get("country", ""),
            "curated_rank": inv.get("curated_rank", 999),
            "active": bool(inv.get("active", True)),
            "homepage": bool(inv.get("homepage", False)),
            "website": inv.get("website"),
            "blurb_en": inv.get("blurb_en", ""), "blurb_ja": inv.get("blurb_ja", ""),
            "notes": inv.get("notes", ""), "stats": stats,
        })

    def feed_rows_for(iid):
        rows = [f for f in filings if f["investor_id"] == iid and visible(f)]
        rows.sort(key=lambda f: (f.get("pinned", False), f.get("filing_date", ""), f["id"]),
                  reverse=True)
        out = []
        for f in rows:
            s = summaries.get(f["id"], {})
            out.append({
                "id": f["id"], "filing_date": f["filing_date"],
                "filing_type": f["filing_type"], "move_type": f["move_type"],
                "qualifying": f["qualifying"], "issuer_name": f["issuer_name"],
                "issuer_name_en": f["issuer_name_en"], "issuer_code": f["issuer_code"],
                "previous_holding_ratio": f["previous_holding_ratio"],
                "current_holding_ratio": f["current_holding_ratio"],
                "change_percentage_points": f["change_percentage_points"],
                "edinet_doc_id": f["edinet_doc_id"], "source_url": f["source_url"],
                "japanese_title": f["japanese_title"], "confidence": f["confidence"],
                "caveats": f["caveats"], "pinned": f.get("pinned", False),
                "intent": s.get("intent"), "signal": s.get("signal"),
                "purpose_en": s.get("purpose_en"),
                "summary_en": s.get("en", {}), "summary_ja": s.get("ja", {}),
            })
        return out

    feed_investors = []
    for rec in pub_investors:
        rec2 = dict(rec)
        rec2["filings"] = feed_rows_for(rec["id"])
        feed_investors.append(rec2)

    mode = cfg.get("ranking_mode", "curated")
    if mode == "activity":
        feed_investors.sort(key=lambda r: (r["stats"]["qualifying_count"],
                                           r["stats"]["last_filing_date"]), reverse=True)
    else:
        feed_investors.sort(key=lambda r: r["curated_rank"])

    generated_at = C.now_jst_iso()
    total_visible = sum(len(r["filings"]) for r in feed_investors)
    meta = {
        "generated_at": generated_at, "as_of_date": C.today_jst(),
        "ranking_mode": mode, "homepage_size": cfg.get("homepage_size", 9),
        "summarize_method": summarize_method,
        "counts": {
            "investors_total": len(cfg["investors"]),
            "investors_homepage": sum(1 for i in cfg["investors"] if i.get("homepage")),
            "filings_total": len(filings), "filings_visible": total_visible,
            "filings_qualifying": sum(1 for f in filings if f["qualifying"] and visible(f)),
            "filings_audit_only": sum(1 for f in filings if f["audit_only"]),
        },
        "window_note": "Seed dataset" if all(f["seed"] for f in filings) and filings
                       else ("Live EDINET" if filings and not any(f["seed"] for f in filings)
                             else "Seed + live EDINET"),
        "error_log": error_log[-50:],
    }

    feed = {"meta": meta, "investors": feed_investors}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    C.write_json(DATA_DIR / "investors.json", pub_investors)
    C.write_json(DATA_DIR / "filings.json", filings)
    C.write_json(DATA_DIR / "summaries.json", summaries)
    C.write_json(DATA_DIR / "feed.json", feed)
    C.write_json(DATA_DIR / "_meta.json", meta)
    return meta
