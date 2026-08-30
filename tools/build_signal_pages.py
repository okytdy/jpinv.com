#!/usr/bin/env python3
"""
build_signal_pages.py -- Generate per-name capital-allocation SIGNAL LOG pages
(EN + JP) plus a bilingual signal-log index, from watchlist_signals.json.

These are STATIC, server-rendered pages: every signal is baked into the HTML,
so they do not depend on the feed's client-side JS. One page per watched name
that has >=1 signal. Output:
    compounders/signals/{tk}/index.html        (JP)
    en/compounders/signals/{tk}/index.html      (EN)
    compounders/signals/index.html              (JP index)
    en/compounders/signals/index.html           (EN index)
Run after watchlist_join.py.
"""
import json, os, html, datetime

from company_names import normalize_company_name_en

# The one navigation for jpinv.com. See assets/nav.js.
NAV_TAG = '<script src="/assets/nav.js?v=348fa48c4e" defer></script>'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "compounders", "feed", "data", "watchlist_signals.json")

INDUSTRY_EN = {
 "水産・農林業":"Fishery, Agriculture & Forestry","鉱業":"Mining","建設業":"Construction",
 "食料品":"Foods","繊維製品":"Textiles & Apparel","パルプ・紙":"Pulp & Paper","化学":"Chemicals",
 "医薬品":"Pharmaceutical","石油・石炭製品":"Oil & Coal Products","ゴム製品":"Rubber Products",
 "ガラス・土石製品":"Glass & Ceramics Products","鉄鋼":"Iron & Steel","非鉄金属":"Nonferrous Metals",
 "金属製品":"Metal Products","機械":"Machinery","電気機器":"Electric Appliances",
 "輸送用機器":"Transportation Equipment","精密機器":"Precision Instruments","その他製品":"Other Products",
 "電気・ガス業":"Electric Power & Gas","陸運業":"Land Transportation","海運業":"Marine Transportation",
 "空運業":"Air Transportation","倉庫・運輸関連業":"Warehousing & Harbor Transportation",
 "情報・通信業":"Information & Communication","卸売業":"Wholesale Trade","小売業":"Retail Trade",
 "銀行業":"Banks","証券・商品先物取引業":"Securities & Commodity Futures","保険業":"Insurance",
 "その他金融業":"Other Financing Business","不動産業":"Real Estate","サービス業":"Services",
}
def industry_en(jp): return INDUSTRY_EN.get((jp or "").strip(), (jp or "").strip())

def esc(s): return html.escape("" if s is None else str(s), quote=True)

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
 '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@200;300;400;500&family=Noto+Sans+JP:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">')

