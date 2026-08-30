#!/usr/bin/env python3
"""
Write compounders/feed/data/hero.json — the small file the homepage hero reads.

WHY IT EXISTS. feed.json is 2.1MB. A homepage cannot fetch that. This writes a
few kilobytes: the newest capital-policy disclosures, already shortened to a
label and one line of detail, plus the counters the hero shows.

Run it after tools/feed_refresh.py and tools/watchlist_join.py, from the repo
root:

    python3 tools/build_hero_data.py

Created August 3, 2026.
"""
import datetime
import glob
import json
import os
import re
import sys  # read by the --no-bake check in main(); see the comment there

from company_names import normalize_company_name_en

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED = os.path.join(ROOT, "compounders", "feed", "data", "feed.json")
WATCH = os.path.join(ROOT, "compounders", "feed", "data", "watchlist_signals.json")
OUT = os.path.join(ROOT, "compounders", "feed", "data", "hero.json")

ROWS = 6
HOME_ROWS = 4

# Short labels. feed.json's tag_jp is a full descriptor and far too long for a
# chip, so the chip comes from the class instead.
LABELS = {
    "BUYBACK_INIT":  ("自社株買い",   "Buyback"),
    "BUYBACK_BLOCK": ("自社株買い",   "Buyback"),
    "BUYBACK_REV":   ("枠拡大",       "Buyback raised"),
    "DIV_HIKE":      ("増配",         "Dividend hike"),
    "DIV_POLICY":    ("配当方針",     "Dividend policy"),
    "MBO":           ("MBO",          "MBO"),
    "CANCEL":        ("消却",         "Cancellation"),
    "M_AND_A":       ("M&A",          "M&A"),
    "COC_UPDATE":    ("資本コスト",   "Cost of capital"),
    "COC_INITIAL":   ("資本コスト",   "Cost of capital"),
    "CROSS":         ("政策保有",     "Cross-holdings"),
}


def home_group(row):
    """Keep the Compounders front page useful when one event type dominates a day."""
    cls = str(row.get("class") or "").upper()
    if cls == "MBO" or "TOB" in cls:
        return "mbo"
    if cls.startswith("BUYBACK") or "CANCEL" in cls:
        return "buyback"
    if cls.startswith("DIV"):
        return "dividend"
    if cls.startswith("COC"):
        return "capital-cost"
    return cls or "other"


def _pct(value):
    """Format a structural percentage without inventing precision."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return (f"{number:.2f}").rstrip("0").rstrip(".")


def home_detail(row):
    """Return short, factual homepage copy from structural feed fields only."""
    cls = str(row.get("class") or "").upper()
    facts = row.get("key_facts") or {}
    pct = _pct(facts.get("pct_so"))
    if cls == "MBO" or "TOB" in cls:
        return "公開買付けの進捗", "Tender-offer update"
    if cls.startswith("BUYBACK"):
        if pct:
            return f"発行済株式の{pct}%を取得", f"Buyback covering {pct}% of shares"
        return "自己株式を取得", "Share buyback"
    if "CANCEL" in cls:
        return "自己株式を消却", "Share cancellation"
    if cls == "DIV_HIKE":
        return "配当を引き上げ", "Dividend increased"
    if cls == "DIV_POLICY":
        return "配当方針を変更", "Dividend policy changed"
    if cls.startswith("COC"):
        return "資本コストを意識した経営方針", "Plan addressing cost of capital"
    if cls == "CROSS":
        return "政策保有株式の方針を開示", "Cross-holding policy disclosed"
    return "資本政策を開示", "Capital-allocation disclosure"

"""
NO YEN FIGURES GO IN THIS FILE — deliberately, from August 3, 2026.

feed.json's amounts come from an LLM enrichment step and 30 of the 242 rows
where the figure can be cross-checked disagree with themselves: the Japanese
tag and key_facts differ, usually by exactly ten times, in both directions.
Marubeni's July 2026 buyback reads 1,000億円 in tag_jp and ¥10.0B in tag_en.
Resona, Alps Alpine, Toho, Ajinomoto and Coca-Cola Bottlers Japan all show the
same split. It is the 億 unit being mishandled.

The homepage is the most externally-facing page JII has, and a ten-times error
on a buyback an IR officer already knows would destroy exactly the credibility
this hero exists to build. So the hero shows the disclosure type, the company
and the date — all structural fields, none of them inferred — and sends the
reader to the feed for the numbers.

