"""
Active Investors in Japan — shared pipeline logic.

This module is the single source of truth for:
  * loading the investor config (the normalization layer),
  * attributing a raw filing to a normalized investor,
  * classifying a filing's move type (new 5% / increase / decrease / other),
  * computing derived fields (previous ratio, pp change, qualifying/audit flags),
  * stable filing IDs,
  * atomic JSON writes (sort_keys, ensure_ascii=False, trailing newline).

It is imported by build_data.py (seed + live), edinet_client.py and refresh.py
so the seed feed and the live feed are produced by identical rules.

Percentages are stored as percent (8.22 == 8.22%). Change is in percentage
POINTS (pp). EDINET-DB / EDINET XBRL express ratios as fractions (0.0822);
callers convert to percent before handing rows here.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path(__file__).resolve().parent / "config"
INVESTORS_CONFIG = CONFIG_DIR / "investors.json"
EDITORIAL_CONFIG = CONFIG_DIR / "editorial.json"

# Qualifying thresholds (kept in sync with config.qualifying_rules).
MIN_ABS_PP_FOR_CHANGE = 1.0
LARGE_HOLDING_THRESHOLD = 5.0  # the 5% reporting threshold

MOVE_NEW = "new_5pct"
MOVE_INCREASE = "increase"
MOVE_DECREASE = "decrease"
MOVE_OTHER = "other"


# ---------------------------------------------------------------------------
# JSON IO (atomic; same convention as the Capital-Allocation feed)
# ---------------------------------------------------------------------------

def read_json(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        with p.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(path, data) -> None:
    """Atomic write: serialize to a tempfile, fsync, os.replace."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
    if not text.endswith("\n"):
        text += "\n"
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    os.replace(tmp, p)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(path=INVESTORS_CONFIG) -> dict:
    cfg = read_json(path)
    if not isinstance(cfg, dict) or "investors" not in cfg:
        raise SystemExit(f"investors config missing or malformed: {path}")
    return cfg


def load_editorial(path=EDITORIAL_CONFIG) -> dict:
    """Editorial overrides: hide filings, override summaries, pin filings.
    Optional — returns empty structure when the file is absent."""
    ed = read_json(path) or {}
    ed.setdefault("hidden_filing_ids", [])
    ed.setdefault("pinned_filing_ids", [])
    ed.setdefault("summary_overrides", {})  # filing_id -> {en:{...}, ja:{...}}
    ed.setdefault("hidden_investor_ids", [])
    return ed


# ---------------------------------------------------------------------------
# Investor identity normalization
# ---------------------------------------------------------------------------

