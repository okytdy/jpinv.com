#!/usr/bin/env python3
"""
watchlist_join.py  --  Join the Capital-Allocation Inflection Feed to the JII watchlist.

Reads:
  _watchlist_v4_compounders.csv          (the 200-name screen: rank, stats, status)
  compounders/universe/index.html        (the standing universe the reader clicks)
  compounders/feed/data/by-ticker/*.json (per-ticker signal archives, already built)
  compounders/{ticker}/initiation/index.html  (profile existence)

Writes:
  compounders/feed/data/watchlist_signals.json
    -> single source of truth for: the post-close alert, the universe-page wiring,
       and the per-name signal pages. One entry per WATCHED ticker that has >=1 signal.

Run from repo root. Safe to run repeatedly (pure function of inputs).
"""
import csv, json, os, re, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(ROOT, "_watchlist_v4_compounders.csv")
UNIV = os.path.join(ROOT, "compounders", "universe", "index.html")
BT   = os.path.join(ROOT, "compounders", "feed", "data", "by-ticker")
OUT  = os.path.join(ROOT, "compounders", "feed", "data", "watchlist_signals.json")

# v2 class codes actually present in the data -> (EN label, JP label, chip group)
CLASS_META = {
    "BUYBACK_INIT":  ("Buyback",                          "自社株買い",            "BUYBACK"),
    "BUYBACK_BLOCK": ("Buyback (block / ASR)",            "自社株買い（市場外・ASR）", "BUYBACK"),
    "CANCEL":        ("Treasury cancellation",            "自己株消却",            "CANCEL"),
    "COC_INITIAL":   ("Cost-of-capital management (new)", "資本コスト経営（初回）",   "COC"),
    "COC_UPDATE":    ("Cost-of-capital management (upd.)","資本コスト経営（更新）",   "COC"),
    "DIV_HIKE":      ("Dividend increase",                "増配",                  "DIV"),
    "DIV_POLICY":    ("Dividend policy",                  "配当方針",              "DIV"),
    "CROSS":         ("Cross-shareholding reduction",     "政策保有株式の縮減",      "CROSS"),
    "MBO":           ("Take-private / tender offer",      "非公開化・TOB",          "MBO"),
    "M_AND_A":       ("M&A",                              "M&A",                  "MBO"),
    "INSIDER_REORG": ("Founder shareholding restructuring","創業者株式整理",         "OTHER"),
}
def cls_meta(c):
    return CLASS_META.get(c, (c or "Signal", c or "開示", "OTHER"))

def ticker_from_sec(sec):
    sec = (sec or "").strip()
    if len(sec) == 5:           # 24770 -> 2477 ; 137A0 -> 137A
        return sec[:-1]
    return sec