CSS = """
  :root { --ink:#1a2a4a; --ink-mid:#172641; --ink-soft:#304466; --rule:#d6dee8; --rule-soft:#e8edf3;
    --bg:#ffffff; --bg-mid:#f5f7fa; --bg-soft:#fafbfc; --text:#1f2937; --text-mid:#4a5566;
    --text-dim:#7a8290; --accent:#b08a4a; --accent-deep:#9a7838; --accent-soft:#f4eee4;
    --ok:#2f6f4f; --bad:#b91c1c;
    --serif:'Noto Serif JP','Yu Mincho',serif; --sans:'Noto Sans JP','Hiragino Kaku Gothic ProN',sans-serif;
    --mono:'DM Mono',monospace; --max:980px; }
  *,*::before,*::after { box-sizing:border-box; }
  html,body { margin:0; padding:0; background:var(--bg); color:var(--text); font-family:var(--sans); font-size:14px; line-height:1.6; }
  a { color:var(--ink-soft); text-decoration:none; } a:hover { color:var(--ink); }
  .wrap { max-width:var(--max); margin:0 auto; padding:0 28px; }
  .hero { padding:60px 0 28px; border-bottom:1px solid var(--rule); }
  .hero-brand { display:flex; align-items:center; gap:14px; margin-bottom:30px; }
  .hero-home-link { display:inline-flex; align-items:center; gap:14px; color:inherit; }
  .hero-brand .mark { font-family:var(--serif); font-size:28px; font-weight:300; color:var(--ink-mid); letter-spacing:0.04em; line-height:1; }
  .hero-brand .mark .pipe { color:var(--accent); font-weight:200; margin:0 4px; }
  .hero-brand .sub { font-family:var(--sans); font-size:12.5px; color:var(--ink-soft); letter-spacing:0.04em; line-height:1.4; }
  .hero-eyebrow { font-family:var(--mono); font-size:11px; letter-spacing:0.32em; color:var(--accent-deep); text-transform:uppercase; margin-bottom:14px; font-weight:500; }
  .hero h1 { font-family:var(--serif); font-size:clamp(1.6rem,3.4vw,2.3rem); font-weight:300; color:var(--ink-mid); margin:0 0 6px; letter-spacing:0.02em; line-height:1.3; }
  .hero .tk { font-family:var(--mono); color:var(--accent-deep); font-weight:500; }
  .hero .sub-line { font-size:13.5px; color:var(--text-mid); margin:8px 0 0; }
  .hero .sub-line b { color:var(--ink-mid); font-weight:500; }
  .meta-line { font-family:var(--mono); font-size:11.5px; letter-spacing:0.08em; color:var(--text-dim); text-transform:uppercase; margin:16px 0 0; }
  .meta-line b { color:var(--ink-soft); font-weight:500; }
  .actions { display:flex; gap:20px; flex-wrap:wrap; margin:20px 0 0; }
  .actions a { font-family:var(--mono); font-size:11px; letter-spacing:0.14em; text-transform:uppercase; color:var(--accent-deep); border-bottom:1px solid var(--accent); padding-bottom:2px; }
  .actions a:hover { color:var(--ink-mid); border-color:var(--ink-mid); }
  .siglist { padding:30px 0 44px; }
  .sig-card { border:1px solid var(--rule); border-left:3px solid var(--accent); background:var(--bg); padding:20px 22px; margin-bottom:16px; }
  .sig-card.published { border-left-color:var(--ink-mid); }
  .sig-head { display:flex; gap:14px; align-items:baseline; flex-wrap:wrap; margin-bottom:10px; }
  .sig-date { font-family:var(--mono); font-size:12px; color:var(--ink-soft); letter-spacing:0.04em; }
  .sig-chip { font-family:var(--mono); font-size:10px; letter-spacing:0.14em; text-transform:uppercase; padding:3px 8px; border:1px solid var(--accent); color:var(--accent-deep); background:var(--accent-soft); white-space:nowrap; }
  .sig-tag { font-family:var(--sans); font-size:14px; color:var(--ink-mid); font-weight:500; margin:0 0 8px; }
  .sig-sum { font-size:13px; line-height:1.75; color:var(--text); margin:0 0 8px; }
  .sig-sum-jp { font-family:var(--serif); }
  .sig-src { margin-top:12px; padding-top:10px; border-top:1px solid var(--rule-soft); }
  .sig-src a { font-family:var(--mono); font-size:10.5px; letter-spacing:0.14em; text-transform:uppercase; color:var(--accent-deep); border-bottom:1px solid var(--accent); padding-bottom:1px; }
  .empty { padding:40px 0; font-family:var(--serif); font-style:italic; color:var(--ink-soft); }
  /* index */
  .idx { padding:26px 0 44px; }
  .idx-row { display:flex; gap:16px; align-items:baseline; flex-wrap:wrap; padding:14px 4px; border-bottom:1px solid var(--rule-soft); }
  .idx-row:hover { background:var(--bg-soft); }
  .idx-date { font-family:var(--mono); font-size:11.5px; color:var(--text-dim); min-width:96px; }
  .idx-tk { font-family:var(--mono); font-weight:500; color:var(--accent-deep); border-bottom:1px solid var(--accent); }
  .idx-name { font-family:var(--serif); color:var(--ink-mid); flex:1; min-width:180px; }
  .idx-chip { font-family:var(--mono); font-size:9.5px; letter-spacing:0.12em; text-transform:uppercase; padding:2px 7px; border:1px solid var(--accent); color:var(--accent-deep); background:var(--accent-soft); }
  .idx-flags { font-family:var(--mono); font-size:10px; letter-spacing:0.1em; color:var(--text-dim); text-transform:uppercase; }
  .disclaimer { padding:48px 0 56px; background:var(--bg-soft); border-top:1px solid var(--rule); margin-top:32px; }
  .d-eyebrow { font-family:var(--mono); font-size:10.5px; letter-spacing:0.22em; color:var(--text-dim); text-transform:uppercase; font-weight:500; }
  .d-title { font-family:var(--serif); font-size:22px; font-weight:300; color:var(--ink-mid); margin:6px 0 16px; letter-spacing:0.03em; }
  .disclaimer-body { font-family:var(--sans); font-size:12px; color:var(--text-mid); line-height:2.0; max-width:1100px; }
  .disclaimer-body p { margin:0 0 12px; } .disclaimer-body b { color:var(--ink-mid); font-weight:500; }
  .d-jp-note,.d-en-note { font-size:11px; color:var(--text-dim); line-height:1.78; padding-top:10px; margin-top:14px; border-top:1px solid var(--rule); }
  .footer { padding:22px 0; border-top:1px solid var(--rule); background:var(--bg); font-size:12px; color:var(--text-dim); }
  .footer .wrap { display:flex; justify-content:space-between; flex-wrap:wrap; gap:20px; }
  .footer a { color:var(--ink-soft); border-bottom:1px solid var(--rule); padding-bottom:1px; }
  .footer-locale-switcher a.current { color:var(--ink-mid); }
  .skip-link { position:fixed; top:10px; left:10px; z-index:1000; transform:translateY(-150%); padding:10px 14px; background:var(--ink); color:#fff; border-radius:4px; }
  .skip-link:focus { transform:translateY(0); }
  @media (max-width:760px) { .wrap { padding:0 16px; } .hero { padding:40px 0 22px; } .idx-date{min-width:auto;} }
"""

