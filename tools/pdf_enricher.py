"""
JII Compounders - PDF enrichment pipeline.

Per-disclosure enrichment:
  - Cache lookup by doc_id (skip if cached)
  - Fetch PDF (max 2 pages, 5k chars)
  - Tier-B: regex extraction of structured key facts (free)
  - Tier-C: LLM (Claude Haiku 4.5) for richer outputs (tags, summaries, title-EN, brief translation)
  - Hardened by tools/llm_budget.BudgetLedger - never exceeds $9/month
  - Idempotent: same doc_id never re-summarised

Output fields written back onto each feed.json row:
  - tag_en, tag_jp                 : human-readable structured tag
  - summary_en, summary_jp         : 1-sentence summary in each language
  - doc_title_jp                   : original Japanese filed title (from scraper)
  - doc_title_en                   : translated English title
  - key_facts                      : dict of structured numeric facts (shares, yen, pct, etc.)
  - translation_en_brief           : 2-3 paragraph English brief (LLM-generated)
  - enriched_at                    : ISO timestamp of last enrichment
  - enrichment_method              : "tier_b_regex" | "tier_c_llm" | "tier_0_fallback"

Cache lives at tools/llm_summary_cache.json. Once a doc_id is in the cache,
it is never re-queried even if the row is re-classified.

Public API:
    enrich(row, llm_client=None, budget=None) -> row
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import requests

from jpx_master import lookup as _jpx_lookup

# PyMuPDF for PDF text extraction. If unavailable, all PDF fetches degrade to
# returning None and rows skip Tier-B regex. We surface this loudly in logs so
# a missing dependency isn't silently swallowed.
try:
    import fitz  # noqa: F401
    _PYMUPDF_AVAILABLE = True
except Exception as _e:
    _PYMUPDF_AVAILABLE = False
    import logging as _log
    _log.getLogger(__name__).error(
        "PyMuPDF (fitz) unavailable - PDF enrichment will be NO-OP. "
        "Install with: pip install pymupdf. Error: %s", _e
    )

LOG = logging.getLogger(__name__)
JST = _dt.timezone(_dt.timedelta(hours=9))

_TOOLS_DIR = Path(__file__).resolve().parent
_CACHE_PATH = _TOOLS_DIR / "llm_summary_cache.json"
_LEDGER_PATH = _TOOLS_DIR / "llm_ledger.json"
_TRANSLATIONS_DIR = _TOOLS_DIR.parent / "compounders" / "feed" / "data" / "translated"

# Per-row PDF fetch / extract limits
_PDF_FETCH_TIMEOUT = 20.0
_PDF_FETCH_MAX_BYTES = 4_000_000  # 4 MB hard cap to avoid huge integrated reports
_MAX_PAGES = 2
_MAX_CHARS = 5_000

# Anthropic Haiku 4.5 model
_LLM_MODEL = "claude-haiku-4-5-20251001"
_LLM_API_URL = "https://api.anthropic.com/v1/messages"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}
    with _CACHE_PATH.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            LOG.warning("llm_summary_cache.json corrupt - starting fresh")
            return {}


def _save_cache(data: dict) -> None:
    with _CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


# ---------------------------------------------------------------------------
# PDF fetch + extract
# ---------------------------------------------------------------------------

def _fetch_pdf_text(url: str) -> Optional[str]:
    """Fetch PDF, extract first _MAX_PAGES of text, truncate to _MAX_CHARS."""
    if not url or not url.startswith("http"):
        return None
    try:
        resp = requests.get(
            url, timeout=_PDF_FETCH_TIMEOUT, stream=True,
            headers={"User-Agent": "Mozilla/5.0 (JII-Feed/1.0)"},
        )
        resp.raise_for_status()
        # Read with size cap
        buf = bytearray()
        for chunk in resp.iter_content(chunk_size=64_000):
            buf.extend(chunk)
            if len(buf) > _PDF_FETCH_MAX_BYTES:
                LOG.warning("PDF %s exceeded %dB cap, truncating", url, _PDF_FETCH_MAX_BYTES)
                break
        # Parse - skip immediately if PyMuPDF didn't import
        if not _PYMUPDF_AVAILABLE:
            return None
        doc = fitz.open(stream=bytes(buf), filetype="pdf")
        text_parts = []
        for i in range(min(_MAX_PAGES, len(doc))):
            text_parts.append(doc[i].get_text())
        doc.close()
        text = "\n".join(text_parts)
        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS]
        return text
    except Exception as e:
        LOG.warning("PDF fetch/parse failed for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Tier-B: regex extraction (free, no LLM)
# ---------------------------------------------------------------------------

_NUM = r"[\d,]+"

def _to_int(s: str) -> Optional[int]:
    try:
        return int(s.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None

def tier_b_regex(text: str, class_code: str) -> dict:
    """Extract structured facts from PDF text via class-specific regex."""
    if not text:
        return {}
    out = {}

    if class_code == "BUYBACK":
        # Share count
        m = re.search(r"(?:取得する|取得した|取得対象)?株式の総数[\s\S]{0,30}?(" + _NUM + r")\s*株", text)
        if m:
            out["shares"] = _to_int(m.group(1))
        # Yen total
        m = re.search(r"(?:取得|取得した)?(?:株式の)?取得?価額(?:の総額)?[\s\S]{0,40}?(" + _NUM + r")\s*円", text)
        if m:
            out["yen"] = _to_int(m.group(1))
        # % of S/O
        m = re.search(r"発行済株式総数(?:[(（]自己株式を除く[)）])?に対する割合\s*([\d.]+)\s*[%％]", text)
        if m:
            try:
                out["pct_so"] = float(m.group(1))
            except ValueError:
                pass
        # Method
        if "ToSTNeT" in text:
            out["method"] = "ToSTNeT-3" if "ToSTNeT-3" in text or "ToSTNeT-３" in text else "ToSTNeT"
        elif "立会外" in text:
            out["method"] = "Off-market"
        elif "市場買付" in text:
            out["method"] = "Open-market"

    elif class_code == "CANCEL":
        m = re.search(r"消却する株式の総数[\s\S]{0,30}?(" + _NUM + r")\s*株", text)
        if m:
            out["shares"] = _to_int(m.group(1))
        m = re.search(r"発行済株式総数(?:[(（]自己株式を除く[)）])?に対する割合\s*([\d.]+)\s*[%％]", text)
        if m:
            try:
                out["pct_so"] = float(m.group(1))
            except ValueError:
                pass

    elif class_code == "DIV":
        # Often: 1株当たり配当金 X円 → Y円
        m = re.search(r"1株当たり配当金[\s\S]{0,80}?(" + _NUM + r")\s*円[\s\S]{0,20}?(" + _NUM + r")\s*円", text)
        if m:
            out["div_old"] = _to_int(m.group(1))
            out["div_new"] = _to_int(m.group(2))

    return out


def _format_tag_en(class_code: str, facts: dict) -> str:
    if class_code == "BUYBACK":
        parts = ["Buyback"]
        if facts.get("shares"):
            sh = facts["shares"]
            parts.append(f"{sh:,} shares" + (f" ({facts['pct_so']}% S/O)" if facts.get("pct_so") else ""))
        if facts.get("yen"):
            y = facts["yen"]
            parts.append(f"¥{y/1e6:.1f}M" if y < 1e9 else f"¥{y/1e9:.1f}bn")
        if facts.get("method"):
            parts.append(facts["method"])
        return " · ".join(parts) if len(parts) > 1 else "Buyback · details pending"
    if class_code == "CANCEL":
        parts = ["Cancellation"]
        if facts.get("shares"):
            sh = facts["shares"]
            parts.append(f"{sh:,} shares" + (f" ({facts['pct_so']}% S/O)" if facts.get("pct_so") else ""))
        return " · ".join(parts) if len(parts) > 1 else "Cancellation · details pending"
    if class_code == "DIV":
        if facts.get("div_old") and facts.get("div_new"):
            old, new = facts["div_old"], facts["div_new"]
            return f"Dividend · ¥{old} → ¥{new}" + (f" (+{round((new-old)/old*100)}%)" if old else "")
        return "Dividend · details pending"
    # COC, CROSS, MBO, COMP, GOV - rely on LLM
    label_map = {"COC":"Cost-of-capital","CROSS":"Cross-shareholding","MBO":"Take-private","COMP":"Comp KPI","GOV":"Governance"}
    return label_map.get(class_code, class_code)


def _format_tag_jp(class_code: str, facts: dict) -> str:
    if class_code == "BUYBACK":
        parts = ["自社株買い"]
        if facts.get("shares"):
            parts.append(f"{facts['shares']:,}株" + (f" (発行済{facts['pct_so']}%)" if facts.get("pct_so") else ""))
        if facts.get("yen"):
            y = facts["yen"]
            if y >= 1e8:
                parts.append(f"{y/1e8:.1f}億円")
            elif y >= 1e4:
                parts.append(f"{y/1e4:.0f}万円")
            else:
                parts.append(f"{y:,}円")
        if facts.get("method"):
            parts.append(facts["method"])
        return " ・ ".join(parts) if len(parts) > 1 else "自社株買い・詳細確認中"
    if class_code == "CANCEL":
        parts = ["自己株式消却"]
        if facts.get("shares"):
            parts.append(f"{facts['shares']:,}株" + (f" (発行済{facts['pct_so']}%)" if facts.get("pct_so") else ""))
        return " ・ ".join(parts) if len(parts) > 1 else "自己株式消却・詳細確認中"
    if class_code == "DIV":
        if facts.get("div_old") and facts.get("div_new"):
            return f"配当 ・ ¥{facts['div_old']} → ¥{facts['div_new']}"
        return "配当方針・詳細確認中"
    label_map = {"COC":"資本コスト経営","CROSS":"政策保有株式","MBO":"TOB / MBO","COMP":"役員報酬制度","GOV":"ガバナンスコード"}
    return label_map.get(class_code, class_code)


# ---------------------------------------------------------------------------
# Tier-C: LLM (Claude Haiku 4.5)
# ---------------------------------------------------------------------------

_LLM_SYSTEM = """You are extracting structured data from Japanese corporate disclosures
(EDINET 臨報 and TDnet press releases). Each disclosure is a capital-allocation
event already classified as one of: BUYBACK_INIT, BUYBACK_REV, BUYBACK_BLOCK,
BUYBACK_PROGRESS, BUYBACK_HOUSE, CANCEL, DIV_POLICY, DIV_HIKE, MBO, M_AND_A,
COC_INITIAL, COC_UPDATE, CROSS, COMP_KPI, GOV, GOV_FLIP.

