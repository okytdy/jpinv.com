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
# Each returns (matched, tag, summary_en, summary_jp).
# ---------------------------------------------------------------------------

MatchResult = Tuple[bool, str, str, str]
_EMPTY: MatchResult = (False, "", "", "")


# --- MBO --------------------------------------------------------------------

_MBO_RE = re.compile(
    r"(公開買付|MBO|ＭＢＯ|"
    r"完全子会社化|TOB|ＴＯＢ|"
    r"株式等売渡請求|"
    r"非公開化|スクイーズ.?アウト)"
)


def _match_mbo(d: dict) -> MatchResult:
    title = d.get("title_jp", "") or ""
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

    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{kind_en} disclosed for {name_en}"
        + (f" at {_fmt_yen(aggregate_yen)}." if aggregate_yen else ".")
        + " Take-private transaction removes the float and resets capital policy."
    )
    summary_jp = (
        f"{name_jp}に対する{kind_jp}を開示"
        + (f"（金額{_fmt_yen_jp(aggregate_yen)}）" if aggregate_yen else "")
        + "。非公開化により資本政策が再構築。"
    )
    return True, tag, summary_en, summary_jp


# --- BUYBACK ----------------------------------------------------------------

_BUYBACK_RE = re.compile(
    r"自己(株式|株券)[^。\n]{0,12}"
    r"(取得|買付|買い付け)"
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

    tag_body = " · ".join(parts_en) if parts_en else "size TBC"
    tag = f"Buyback · {tag_body}"[:60]

    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{name_en} authorised a share buyback"
        + (f" of {' / '.join(parts_en)}" if parts_en else "")
        + ". Direct return of capital and a signal management views shares as undervalued."
    )
    summary_jp = (
        f"{name_jp}が自己株式取得"
        + (f"（{' / '.join(parts_jp)}）" if parts_jp else "")
        + "を決議。資本還元と株価評価のシグナル。"
    )
    return True, tag, summary_en, summary_jp


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

    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{name_en} cancelled treasury stock"
        + (f" ({' / '.join(parts_en)})" if parts_en else "")
        + ". Permanent share-count reduction lifts per-share economics."
    )
    summary_jp = (
        f"{name_jp}が自己株式消却"
        + (f"（{' / '.join(parts_jp)}）" if parts_jp else "")
        + "を実施。発行済株式数が恒久的に減少。"
    )
    return True, tag, summary_en, summary_jp


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

    if is_progressive:
        flavour_en, flavour_jp = "progressive policy", "累進配当方針"
    elif is_first_ever:
        flavour_en, flavour_jp = "first/resumed dividend", "初配・復配"
    elif is_special:
        flavour_en, flavour_jp = "special dividend", "特別配当"
    elif payout_jump:
        flavour_en, flavour_jp = "+10pp payout", "配当性向引上"
    else:
        flavour_en, flavour_jp = "dividend hike", "増配"

    tag_extras: list[str] = []
    if yen and is_special:
        tag_extras.append(_fmt_yen(yen))
    tag_suffix = " · " + " · ".join(tag_extras) if tag_extras else ""
    tag = f"Dividend · {flavour_en}{tag_suffix}"[:60]

    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{name_en} announced a material dividend change ({flavour_en})"
        + (f" totalling {_fmt_yen(yen)}." if yen else ".")
        + " Reframes the return-of-capital baseline."
    )
    summary_jp = (
        f"{name_jp}が配当方針変更を開示（{flavour_jp}）"
        + (f"（{_fmt_yen_jp(yen)}）" if yen else "")
        + "。資本還元基準が刷新。"
    )
    return True, tag, summary_en, summary_jp


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

    is_initial = bool(re.search(r"初回|公表|策定|新たに", title))
    is_mtp = bool(re.search(r"中期経営計画|中計", combined))
    if "資本コスト" in title:
        flavour_en = "MTP update" if is_mtp else ("initial publication" if is_initial else "update")
        flavour_jp = "中計更新" if is_mtp else ("初回公表" if is_initial else "更新")
    elif is_mtp:
        flavour_en, flavour_jp = "MTP w/ ROIC/ROE target", "中計に資本効率目標"
    else:
        flavour_en, flavour_jp = "capital-efficiency target", "資本効率目標"

    tag = f"Cost-of-capital · {flavour_en}"[:60]
    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{name_en} published a cost-of-capital / capital-efficiency disclosure "
        f"({flavour_en}). Signals management is engaging with the Principle-6 framework."
    )
    summary_jp = (
        f"{name_jp}が資本コスト・株価を意識した"
        f"経営に関する開示（{flavour_jp}）。"
        f"資本効率を踏まえた経営方針への対応。"
    )
    return True, tag, summary_en, summary_jp