DISC_JP = """<section class="disclaimer"><div class="wrap">
  <div class="disclaimer-head"><span class="d-eyebrow">重要なご注意 · Important Disclaimer</span>
  <h2 class="d-title">本資料は投資助言ではありません。</h2></div>
  <div class="disclaimer-body">
  <p><b>株式会社ジャパン・インベスター・インターフェース（以下「JII」）</b>はIRコンサルティング事業を行う会社であり、いかなる管轄においても投資助言業者、金融アドバイザー、証券会社、または証券業者として登録されていません。JIIは、日本の金融商品取引法に基づく<b>金融商品取引業者</b>ではなく、投資助言・代理業の登録も保有しておりません。JIIは、投資助言を行うものでも、特定の有価証券の取得・売却・保有を勧誘するものでもありません。</p>
  <p><b>JII Compoundersは、教育・調査を目的とする編集コンテンツです。</b>各銘柄レポートおよび本シグナルログは、日本の上場企業が公表している情報をもとに、その情報が市場でどのように受け止められてきたかを考察するものです。<b>掲載内容は、いかなる有価証券の取得・売却・保有を推奨、提案、勧誘するものではありません。</b></p>
  <p><b>ご利用にあたって。</b>記載情報は不完全であったり、古くなっていたり、誤りを含んでいたりする可能性があります。過去の株価推移は将来の成果を示すものではありません。投資判断にあたっては、資格を有する専門家にご相談ください。</p>
  <p><b>利益相反に関する開示。</b> JII、その役員および関係者は、JIIの調査レポートで取り上げる企業の有価証券を保有せず、売買も行いません。JIIが対象企業から有償で業務を受託している場合は、その事実を該当するレポートで開示します。JIIが公表する情報は情報提供を目的とするものであり、投資助言や特定の有価証券の売買を勧めるものではありません。</p>
  <p class="d-en-note" lang="en">Japan Investor Interface Co., Ltd. ("JII") is an investor-relations consultancy and is not registered as a Financial Instruments Business Operator under Japan's Financial Instruments and Exchange Act. JII does not provide investment advice. JII Compounders is an editorial publication for educational and research purposes. Nothing herein constitutes a recommendation. Consult qualified, licensed advisors before any investment decision.</p>
  </div></div></section>"""