Return STRICT JSON with the keys below. Output ONLY the JSON object - no
prose, no markdown fences.

{
  "tag_en": "concise structured English tag, e.g. 'Buyback - 15,700 shares (0.32% S/O) - Y14.3M - ToSTNeT-3'",
  "tag_jp": "Japanese equivalent",
  "summary_en": "see SUMMARY RULES below - max 280 characters",
  "summary_jp": "Japanese equivalent - max 140 characters, same structure",
  "doc_title_en": "Faithful English translation of the disclosure title",
  "key_facts": { "shares": int_or_null, "yen": int_or_null, "pct_so": float_or_null,
                 "price_ceiling_yen": int_or_null, "method": "string_or_empty",
                 "period_start": "YYYY-MM-DD_or_empty", "period_end": "YYYY-MM-DD_or_empty",
                 "reason_jp": "short JP excerpt or empty" },
  "translation_en_brief": "2-3 short paragraphs in plain English explaining the disclosure: what was filed, the specific terms, and any stated rationale. Max 1500 chars."
}

=== SUMMARY RULES (summary_en, summary_jp) ===

Clause 1 - NUMERIC FACTS ONLY. Lead with the primary numeric facts from the
filing. NO framing verbs, NO interpretation, NO "company X announced". Just
the numbers.

