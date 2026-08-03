#!/usr/bin/env python3
"""
Build the human sitemap pages: /sitemap/ and /en/sitemap/.

This is the COMPLETE index. The footer sitemap that assets/nav.js renders is a
navigational summary and deliberately stops at section level; this page lists
every real page, including all 32 Compounder profiles and all 34 IR-training
lessons.

It reads the built site rather than a hand-kept list, so it cannot drift. Run it
after any ship that adds pages:

    python3 tools/build_sitemap_page.py

Redirect stubs (meta refresh) and noindex pages are skipped on purpose.
Created August 3, 2026.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAV_TAG = '<script src="/assets/nav.js?v=02757dad69" defer></script>'

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
REFRESH_RE = re.compile(r'http-equiv="refresh"', re.I)
NOINDEX_RE = re.compile(r'name="robots"[^>]*noindex', re.I)


def page_title(rel):
    """Return the cleaned title of a real page, or None if it is not one."""
    path = os.path.join(ROOT, rel, "index.html")
    if not os.path.exists(path):
        return None
    try:
        html = open(path, encoding="utf-8").read()
    except OSError:
        return None
    if len(html) < 1500 or REFRESH_RE.search(html) or NOINDEX_RE.search(html):
        return None
    m = TITLE_RE.search(html)
    if not m:
        return None
    title = re.sub(r"\s+", " ", m.group(1)).strip()
    # Titles are "{name}｜{descriptor} | JII" — keep the name only.
    title = re.split(r"[｜|]", title)[0].strip()
    return title or None


def children(prefix, depth=1):
    """Real pages exactly `depth` levels under prefix, sorted by path."""
    base = os.path.join(ROOT, prefix)
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        sub = os.path.join(base, name)
        if not os.path.isdir(sub):
            continue
        rel = f"{prefix}/{name}" if prefix else name
        t = page_title(rel)
        if t:
            out.append((("/" + rel + "/"), t))
    return out


def profiles(lang):
    p = "en/compounders" if lang == "en" else "compounders"
    out = []
    base = os.path.join(ROOT, p)
    if not os.path.isdir(base):
        return out
    for name in sorted(os.listdir(base)):
        if not re.fullmatch(r"[0-9]{4}[0-9A-Z]?", name):
            continue
        rel = f"{p}/{name}/initiation"
        t = page_title(rel)
        if t:
            out.append(("/" + rel + "/", t))
    return out


def build(lang):
    en = lang == "en"
    P = "/en" if en else ""
    S = "en/" if en else ""

    def L(ja, eng):
        return eng if en else ja

    svc = "en/services" if en else "サービス"
    gov = f"{S}governance"
    cmp_ = f"{S}compounders"

    groups = []

    # Services
    items = children(svc)
    if not en:
        t = page_title("特急翻訳")
        if t:
            items.append(("/特急翻訳/", t))
    groups.append((L("サービス", "Services"), f"{P}/services/" if en else "/サービス/", [("", items)]))

    # Research
    sect = []
    for rel, ja, eng in [
        (f"{cmp_}/profiles", "銘柄分析", "Profiles"),
        (f"{cmp_}/universe", "銘柄スクリーニング", "Universe"),
        (f"{cmp_}/methodology", "着眼点", "Methodology"),
        (f"{cmp_}/feed", "資本政策開示", "Capital actions"),
        (f"{cmp_}/active-investors", "大量保有報告", "5% filings"),
        (f"{cmp_}/signals", "シグナルログ", "Signal log"),
    ]:
        if page_title(rel):
            sect.append(("/" + rel + "/", L(ja, eng)))
    groups.append((L("銘柄レポート", "Research"), f"{P}/compounders/",
                   [(L("セクション", "Sections"), sect),
                    (L("銘柄分析一覧", "All profiles"), profiles(lang))]))

    # IR training
    themes = []
    for rel, ja, eng in [
        (f"{gov}/foundations", "改革の起源", "Origins of reform"),
        (f"{gov}/cg-code", "コードの時代", "The code era"),
        (f"{gov}/market-restructuring", "市場区分の見直し", "Market restructuring"),
        (f"{gov}/capital-efficiency", "資本効率革命", "Capital efficiency"),
        (f"{gov}/frontier", "最前線", "The frontier"),
    ]:
        if page_title(rel):
            themes.append((L(ja, eng), children(rel)))
    tb = page_title(f"{gov}/toolbox")
    if tb:
        themes.append((L("ツール", "Tools"), [("/" + gov + "/toolbox/", tb)]))
    groups.append((L("IR研修", "IR training"), f"{P}/governance/", themes))

    # Company
    co = []
    for row in ([
        ("en/company", "会社概要", "Company"), ("en/pricing", "料金", "Pricing"),
        ("en/contact", "お問い合わせ", "Contact"), ("en/faq", "よくある質問", "FAQ"),
        ("en/privacy", "プライバシーポリシー", "Privacy policy"),
    ] if en else [
        ("会社概要", "会社概要", ""), ("料金", "料金", ""), ("お問い合わせ", "お問い合わせ", ""),
        ("faq", "よくある質問", ""), ("articles", "考察記事", ""), ("privacy", "プライバシーポリシー", ""),
    ]):
        if page_title(row[0]):
            co.append(("/" + row[0] + "/", L(row[1], row[2] or row[1])))
    if not en:
        for href, t in children("articles"):
            co.append((href, t))
    groups.append((L("会社情報", "Company"), f"{P}/company/" if en else "/会社概要/", [("", co)]))

    total = sum(len(i) for _, _, gg in groups for _, i in gg)

    secs = []
    for head, head_href, blocks in groups:
        b = ""
        for sub, items in blocks:
            if not items:
                continue
            if sub:
                b += f'<h3 class="sm-sub">{sub}</h3>'
            b += '<ul class="sm-list">' + "".join(
                f'<li><a href="{h}">{t}</a></li>' for h, t in items) + "</ul>"
        secs.append(f'<section class="sm-sec"><h2><a href="{head_href}">{head}</a></h2>{b}</section>')

    title = L("サイトマップ", "Sitemap")
    desc = L("jpinv.com の全ページ一覧です。",
             "Every page on jpinv.com, listed in one place.")
    lead = L(f"jpinv.com に公開されているページを、セクションごとにすべて並べています（全 {total} ページ）。",
             f"Every published page on jpinv.com, grouped by section ({total} pages in total).")
    alt_ja, alt_en = "https://jpinv.com/sitemap/", "https://jpinv.com/en/sitemap/"

    html = f"""<!DOCTYPE html>