DISC_EN = """<section class="disclaimer"><div class="wrap">
  <div class="disclaimer-head"><span class="d-eyebrow">Important Disclaimer · 重要なご注意</span>
  <h2 class="d-title">This is not investment advice.</h2></div>
  <div class="disclaimer-body">
  <p><b>Japan Investor Interface Co., Ltd. ("JII")</b> is an investor-relations (IR) consultancy. JII is <b>not</b> a registered investment advisor, financial advisor, broker-dealer, or securities firm in any jurisdiction, and is <b>not</b> registered as a Financial Instruments Business Operator (金融商品取引業者) under Japan's Financial Instruments and Exchange Act. JII does not provide investment advice or solicit the purchase, sale, or holding of any security.</p>
  <p><b>JII Compounders is an editorial publication.</b> Each profile and this signal log are analytical studies of how publicly disclosed information about Japanese listed companies has been received by the market, for educational and research purposes. <b>Nothing here constitutes a recommendation or solicitation to buy, sell, or hold any security.</b></p>
  <p><b>No reliance.</b> The information may be incomplete, out of date, or incorrect. Past price performance does not indicate future results. Before any investment, tax, accounting, or legal decision, consult qualified, licensed advisors and conduct your own due diligence based on the company's primary disclosures.</p>
  <p><b>Conflicts of interest.</b> JII, its officers, and related parties do not hold or trade securities of companies covered in JII research. If JII has a paid engagement with a company covered in a publication, that relationship is disclosed in the relevant publication. JII's publications are for informational purposes only and do not constitute investment advice or a recommendation to buy or sell any security.</p>
  <p class="d-jp-note" lang="ja">本資料は投資助言・代理業ではなく、特定の有価証券の売買の勧誘・推奨を目的とするものではありません。教育・研究を目的とした分析記事です。</p>
  </div></div></section>"""

def brand(lang):
    if lang == "ja":
        return ('<div class="hero-brand">'
          '<a class="hero-home-link" href="/compounders/" aria-label="JII Compoundersへ戻る">'
          '<span class="mark">J<span class="pipe">|</span>I</span>'
          '<span class="sub"><span lang="ja">株式会社ジャパン・インベスター・インターフェース</span><br>'
          '<span lang="en">Japan Investor Interface Co., Ltd.</span></span></a></div>')
    return ('<div class="hero-brand">'
      '<a class="hero-home-link" href="/en/compounders/" aria-label="Return to JII Compounders home">'
      '<span class="mark">J<span class="pipe">|</span>I</span>'
      '<span class="sub"><span lang="en">Japan Investor Interface Co., Ltd.</span><br>'
      '<span lang="ja">株式会社ジャパン・インベスター・インターフェース</span></span></a></div>')

def footer(lang, ja_path, en_path):
    if lang == "ja":
        return ('<footer class="footer"><div class="wrap">'
          '<span><a href="/compounders/methodology/#p6">このシグナルログについて</a> · '
          '<a href="/compounders/signals/">すべてのシグナル</a> · <a href="/compounders/">銘柄レポート</a></span>'
          '<span>Japan Investor Interface Co., Ltd.</span>'
          f'<span class="footer-locale-switcher">言語: <a href="{ja_path}" class="current" aria-current="page" lang="ja">JP</a> · '
          f'<a href="{en_path}" data-locale-route lang="en">EN</a></span></div></footer>')
    return ('<footer class="footer"><div class="wrap">'
      '<span><a href="/en/compounders/methodology/#p6">About this signal log</a> · '
      '<a href="/en/compounders/signals/">All signals</a> · <a href="/en/compounders/">Compounder Profiles</a></span>'
      '<span>Japan Investor Interface Co., Ltd.</span>'
      f'<span class="footer-locale-switcher">Language: <a href="{en_path}" class="current" aria-current="page" lang="en">EN</a> · '
      f'<a href="{ja_path}" data-locale-route lang="ja">JP</a></span></div></footer>')

def fmt_dt(ts, lang):
    if not ts: return ""
    d = ts[:10]
    hm = ts[11:16] if len(ts) >= 16 else ""
    return f"{d} · {hm} JST" if hm else d