def load_screen():
    rows = {}
    with open(CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tk = ticker_from_sec(r.get("sec_code", ""))
            if not tk:
                continue
            def num(v):
                try: return float(v)
                except: return None
            rows[tk] = {
                "screen_rank": int(r["rank"]) if r.get("rank", "").strip().isdigit() else None,
                "name_en": r.get("name_en", "").strip().strip('"'),
                "name_jp": r.get("filer_name", "").strip().strip('"'),
                "industry": r.get("industry", "").strip(),
                "composite_score": num(r.get("composite_score")),
                "status": r.get("status", "").strip(),
                "published_url_csv": r.get("published_url", "").strip(),
            }
    return rows

def load_universe():
    """Return {ticker: jp_name} for the standing universe table (the clickable list)."""
    html = open(UNIV, encoding="utf-8").read()
    out = {}
    # rows look like: <td class="cell-tk">2477</td> ... <td class="cell-name">手間いらず株式会社</td>
    for m in re.finditer(r'cell-tk">(?:<a[^>]*>)?([0-9A-Z]{4})(?:</a>)?</td>\s*<td class="cell-name">([^<]*)</td>', html):
        out[m.group(1)] = m.group(2).strip()
    return out

def profile_exists(tk):
    return os.path.exists(os.path.join(ROOT, "compounders", tk, "initiation", "index.html"))

def main():
    # Preserve entries for tickers whose by-ticker file is unreadable in THIS environment
    # (OneDrive Files-On-Demand can serve a truncated/dehydrated copy in the sandbox). Without
    # this, a dehydrated file would be silently dropped from the watchlist. The cron (server-side,
    # fully hydrated) reads the real file and overrides the preserved entry.
    prior_names = {}
    if os.path.exists(OUT):
        try:
            for _n in json.load(open(OUT, encoding="utf-8")).get("names", []):
                prior_names[_n["ticker"]] = _n
        except Exception:
            pass
    screen = load_screen()
    universe = load_universe()
    watched = set(screen) | set(universe)   # union: anything we track

    names = []
    total_signals = 0
    for tk in sorted(watched):
        p = os.path.join(BT, f"{tk}.json")
        if not os.path.exists(p):
            continue
        try:
            arr = json.load(open(p, encoding="utf-8"))
        except Exception:
            if tk in prior_names:        # dehydrated/unreadable here -> keep last good entry
                names.append(prior_names[tk]); total_signals += prior_names[tk].get("signal_count", 0)
            continue
        if not arr:
            continue
        arr = sorted(arr, key=lambda s: s.get("ts", ""), reverse=True)
        sigs = []
        for s in arr:
            en, jp, grp = cls_meta(s.get("class"))
            sigs.append({
                "id": s.get("id"),
                "ts": s.get("ts", ""),
                "date": (s.get("ts", "") or "")[:10],
                "class": s.get("class"),
                "class_en": en, "class_jp": jp, "group": grp,
                "tag_en": s.get("tag_en") or s.get("tag") or "",
                "tag_jp": s.get("tag_jp") or s.get("tag") or "",
                "summary_en": s.get("summary_en", "") or "",
                "summary_jp": s.get("summary_jp", "") or "",
                "doc_url": s.get("doc_url", ""),
                "source": s.get("source", "TDnet"),
                "signal_score": s.get("signal_score"),
                "enriched": bool(s.get("has_translation")),
            })
        total_signals += len(sigs)
        sc = screen.get(tk, {})
        nm_en = sc.get("name_en") or (arr[0].get("name_en") or "").strip()
        nm_jp = universe.get(tk) or sc.get("name_jp") or (arr[0].get("name_jp") or "").strip()
        prof = profile_exists(tk)
        names.append({
            "ticker": tk,
            "name_en": nm_en,
            "name_jp": nm_jp,
            "industry": sc.get("industry", ""),
            "in_universe": tk in universe,
            "in_screen": tk in screen,
            "screen_rank": sc.get("screen_rank"),
            "composite_score": sc.get("composite_score"),
            "status": sc.get("status", ""),
            "profile_exists": prof,
            "profile_url": f"/en/compounders/{tk}/initiation/" if prof else None,
            "signal_page": f"/compounders/signals/{tk}/",
            "signal_page_en": f"/en/compounders/signals/{tk}/",
            "signal_count": len(sigs),
            "first_ts": sigs[-1]["ts"],
            "latest": sigs[0],
            "signals": sigs,
        })

    # newest signal first
    names.sort(key=lambda n: n["latest"]["ts"], reverse=True)

    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds"),
        "sources": {"screen_csv": os.path.basename(CSV), "universe_html": "compounders/universe/index.html"},
        "counts": {
            "screen_names": len(screen),
            "universe_names": len(universe),
            "watched_union": len(watched),
            "names_with_signals": len(names),
            "total_signals": total_signals,
        },
        "names": names,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # idempotent: only rewrite when the substantive content (names) changed,
    # so the 30-min cron does not churn on the generated_at timestamp alone.
    if os.path.exists(OUT):
        try:
            prev = json.load(open(OUT, encoding="utf-8"))
            if prev.get("names") == payload["names"]:
                print(f"UNCHANGED {os.path.relpath(OUT, ROOT)} (names identical; not rewritten)")
                _print_summary(screen, universe, watched, names, total_signals)
                return
        except Exception:
            pass
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"WROTE {os.path.relpath(OUT, ROOT)}")
    _print_summary(screen, universe, watched, names, total_signals)

def _print_summary(screen, universe, watched, names, total_signals):
    print(f"  screen={len(screen)}  universe={len(universe)}  watched(union)={len(watched)}")
    print(f"  names_with_signals={len(names)}  total_signals={total_signals}")
    print("  most-recent 6:")
    for n in names[:6]:
        flag = "U" if n["in_universe"] else " "
        prof = "P" if n["profile_exists"] else "."
        print(f"    {n['latest']['date']}  {n['ticker']:5} [{flag}{prof}] {n['latest']['class_en']:24} | {n['name_en'][:26]}")

if __name__ == "__main__":
    main()