By class, the required primary facts are:
  BUYBACK_INIT / BUYBACK_REV  -> upper limit in yen, share count, % of shares
                                outstanding, price ceiling if disclosed,
                                execution window (start-end), method
                                (ToSTNeT-3 / open-market / self-tender)
  BUYBACK_BLOCK               -> block size yen, share count, % of S/O,
                                ToSTNeT-3 or 立会外 method, settlement date
  BUYBACK_PROGRESS            -> cumulative acquired (shares + yen), pct of
                                authorized limit consumed, period covered
  BUYBACK_HOUSE               -> trigger (J-ESOP / 定款変更 / 報酬制度),
                                shares affected, effective date
  CANCEL                      -> shares to be cancelled, % of S/O post-cancel,
                                effective date
  DIV_POLICY                  -> policy change: yen/share (old -> new),
                                payout ratio if disclosed, DOE if disclosed,
                                progressive / first / restored / special
  DIV_HIKE                    -> yen/share (old -> new), payout ratio if
                                disclosed, period covered
  MBO                         -> offeror name, tender price yen/share,
                                premium to undisturbed close (%), period,
                                minimum/maximum acceptance threshold, board
                                stance (recommend / oppose / neutral)
  M_AND_A                     -> target name and ticker, deal value, % stake,
                                premium if applicable, expected closing
  COC_INITIAL / COC_UPDATE    -> specific target metric and level
                                (e.g. "ROE 8.5%+ by FY3/28",
                                "operating margin 12%+"), horizon,
                                payout-ratio floor if any
  CROSS                       -> yen value of holdings to be unwound, % of
                                total cross-holdings, timeline
  COMP_KPI                    -> KPI added, % weight of LTI tied to it,
                                vesting horizon
  GOV / GOV_FLIP              -> specific principle / committee change,
                                effective date