def head(lang, title, desc, canon, alt_ja, alt_en, noindex=False):
    # noindex=True is used for the per-ticker signal pages only.
    #
    # Why: each per-ticker page is a filtered slice of /compounders/feed/. The unique
    # part of the page is 2-5 short disclosure summaries; the rest (nav, hero, the full
    # bilingual disclaimer, footer) is byte-identical across every ticker. Measured on
    # 2026-07-28, median pairwise text similarity between two such pages was 0.65 (EN)
    # and 0.73 (JA), and the median EN page carried 69 unique words out of 334.
    # Google therefore clustered all ~216 of them as duplicates, picked one member as
    # the cluster representative, and rejected the self-canonical on the rest. That is
    # what Search Console reported as "Duplicate, Google chose different canonical
    # than user" on https://jpinv.com/ (validation failed 2026-07-03, 07-18, 07-27).
    #
    # noindex,follow keeps the pages crawlable and keeps link equity flowing through to
    # the Compounder profiles, while removing them from the index deliberately instead
    # of having Google exclude them as an error. The indexable representation of the
    # same data stays /compounders/feed/ and /compounders/universe/.
    #
    # Do NOT set noindex on the /compounders/signals/ hub page - it is a real index page.
    htmltag = '<html lang="ja">' if lang == "ja" else '<html lang="en">'
    robots = '<meta name="robots" content="noindex,follow">\n' if noindex else ''
    return (f'<!DOCTYPE html>\n{htmltag}\n<head>\n<meta charset="UTF-8">\n'
      '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
      f'<title>{esc(title)}</title>\n<meta name="description" content="{esc(desc)}">\n'
      f'<meta property="og:title" content="{esc(title)}">\n'
      f'<meta property="og:description" content="{esc(desc)}">\n'
      f'<meta property="og:url" content="{esc(canon)}">\n'
      f'{robots}'
      f'<link rel="canonical" href="{esc(canon)}">\n'
      f'<link rel="alternate" hreflang="ja" href="{esc(alt_ja)}">\n'
      f'<link rel="alternate" hreflang="en" href="{esc(alt_en)}">\n'
      f'<link rel="alternate" hreflang="x-default" href="{esc(alt_ja)}">\n'
      '<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
      '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">\n'
      f'{FONTS}\n<style>{CSS}</style>\n'
      '<script src="/assets/locale-switcher.js" defer></script>\n</head>\n')

def sig_card(s, lang):
    chip = s["class_jp"] if lang == "ja" else s["class_en"]
    tag = s["tag_jp"] if lang == "ja" else s["tag_en"]
    cls = "ja" if lang == "ja" else "en"
    parts = ['<article class="sig-card">']
    parts.append('<div class="sig-head">')
    parts.append(f'<span class="sig-date">{esc(fmt_dt(s["ts"], lang))}</span>')
    parts.append(f'<span class="sig-chip">{esc(chip)}</span>')
    parts.append('</div>')
    if tag: parts.append(f'<p class="sig-tag">{esc(tag)}</p>')
    if lang == "ja":
        if s.get("summary_jp"): parts.append(f'<p class="sig-sum sig-sum-jp">{esc(s["summary_jp"])}</p>')
        elif s.get("summary_en"): parts.append(f'<p class="sig-sum" lang="en">{esc(s["summary_en"])}</p>')
    else:
        if s.get("summary_en"): parts.append(f'<p class="sig-sum">{esc(s["summary_en"])}</p>')
        elif s.get("summary_jp"): parts.append(f'<p class="sig-sum sig-sum-jp" lang="ja">{esc(s["summary_jp"])}</p>')
    if s.get("doc_url"):
        label = "原文開示を見る (TDnet) →" if lang == "ja" else "Source disclosure (TDnet) →"
        parts.append(f'<div class="sig-src"><a href="{esc(s["doc_url"])}" target="_blank" rel="noopener">{label}</a></div>')
    parts.append('</article>')
    return "".join(parts)

