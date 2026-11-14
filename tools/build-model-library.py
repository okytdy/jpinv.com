#!/usr/bin/env python3
"""Build the English public model library from their ticker-sorted manifest.

Run after adding or updating an approved public model. Numerical model files
are owned by their verified research package, not this presentation generator.
"""
from pathlib import Path
import json,re,html
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'en/models/model-index.json').read_text(encoding='utf-8'))
esc=lambda value:html.escape(str(value),quote=True)
def ticker_key(model):
    return [(0,int(x)) if x.isdigit() else (1,x.upper()) for x in re.findall(r'\d+|\D+',model['ticker'])]
models=sorted(data['models'],key=ticker_key)
assert len({m['ticker'] for m in models})==len(models),'Duplicate model ticker'
for lang in ['en']:
    en=lang=='en';route='/en/models/' if en else '/models/'
    title='Forecast models' if en else '業績予想モデル'
    intro='The annual forecasts, key assumptions and source data behind our published research. Browse by ticker, open a concise overview or download the complete model.' if en else '公開レポートで用いた業績予想、主な前提、出典データを掲載しています。証券コード順に、モデルの概要と計算ファイルをご覧いただけます。'
    rows=[]
    for m in models:
        company=m['company_en']
        cutoff=('Research cutoff: ' if en else '調査基準日：')+m['as_of']
        desc=m['description_en']
        years=' / '.join(m['forecast_years'])
        overview='View model' if en else 'モデル概要（英語）'
        download='Download full model · ZIP' if en else '全データをダウンロード · ZIP'
        csv='Annual forecast table · CSV' if en else '年度別予想表 · CSV（英語）'
        article='Read the research article ↗' if en else 'レポートを読む（英語）↗'
        article_link='<p><a href="'+esc(m['article_url'])+'">'+article+'</a></p>' if m.get('article_url') else ''
        rows.append(f'<article class="ml-row" data-ticker="{esc(m["ticker"])}"><div class="ml-ticker">{esc(m["ticker"])}</div><div class="ml-company"><h2><a href="{esc(m["overview_url"])}">{esc(company)}</a></h2><p class="ml-meta">{esc(cutoff)}</p><p>{esc(desc)}</p><p class="ml-years">{esc(years)}</p>{article_link}</div><div class="ml-actions"><a href="{esc(m["overview_url"])}">{overview}</a><a href="{esc(m["full_model_url"])}" download>{download}</a><a class="ml-csv" href="{esc(m["annual_csv_url"])}" download>{csv}</a></div></article>')
    count=f'{len(models)} model'+('s' if len(models)!=1 else '') if en else f'{len(models)}件のモデル'
    order='Ticker · ascending' if en else '証券コード順'
    notes=('Each model is a dated JII estimate, distinct from company guidance. Its overview explains the reporting basis and the complete download retains assumptions, scenarios, sensitivities and calculation files. Forecasts are conditional and may differ from actual results.' if en else '各モデルは調査基準日時点のJII独自予想であり、会社予想とは区別しています。概要ページに計算基準を記載し、全データのダウンロードには前提、シナリオ、感応度分析、計算ファイルを含めています。予想は一定の前提に基づくもので、実績と異なる場合があります。')
    portfolio_link='<a href="/en/portfolio/">Model portfolio</a>'
    site_title=title+' | JII'
    out=f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{site_title}</title><meta name="description" content="{esc(intro)}"><meta property="og:title" content="{site_title}"><meta property="og:url" content="https://jpinv.com{route}"><link rel="canonical" href="https://jpinv.com{route}"><link rel="alternate" hreflang="en" href="https://jpinv.com/en/models/"><link rel="alternate" hreflang="x-default" href="https://jpinv.com/en/models/"><link rel="icon" href="/favicon.svg"><link rel="stylesheet" href="/assets/site.css?v=20260831c"><link rel="stylesheet" href="/assets/model-library.css?v=20261104"></head>
<body class="model-library"><a class="skip-link" href="#main-content">{'Skip to models' if en else 'モデル一覧へ'}</a><main id="main-content" class="ml-main"><header class="ml-header"><span class="ml-kicker">JII / {'Published research' if en else '公開リサーチ'}</span><h1>{title}</h1><p class="ml-intro">{intro}</p></header><div class="ml-toolbar"><span>{count}</span><span>{order}</span></div>{''.join(rows)}<p class="ml-notes">{notes}</p><p class="ml-notes">{portfolio_link}</p></main><script src="/assets/nav.js?v=e804627fe1" defer></script></body></html>'''
    p=ROOT/route.strip('/')/'index.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(out,encoding='utf-8')
    print(str(p.relative_to(ROOT))+f': {len(models)} model(s), numeric ticker order')