def _norm_name(s: str) -> str:
    """Fold a filer name for fuzzy matching: NFKC (full-width -> half-width),
    lowercase, drop corporate suffixes, punctuation and spaces."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    # Strip common legal-entity tails (EN + JA) so 'Dalton Investments LLC' and
    # 'ダルトン・インベストメンツ・エルエルシー' both reduce toward 'daltoninvestments'.
    tails = [
        "co.,ltd.", "co.,ltd", "co.ltd", "company", "limited", "ltd.", "ltd",
        "llc", "l.l.c.", "inc.", "inc", "plc", "lp", "l.p.", "pte", "k.k.",
        "株式会社", "有限会社", "合同会社",
        "エルエルシー", "リミテッド", "カンパニー", "インク", "ピーティーイー",
        "ピーエルシー", "エルティーディー", "エルピー",
    ]
    for t in tails:
        s = s.replace(t, "")
    s = re.sub(r"[\s　・,，.。()（）「」『』&＆/-]", "", s)
    return s


def build_alias_index(cfg: dict) -> dict:
    """Return {normalized_alias_or_code: investor_id} for attribution.
    Indexes every alias name, every EDINET code, and the parent_group_id."""
    idx: dict[str, str] = {}
    for inv in cfg["investors"]:
        iid = inv["id"]
        keys = [inv.get("display_name", ""), inv.get("display_name_ja", ""),
                inv.get("parent_group_id", "")]
        for al in inv.get("aliases", []):
            if isinstance(al, dict):
                if al.get("name"):
                    keys.append(al["name"])
                if al.get("edinet_code"):
                    idx[al["edinet_code"].strip().upper()] = iid
            elif isinstance(al, str):
                keys.append(al)
        for k in keys:
            nk = _norm_name(k)
            if nk:
                idx.setdefault(nk, iid)
        # parent_group_id verbatim (EDINET-DB groups, e.g. 'dalton')
        if inv.get("parent_group_id"):
            idx.setdefault(inv["parent_group_id"].strip().lower(), iid)
    return idx


def attribute_investor(alias_index: dict, *, filer_name: str = "",
                       edinet_code: str = "", parent_group_id: str = "") -> Optional[str]:
    """Map a raw filing to an investor_id. Tries, in order: EDINET code (exact),
    parent_group_id (exact), then normalized filer-name (exact, then substring).
    Returns None when no confident match — caller routes to the debug set."""
    if edinet_code:
        hit = alias_index.get(edinet_code.strip().upper())
        if hit:
            return hit
    if parent_group_id:
        hit = alias_index.get(parent_group_id.strip().lower())
        if hit:
            return hit
    nk = _norm_name(filer_name)
    if not nk:
        return None
    if nk in alias_index:
        return alias_index[nk]
    # Substring both ways (handles 'Baillie Gifford Overseas' vs 'Baillie Gifford').
    for alias, iid in alias_index.items():
        if len(alias) >= 6 and (alias in nk or nk in alias):
            return iid
    return None


# ---------------------------------------------------------------------------
# Move classification (the core rule, shared seed + live)
# ---------------------------------------------------------------------------

def classify_move(*, is_change_report: bool, current_pct: Optional[float],
                  change_pp: Optional[float],
                  previous_pct: Optional[float] = None) -> dict:
    """Classify one filing. Returns
        {move_type, qualifying, audit_only, previous_pct, change_pp, confidence_floor}

    Rules:
      * initial report (大量保有報告書) with holding >= 5%  -> new_5pct (qualifying)
      * change report (変更報告書):
          - holding now 0, or crossed below 5% from >=5%   -> decrease (cessation, qualifying)
          - change >= +1.0pp                               -> increase (qualifying)
          - change <= -1.0pp                               -> decrease (qualifying)
          - change known but |change| < 1.0pp, not cessation -> other, audit_only (noise)
          - change unknown (None) on a material holding    -> other, visible (recent filing)
      * anything we cannot stand behind                    -> other, low confidence
    """
    cur = current_pct
    chg = change_pp
    if chg is None and previous_pct is not None and cur is not None:
        chg = round(cur - previous_pct, 2)
    if previous_pct is None and chg is not None and cur is not None:
        previous_pct = round(cur - chg, 2)

    confidence_floor = "high"

    # Initial large-shareholding report.
    if not is_change_report:
        if cur is not None and cur >= LARGE_HOLDING_THRESHOLD:
            return _mv(MOVE_NEW, True, False, previous_pct, chg, "high")
        # Initial report below 5% (rare special-reporting cases) — keep, low signal.
        return _mv(MOVE_OTHER, False, False, previous_pct, chg, "medium")

    # Change report.
    crossed_below = (cur is not None and cur < LARGE_HOLDING_THRESHOLD and
                     (previous_pct is None or previous_pct >= LARGE_HOLDING_THRESHOLD))
    if cur is not None and cur == 0:
        return _mv(MOVE_DECREASE, True, False, previous_pct, chg, "high")
    if crossed_below:
        return _mv(MOVE_DECREASE, True, False, previous_pct, chg, "high")
    if chg is not None:
        if chg >= MIN_ABS_PP_FOR_CHANGE:
            return _mv(MOVE_INCREASE, True, False, previous_pct, chg, "high")
        if chg <= -MIN_ABS_PP_FOR_CHANGE:
            return _mv(MOVE_DECREASE, True, False, previous_pct, chg, "high")
        # Known but sub-1pp amendment -> audit-only noise.
        return _mv(MOVE_OTHER, False, True, previous_pct, chg, "high")
    # Change report with no isolated delta but a material holding -> show as a
    # recent filing (e.g. group-level reports, address/collateral amendments on
    # large positions). Confidence floored to medium since the delta is unknown.
    return _mv(MOVE_OTHER, False, False, previous_pct, chg, "medium")


def _mv(move_type, qualifying, audit_only, previous_pct, change_pp, conf):
    return {
        "move_type": move_type,
        "qualifying": qualifying,
        "audit_only": audit_only,
        "previous_pct": previous_pct,
        "change_pp": change_pp,
        "confidence_floor": conf,
    }


# ---------------------------------------------------------------------------
# IDs / dates
# ---------------------------------------------------------------------------

def filing_id(*, investor_id: str, issuer_code: str, date: str,
              current_pct, edinet_doc_id: str = "") -> str:
    """Stable, dedupe-friendly id. Prefers the EDINET doc id when present."""
    if edinet_doc_id:
        return f"edinet-{edinet_doc_id}"
    raw = f"{investor_id}|{issuer_code}|{date}|{current_pct}"
    h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"seed-{h}"


def today_jst() -> str:
    jst = _dt.timezone(_dt.timedelta(hours=9))
    return _dt.datetime.now(jst).strftime("%Y-%m-%d")


def now_jst_iso() -> str:
    jst = _dt.timezone(_dt.timedelta(hours=9))
    return _dt.datetime.now(jst).strftime("%Y-%m-%dT%H:%M:%S+09:00")


def pct(x, nd=2):
    """Format a percent value without trailing-zero noise: 5.0 -> '5', 8.22 -> '8.22'."""
    if x is None:
        return ""
    s = f"{round(float(x), nd):.{nd}f}".rstrip("0").rstrip(".")
    return s


# ---------------------------------------------------------------------------
# High-signal intent + reason interpretation (from 保有目的 / 変更理由)
# ---------------------------------------------------------------------------
# The numbers (filer, date, ratios, change) are shown structurally in the UI.
# The genuinely high-signal field is the STATED PURPOSE OF HOLDING (保有目的):
# does the holder declare activist intent, a strategic alliance, or just pure
# (passive) investment? plus event-driven REASONS (purpose changed, collateral
# agreement, tender offer). These functions turn that free text into a compact
# intent tag + an optional event note — never a restatement of the numbers.

_ACTIVIST_KW = ("重要提案", "提案行為", "株主提案", "委任状", "支配権", "役員の選任",
                "役員の解任", "事業活動を支配", "経営に参加", "経営への関与")
_ENGAGE_KW = ("建設的対話", "対話", "助言", "エンゲージ", "株主価値", "提言")
_STRATEGIC_KW = ("資本業務提携", "業務提携", "資本提携", "政策保有", "協業",
                 "シナジー", "事業上の関係", "取引関係")


def classify_intent(purpose_ja: str) -> str:
    """Map the stated 保有目的 to an intent tag.
    activist > strategic > engagement > pure_investment > unknown."""
    p = purpose_ja or ""
    if not p:
        return "unknown"
    if any(k in p for k in _ACTIVIST_KW):
        return "activist"
    if any(k in p for k in _STRATEGIC_KW):
        return "strategic"
    if any(k in p for k in _ENGAGE_KW):
        return "engagement"
    if "純投資" in p:
        return "pure_investment"
    return "engagement"   # some stated, non-passive purpose


INTENT_LABEL = {
    "activist":       {"en": "Activist intent", "ja": "重要提案"},
    "engagement":     {"en": "Engagement",      "ja": "対話"},
    "strategic":      {"en": "Strategic / alliance", "ja": "資本提携"},
    "pure_investment": {"en": "Pure investment", "ja": "純投資"},
    "unknown":        {"en": "", "ja": ""},
}


def reason_note(reason_ja: str):
    """Return (en, ja) for an event-driven reason, or ('','') for a bare
    ratio-change / address change (which the columns already show)."""
    r = reason_ja or ""
    ru = r.upper()
    if "保有目的の変更" in r or "保有目的が変更" in r:
        return ("Stated purpose changed", "保有目的の変更")
    if "公開買付" in r or "ＴＯＢ" in ru or "TOB" in ru:
        return ("Linked to a tender offer", "公開買付けに関連")
    if "支配権" in r:
        return ("Relates to control of the issuer", "支配権に関連")
    if "担保" in r:
        return ("Pledge / collateral agreement amended", "担保契約の変更")
    if "貸株" in r or "借株" in r:
        return ("Stock-lending arrangement", "貸借に関する変更")
    if "共同保有者" in r and ("増加" in r or "減少" in r):
        return ("Change in joint holders", "共同保有者の変動")
    return ("", "")


_CATEGORY_INTENT = {"activist": "activist", "activist_implied": "activist",
                    "strategic": "strategic", "institutional": "pure_investment",
                    "pure_investment": "pure_investment", "dealer": "pure_investment"}


def intent_from(purpose_ja: str, purpose_category: str = "") -> str:
    """Intent from the stated purpose text; fall back to an EDINET-DB
    purpose_category (seed rows) when the free text is absent."""
    it = classify_intent(purpose_ja)
    if it == "unknown" and purpose_category:
        return _CATEGORY_INTENT.get(purpose_category, "unknown")
    return it