def name_page(n, lang):
    tk = n["ticker"]
    nm_en, nm_jp = normalize_company_name_en(n["name_en"], tk), n["name_jp"]
    canon = f"https://jpinv.com/{'en/' if lang=='en' else ''}compounders/signals/{tk}/"
    alt_ja = f"https://jpinv.com/compounders/signals/{tk}/"
    alt_en = f"https://jpinv.com/en/compounders/signals/{tk}/"
    cnt = n["signal_count"]; latest = n["latest"]["date"]
    if lang == "ja":
        title = f"{nm_jp}（{tk}）資本政策シグナルログ｜JII Compounders"
        desc = f"{nm_jp}（{tk}）の資本政策に関する開示（自社株買い・配当・消却・資本コスト経営等）の記録。直近{cnt}件、最新は{latest}。"
        h1 = f"{esc(nm_jp)} <span class='tk'>{esc(tk)}</span>"
        eyebrow = "JII COMPOUNDERS · 資本政策シグナルログ"
        subline = f"{esc(n['industry'])}" + (f" · 標準ユニバース" if n["in_universe"] else "")
        meta = f'<b>{cnt}</b> 件のシグナル · 最新 <b>{esc(latest)}</b>'
    else:
        title = f"{nm_en} ({tk}) — Capital-Allocation Signal Log | JII Compounders"
        desc = f"Record of {nm_en} ({tk}) capital-allocation disclosures (buybacks, dividends, cancellations, cost-of-capital). {cnt} on file, latest {latest}."
        h1 = f"{esc(nm_en)} <span class='tk'>({esc(tk)})</span>"
        eyebrow = "JII COMPOUNDERS · CAPITAL-ALLOCATION SIGNAL LOG"
        subline = f"{esc(industry_en(n['industry']))}" + (" · Standing universe" if n["in_universe"] else "")
        meta = f'<b>{cnt}</b> signals on file · latest <b>{esc(latest)}</b>'
    # action links
    acts = []
    if n["profile_exists"]:
        purl = f"/en/compounders/{tk}/initiation/" if lang == "en" else f"/compounders/{tk}/initiation/"
        acts.append(f'<a href="{purl}">{"JII Compounderレポートを読む →" if lang=="ja" else "Read the JII Compounder profile →"}</a>')
    feedurl = "/en/compounders/feed/" if lang == "en" else "/compounders/feed/"
    univurl = "/en/compounders/universe/" if lang == "en" else "/compounders/universe/"
    acts.append(f'<a href="{feedurl}">{"全社フィードで見る →" if lang=="ja" else "Open in the full feed →"}</a>')
    acts.append(f'<a href="{univurl}">{"← ユニバースに戻る" if lang=="ja" else "← Back to the universe"}</a>')
    # Per-ticker page: noindex,follow. See the comment on head() for the reasoning.
    body = [head(lang, title, desc, canon, alt_ja, alt_en, noindex=True)]
    body.append('<body>')
    body.append(f'<a class="skip-link" href="#main-content">{"本文へ移動" if lang=="ja" else "Skip to main content"}</a>')
    body.append('<main id="main-content" tabindex="-1"><div class="wrap"><header class="hero">')
    body.append(brand(lang))
    body.append(f'<div class="hero-eyebrow">{eyebrow}</div>')
    body.append(f'<h1>{h1}</h1>')
    body.append(f'<p class="sub-line">{subline}</p>')
    body.append(f'<p class="meta-line">{meta}</p>')
    body.append('<div class="actions">' + "".join(acts) + '</div>')
    body.append('</header></div>')
    body.append('<div class="wrap"><section class="siglist">')
    for s in n["signals"]:
        body.append(sig_card(s, lang))
    body.append('</section></div></main>')
    body.append(DISC_JP if lang == "ja" else DISC_EN)
    body.append(footer(lang, alt_ja, alt_en))
    body.append(NAV_TAG)
    body.append('</body></html>')
    return "\n".join(body)