<html lang="{'en' if en else 'ja'}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}｜Japan Investor Interface Co., Ltd.</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{alt_en if en else alt_ja}">
<link rel="alternate" hreflang="ja" href="{alt_ja}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="alternate" hreflang="x-default" href="{alt_ja}">
<meta property="og:title" content="{title}｜Japan Investor Interface Co., Ltd.">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{alt_en if en else alt_ja}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://jpinv.com/og/jii-default.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500&family=Noto+Sans+JP:wght@300;400;500&family=DM+Mono:wght@400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
<style>
.sm-sec{{padding:0 0 40px}}
.sm-sec h2{{font-family:var(--serif);font-size:clamp(18px,2.1vw,23px);font-weight:300;color:var(--ink);
  padding-bottom:12px;margin-bottom:18px;border-bottom:1px solid var(--rule)}}
.sm-sec h2 a{{text-decoration:none}}
.sm-sec h2 a:hover{{text-decoration:underline}}
.sm-sub{{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--ink-soft);margin:20px 0 10px;font-weight:400}}
.sm-list{{list-style:none;margin:0 0 6px;padding:0;columns:2;column-gap:40px}}
.sm-list li{{break-inside:avoid;margin-bottom:8px;font-size:14px;line-height:1.6}}
.sm-list a{{color:var(--text);text-decoration:none;border-bottom:1px solid transparent}}
.sm-list a:hover{{color:var(--ink);border-bottom-color:var(--accent)}}
@media(max-width:700px){{.sm-list{{columns:1}}}}
</style>
</head>
<body>
<main id="main-content" tabindex="-1">
<section id="top"><div class="wrap">
<span class="label">{L('サイトマップ', 'Sitemap')}</span>
<h1 class="mincho-xl">{title}</h1>
<div class="rule-accent"></div>
<p class="lead">{lead}</p>
</div></section>
<section><div class="wrap">
{"".join(secs)}
</div></section>
</main>
{NAV_TAG}
</body>
</html>
"""
    out_dir = os.path.join(ROOT, "en", "sitemap") if en else os.path.join(ROOT, "sitemap")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    return total


if __name__ == "__main__":
    for lang in ("ja", "en"):
        n = build(lang)
        print(f"{lang}: wrote sitemap page with {n} links")
    print("Remember: rerun this after any ship that adds pages.")
