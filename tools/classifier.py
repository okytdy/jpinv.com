"""
JII Compounders - Capital-Allocation Inflection Feed - Classifier sub-agent.

Single self-contained module implementing the 8-class taxonomy defined in:
    3 Pipeline/5 Assets/Website/jpinv.com/compounders/feed/_SPEC.md
    (Section 2 = taxonomy; Section 4 = output row shape).

Public API:
    classify(disclosure: dict) -> dict | None

Returns a feed.json row dict for Principle-6 inflections, else None.
Standard library only. No network calls.

Run as a script (`python tools/classifier.py`) to execute the inline test bank.
"""
from __future__ import annotations

import csv
import re
from datetime import datetime, timezone, timedelta

from jpx_master import lookup as _jpx_lookup
from pathlib import Path
from typing import Callable, Optional, Tuple

JST = timezone(timedelta(hours=9))

# Fallback universe (active compounders, visible on /en/compounders/).
# Used only if the watchlist CSV is missing or unparseable.
_FALLBACK_UNIVERSE: frozenset[str] = frozenset({
    "4578", "4568", "7733", "4716", "8136", "3092", "6869", "4732", "6532",
    "8111", "4194", "6055", "9759", "9746", "4722", "7148", "4776", "9757",
    "4071", "4432", "2353", "7085", "8771", "6196", "7818", "3854", "4481",
    "6200", "299A", "6088", "3836", "9467", "4475", "4377", "3983", "3922",
    "296A", "3798", "3984", "3989", "6539", "2301", "4393", "4058", "421A",
    "3649", "3835", "6037", "7373", "4493", "431A", "9272", "4482", "5621",
    "2477", "6176", "7775", "3963", "4811", "9554", "3804", "9560", "5570",
    "5843", "9271", "324A", "4428", "6090", "340A", "137A", "Cocolive",
})

_WATCHLIST_CSV = Path(
    r"C:\Users\okuya\OneDrive\Desktop\JII\3 Pipeline\watchlist_v4_compounders.csv"
)


# ---------------------------------------------------------------------------
# Exclusion patterns (spec Section 2) - applied BEFORE any class match
# ---------------------------------------------------------------------------

_EXCLUDE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"決算短信"),
    re.compile(r"月次(売上|販売|受注|営業)"),
    re.compile(r"IR説明会"),
    re.compile(r"株式分割"),
    re.compile(r"新株予約権"),
    re.compile(r"翻訳"),
    re.compile(r"自己株式.*ストックオプション"),
    re.compile(r"自己株式.*新株予約権"),
)


# ---------------------------------------------------------------------------
# Universe loader
# ---------------------------------------------------------------------------


def _load_universe() -> frozenset[str]:
    if not _WATCHLIST_CSV.exists():
        return _FALLBACK_UNIVERSE
    try:
        tickers: set[str] = set()
        with _WATCHLIST_CSV.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None or "sec_code" not in reader.fieldnames:
                return _FALLBACK_UNIVERSE
            for row in reader:
                raw = (row.get("sec_code") or "").strip()
                if not raw:
                    continue
                # JPX 5-digit form: 45780 -> 4578. Alphanumeric 5-char (e.g.
                # 299A0) -> 299A. If already 4-char, keep as-is.
                if len(raw) == 5 and raw[-1] == "0" and raw[:4].isalnum():
                    tickers.add(raw[:4])
                elif len(raw) == 4:
                    tickers.add(raw)
                else:
                    tickers.add(raw)
        return frozenset(tickers) if tickers else _FALLBACK_UNIVERSE
    except (OSError, csv.Error, UnicodeDecodeError):
        return _FALLBACK_UNIVERSE


_UNIVERSE: frozenset[str] = _load_universe()


def _in_universe(ticker: str) -> bool:
    return ticker in _UNIVERSE


# ---------------------------------------------------------------------------
# Quantitative-gate helpers
# ---------------------------------------------------------------------------

_NUM = r"[0-9０-９,，\.]+"


def _to_float(s: str) -> Optional[float]:
    if not s:
        return None
    trans = str.maketrans("０１２３４５６７８９，",
                          "0123456789,")
    cleaned = s.translate(trans).replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


_YEN_UNIT_MULTIPLIERS: dict[str, float] = {
    "兆": 1_000_000_000_000.0,
    "千億": 100_000_000_000.0,
    "百億": 10_000_000_000.0,
    "十億": 1_000_000_000.0,
    "億": 100_000_000.0,
    "千万": 10_000_000.0,
    "百万": 1_000_000.0,
    "万": 10_000.0,
}


def _parse_yen(text: str) -> Optional[int]:
    if not text:
        return None
    best: Optional[int] = None
    pat = re.compile(
        rf"({_NUM})\s*(兆|千億|百億|十億|億|千万|百万|万)?\s*円"
    )
    for m in pat.finditer(text):
        val = _to_float(m.group(1))
        if val is None:
            continue
        unit = m.group(2) or ""
        amt = int(val * _YEN_UNIT_MULTIPLIERS.get(unit, 1.0))
        if best is None or amt > best:
            best = amt
    return best


def _parse_percent(text: str) -> Optional[float]:
    if not text:
        return None
    near = re.search(
        rf"(?:発行済[株式数]*[^0-9０-９%％]{{0,40}}"
        rf"(?:割合)?[^0-9０-９%％]{{0,20}})"
        rf"({_NUM})\s*[%％]",
        text,
    )
    if near:
        v = _to_float(near.group(1))
        if v is not None:
            return v
    m = re.search(rf"({_NUM})\s*[%％]", text)
    if m:
        return _to_float(m.group(1))
    return None


def _parse_shares(text: str) -> Optional[int]:
    if not text:
        return None
    pat = re.compile(rf"({_NUM})\s*(百万|万)?\s*株")
    m = pat.search(text)
    if not m:
        return None
    val = _to_float(m.group(1))
    if val is None:
        return None
    unit = m.group(2) or ""
    mult = {"百万": 1_000_000.0, "万": 10_000.0}.get(unit, 1.0)
    return int(val * mult)