def index_page(names, lang):
    canon = f"https://jpinv.com/{'en/' if lang=='en' else ''}compounders/signals/"
    alt_ja = "https://jpinv.com/compounders/signals/"
    alt_en = "https://jpinv.com/en/compounders/signals/"
    if lang == "ja":
        title = "資本政策シグナルログ｜JII Compounders"
        desc = "JIIウォッチリスト銘柄が公表した資本政策シグナル（自社株買い・配当・消却・資本コスト経営等）の一覧。銘柄ごとの記録にリンク。"
        eyebrow = "JII COMPOUNDERS · 資本政策シグナルログ"
        h1 = "資本政策シグナルログ"
        lede = "JIIが追う銘柄が公表した、マルチプル再評価につながりうる資本政策の開示を、銘柄ごとに記録しています。新しい順。銘柄名をクリックすると、その銘柄の全シグナル履歴に移動します。"
    else:
        title = "Capital-Allocation Signal Log | JII Compounders"
        desc = "Every capital-allocation signal disclosed by a JII watchlist name (buybacks, dividends, cancellations, cost-of-capital), linked to each name's record."
        eyebrow = "JII COMPOUNDERS · CAPITAL-ALLOCATION SIGNAL LOG"
        h1 = "Capital-Allocation Signal Log"
        lede = "Every multiple-relevant capital-allocation disclosure by a name we watch, recorded per company, newest first. Click a name for its full signal history."
    rows = []
    for n in names:
        l = n["latest"]
        chip = l["class_jp"] if lang == "ja" else l["class_en"]
        nm = n["name_jp"] if lang == "ja" else normalize_company_name_en(n["name_en"], n["ticker"])
        page = f"/en/compounders/signals/{n['ticker']}/" if lang == "en" else f"/compounders/signals/{n['ticker']}/"
        flags = []
        if n["in_universe"]: flags.append("UNIVERSE" if lang == "en" else "ユニバース")
        if n["profile_exists"]: flags.append("PROFILE" if lang == "en" else "レポート")
        cntlbl = f'{n["signal_count"]}' + ("件" if lang == "ja" else "")
        rows.append('<a class="idx-row" href="' + page + '">'
            f'<span class="idx-date">{esc(l["date"])}</span>'
            f'<span class="idx-tk">{esc(n["ticker"])}</span>'
            f'<span class="idx-name">{esc(nm)}</span>'
            f'<span class="idx-chip">{esc(chip)}</span>'
            f'<span class="idx-flags">{esc("  ".join(flags))} · {cntlbl}</span>'
            '</a>')
    body = [head(lang, title, desc, canon, alt_ja, alt_en), '<body>']
    body.append(f'<a class="skip-link" href="#main-content">{"本文へ移動" if lang=="ja" else "Skip to main content"}</a>')
    body.append('<main id="main-content" tabindex="-1"><div class="wrap"><header class="hero">')
    body.append(brand(lang))
    body.append(f'<div class="hero-eyebrow">{eyebrow}</div><h1>{esc(h1)}</h1>')
    body.append(f'<p class="sub-line">{esc(lede)}</p>')
    cnt_line = (f'<b>{len(names)}</b> 銘柄 · <b>{sum(n["signal_count"] for n in names)}</b> 件のシグナル'
                if lang == "ja" else
                f'<b>{len(names)}</b> names · <b>{sum(n["signal_count"] for n in names)}</b> signals on file')
    body.append(f'<p class="meta-line">{cnt_line}</p></header></div>')
    body.append('<div class="wrap"><section class="idx">' + "".join(rows) + '</section></div></main>')
    body.append(DISC_JP if lang == "ja" else DISC_EN)
    body.append(footer(lang, alt_ja, alt_en))
    body.append(NAV_TAG)
    body.append('</body></html>')
    return "\n".join(body)

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def main():
    payload = json.load(open(DATA, encoding="utf-8"))
    names = payload["names"]
    n_pages = 0
    for n in names:
        tk = n["ticker"]
        write(os.path.join(ROOT, "compounders", "signals", tk, "index.html"), name_page(n, "ja"))
        write(os.path.join(ROOT, "en", "compounders", "signals", tk, "index.html"), name_page(n, "en"))
        n_pages += 2
    write(os.path.join(ROOT, "compounders", "signals", "index.html"), index_page(names, "ja"))
    write(os.path.join(ROOT, "en", "compounders", "signals", "index.html"), index_page(names, "en"))
    n_pages += 2
    print(f"Generated {n_pages} pages for {len(names)} names (+2 index).")
    print(f"  sample JP: compounders/signals/2353/index.html")
    print(f"  sample EN: en/compounders/signals/2353/index.html")

if __name__ == "__main__":
    main()