# --- CROSS ------------------------------------------------------------------

_CROSS_RE = re.compile(
    r"(政策保有株式.{0,15}(縮減|売却|削減)方針|"
    r"政策保有株式の縮減|"
    r"政策保有株式.{0,15}売却)"
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
    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{name_en} disclosed a cross-shareholding unwind "
        + ("policy" if is_policy else "sale")
        + (f" of {_fmt_yen(yen)}." if yen else ".")
        + " Frees balance-sheet capital and improves capital efficiency."
    )
    summary_jp = (
        f"{name_jp}が政策保有株式の"
        + ("縮減方針" if is_policy else "売却")
        + (f"（{_fmt_yen_jp(yen)}）" if yen else "")
        + "を開示。資本効率の改善要因。"
    )
    return True, tag, summary_en, summary_jp


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
    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{name_en} revised exec compensation to add {kpi} linkage. "
        f"Aligns management pay with capital-efficiency outcomes."
    )
    summary_jp = (
        f"{name_jp}が役員報酬制度を改定し"
        f"{kpi}を導入。"
        f"資本効率と経営陣報酬の連動が強化。"
    )
    return True, tag, summary_en, summary_jp


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
    elif principle:
        pp = principle.group(2).replace("－", "-")
        flavour_en = f"update on Principle {pp}"
        flavour_jp = f"原則{principle.group(2)}の更新"
    else:
        flavour_en, flavour_jp = "CG report update", "CG報告書更新"

    tag = f"Governance · {flavour_en}"[:60]
    name_en = d.get("name_en") or d.get("name_jp", "")
    name_jp = d.get("name_jp", "")
    summary_en = (
        f"{name_en} updated its corporate governance report ({flavour_en}). "
        f"Signals movement on capital-policy principles."
    )
    summary_jp = (
        f"{name_jp}がコーポレートガバナンス"
        f"報告書を更新（{flavour_jp}）。"
        f"資本政策関連の原則対応が変化。"
    )
    return True, tag, summary_en, summary_jp


# ---------------------------------------------------------------------------
# Composition: classify()
# ---------------------------------------------------------------------------

