#!/usr/bin/env python3
"""
Active Investors in Japan — 12-month ACTIVE-FUND ROSTER.

Reads the filer tally built by rank_filers.py (.filer_tally.json — every
large-shareholding filer over the scanned window) and emits
compounders/active-investors/data/roster.json: every ACTIVE investor — activist
funds, engaged funds, foreign active managers — with at least one 5% filing in
the window. Sell-side (brokers/banks/trust/insurers), domestic passive AMs,
index giants, operating companies and individuals are excluded by heuristic;
config/roster_overrides.json corrects misclassifications. The 9 tracked
investors are always included (merged across their legal entities).
"""
from __future__ import annotations
import sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C
from build_data import DATA_DIR

TALLY = Path(__file__).resolve().parent / ".filer_tally.json"
OVERRIDES = C.CONFIG_DIR / "roster_overrides.json"
KABUTAN = "https://kabutan.jp/holder/lists/?edicode={code}"

# fund-style name markers (checked on the NFKC-normalized, lowercased name)
FUND_HINTS = ("キャピタル", "ファンド", "パートナーズ", "インベスト", "インベスター",
              "アセット", "アドバイザ", "マネジメント", "マネージメント", "投資",
              "capital", "fund", "partner", "invest", "advis", "asset",
              "management", "value", "llc", "l.p.", "pte", "sicav")
# sell-side / banks / insurers — never "active investors" in this sense
EXCL_KEYWORDS = ("証券", "銀行", "信託", "保険", "信金", "金庫", "共済", "農林中央")
# domestic passive AMs + index giants (mandate/index-driven 5% filings)
EXCL_PASSIVE = ("アセットマネジメントone", "野村アセットマネジメント", "大和アセットマネジメント",
                "三井住友dsアセットマネジメント", "三井住友トラスト・アセットマネジメント",
                "ニッセイアセットマネジメント", "りそなアセットマネジメント",
                "三菱ufjアセットマネジメント", "jpモルガン・アセット・マネジメント",
                "ゴールドマン・サックス・アセット・マネジメント", "ブラックロック",
                "ステート・ストリート", "バンガード", "ノルゲス・バンク", "アムンディ",
                "フィデリティ投信")  # the投信 arm files mandate-driven; FMR LLC (active) still passes


def norm(name: str) -> str:
    return unicodedata.normalize("NFKC", name or "").strip()


def is_active_fund(name_n: str, force_inc, force_exc) -> bool:
    low = name_n.lower()
    if any(k in name_n for k in force_exc) or any(k in low for k in (f.lower() for f in force_exc)):
        return False
    if any(k in name_n for k in force_inc) or any(k.lower() in low for k in force_inc):
        return True
    if any(k in name_n for k in EXCL_KEYWORDS):
        return False
    if any(k in low for k in EXCL_PASSIVE):
        return False
    return any(k in low for k in FUND_HINTS)


def main() -> int:
    tally = C.read_json(TALLY, {}) or {}
    filers = tally.get("filers", {})
    scanned = sorted(tally.get("scanned", []))
    if not filers:
        print("no tally — run rank_filers.py first", file=sys.stderr); return 2
    cfg = C.load_config()
    ov = C.read_json(OVERRIDES, {}) or {}
    finc = [norm(x) for x in ov.get("force_include", [])]
    fexc = [norm(x) for x in ov.get("force_exclude", [])]

    # tracked investors: alias-code -> investor (merge entities; always include)
    code2inv, inv_meta = {}, {}
    for inv in cfg["investors"]:
        # Roster = strictly active funds: keep activist / long-only investors,
        # drop strategic holders (operating companies) and passive institutions
        # even when they are on the curated cards.
        if inv.get("category") not in ("activist", "long_only"):
            continue
        inv_meta[inv["id"]] = inv
        for al in inv.get("aliases", []):
            if isinstance(al, dict) and al.get("edinet_code"):
                code2inv[al["edinet_code"].upper()] = inv["id"]

    tracked_rows: dict[str, dict] = {}
    rows = []
    for code, r in filers.items():
        name_n = norm(r.get("name", ""))
        iid = code2inv.get(str(code).upper())
        if iid:  # tracked: merge across entities
            t = tracked_rows.setdefault(iid, {"name": inv_meta[iid]["display_name"],
                                              "name_ja": inv_meta[iid].get("display_name_ja", ""),
                                              "tracked": bool(inv_meta[iid].get("homepage")), "investor_id": iid,
                                              "edinet_code": code, "total": 0, "new5": 0,
                                              "chg": 0, "last": ""})
            t["total"] += r.get("total", 0); t["new5"] += r.get("new5", 0)
            t["chg"] += r.get("chg", 0); t["last"] = max(t["last"], r.get("last", ""))
            continue
        if not is_active_fund(name_n, finc, fexc):
            continue
        rows.append({"name": name_n, "name_ja": name_n, "tracked": False,
                     "investor_id": None, "edinet_code": code,
                     "total": r.get("total", 0), "new5": r.get("new5", 0),
                     "chg": r.get("chg", 0), "last": r.get("last", ""),
                     "url": KABUTAN.format(code=code)})
    for t in tracked_rows.values():
        t["url"] = KABUTAN.format(code=t["edinet_code"])
        rows.append(t)
    rows.sort(key=lambda x: (x["total"], x["last"]), reverse=True)

    out = {"meta": {"generated_at": C.now_jst_iso(),
                    "window_start": scanned[0] if scanned else "",
                    "window_end": scanned[-1] if scanned else "",
                    "count": len(rows),
                    "tracked_count": sum(1 for x in rows if x["tracked"]),
                    "note": "Active funds (activist / engaged / foreign active managers) with >=1 large-shareholding filing in the window. Heuristic + roster_overrides.json."},
           "rows": rows}
    C.write_json(DATA_DIR / "roster.json", out)
    print(f"[roster] {len(rows)} active funds ({out['meta']['tracked_count']} tracked) "
          f"window {out['meta']['window_start']}..{out['meta']['window_end']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