Clause 2 - COMPARATIVE OR CONDITIONAL CONTEXT (optional, only if grounded in
the PDF text). Examples:
  - "Larger than the YX buyback completed in {date}"  (only if PDF references the prior program)
  - "First dividend reinstatement since {year}"
  - "Premium of {N}% over {date} close"
  - "Subject to TSE approval and FTC clearance"
  - "Excludes shares already held in treasury"
Do NOT invent comparisons. If no comparative is supported by the PDF text,
omit clause 2.

If a required fact is absent from the PDF, write "size not disclosed" (or
the appropriate "X not disclosed") in clause 1 rather than padding with
framing.

=== BANNED PHRASES ===
Do NOT use any of: "signals confidence", "signal management views shares as
undervalued", "direct return of capital", "returns capital to shareholders",
"lifts per-share economics", "reframes the return-of-capital baseline",
"removes the float", "frees balance-sheet capital", "underscores",
"reaffirms", "demonstrates commitment", "shareholder-friendly", "management
focus on capital-efficiency targets", or any other interpretive boilerplate.

=== CRITICAL distinction on tender offers ===
If the issuer is buying its OWN shares via tender (自己株式の公開買付け),
this is a BUYBACK method (self-tender). NEVER call it "take-private" or
"MBO". True take-privates / MBO involve a THIRD PARTY acquiring the company
with intent to delist (markers: 完全子会社化, 非公開化, スクイーズアウト,
external acquirer named).

=== STYLE ===
- Plain English. No proprietary terms ("JII", "watch universe", "compounder",
  "Principle-6").