Restore figures here only after the enrichment bug is fixed and the archive is
re-checked. See the publication fact-gate in CLAUDE.md.
"""


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def bake(payload):
    """Write the same rows into the two homepages between HTML markers.

    The hero must never render an empty panel. Baking the rows in means the
    page is correct before any JavaScript runs, and the cron that refreshes
    the feed refreshes these too, so what is baked is at most one cron cycle
    behind what the fetch would return.
    """
    for path, lang in (("index.html", "jp"), (os.path.join("en", "index.html"), "en")):
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            continue
        html = open(full, encoding="utf-8").read()

        rows_html = "".join(
            '<li><span class="jh-date">{d}</span>'
            '<span class="jh-tag">{t}</span>'
            '<span class="jh-name"><span class="jh-tick">{k}</span>{n}</span></li>'.format(
                d=esc(r["date"][5:].replace("-", ".")),
                t=esc(r["label_en"] if lang == "en" else r["label_jp"]),
                k=esc(r["ticker"]),
                n=esc(normalize_company_name_en(r["name_en"], r["ticker"]) if lang == "en" else r["name_jp"]),
            )
            for r in payload["rows"]
        )

        c = payload["counts"]
        labels = ([("last30", "disclosures, 30 days"), ("watched", "names watched"),
                   ("profiles", "research profiles")] if lang == "en" else
                  [("last30", "開示件数・直近30日"), ("watched", "追跡銘柄"),
                   ("profiles", "銘柄レポート")])
        stats_html = "".join(
            "<span><b>{v:,}</b><span>{l}</span></span>".format(v=c.get(k, 0), l=esc(lab))
            for k, lab in labels
        )

        for marker, content in (("hero-rows", rows_html), ("hero-stats", stats_html)):
            html = re.sub(
                r"(<!--%s-->).*?(<!--/%s-->)" % (marker, marker),
                lambda m: m.group(1) + content + m.group(2),
                html, count=1, flags=re.S)

        open(full, "w", encoding="utf-8", newline="\n").write(html)
        print(f"  baked into {path}")


def main():
    feed = json.load(open(FEED, encoding="utf-8"))
    feed = [r for r in feed if r.get("ts")]
    feed.sort(key=lambda r: r["ts"], reverse=True)

    today = datetime.date.today()
    cutoff = (today - datetime.timedelta(days=30)).isoformat()
    last30 = sum(1 for r in feed if r["ts"][:10] >= cutoff)

    rows, seen = [], set()
    for r in feed:
        if r.get("signal_score", 0) < 2:
            continue
        if r.get("ticker") in seen:
            continue
        seen.add(r.get("ticker"))
        ja, en = LABELS.get(r.get("class"), ("資本政策", "Capital action"))
        rows.append({
            "date": r["ts"][:10],
            "ticker": r.get("ticker", ""),
            "name_jp": r.get("name_jp", ""),
            "name_en": normalize_company_name_en(r.get("name_en", "") or r.get("name_jp", ""), r.get("ticker", "")),
            "label_jp": ja,
            "label_en": en,
        })
        if len(rows) >= ROWS:
            break

    watched = 0
    if os.path.exists(WATCH):
        watched = json.load(open(WATCH, encoding="utf-8")).get("counts", {}).get("watched_union", 0)

    profiles = len(glob.glob(os.path.join(ROOT, "compounders", "[0-9]*", "initiation", "index.html")))

    home_rows, home_groups, home_tickers = [], set(), set()
    for r in feed:
        if r.get("signal_score", 0) < 1:
            continue
        group = home_group(r)
        ticker = r.get("ticker")
        if not ticker or ticker in home_tickers or group in home_groups:
            continue
        home_tickers.add(ticker)
        home_groups.add(group)
        ja, en = LABELS.get(r.get("class"), ("資本政策", "Capital action"))
        detail_jp, detail_en = home_detail(r)
        home_rows.append({
            "date": r["ts"][:10],
            "ticker": ticker,
            "name_jp": r.get("name_jp", ""),
            "name_en": normalize_company_name_en(r.get("name_en", "") or r.get("name_jp", ""), ticker),
            "source_url": r.get("doc_url", ""),
            "source_title_jp": r.get("doc_title_jp", ""),
            "source_title_en": r.get("doc_title_en", ""),
            "label_jp": ja,
            "label_en": en,
            "detail_jp": detail_jp,
            "detail_en": detail_en,
        })
        if len(home_rows) >= HOME_ROWS:
            break

    payload = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "since": feed[-1]["ts"][:10] if feed else "",
        "counts": {
            "last30": last30,
            "total": len(feed),
            "watched": watched,
            "profiles": profiles,
        },
        "rows": rows,
        "home_rows": home_rows,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    # --no-bake is for CI. The scheduled feed job stages only
    # compounders/feed/data/ and the signal pages, so anything baked into
    # index.html there is thrown away — and if it were staged instead, a bot
    # would be committing to a file Teddy edits by hand every 30 minutes,
    # which is how a stash/pop conflict across 382 files happens.
    if "--no-bake" not in sys.argv:
        bake(payload)

    size = os.path.getsize(OUT)
    print(f"hero.json written: {len(rows)} rows, {size:,} bytes")
    print(f"  last 30 days: {last30}   total since {payload['since']}: {len(feed)}")
    print(f"  watched: {watched}   profiles: {profiles}")
    for r in rows:
        print(f"  {r['date']}  {r['label_jp']:<10} {r['ticker']} {r['name_jp']}")


if __name__ == "__main__":
    main()