def _fmt_yen(amount: int) -> str:
    if amount >= 1_000_000_000_000:
        return f"¥{amount / 1_000_000_000_000:.1f}tn"
    if amount >= 100_000_000:
        return f"¥{amount / 100_000_000:.1f}bn"
    if amount >= 1_000_000:
        return f"¥{amount / 1_000_000:.0f}m"
    return f"¥{amount:,}"


def _fmt_yen_jp(amount: int) -> str:
    if amount >= 1_000_000_000_000:
        return f"{amount / 1_000_000_000_000:.1f}兆円"
    if amount >= 100_000_000:
        return f"{amount / 100_000_000:.0f}億円"
    if amount >= 10_000:
        return f"{amount / 10_000:.0f}万円"
    return f"{amount:,}円"


# ---------------------------------------------------------------------------
# Exclusion logic
# ---------------------------------------------------------------------------


def _is_excluded(title: str, body: Optional[str]) -> bool:
    if not title:
        return True
    for pat in _EXCLUDE_PATTERNS:
        if pat.search(title):
            return True
    # ストックオプション grants excluded
    # unless paired with comp-revision context.
    if "ストックオプション" in title:
        if not re.search(
            r"役員報酬制度|報酬制度の改定|報酬体系",
            title + (body or ""),
        ):
            return True
    return False


# ---------------------------------------------------------------------------
# Per-class matchers

def _enrich_names_from_jpx(disclosure: dict) -> tuple[str, str]:
    """Return (name_en, name_jp) preferring JPX official names over scraped names."""
    ticker = disclosure.get("ticker") or ""
    jpx = _jpx_lookup(ticker) or {}
    raw_jp = disclosure.get("name_jp", "")
    raw_en = disclosure.get("name_en", "") or raw_jp
    name_jp = jpx.get("name_jp") or raw_jp
    name_en = jpx.get("name_en") or raw_en
    return name_en, name_jp

# Each returns (matched, tag, summary_en, summary_jp, class_override, facts).
# class_override: "" means "use the _MATCHERS-table default class code for this
# matcher". A non-empty string lets a matcher emit a subtype class
# (e.g. _match_buyback emits BUYBACK_INIT / BUYBACK_REV / ... ;
# _match_div emits DIV_POLICY / DIV_HIKE; _match_mbo emits M_AND_A
# when the outbound-TOB guard fires).
# facts: dict of structured numbers the matcher already extracted from the
# disclosure (pct_so, yen, shares). Surfaced to classify() so signal_score
# can be derived without re-parsing.
# ---------------------------------------------------------------------------

MatchResult = Tuple[bool, str, str, str, str, dict]
_EMPTY: MatchResult = (False, "", "", "", "", {})


# --- MBO --------------------------------------------------------------------

_MBO_RE = re.compile(
    r"(公開買付|MBO|ＭＢＯ|"
    r"完全子会社化|TOB|ＴＯＢ|"
    r"株式等売渡請求|"
    r"非公開化|スクイーズ.?アウト)"
)