- Use standard market terminology (S/O, ToSTNeT-3, MTP, ROE, payout ratio, DOE).
- Numbers always with units (yen, %, shares).
- Past tense for completed actions, "to" + infinitive for prospective.
- No em-dash decoration, no rhetorical questions."""


def tier_c_llm(text: str, class_code: str, ticker: str, name_en: str, name_jp: str,
               doc_title_jp: str, budget, llm_api_key: str) -> Optional[dict]:
    """Call Claude Haiku 4.5 to produce the rich output. Returns dict or None."""
    if not llm_api_key:
        return None
    user_msg = (
        f"Disclosure metadata:\n"
        f"- Ticker: {ticker}\n"
        f"- Company (EN): {name_en}\n"
        f"- Company (JP): {name_jp}\n"
        f"- Class: {class_code}\n"
        f"- Original title (JP): {doc_title_jp}\n\n"
        f"PDF text (first 2 pages, may be truncated):\n---\n{text}\n---"
    )
    payload = {
        "model": _LLM_MODEL,
        "max_tokens": 900,
        "system": _LLM_SYSTEM,
        "messages": [{"role": "user", "content": user_msg}],
    }
    # Pre-flight budget check
    from llm_budget import estimate_cost_usd
    in_tokens = (len(_LLM_SYSTEM) + len(user_msg)) // 4   # rough JP-friendly approximation
    est = estimate_cost_usd(in_tokens, 900)
    ok, reason = budget.can_call(est)
    if not ok:
        LOG.warning("LLM call skipped: %s", reason)
        return None
    headers = {
        "x-api-key": llm_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    backoff = 5.0
    for attempt in range(2):
        try:
            r = requests.post(_LLM_API_URL, json=payload, headers=headers, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                LOG.warning("LLM HTTP %d (attempt %d) - backing off %.0fs", r.status_code, attempt + 1, backoff)
                time.sleep(backoff)
                backoff *= 2
                continue
            r.raise_for_status()
            j = r.json()
            usage = j.get("usage", {}) or {}
            actual_cost = estimate_cost_usd(
                int(usage.get("input_tokens", in_tokens)),
                int(usage.get("output_tokens", 900)),
            )
            budget.record_call(actual_cost)
            content = j.get("content", [])
            if not content:
                return None
            raw = content[0].get("text", "").strip()
            # Strip accidental markdown fences
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except Exception as e:
            LOG.warning("LLM call failed (attempt %d): %s", attempt + 1, e)
            time.sleep(backoff)
            backoff *= 2
    return None


# ---------------------------------------------------------------------------
# Translation file output
# ---------------------------------------------------------------------------

def _write_translation_file(doc_id: str, payload: dict) -> None:
    if not payload.get("translation_en_brief"):
        return
    _TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "doc_id": doc_id,
        "title_en": payload.get("doc_title_en", ""),
        "summary_en": payload.get("summary_en", ""),
        "translation_en_brief": payload.get("translation_en_brief", ""),
        "generated_at": _dt.datetime.now(JST).isoformat(timespec="seconds"),
    }
    path = _TRANSLATIONS_DIR / f"{doc_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


# ---------------------------------------------------------------------------
# Main entry: enrich
# ---------------------------------------------------------------------------

def enrich(row: dict, llm_api_key: Optional[str] = None, budget=None) -> dict:
    """Enrich a feed.json row in place; return the same dict for chaining."""
    doc_id = row.get("id")
    if not doc_id:
        return row

    # Always refresh name_en / name_jp from JPX. This fixes legacy rows that
    # were classified before the JPX integration shipped (where name_en was
    # just a copy of the scraped Japanese name).
    ticker = (row.get("ticker") or "").strip()
    if ticker:
        jpx = _jpx_lookup(ticker) or {}
        if jpx.get("name_en"):
            row["name_en"] = jpx["name_en"]
        if jpx.get("name_jp"):
            row["name_jp"] = jpx["name_jp"]

    cache = _load_cache()
    cached = cache.get(doc_id)
    if cached:
        # Already enriched. Just merge.
        for k, v in cached.items():
            if k in ("translation_en_brief",):  # large fields go to per-doc file, not feed.json
                continue
            row[k] = v
        return row

    class_code = row.get("class", "")
    pdf_text = _fetch_pdf_text(row.get("doc_url", ""))
    facts = tier_b_regex(pdf_text or "", class_code)

    enriched: dict = {
        "key_facts": facts,
        "tag_en": _format_tag_en(class_code, facts),
        "tag_jp": _format_tag_jp(class_code, facts),
        "doc_title_jp": row.get("doc_title_jp", ""),
        "doc_title_en": "",
        "enrichment_method": "tier_b_regex",
        "enriched_at": _dt.datetime.now(JST).isoformat(timespec="seconds"),
    }

    # Tier-C only if (a) we have an LLM key, (b) budget allows, (c) row would benefit.
    tier_c_classes = {"COC", "CROSS", "MBO", "COMP", "GOV"}  # always benefit from prose
    incomplete_tier_b = class_code in {"BUYBACK", "CANCEL", "DIV"} and not facts
    needs_tier_c = class_code in tier_c_classes or incomplete_tier_b or pdf_text  # if we have text, summarize

    if needs_tier_c and llm_api_key and budget is not None and pdf_text:
        llm_out = tier_c_llm(
            text=pdf_text, class_code=class_code, ticker=row.get("ticker", ""),
            name_en=row.get("name_en", ""), name_jp=row.get("name_jp", ""),
            doc_title_jp=row.get("doc_title_jp", ""),
            budget=budget, llm_api_key=llm_api_key,
        )
        if llm_out:
            enriched.update({
                "tag_en": llm_out.get("tag_en") or enriched["tag_en"],
                "tag_jp": llm_out.get("tag_jp") or enriched["tag_jp"],
                "summary_en": llm_out.get("summary_en") or row.get("summary_en", ""),
                "summary_jp": llm_out.get("summary_jp") or row.get("summary_jp", ""),
                "doc_title_en": llm_out.get("doc_title_en", ""),
                "key_facts": {**facts, **(llm_out.get("key_facts") or {})},
                "enrichment_method": "tier_c_llm",
                "has_translation": bool(llm_out.get("translation_en_brief")),
            })
            _write_translation_file(doc_id, llm_out)

    # Update feed.json row
    for k, v in enriched.items():
        if v != "" and v is not None:
            row[k] = v

    # Persist cache (excluding large translation field)
    cache[doc_id] = {k: v for k, v in enriched.items() if k not in ("translation_en_brief",)}
    _save_cache(cache)
    return row
