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
    # COC, CROSS, MBO, M_AND_A, COMP, GOV - rely on LLM
    label_map = {"COC":"Cost-of-capital","CROSS":"Cross-shareholding","MBO":"Take-private",
                 "M_AND_A":"M&A / Acquisition","COMP":"Comp KPI","GOV":"Governance"}
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
    label_map = {"COC":"資本コスト経営","CROSS":"政策保有株式","MBO":"TOB / MBO",
                 "M_AND_A":"買収・子会社化","COMP":"役員報酬制度","GOV":"ガバナンスコード"}
    return label_map.get(class_code, class_code)


# ---------------------------------------------------------------------------
# Tier-C: LLM (Claude Haiku 4.5)
# ---------------------------------------------------------------------------

_LLM_SYSTEM = """日本企業のTDnet開示から、資本政策に関する情報を構造化して抽出する。対象の開示には、あらかじめ BUYBACK_INIT、BUYBACK_REV、BUYBACK_BLOCK、BUYBACK_PROGRESS、BUYBACK_HOUSE、CANCEL、DIV_POLICY、DIV_HIKE、MBO、M_AND_A、COC_INITIAL、COC_UPDATE、CROSS、COMP_KPI、GOV、GOV_FLIP のいずれかの区分が付与されている。出力は指定されたJSONオブジェクトだけとし、説明文やMarkdownは付けない。キーは tag_en、tag_jp、summary_en、summary_jp、doc_title_en、key_facts、translation_en_brief とする。tag_enは簡潔な英語タグ、tag_jpは日本語タグ、summary_enは280文字以内の英語要約、summary_jpは140文字以内の日本語要約、doc_title_enは開示タイトルの忠実な英訳とする。key_factsには shares、yen、pct_so、price_ceiling_yen、method、period_start、period_end、reason_jp を入れ、数値や日付が確認できない項目はnullまたは空文字列とする。translation_en_briefは、何が開示されたか、具体的な条件、会社が示した理由を平易な英語で2～3段落にまとめ、1500文字以内とする。 日本語のtag_jpとsummary_jpは、summary_enを英語の語順のまま訳して作らない。必ず日本語の開示原文から事実関係を取り出し、日本語として最初から書く。主語を置く必要がない場面では無理に置かず、数字、対象、行為、時期、理由の順序は、日本語で最も読みやすい形に組み直す。英語の名詞句を連結した表現、抽象名詞の重ね書き、直訳調の金融メモ表現、不自然なカタカナ語を避ける。一方、ROE、DOE、ToSTNeT-3、MTPなど、日本の資本市場で通常使われる用語はそのまま使ってよい。 pct_soおよびタグ・要約に記す発行済株式数に対する割合は、会社が本文に記載した比率をそのまま転記せず、取得・消却株式数を「自己株式を除く発行済株式総数」で割り、100を掛けて自ら計算し、小数第1位に丸める。開示には通常、「（参考）…発行済株式総数（自己株式を除く）」の記載があるので、その分母を使う。会社記載の比率と計算値が0.2ポイントを超えて異なる場合は計算値を採用し、translation_en_briefに差異を記す。自己株式控除後の分母が開示されていない場合は、会社記載の比率を流用せずpct_soをnullとする。 summary_enとsummary_jpの第1文は数値事実を中心に書く。『会社が発表した』『経営陣は自信を示した』などの前置きや解釈は入れない。必要な事実は区分ごとに次のとおり。BUYBACK_INIT／BUYBACK_REVは上限金額、株式数、発行済株式数に対する割合、開示があれば上限価格、取得期間、方法（ToSTNeT-3、市場買付け、自己株式の公開買付け）。BUYBACK_BLOCKは金額、株式数、発行済株式数に対する割合、ToSTNeT-3または立会外の方法、決済日。BUYBACK_PROGRESSは累計取得株式数と金額、取得枠の消化率、対象期間。BUYBACK_HOUSEはJ-ESOP、定款変更、報酬制度などの発生事由、対象株式数、効力発生日。CANCELは消却株式数、消却後の発行済株式数に対する割合、効力発生日。DIV_POLICYは1株当たり配当の変更前後、開示があれば配当性向とDOE、累進配当・初配・復配・特別配当などの内容。DIV_HIKEは1株当たり配当の変更前後、開示があれば配当性向、対象期間。MBOは公開買付者名、買付価格、影響を受けていない終値に対するプレミアム率、買付期間、応募株式の下限・上限、取締役会の賛否または中立姿勢。M_AND_Aは対象会社名とコード、取引金額、取得比率、該当する場合はプレミアム率、予定するクロージング時期。COC_INITIAL／COC_UPDATEはROEや営業利益率など具体的な目標指標と水準、達成時期、開示があれば配当性向の下限。CROSSは縮減する政策保有株式の金額、政策保有株式全体に占める割合、実施時期。COMP_KPIは追加したKPI、LTIに占める比重、権利確定までの期間。GOV／GOV_FLIPは変更する原則・委員会などの具体的内容と効力発生日。 第2文は、PDF本文に根拠がある比較情報または条件だけを必要に応じて補足する。たとえば、開示が過去の取得枠に触れている場合の規模比較、何年ぶりの復配か、特定日の終値に対するプレミアム率、東証承認や公取委の審査を条件とする旨、既保有自己株式を除く旨などである。PDFに根拠がない比較や意味づけは加えない。必須事実が開示されていない場合は、無理に文章を埋めず、『取得金額は非開示』『割合は非開示』など、何が開示されていないかを明記する。 『自信を示す』『株価が割安との見方を示す』『株主に資本を返す』『1株当たりの価値を高める』『株主還元の基準を塗り替える』『流通株式を減らす』『貸借対照表の資本を解放する』『強く示す』『改めて確認する』『コミットメントを示す』『株主に友好的』『資本効率目標を重視する』など、開示事実を評価する定型句は使わない。これらと同種の解釈的な決まり文句も避ける。 M&Aでは、誰が誰を買うのかを必ず先に確認する。上場会社が自己株式を公開買付けで取得する場合はBUYBACKであり、非公開化やMBOと表現しない。『完全子会社化』という語だけでは方向を判断しない。上場会社自身が親会社などに完全子会社化され、上場廃止となる場合はMBOとして扱う。上場会社が別の会社の株式を取得して完全子会社化する場合は、上場会社が買い手でありM_AND_Aとして扱う。付与された区分を優先し、MBOでは上場会社が買収対象、M_AND_Aでは上場会社が買い手であるという方向を取り違えない。 英文は平易にし、JII、watch universe、compounder、Principle-6など独自用語を入れない。数字には必ず単位を付ける。完了した行為は過去形、予定される行為は将来の予定であることが分かる形にする。英語では装飾的なダッシュや修辞疑問を使わない。日本語では、短いタグだからといって英語の要素を中黒やスラッシュで機械的に並べず、必要な助詞や句読点を使って一読で意味が取れる形にする。summary_jpは特に、英語要約と同じ節数・同じ語順にそろえる必要はない。事実と数値を変えず、日本語として自然な順序に組み替える。"""


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
        # Merge cached enrichment into row.
        for k, v in cached.items():
            if k in ("translation_en_brief",):  # large fields go to per-doc file, not feed.json
                continue
            row[k] = v
        # If cached as Tier-C (has LLM summary), we're done.
        # If cached as Tier-B-only AND we now have LLM capacity, fall through to
        # attempt the Tier-C upgrade (re-fetches the PDF once per upgrade; the cache
        # entry will then be replaced with the Tier-C version).
        is_tier_b_only = cached.get("enrichment_method") == "tier_b_regex"
        have_llm_capacity = bool(llm_api_key) and budget is not None
        if not (is_tier_b_only and have_llm_capacity):
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
    tier_c_classes = {"COC", "CROSS", "MBO", "M_AND_A", "COMP", "GOV"}  # always benefit from prose
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