def _match_mbo(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    # GUARD: An issuer's tender offer for its OWN treasury shares
    # (自己株式の公開買付け) is a BUYBACK method, not a take-private.
    # Pattern: treasury marker appears BEFORE tender marker, tight co-location.
    # This catches "自己株式の公開買付け" (real bug) but spares
    # "公開買付けの開始及び自己株式の取得" (real MBO with treasury sub-step).
    if re.search(
        r"(?:自己株式|自社株式|自己株)[^。\n]{0,8}(?:公開買付|公開買い付け|TOB|ＴＯＢ)",
        title,
    ):
        return _EMPTY
    if not _MBO_RE.search(title):
        return _EMPTY
    if "MBO" in title or "ＭＢＯ" in title:
        kind_en, kind_jp = "MBO", "MBO"
    elif "完全子会社化" in title:
        kind_en, kind_jp = "Going-private (parent)", "完全子会社化"
    elif "公開買付" in title or "TOB" in title or "ＴＯＢ" in title:
        kind_en, kind_jp = "Tender offer", "公開買付"
    else:
        kind_en, kind_jp = "Going-private", "非公開化"

    body = d.get("body_jp") or ""
    aggregate_yen: Optional[int] = None
    agg_match = re.search(
        rf"(?:買付(?:け)?(?:代金|総額|価額の総額)|"
        rf"取得価額の総額)"
        rf"[^0-9０-９]{{0,10}}({_NUM})\s*"
        rf"(兆|千億|百億|十億|億|千万|百万|万)?\s*円",
        title + "\n" + body,
    )
    if agg_match:
        val = _to_float(agg_match.group(1))
        if val is not None:
            unit = agg_match.group(2) or ""
            aggregate_yen = int(val * _YEN_UNIT_MULTIPLIERS.get(unit, 1.0))
    tag_suffix = f" · {_fmt_yen(aggregate_yen)}" if aggregate_yen else ""
    tag = f"{kind_en}{tag_suffix}"[:60]

    # OUTBOUND-TOB GUARD: if the title carries a target ticker in parens that
    # differs from the filer's ticker, this is an outbound acquisition tender
    # offer — not a take-private of the filer. Reclassify as M_AND_A.
    # Examples: TDK (6762) tendering for InvenSense; infoNet (4444) acquiring
    # a target. Without this guard ~10% of MBO rows are mislabeled.
    # Match patterns: "(1234)", "（1234）", "(証券コード 1234)", "（コード番号: 1234）".
    filer_ticker = str(d.get("ticker", "") or "").strip()
    target_match = re.search(
        r"[(（]\s*(?:証券コード|コード番号|コード)?\s*[::]?\s*(\d{4})\s*[)）]",
        title,
    )
    class_override = ""
    if target_match:
        target_ticker = target_match.group(1)
        if filer_ticker and target_ticker != filer_ticker:
            class_override = "M_AND_A"
            tag = f"M&A · {kind_en}{tag_suffix}"[:60]
    else:
        # No parseable target ticker — keep existing MBO classification but
        # log a warning so the audit pass can review.
        if filer_ticker:
            print(
                "[classifier:warn] MBO with no parseable target ticker - "
                f"filer={filer_ticker} title={title[:80]!r}"
            )

    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    facts: dict = {}
    if aggregate_yen is not None:
        facts["yen"] = aggregate_yen
    return True, tag, summary_en, summary_jp, class_override, facts


# --- BUYBACK ----------------------------------------------------------------

_BUYBACK_RE = re.compile(
    # Treasury-stock markers — formal forms AND the 自社 variant.
    # Also catches the short-form 自己株 when paired with TOB/公開買付 (issuer self-tender).
    r"(?:"
    r"自己(?:株式|株券)[^。\n]{0,12}(?:取得|買付|買い付け)"
    r"|"
    r"自社株式[^。\n]{0,12}(?:取得|買付|買い付け)"
    r"|"
    r"自己株(?!式|券)[^。\n]{0,8}(?:TOB|ＴＯＢ|公開買付|公開買い付け)"
    r")"
)


def _match_buyback(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    if not _BUYBACK_RE.search(title):
        return _EMPTY
    # Distinguish from cancellation: 消却 belongs to CANCEL.
    if "消却" in title and not re.search(r"取得|買付", title):
        return _EMPTY

    body = d.get("body_jp") or ""
    combined = title + "\n" + body

    pct = _parse_percent(combined)
    yen = _parse_yen(combined)
    shares = _parse_shares(combined)
    so = d.get("shares_outstanding")
    mc = d.get("market_cap_jpy")

    # Gate: >=1% of S/O OR >=Y1bn for sub-Y100bn mkt cap. If neither
    # parseable, include with tag suffix "size TBC".
    passes_gate = False
    if pct is not None and pct >= 1.0:
        passes_gate = True
    elif yen is not None and yen >= 1_000_000_000:
        if mc is None or mc < 100_000_000_000:
            passes_gate = True
        else:
            if shares and so and (shares / so) >= 0.01:
                passes_gate = True
            else:
                passes_gate = True  # still material in absolute terms
    elif pct is None and yen is None and shares is None:
        passes_gate = True  # no info -> accept with TBC tag

    if not passes_gate:
        return _EMPTY

    parts_en: list[str] = []
    parts_jp: list[str] = []
    if pct is not None:
        parts_en.append(f"{pct:.1f}% of S/O")
        parts_jp.append(f"発行済{pct:.1f}%")
    elif shares is not None and so:
        ratio = shares / so * 100
        parts_en.append(f"{ratio:.1f}% of S/O")
        parts_jp.append(f"発行済{ratio:.1f}%")
    if yen is not None:
        parts_en.append(_fmt_yen(yen))
        parts_jp.append(_fmt_yen_jp(yen))
    if shares is not None and not parts_en:
        parts_en.append(f"{shares:,} shares")
        parts_jp.append(f"{shares:,}株")

    # ---- Subtype routing (most-specific to least): HOUSE -> PROGRESS ->
    # BLOCK -> REV -> INIT. Each sets (subtype_code, subtype_label).
    has_treasury = re.search(r"自己株式|自社株式|自己株", title) is not None
    is_house = (
        bool(re.search(r"J-ESOP|定款変更|報酬制度.{0,5}改定", title))
        and has_treasury
    )
    is_progress = bool(
        re.search(r"取得状況|取得結果|取得終了|取得完了", title)
    )
    is_block = bool(
        re.search(r"ToSTNeT|トストネット|立会外", title + "\n" + body)
    )
    is_rev = bool(
        re.search(r"増額|上方修正|上限引上|拡大", title)
        and re.search(r"取得", title)
    )

    if is_house:
        subtype_code = "BUYBACK_HOUSE"
        subtype_label = "housekeeping"
    elif is_progress:
        subtype_code = "BUYBACK_PROGRESS"
        subtype_label = "progress"
    elif is_block:
        subtype_code = "BUYBACK_BLOCK"
        subtype_label = "block"
    elif is_rev:
        subtype_code = "BUYBACK_REV"
        subtype_label = "revision"
    else:
        subtype_code = "BUYBACK_INIT"
        subtype_label = "authorization"

    tag_body = " · ".join(parts_en) if parts_en else "size TBC"
    tag = f"Buyback ({subtype_label}) · {tag_body}"[:60]

    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    facts: dict = {}
    if pct is not None:
        facts["pct_so"] = pct
    elif shares is not None and so:
        facts["pct_so"] = shares / so * 100
    if yen is not None:
        facts["yen"] = yen
    if shares is not None:
        facts["shares"] = shares
    return True, tag, summary_en, summary_jp, subtype_code, facts


# --- CANCEL -----------------------------------------------------------------

_CANCEL_RE = re.compile(
    r"自己(株式|株券)[^。\n]{0,12}消却"
)


def _match_cancel(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    if not _CANCEL_RE.search(title):
        return _EMPTY
    body = d.get("body_jp") or ""
    combined = title + "\n" + body

    pct = _parse_percent(combined)
    shares = _parse_shares(combined)
    so = d.get("shares_outstanding")

    passes_gate = False
    if pct is not None and pct >= 0.5:
        passes_gate = True
    elif shares is not None and so and (shares / so) >= 0.005:
        passes_gate = True
        pct = shares / so * 100
    elif pct is None and shares is None:
        passes_gate = True

    if not passes_gate:
        return _EMPTY

    parts_en: list[str] = []
    parts_jp: list[str] = []
    if pct is not None:
        parts_en.append(f"{pct:.1f}% of S/O")
        parts_jp.append(f"発行済{pct:.1f}%")
    if shares is not None:
        parts_en.append(f"{shares:,} shares")
        parts_jp.append(f"{shares:,}株")

    tag_body = " · ".join(parts_en) if parts_en else "size TBC"
    tag = f"Cancellation · {tag_body}"[:60]

    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    facts: dict = {}
    if pct is not None:
        facts["pct_so"] = pct
    if shares is not None:
        facts["shares"] = shares
    return True, tag, summary_en, summary_jp, "", facts


# --- DIV --------------------------------------------------------------------

_DIV_RE = re.compile(
    r"(配当予想の修正|剰余金の配当|"
    r"期末配当|中間配当|特別配当|"
    r"記念配当|配当方針|増配|復配|"
    r"配当の開始)"
)


def _match_div(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    if not _DIV_RE.search(title):
        return _EMPTY
    body = d.get("body_jp") or ""
    combined = title + "\n" + body

    is_special = bool(re.search(r"特別配当|記念配当|創立記念", combined))
    is_first_ever = bool(re.search(r"初配|復配|配当の開始|無配からの転換", combined))
    is_progressive = bool(re.search(r"累進的?配当|累進配当方針|連続増配", combined))
    is_increase = bool(re.search(r"増配", combined))
    is_revision = bool(re.search(r"配当予想の修正", combined))

    payout_jump = False
    pr = re.search(
        rf"配当性向[^0-9０-９%％]{{0,10}}({_NUM})\s*[%％]"
        rf"[^0-9０-９%％]{{0,30}}({_NUM})\s*[%％]",
        combined,
    )
    if pr:
        a, b = _to_float(pr.group(1)), _to_float(pr.group(2))
        if a is not None and b is not None and abs(b - a) >= 10.0:
            payout_jump = True

    yen = _parse_yen(combined)
    if not (
        is_special or is_first_ever or is_progressive or payout_jump
        or (is_revision and is_increase)
    ):
        return _EMPTY

    # ---- Subtype routing: DIV_POLICY (policy change / first-ever / special /
    # payout-ratio raise / progressive) vs DIV_HIKE (ordinary 増配 with no
    # policy signal). Order matters — policy-class flavours win over the
    # plain 増配 catchall.
    if is_progressive:
        flavour_en, flavour_jp = "progressive policy", "累進配当方針"
        subtype_code = "DIV_POLICY"
    elif is_first_ever:
        flavour_en, flavour_jp = "first/resumed dividend", "初配・復配"
        subtype_code = "DIV_POLICY"
    elif is_special:
        flavour_en, flavour_jp = "special dividend", "特別配当"
        subtype_code = "DIV_POLICY"
    elif payout_jump:
        flavour_en, flavour_jp = "+10pp payout", "配当性向引上"
        subtype_code = "DIV_POLICY"
    else:
        flavour_en, flavour_jp = "dividend hike", "増配"
        subtype_code = "DIV_HIKE"

    tag_extras: list[str] = []
    if yen and is_special:
        tag_extras.append(_fmt_yen(yen))
    tag_suffix = " · " + " · ".join(tag_extras) if tag_extras else ""
    tag = f"Dividend · {flavour_en}{tag_suffix}"[:60]

    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    facts: dict = {}
    if yen is not None:
        facts["yen"] = yen
    return True, tag, summary_en, summary_jp, subtype_code, facts


# --- COC --------------------------------------------------------------------

_COC_RE = re.compile(
    r"(資本コスト[や・]?株価を意識した経営|"
    r"資本収益性|PBR.?1.?倍|PBR1倍割れ|"
    r"中期経営計画.*(ROIC|ROE|WACC)|"
    r"(ROIC|ROE|WACC).{0,20}目標)"
)


def _match_coc(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    body = d.get("body_jp") or ""
    combined = title + "\n" + body
    if not _COC_RE.search(combined):
        return _EMPTY

    # Look for "initial publication" markers in title OR body. (Body is often
    # where companies say 新たに設定 / 初めて公表 even when the title is
    # generic.)
    is_initial = bool(re.search(r"初回|公表|策定|新たに|初めて", title + "\n" + body))
    is_mtp = bool(re.search(r"中期経営計画|中計", combined))
    if "資本コスト" in title:
        flavour_en = "MTP update" if is_mtp else ("initial publication" if is_initial else "update")
        flavour_jp = "中計更新" if is_mtp else ("初回公表" if is_initial else "更新")
    elif is_mtp:
        flavour_en, flavour_jp = "MTP w/ ROIC/ROE target", "中計に資本効率目標"
    else:
        flavour_en, flavour_jp = "capital-efficiency target", "資本効率目標"

    # Subtype: COC_INITIAL is a higher-signal first-publication / new MTP
    # commitment; COC_UPDATE is a refresh of an existing one.
    if is_initial and not is_mtp:
        subtype_code = "COC_INITIAL"
    elif is_initial and is_mtp:
        subtype_code = "COC_INITIAL"
    else:
        subtype_code = "COC_UPDATE"

    tag = f"Cost-of-capital · {flavour_en}"[:60]
    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    return True, tag, summary_en, summary_jp, subtype_code, {}


# --- CROSS ------------------------------------------------------------------

_CROSS_RE = re.compile(
    # Cross-shareholding terms (any of):
    #   政策保有株式 / 政策投資株式 / 持合株式 / 持ち合い株式 /
    #   相互保有 / 株式持ち合い
    # COMBINED with an unwind verb:
    #   縮減 / 売却 / 削減方針 / 解消
    # Window is generous (up to 20 chars between term and verb) but
    # constrained to a single sentence (no 。 in the gap).
    r"(?:"
    r"政策保有株式|政策投資株式|"
    r"持合株式|持ち合い株式|"
    r"株式持ち合い|相互保有"
    r")"
    r"[^。\n]{0,20}"
    r"(?:縮減|売却|削減方針|解消)"
)


def _match_cross(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    body = d.get("body_jp") or ""
    combined = title + "\n" + body
    if not _CROSS_RE.search(combined):
        return _EMPTY

    is_policy = bool(re.search(
        r"方針|プログラム|計画|"
        r"削減目標|縮減方針",
        combined,
    ))
    yen = _parse_yen(combined)
    if not is_policy:
        if yen is None or yen < 500_000_000:
            return _EMPTY

    parts_en: list[str] = []
    parts_jp: list[str] = []
    if yen:
        parts_en.append(_fmt_yen(yen))
        parts_jp.append(_fmt_yen_jp(yen))
    parts_en.append("policy" if is_policy else "tactical")
    parts_jp.append("方針" if is_policy else "売却")

    tag = ("Cross-holding · " + " · ".join(parts_en))[:60]
    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    facts: dict = {}
    if yen is not None:
        facts["yen"] = yen
    return True, tag, summary_en, summary_jp, "", facts


# --- COMP -------------------------------------------------------------------

_COMP_RE = re.compile(
    r"(役員報酬制度.{0,10}(改定|変更|見直し)|"
    r"報酬制度の(改定|変更|見直し)|"
    r"業績連動報酬|長期インセンティブ)"
)
_COMP_KPI_RE = re.compile(
    r"(ROIC|ＲＯＩＣ|ROCE|ＲＯＣＥ|TSR|ＴＳＲ|"
    r"ROE|ＲＯＥ|EPS|ＥＰＳ)"
)


def _match_comp(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    body = d.get("body_jp") or ""
    combined = title + "\n" + body
    if not _COMP_RE.search(combined):
        return _EMPTY
    kpi_match = _COMP_KPI_RE.search(combined)
    if not kpi_match:
        return _EMPTY
    kpi = kpi_match.group(1)
    kpi = (
        kpi.replace("ＲＯＩＣ", "ROIC")
        .replace("ＲＯＣＥ", "ROCE")
        .replace("ＴＳＲ", "TSR")
        .replace("ＲＯＥ", "ROE")
        .replace("ＥＰＳ", "EPS")
    )
    tag = f"Comp · adds {kpi} linkage"[:60]
    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    # Subtype: COMP with explicit KPI linkage is always COMP_KPI (the matcher
    # already gates on a KPI keyword being present).
    return True, tag, summary_en, summary_jp, "COMP_KPI", {}


# --- GOV --------------------------------------------------------------------

_GOV_RE = re.compile(
    r"コーポレート[・]?ガバナンス"
    r"[・]?(コード|報告書|に関する報告書)"
)
_GOV_PRINCIPLE_RE = re.compile(
    r"(原則|補充原則)?\s*(1[\-－]4|1[\-－]5|5[\-－]2)"
)


def _match_gov(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
    body = d.get("body_jp") or ""
    combined = title + "\n" + body
    if not _GOV_RE.search(combined):
        return _EMPTY
    principle = _GOV_PRINCIPLE_RE.search(combined)
    has_flip = bool(re.search(
        r"explain.{0,20}comply|エクスプレイン.{0,10}コンプライ|"
        r"コンプライへ.{0,5}変更|"
        r"遵守へ.{0,5}変更",
        combined,
    ))
    if not (principle or has_flip or "報告書" in title):
        return _EMPTY

    if principle and has_flip:
        pp = principle.group(2).replace("－", "-")
        flavour_en = f"explain->comply on Principle {pp}"
        flavour_jp = f"原則{principle.group(2)}でコンプライ化"
        subtype_code = "GOV_FLIP"
    elif principle:
        pp = principle.group(2).replace("－", "-")
        flavour_en = f"update on Principle {pp}"
        flavour_jp = f"原則{principle.group(2)}の更新"
        subtype_code = ""  # use default GOV class
    else:
        flavour_en, flavour_jp = "CG report update", "CG報告書更新"
        subtype_code = ""  # use default GOV class

    tag = f"Governance · {flavour_en}"[:60]
    # Boilerplate summary stripped - LLM enricher (pdf_enricher.py) owns this.
    summary_en = ""
    summary_jp = ""
    return True, tag, summary_en, summary_jp, subtype_code, {}


# ---------------------------------------------------------------------------
# Composition: classify()
# ---------------------------------------------------------------------------

# Default class codes per matcher. Each matcher may return a class_override
# (the 5th element of MatchResult) that supersedes the default. Subtype codes
# the matchers can emit:
#   _match_mbo      -> MBO  (or M_AND_A if outbound-TOB guard fires)
#   _match_buyback  -> BUYBACK_INIT / BUYBACK_REV / BUYBACK_BLOCK /
#                      BUYBACK_PROGRESS / BUYBACK_HOUSE
#   _match_cancel   -> CANCEL
#   _match_div      -> DIV_POLICY / DIV_HIKE
#   _match_coc      -> COC_INITIAL / COC_UPDATE
#   _match_cross    -> CROSS
#   _match_comp     -> COMP_KPI
#   _match_gov      -> GOV (or GOV_FLIP for explain->comply)
# Full recognised class string set (union across all matchers):
#   MBO, M_AND_A, BUYBACK_INIT, BUYBACK_REV, BUYBACK_BLOCK,
#   BUYBACK_PROGRESS, BUYBACK_HOUSE, CANCEL, DIV_POLICY, DIV_HIKE,
#   COC_INITIAL, COC_UPDATE, CROSS, COMP_KPI, GOV, GOV_FLIP.
_MATCHERS: tuple[tuple[str, Callable[[dict], MatchResult]], ...] = (
    ("MBO", _match_mbo),
    ("BUYBACK_INIT", _match_buyback),
    ("CANCEL", _match_cancel),
    ("DIV_HIKE", _match_div),
    ("COC_UPDATE", _match_coc),
    ("CROSS", _match_cross),
    ("COMP_KPI", _match_comp),
    ("GOV", _match_gov),
)


def _normalise_ts(raw: str) -> str:
    if not raw:
        return datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    s = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(raw.strip(), fmt)
                break
            except ValueError:
                continue
        else:
            return datetime.now(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.astimezone(JST).strftime("%Y-%m-%dT%H:%M:%S+09:00")


# ---------------------------------------------------------------------------
# signal_score derivation (1=Housekeeping, 2=Material, 3=Inflection)
# ---------------------------------------------------------------------------

# Block-trade size threshold for upgrading BUYBACK_BLOCK from 1 -> 2.
_BLOCK_YEN_THRESHOLD = 10_000_000_000  # ¥10bn


def _signal_score(class_code: str, facts: dict) -> int:
    """Derive a 1-3 signal score from class and extracted facts.

    - 3 = Inflection
    - 2 = Material
    - 1 = Housekeeping
    Defaults to 2 (material) for any class with no specific rule, to avoid
    losing rows in the feed.
    """
    pct = facts.get("pct_so") if isinstance(facts, dict) else None
    yen = facts.get("yen") if isinstance(facts, dict) else None

    # --- 3: Inflection -----------------------------------------------------
    if class_code in ("COC_INITIAL", "DIV_POLICY", "GOV_FLIP", "COMP_KPI"):
        return 3
    if class_code == "MBO":
        return 3  # surviving MBOs are true take-privates after outbound guard
    if class_code == "BUYBACK_INIT":
        if isinstance(pct, (int, float)) and pct >= 3.0:
            return 3

    # --- 2: Material -------------------------------------------------------
    if class_code == "BUYBACK_INIT":
        if isinstance(pct, (int, float)) and 1.0 <= pct < 3.0:
            return 2
        return 2  # default for BUYBACK_INIT with unknown pct
    if class_code == "BUYBACK_REV":
        return 2
    if class_code == "CANCEL":
        if isinstance(pct, (int, float)) and pct >= 1.0:
            return 2
        # CANCEL with pct < 1.0 OR no pct info -> housekeeping
        return 1
    if class_code == "DIV_HIKE":
        # Magnitude info isn't structured here; default to material. Brief
        # says "heuristic — leave as 2 by default for DIV_HIKE".
        return 2
    if class_code == "COC_UPDATE":
        return 2
    if class_code == "CROSS":
        return 2
    if class_code == "BUYBACK_BLOCK":
        big = (isinstance(yen, (int, float)) and yen >= _BLOCK_YEN_THRESHOLD) or (
            isinstance(pct, (int, float)) and pct >= 3.0
        )
        return 2 if big else 1

    # --- 1: Housekeeping ---------------------------------------------------
    if class_code in ("BUYBACK_PROGRESS", "BUYBACK_HOUSE", "M_AND_A"):
        return 1

    # Fallback: legacy class codes (GOV, COC, DIV) and anything else default
    # to 2 (material) so we don't silently drop signal.
    return 2


def classify(disclosure: dict) -> Optional[dict]:
    """Classify a normalised disclosure dict.

    Returns a feed.json row dict (per _SPEC.md Section 4) if the disclosure
    matches one of the 8 Principle-6 classes, else None.
    """
    if not disclosure:
        return None
    title = disclosure.get("title_jp", "") or ""
    body = disclosure.get("body_jp")
    if _is_excluded(title, body):
        return None

    for default_class, matcher in _MATCHERS:
        matched, tag, summary_en, summary_jp, class_override, facts = matcher(
            disclosure
        )
        if matched:
            class_code = class_override or default_class
            source = disclosure.get("source", "EDINET")
            doc_id = disclosure.get("doc_id", "")
            ticker = str(disclosure.get("ticker", "") or "").strip()
            ts = _normalise_ts(disclosure.get("submitted_at", ""))
            name_en = disclosure.get("name_en") or disclosure.get("name_jp", "")
            name_jp = disclosure.get("name_jp", "")
            profile_url = f"/en/compounders/{ticker}/" if _in_universe(ticker) else None
            return {
                "id": f"{source}-{doc_id}",
                "ts": ts,
                "ticker": ticker,
                "name_en": name_en,
                "name_jp": name_jp,
                "class": class_code,
                "tag": tag,
                "doc_title_jp": disclosure.get("title_jp", ""),
                "summary_en": summary_en,
                "summary_jp": summary_jp,
                "key_facts": facts,
                "signal_score": _signal_score(class_code, facts),
                "source": source,
                "doc_url": disclosure.get("doc_url", ""),
                "profile_url": profile_url,
            }
    return None


# ---------------------------------------------------------------------------
# Inline test bank
# ---------------------------------------------------------------------------


def _make_disclosure(**overrides) -> dict:
    base = {
        "source": "EDINET",
        "doc_id": "S100TEST",
        "submitted_at": "2026-05-17T08:23:00+09:00",
        "ticker": "4776",
        "name_jp": "サイボウズ株式会社",
        "name_en": "Cybozu, Inc.",
        "title_jp": "",
        "doc_url": "https://disclosure2.edinet-fsa.go.jp/EKW0EZ0001.aspx?docID=S100TEST",
        "body_jp": None,
        "shares_outstanding": None,
        "market_cap_jpy": None,
    }
    base.update(overrides)
    return base


def _run_tests() -> tuple[int, int]:
    # Each case is (label, disclosure, expected_class, expected_tag_substr,
    # expected_signal_score). expected_class=None means the disclosure should
    # be filtered out. expected_signal_score=None disables the score check.
    # Each case is (label, disclosure, expected_class, expected_tag_substr,
    # expected_signal_score). expected_class=None means the disclosure should
    # be filtered out. expected_signal_score=None disables the score check.
    cases: list[
        tuple[str, dict, Optional[str], Optional[str], Optional[int]]
    ] = [
        # ---- BUYBACK subtypes ----------------------------------------------
        (
            "BUYBACK_INIT . 2.1% S/O -> material",
            _make_disclosure(
                title_jp="自己株式の取得に係る事項の決定に関するお知らせ",
                body_jp=(
                    "取得する株式の総数 1,400,000 株\r\n"
                    "発行済株式総数（自己株式を除く）に対する割合 2.1%\r\n"
                    "取得価額の総額 3,000,000,000 円"
                ),
                shares_outstanding=66_000_000,
                market_cap_jpy=200_000_000_000,
            ),
            "BUYBACK_INIT",
            "Buyback",
            2,
        ),
        (
            "BUYBACK_INIT . 4.0% S/O -> inflection (>=3.0% pct_so)",
            _make_disclosure(
                title_jp="自己株式の取得に係る事項の決定に関するお知らせ",
                body_jp="発行済株式総数に対する割合 4.0% 取得価額の総額 5,000,000,000円",
            ),
            "BUYBACK_INIT",
            "Buyback",
            3,
        ),
        (
            "BUYBACK_PROGRESS . status update",
            _make_disclosure(
                title_jp="自己株式取得状況に関するお知らせ",
                body_jp=None,
            ),
            "BUYBACK_PROGRESS",
            "Buyback (progress)",
            1,
        ),
        (
            "BUYBACK_REV . upward revision of program",
            _make_disclosure(
                title_jp=(
                    "自己株式の取得に係る事項の一部変更（取得上限引上）に関するお知らせ"
                ),
                body_jp="取得価額の総額の上限 5,000,000,000 円",
            ),
            "BUYBACK_REV",
            "Buyback (revision)",
            2,
        ),
        (
            "BUYBACK_BLOCK . ToSTNeT-3 block ¥15bn -> material",
            _make_disclosure(
                title_jp="ToSTNeT-3を通じた自己株式の取得に関するお知らせ",
                body_jp="取得価額の総額 15,000,000,000 円",
            ),
            "BUYBACK_BLOCK",
            "Buyback (block)",
            2,
        ),
        (
            "BUYBACK_BLOCK . small block -> housekeeping",
            _make_disclosure(
                title_jp="立会外取引による自己株式の取得に関するお知らせ",
                body_jp="取得価額の総額 1,000,000,000 円",
            ),
            "BUYBACK_BLOCK",
            "Buyback (block)",
            1,
        ),
        (
            "BUYBACK_HOUSE . J-ESOP bundle",
            _make_disclosure(
                title_jp=(
                    "J-ESOP導入及び自己株式の処分に係る取得に関するお知らせ"
                ),
                body_jp="取得価額の総額 1,500,000,000 円",
            ),
            "BUYBACK_HOUSE",
            "Buyback (housekeeping)",
            1,
        ),
        # ---- CANCEL --------------------------------------------------------
        (
            "CANCEL . 0.8% of S/O -> housekeeping",
            _make_disclosure(
                title_jp="自己株式の消却に関するお知らせ",
                body_jp=(
                    "消却する株式の種類及び数 "
                    "普通株式 500,000 株 "
                    "発行済株式総数に対する割合 0.8%"
                ),
            ),
            "CANCEL",
            "Cancellation",
            1,
        ),
        (
            "CANCEL . 1.5% of S/O -> material",
            _make_disclosure(
                title_jp="自己株式の消却に関するお知らせ",
                body_jp="発行済株式総数に対する割合 1.5%",
            ),
            "CANCEL",
            "Cancellation",
            2,
        ),
        # ---- DIV split -----------------------------------------------------
        (
            "DIV_POLICY . payout +15pp -> inflection",
            _make_disclosure(
                title_jp="配当予想の修正に関するお知らせ",
                body_jp="配当性向 30% から 配当性向 45% へ引き上げ",
            ),
            "DIV_POLICY",
            "Dividend",
            3,
        ),
        (
            "DIV_POLICY . special dividend -> inflection",
            _make_disclosure(
                title_jp="特別配当の実施に関するお知らせ",
                body_jp="特別配当として1株あたり50円、総額50億円を実施。",
            ),
            "DIV_POLICY",
            "Dividend",
            3,
        ),
        (
            "DIV_POLICY . progressive dividend policy -> inflection",
            _make_disclosure(
                title_jp="配当方針の変更（累進配当方針の導入）に関するお知らせ",
                body_jp="累進配当方針を導入する。",
            ),
            "DIV_POLICY",
            "Dividend",
            3,
        ),
        (
            "DIV_HIKE . ordinary 増配 -> material",
            _make_disclosure(
                title_jp="配当予想の修正に関するお知らせ",
                body_jp="今期増配を実施する。",
            ),
            "DIV_HIKE",
            "Dividend",
            2,
        ),
        # ---- COC -----------------------------------------------------------
        (
            "COC_INITIAL . cost-of-capital initial publication",
            _make_disclosure(
                title_jp="資本コストや株価を意識した経営の実現に向けた対応について",
                body_jp="ROE 目標 12%、ROIC 目標 10% を新たに設定。",
            ),
            "COC_INITIAL",
            "Cost-of-capital",
            3,
        ),
        # ---- CROSS (broadened regex) --------------------------------------
        (
            "CROSS . 政策保有株式 unwind policy",
            _make_disclosure(
                title_jp="政策保有株式の縮減方針に関するお知らせ",
                body_jp="2030年までに政策保有株式を簿価で半減する方針。",
            ),
            "CROSS",
            "Cross-holding",
            2,
        ),
        (
            "CROSS . 政策投資株式 alt term",
            _make_disclosure(
                title_jp="政策投資株式の縮減方針に関するお知らせ",
                body_jp="政策投資株式を段階的に売却していく方針。",
            ),
            "CROSS",
            "Cross-holding",
            2,
        ),
        (
            "CROSS . 持合株式 (cross-shareholding)",
            _make_disclosure(
                title_jp="持合株式の解消に関するお知らせ",
                body_jp="持合株式の解消を進める方針。",
            ),
            "CROSS",
            "Cross-holding",
            2,
        ),
        (
            "CROSS . 相互保有 unwind",
            _make_disclosure(
                title_jp="相互保有株式の縮減方針に関するお知らせ",
                body_jp="相互保有を縮減していく。",
            ),
            "CROSS",
            "Cross-holding",
            2,
        ),
        # ---- MBO + outbound-TOB guard --------------------------------------
        (
            "MBO . own going-private (no target ticker in title)",
            _make_disclosure(
                title_jp="MBOの実施及び公開買付けに関するお知らせ",
                body_jp="公開買付価格 1株あたり 2,500円。",
                ticker="9999",
            ),
            "MBO",
            "MBO",
            3,
        ),
        (
            "M_AND_A . outbound TOB (filer != target ticker)",
            _make_disclosure(
                title_jp="〇〇株式会社（証券コード 1234）に対する公開買付けの開始に関するお知らせ",
                body_jp="買付代金 50,000,000,000円。",
                ticker="6762",
            ),
            "M_AND_A",
            "M&A",
            1,
        ),
        (
            "MBO . filer == target ticker -> true MBO",
            _make_disclosure(
                title_jp="当社株式（証券コード 4776）に対する公開買付けに関するお知らせ",
                body_jp="完全子会社化を目的とする公開買付け。",
                ticker="4776",
            ),
            "MBO",
            "Tender offer",
            3,
        ),
        # ---- COMP / GOV ---------------------------------------------------
        (
            "COMP_KPI . ROIC linkage added",
            _make_disclosure(
                title_jp="役員報酬制度の改定に関するお知らせ",
                body_jp="業績連動報酬の指標としてROICおよびTSRを導入する。",
            ),
            "COMP_KPI",
            "Comp",
            3,
        ),
        (
            "GOV_FLIP . CG report Principle 1-4 explain->comply",
            _make_disclosure(
                title_jp="コーポレート・ガバナンスに関する報告書",
                body_jp="補充原則 1-4 について、これまでexplainとしていたが今回 comply に変更する。",
            ),
            "GOV_FLIP",
            "Governance",
            3,
        ),
        # ---- Negative cases -----------------------------------------------
        (
            "NEG . kessan tanshin (earnings)",
            _make_disclosure(
                title_jp="2026年3月期 決算短信〔日本基準〕（連結）",
                body_jp="自己株式の取得 1,000,000株",
            ),
            None,
            None,
            None,
        ),
        (
            "NEG . monthly sales",
            _make_disclosure(title_jp="2026年4月度 月次売上高に関するお知らせ"),
            None,
            None,
            None,
        ),
        (
            "NEG . stock split",
            _make_disclosure(title_jp="株式分割（普通株式1株につき2株）に関するお知らせ"),
            None,
            None,
            None,
        ),
        (
            "BUYBACK_INIT . non-universe -> no profile_url",
            _make_disclosure(
                title_jp="自己株式の取得に係る事項の決定に関するお知らせ",
                body_jp="発行済株式総数に対する割合 1.5% 取得価額の総額 2,000,000,000円",
                ticker="9999",
                name_jp="Random KK",
                name_en="Random KK",
            ),
            "BUYBACK_INIT",
            "Buyback",
            2,
        ),
        (
            "MBO . precedence over buyback (treasury sub-step)",
            _make_disclosure(
                title_jp="公開買付けの開始及び自己株式の取得に係るお知らせ",
                body_jp="完全子会社化を目的とする公開買付け。",
                ticker="8888",
                name_en="X Holdings",
                name_jp="X Holdings",
            ),
            "MBO",
            "Tender offer",
            3,
        ),
        (
            "NEG . stock-option grant alone",
            _make_disclosure(
                title_jp="ストックオプションとしての新株予約権発行に関するお知らせ",
            ),
            None,
            None,
            None,
        ),
    ]

    passed = 0
    total = len(cases)
    for label, disc, expected_class, tag_sub, expected_score in cases:
        result = classify(disc)
        ok = True
        reason = ""
        if expected_class is None:
            if result is not None:
                ok = False
                reason = f"expected None, got class={result.get('class')}"
        else:
            if result is None:
                ok = False
                reason = "expected match, got None"
            elif result.get("class") != expected_class:
                ok = False
                reason = (
                    f"expected class={expected_class}, "
                    f"got class={result.get('class')}"
                )
            elif tag_sub and tag_sub not in result.get("tag", ""):
                ok = False
                reason = (
                    f"tag missing substring '{tag_sub}': "
                    f"got '{result.get('tag')}'"
                )
            else:
                tk = disc.get("ticker", "")
                exp_profile = (
                    f"/en/compounders/{tk}/" if _in_universe(tk) else None
                )
                if result.get("profile_url") != exp_profile:
                    ok = False
                    reason = (
                        f"profile_url={result.get('profile_url')!r}, "
                        f"expected {exp_profile!r}"
                    )
                else:
                    # Boilerplate summaries must be empty - LLM enricher
                    # (pdf_enricher.py) is now the sole source.
                    if result.get("summary_en") != "":
                        ok = False
                        reason = (
                            f"summary_en should be empty, "
                            f"got {result.get('summary_en')!r}"
                        )
                    elif result.get("summary_jp") != "":
                        ok = False
                        reason = (
                            f"summary_jp should be empty, "
                            f"got {result.get('summary_jp')!r}"
                        )
                    elif expected_score is not None and (
                        result.get("signal_score") != expected_score
                    ):
                        ok = False
                        reason = (
                            f"expected signal_score={expected_score}, "
                            f"got {result.get('signal_score')}"
                        )

        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {label}" + (f"  - {reason}" if not ok else ""))
        if ok:
            passed += 1

    print(f"\n{passed}/{total} test cases passed.")
    return passed, total


if __name__ == "__main__":
    import sys
    p, t = _run_tests()
    sys.exit(0 if p == t else 1)
