#!/usr/bin/env python3
"""
scrub_sample_signals.py -- Remove leftover EDINET-SAMPLE placeholder signals from the
per-ticker archives and index, and replace any now-empty name's signal page with a clean
"no signals on file" empty state. feed.json is NOT touched (its readable newest portion
contains zero samples; the placeholders were a by-ticker-only artifact).

A bad entry is any signal whose id starts with 'EDINET-SAMPLE' or whose id/doc_url
contains 'SAMPLE'. Run, then re-run watchlist_join.py + build_signal_pages.py.
"""
import json, os, glob, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BT   = os.path.join(ROOT, "compounders", "feed", "data", "by-ticker")
IDX  = os.path.join(ROOT, "compounders", "feed", "data", "index.json")
WLS  = os.path.join(ROOT, "compounders", "feed", "data", "watchlist_signals.json")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_signal_pages as bsp   # reuse the exact page chrome

def is_sample(s):
    sid = (s.get("id") or "")
    doc = (s.get("doc_url") or "")
    return sid.startswith("EDINET-SAMPLE") or "SAMPLE" in sid.upper() or "SAMPLE" in doc.upper()

# capture names (for empty-state pages) BEFORE the join drops these tickers
names = {}
try:
    for n in json.load(open(WLS, encoding="utf-8"))["names"]:
        names[n["ticker"]] = (n["name_en"], n["name_jp"])
except Exception:
    pass

removed = []          # (ticker, class, id)
emptied = []          # tickers now with zero real signals
for p in sorted(glob.glob(os.path.join(BT, "*.json"))):
    tk = os.path.basename(p)[:-5]
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue       # dehydrated/unreadable -> can't contain a sample we can see; skip
    bad = [s for s in d if is_sample(s)]
    if not bad:
        continue
    keep = [s for s in d if not is_sample(s)]
    for s in bad:
        removed.append((tk, s.get("class"), s.get("id")))
    with open(p, "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=2)
    if not keep:
        emptied.append(tk)

# index.json: drop the emptied tickers (defensive; recompute counts for any touched ones)
try:
    idx = json.load(open(IDX, encoding="utf-8"))
except Exception:
    idx = {}
for tk in emptied:
    idx.pop(tk, None)
with open(IDX, "w", encoding="utf-8") as f:
    json.dump(idx, f, ensure_ascii=False, indent=2)

# feed.json (public flat feed): scrub when readable. In this OneDrive sandbox the file is
# often dehydrated (truncated read) -> skip gracefully; the GitHub Actions cron runs this
# same script where feed.json is fully hydrated and scrubs it definitively.
FEED = os.path.join(ROOT, "compounders", "feed", "data", "feed.json")
try:
    fd = json.load(open(FEED, encoding="utf-8"))
    fkeep = [r for r in fd if not is_sample(r)]
    n_feed = len(fd) - len(fkeep)
    if n_feed:
        with open(FEED, "w", encoding="utf-8") as f:
            json.dump(fkeep, f, ensure_ascii=False, indent=2)
    print(f"feed.json: {'scrubbed ' + str(n_feed) + ' samples' if n_feed else 'no samples found'} (rows {len(fkeep)})")
except Exception as e:
    print(f"feed.json: SKIPPED here (unreadable - OneDrive-dehydrated); the cron will scrub it server-side [{type(e).__name__}]")

# Replace each emptied ticker's per-name signal page with a clean empty state (JA + EN),
# so a direct URL no longer serves the fake signal.
def empty_page(tk, lang):
    nm_en, nm_jp = names.get(tk, (tk, tk))
    canon = f"https://jpinv.com/{'en/' if lang=='en' else ''}compounders/signals/{tk}/"
    alt_ja = f"https://jpinv.com/compounders/signals/{tk}/"
    alt_en = f"https://jpinv.com/en/compounders/signals/{tk}/"
    if lang == "ja":
        title = f"{nm_jp}（{tk}）資本政策シグナルログ｜JII Compounders"
        desc  = f"{nm_jp}（{tk}）について、追跡期間内に該当する資本政策開示の記録はありません。"
        eyebrow = "JII COMPOUNDERS · 資本政策シグナルログ"
        h1 = f"{bsp.esc(nm_jp)} <span class='tk'>{bsp.esc(tk)}</span>"
        msg = "追跡期間内に、該当する資本政策（プリンシプル6）開示の記録はありません。該当する開示が出れば自動的にこのページに表示されます。"
    else:
        title = f"{nm_en} ({tk}) — Capital-Allocation Signal Log | JII Compounders"
        desc  = f"No capital-allocation disclosures on file for {nm_en} ({tk}) in the tracked window."
        eyebrow = "JII COMPOUNDERS · CAPITAL-ALLOCATION SIGNAL LOG"
        h1 = f"{bsp.esc(nm_en)} <span class='tk'>({bsp.esc(tk)})</span>"
        msg = "No capital-allocation (Principle-6) disclosures on file for this name in the tracked window. If one is disclosed, it will appear here automatically."
    parts = [bsp.head(lang, title, desc, canon, alt_ja, alt_en), "<body>",
        f'<a class="skip-link" href="#main-content">{"本文へ移動" if lang=="ja" else "Skip to main content"}</a>',
        '<main id="main-content" tabindex="-1"><div class="wrap"><header class="hero">',
        bsp.brand(lang), f'<div class="hero-eyebrow">{eyebrow}</div>', f"<h1>{h1}</h1>",
        "</header></div>",
        f'<div class="wrap"><section class="siglist"><p class="empty">{bsp.esc(msg)}</p></section></div></main>',
        bsp.DISC_JP if lang == "ja" else bsp.DISC_EN, bsp.footer(lang, alt_ja, alt_en), "</body></html>"]
    return "\n".join(parts)

for tk in emptied:
    for lang, rel in (("ja", f"compounders/signals/{tk}/index.html"),
                      ("en", f"en/compounders/signals/{tk}/index.html")):
        full = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(empty_page(tk, lang))

print(f"Removed {len(removed)} sample entries from {len(set(t for t,_,_ in removed))} tickers.")
print(f"Emptied (now zero real signals): {emptied}")
print("Per removed entry:")
for tk, cls, sid in removed:
    print(f"  {tk}  {cls:8}  {sid}")
