"""
Active Investors in Japan — HIGH-SIGNAL summary layer.

The structured facts (filer, date, move type, prev/new ratio, change) are shown
as columns/badges in the UI, so the summary must NOT restate them. Instead it
surfaces the genuinely informative content of the filing:

  * intent   — from the stated 保有目的 (purpose of holding): activist /
               engagement / strategic / pure_investment.
  * note     — an event-driven 変更理由 (purpose changed, pledge agreement,
               tender offer, joint-holder change). Bare "+1% ratio change" /
               address-change reasons are dropped (the columns show them).
  * purpose_en (optional Claude tier) — a faithful one-line English rendering
               of the actual stated purpose, only for activist/engagement/
               strategic filings where the wording carries signal.

Output per filing:
  {"intent": "...", "signal": "high|low",
   "en": {"label": "...", "note": "..."}, "ja": {"label": "...", "note": "..."},
   "purpose_en": "..."|None, "purpose_ja": "...", "confidence": "...", "caveats": [...],
   "move_type": "...", "method": "template|llm"}

Low-signal rows (pure investment + a bare ratio change) get signal="low" and an
empty note — the UI renders just the intent chip and a "Download source" link.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import common as C


def _num(filing, *keys):
    for k in keys:
        if filing.get(k) is not None:
            return filing.get(k)
    return None


CLAUDE_MODEL = os.environ.get("ACTIVE_INVESTORS_CLAUDE_MODEL", "claude-haiku-4-5-20251001")
_HIGH_INTENTS = ("activist", "engagement", "strategic")


def template_summary(filing: dict, investor: dict) -> dict:
    """Deterministic high-signal summary (no Claude)."""
    purpose = filing.get("purpose_ja") or ""
    reason = filing.get("reason_ja") or filing.get("japanese_title") or ""
    intent = filing.get("intent") or C.intent_from(purpose, filing.get("purpose_category", ""))
    note_en, note_ja = C.reason_note(reason)
    lab = C.INTENT_LABEL.get(intent, C.INTENT_LABEL["unknown"])
    signal = "high" if (intent in _HIGH_INTENTS or note_en) else "low"
    return {
        "intent": intent,
        "signal": signal,
        "en": {"label": lab["en"], "note": note_en},
        "ja": {"label": lab["ja"], "note": note_ja},
        "purpose_en": None,
        "purpose_ja": purpose,
        "move_type": filing.get("move_type"),
        "confidence": filing.get("confidence", "high"),
        "caveats": list(filing.get("caveats") or []),
        "method": "template",
    }


SYSTEM_PROMPT = (
    "You translate the STATED PURPOSE OF HOLDING from a Japanese EDINET "
    "large-shareholding filing into ONE concise, high-signal English clause "
    "(max ~18 words). Convey what the holder says they intend (e.g. constructive "
    "dialogue, shareholder proposals, capital/business alliance, pure investment). "
    "Do NOT mention the holding percentage, the change, the date or the filer name "
    "— those are shown separately. Do not infer beyond the text. Return JSON only: "
    '{"purpose_en": "..."}'
)


def llm_purpose(filing: dict, *, api_key: str, budget=None) -> Optional[str]:
    """Claude one-line translation of the actual stated purpose (high-signal cases)."""
    try:
        import anthropic  # type: ignore
    except Exception:
        return None
    if not api_key or budget is not None and not budget.can_spend():
        return None
    purpose = filing.get("purpose_ja") or ""
    if not purpose:
        return None
    try:
        # Bound every call hard: a short per-request timeout and NO retries, so a
        # rate-limited / overloaded API (or a long Retry-After backoff) can never
        # stall the run. purpose_en is optional enrichment — on any failure we
        # simply fall back to the template summary for this filing.
        client = anthropic.Anthropic(api_key=api_key, timeout=20.0, max_retries=0)
        resp = client.messages.create(
            model=CLAUDE_MODEL, max_tokens=120, system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "保有目的: " + purpose}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        data = _extract_json(text)
        if budget is not None:
            budget.record(getattr(resp, "usage", None))
        return (data or {}).get("purpose_en") or None
    except Exception:
        return None


def _extract_json(text):
    text = (text or "").strip().strip("`")
    try:
        return json.loads(text[text.index("{"):text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return None


def make_summary(filing: dict, investor: dict, *, method="template",
                 api_key="", budget=None, cache=None) -> dict:
    """Cache-aware. Claude (when method='llm') only adds a purpose translation for
    activist/engagement/strategic filings — pure-investment rows stay key-free."""
    fid = filing.get("id")
    if cache is not None and fid in cache:
        return cache[fid]
    out = template_summary(filing, investor)
    if method == "llm" and out["intent"] in _HIGH_INTENTS:
        p = llm_purpose(filing, api_key=api_key, budget=budget)
        if p:
            out["purpose_en"] = p
            out["method"] = "llm"
    if cache is not None and fid:
        cache[fid] = out
    return out
