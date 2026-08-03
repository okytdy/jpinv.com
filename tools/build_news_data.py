#!/usr/bin/env python3
"""
Write compounders/feed/data/news.json — the three lists behind the homepage
news tabs — and bake the same rows into both homepages as the no-JavaScript
fallback.

THE TAB DECISION (August 3, 2026). There is no すべて tab. In the last 30
days the sources ran 297 capital-policy disclosures, 85 new 5% filings, and
11 JII reports; a merged tab would be 97% machine rows and would drown the
one list that is actually JII's own news. The default tab is 新着レポート.

NO YEN FIGURES — same rule as the hero, see build_hero_data.py. Percentages
on the 5% tab are allowed: current_holding_ratio is parsed structurally from
the EDINET filing CSV, not by the LLM enrichment tier that produced the 億
conversion errors.

CI runs this with --no-bake (it stages only compounders/feed/data/).

    python3 tools/build_news_data.py [--no-bake]
"""
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, "compounders", "feed", "data", "feed.json")
NEW5 = os.path.join(ROOT, "compounders", "active-investors", "data", "new5_feed.json")
OUT = os.path.join(ROOT, "compounders", "feed", "data", "news.json")
ROWS = 5

CAP_LABELS = {
    "BUYBACK_INIT": ("自社株買い", "Buyback"), "BUYBACK_BLOCK": ("自社株買い", "Buyback"),
    "BUYBACK_REV": ("枠拡大", "Buyback raised"), "DIV_HIKE": ("増配", "Dividend hike"),
    "DIV_POLICY": ("配当方針", "Dividend policy"), "MBO": ("MBO", "MBO"),
    "CANCEL": ("消却", "Cancellation"), "M_AND_A": ("M&A", "M&A"),
    "COC_UPDATE": ("資本コスト", "Cost of capital"), "COC_INITIAL": ("資本コスト", "Cost of capital"),
    "CROSS": ("政策保有", "Cross-holdings"),
}
MOVE_LABELS = {
    "new_5pct": ("新規5%", "New 5%"), "increase": ("買増し", "Increase"),
    "decrease": ("売却", "Decrease"), "exit": ("解消", "Exit"),
    "amendment": ("訂正", "Amendment"),
}


def reports():
    out = []
    for lang, path in (("ja", "compounders/profiles/index.html"),
                       ("en", "en/compounders/profiles/index.html")):
        html = open(os.path.join(ROOT, path), encoding="utf-8").read()
        cards = {}
        for m in re.finditer(
                r'<a class="card"[^>]*href="([^"]+)"[^>]*data-date="([0-9-]+)"[^>]*data-ticker="([^"]+)"'
                r'.*?<h3 class="card-name">([^<]+)</h3>', html, re.S):
            cards[m.group(3)] = {"href": m.group(1), "date": m.group(2),
                                 "name": m.group(4).strip()}
        for t, c in cards.items():
            row = next((r for r in out if r["ticker"] == t), None)
            if not row:
                row = {"ticker": t, "date": c["date"]}
                out.append(row)
            row["name_" + ("jp" if lang == "ja" else "en")] = c["name"]
            row["href_" + ("jp" if lang == "ja" else "en")] = c["href"]
    out.sort(key=lambda r: r["date"], reverse=True)
    return out[:ROWS]


def capital():
    feed = json.load(open(FEED, encoding="utf-8"))
    feed = [r for r in feed if r.get("ts")]
    feed.sort(key=lambda r: r["ts"], reverse=True)
    out, seen = [], set()
    for r in feed:
        if r.get("signal_score", 0) < 2 or r.get("ticker") in seen:
            continue
        seen.add(r.get("ticker"))
        ja, en = CAP_LABELS.get(r.get("class"), ("資本政策", "Capital action"))
        out.append({"date": r["ts"][:10], "ticker": r.get("ticker", ""),
                    "name_jp": r.get("name_jp", ""),
                    "name_en": r.get("name_en") or r.get("name_jp", ""),
                    "label_jp": ja, "label_en": en})
        if len(out) >= ROWS:
            break
    return out


def holdings():
    rows = json.load(open(NEW5, encoding="utf-8"))["rows"]
    rows = [r for r in rows if r.get("filing_date")]
    rows.sort(key=lambda r: r["filing_date"], reverse=True)
    out = []
    for r in rows[:ROWS]:
        ja, en = MOVE_LABELS.get(r.get("move_type"), ("大量保有", "Large holding"))
        pct = r.get("current_holding_ratio")
        out.append({"date": r["filing_date"], "ticker": r.get("issuer_code", ""),
                    "issuer_jp": r.get("issuer_name", ""),
                    "issuer_en": r.get("issuer_name_en") or r.get("issuer_name", ""),
                    "filer_en": r.get("filer_name_en") or r.get("filer_raw_name", ""),
                    "pct": round(pct, 2) if isinstance(pct, (int, float)) else None,
                    "label_jp": ja, "label_en": en})
    return out


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def short(d):
    p = str(d or "").split("-")
    return p[0] + "." + p[1] + "." + p[2] if len(p) == 3 else ""


def rows_html(payload, which, lang):
    en = lang == "en"
    L = []
    if which == "reports":
        for r in payload["reports"]:
            href = r.get("href_en" if en else "href_jp") or "#"
            name = r.get("name_en" if en else "name_jp") or r.get("name_jp", "")
            L.append('<li><a href="%s"><span class="nw-date">%s</span>'
                     '<span class="nw-tag">%s</span>'
                     '<span class="nw-tx"><b>%s</b> %s</span></a></li>'
                     % (esc(href), short(r["date"]),
                        "Report" if en else "銘柄レポート", esc(r["ticker"]), esc(name)))
    elif which == "capital":
        for r in payload["capital"]:
            L.append('<li><span class="nw-date">%s</span>'
                     '<span class="nw-tag">%s</span>'
                     '<span class="nw-tx"><b>%s</b> %s</span></li>'
                     % (short(r["date"]), esc(r["label_en" if en else "label_jp"]),
                        esc(r["ticker"]), esc(r["name_en" if en else "name_jp"])))
    else:
        for r in payload["holdings"]:
            pct = (" (%.2f%%)" % r["pct"]) if r.get("pct") is not None else ""
            tail = ("%s → %s %s%s" % (r["filer_en"], r["ticker"],
                    r["issuer_en" if en else "issuer_jp"], pct))
            L.append('<li><span class="nw-date">%s</span>'
                     '<span class="nw-tag">%s</span>'
                     '<span class="nw-tx">%s</span></li>'
                     % (short(r["date"]), esc(r["label_en" if en else "label_jp"]), esc(tail)))
    return "".join(L)


def bake(payload):
    for path, lang in (("index.html", "ja"), (os.path.join("en", "index.html"), "en")):
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            continue
        html = open(full, encoding="utf-8").read()
        for which in ("reports", "capital", "holdings"):
            html = re.sub(
                r"(<!--news-%s-->).*?(<!--/news-%s-->)" % (which, which),
                lambda m: m.group(1) + rows_html(payload, which, lang) + m.group(2),
                html, count=1, flags=re.S)
        open(full, "w", encoding="utf-8", newline="").write(html)
        print("  baked into", path)


def main():
    payload = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "reports": reports(), "capital": capital(), "holdings": holdings(),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("news.json: %d reports / %d capital / %d holdings, %s bytes"
          % (len(payload["reports"]), len(payload["capital"]),
             len(payload["holdings"]), format(os.path.getsize(OUT), ",")))
    if "--no-bake" not in sys.argv:
        bake(payload)


if __name__ == "__main__":
    main()