_MATCHERS: tuple[tuple[str, Callable[[dict], MatchResult]], ...] = (
    ("MBO", _match_mbo),
    ("BUYBACK", _match_buyback),
    ("CANCEL", _match_cancel),
    ("DIV", _match_div),
    ("COC", _match_coc),
    ("CROSS", _match_cross),
    ("COMP", _match_comp),
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

    for class_code, matcher in _MATCHERS:
        matched, tag, summary_en, summary_jp = matcher(disclosure)
        if matched:
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
                "summary_en": summary_en,
                "summary_jp": summary_jp,
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
    cases: list[tuple[str, dict, Optional[str], Optional[str]]] = [
        (
            "BUYBACK . pct in body",
            _make_disclosure(
                title_jp="自己株式の取得に係る事項の決定に関するお知らせ",
                body_jp=(
                    "取得する株式の総数 1,400,000 株\n"
                    "発行済株式総数（自己株式を除く）に対する割合 2.1%\n"
                    "取得価額の総額 3,000,000,000 円"
                ),
                shares_outstanding=66_000_000,
                market_cap_jpy=200_000_000_000,
            ),
            "BUYBACK",
            "Buyback",
        ),
        (
            "BUYBACK . size TBC fallback",
            _make_disclosure(
                title_jp="自己株式取得状況に関するお知らせ",
                body_jp=None,
            ),
            "BUYBACK",
            "Buyback",
        ),
        (
            "CANCEL . 0.8% of S/O",
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
        ),
        (
            "DIV . payout +15pp",
            _make_disclosure(
                title_jp="配当予想の修正に関するお知らせ",
                body_jp="配当性向 30% から 配当性向 45% へ引き上げ",
            ),
            "DIV",
            "Dividend",
        ),
        (
            "DIV . special dividend",
            _make_disclosure(
                title_jp="特別配当の実施に関するお知らせ",
                body_jp="特別配当として1株あたり50円、総額50億円を実施。",
            ),
            "DIV",
            "Dividend",
        ),
        (
            "COC . cost-of-capital initial publication",
            _make_disclosure(
                title_jp="資本コストや株価を意識した経営の実現に向けた対応について",
                body_jp="ROE 目標 12%、ROIC 目標 10% を設定。",
            ),
            "COC",
            "Cost-of-capital",
        ),
        (
            "CROSS . policy unwind",
            _make_disclosure(
                title_jp="政策保有株式の縮減方針に関するお知らせ",
                body_jp="2030年までに政策保有株式を簿価で半減する方針。",
            ),
            "CROSS",
            "Cross-holding",
        ),
        (
            "MBO . tender offer",
            _make_disclosure(
                title_jp="MBOの実施及び公開買付けに関するお知らせ",
                body_jp="公開買付価格 1株あたり 2,500円。",
                ticker="9999",
            ),
            "MBO",
            "MBO",
        ),
        (
            "COMP . ROIC linkage added",
            _make_disclosure(
                title_jp="役員報酬制度の改定に関するお知らせ",
                body_jp="業績連動報酬の指標としてROICおよびTSRを導入する。",
            ),
            "COMP",
            "Comp",
        ),
        (
            "GOV . CG report Principle 1-4 flip",
            _make_disclosure(
                title_jp="コーポレート・ガバナンスに関する報告書",
                body_jp="補充原則 1-4 について、これまでexplainとしていたが今回 comply に変更する。",
            ),
            "GOV",
            "Governance",
        ),
        (
            "NEG . kessan tanshin (earnings)",
            _make_disclosure(
                title_jp="2026年3月期 決算短信〔日本基準〕（連結）",
                body_jp="自己株式の取得 1,000,000株",
            ),
            None,
            None,
        ),
        (
            "NEG . monthly sales",
            _make_disclosure(title_jp="2026年4月度 月次売上高に関するお知らせ"),
            None,
            None,
        ),
        (
            "NEG . stock split",
            _make_disclosure(title_jp="株式分割（普通株式1株につき2株）に関するお知らせ"),
            None,
            None,
        ),
        (
            "BUYBACK . non-universe -> no profile_url",
            _make_disclosure(
                title_jp="自己株式の取得に係る事項の決定に関するお知らせ",
                body_jp="発行済株式総数に対する割合 1.5% 取得価額の総額 2,000,000,000円",
                ticker="9999",
                name_jp="Random KK",
                name_en="Random KK",
            ),
            "BUYBACK",
            "Buyback",
        ),
        (
            "MBO . precedence over buyback",
            _make_disclosure(
                title_jp="公開買付けの開始及び自己株式の取得に係るお知らせ",
                body_jp="完全子会社化を目的とする公開買付け。",
                ticker="8888",
                name_en="X Holdings",
                name_jp="X Holdings",
            ),
            "MBO",
            "Tender offer",
        ),
        (
            "NEG . stock-option grant alone",
            _make_disclosure(
                title_jp="ストックオプションとしての新株予約権発行に関するお知らせ",
            ),
            None,
            None,
        ),
    ]

    passed = 0
    total = len(cases)
    for label, disc, expected_class, tag_sub in cases:
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
                exp_profile = f"/en/compounders/{tk}/" if _in_universe(tk) else None
                if result.get("profile_url") != exp_profile:
                    ok = False
                    reason = (
                        f"profile_url={result.get('profile_url')!r}, "
                        f"expected {exp_profile!r}"
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

