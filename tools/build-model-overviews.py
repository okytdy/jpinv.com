#!/usr/bin/env python3
"""Presentation only: forecast -> <=150-word assumptions -> downloads.

Retains each existing annual table and every existing numerical/download file.
Public summaries are authored against the catalog's dated forecast authority;
this tool neither rebuilds forecasts nor advances their research cutoffs.
"""
from pathlib import Path
from urllib.parse import urljoin
import argparse
import hashlib
import html
import json
from datetime import date
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
esc = lambda value: html.escape(str(value), quote=True)


def bullet_html(text):
    label, separator, explanation = text.partition(': ')
    return f'<li><strong>{esc(label)}:</strong> {esc(explanation)}</li>' if separator else f'<li>{esc(text)}</li>'


def build(check=False):
    catalog = json.loads((ROOT / 'en/models/model-index.json').read_text('utf-8'))['models']
    summaries = json.loads((ROOT / 'en/models/public-summaries.json').read_text('utf-8'))['models']
    announcements = json.loads((ROOT / 'en/models/announcements.json').read_text('utf-8'))['models']
    assert set(summaries) == {m['ticker'] for m in catalog}, 'Every published model needs a summary'
    assert set(announcements) == set(summaries), 'Every model needs its next announcement'
    report = []
    for model in catalog:
        ticker = model['ticker']
        summary = summaries[ticker]
        event = announcements[ticker]
        upcoming = event['next_announcement']
        assert upcoming['source_url'].startswith('https://')
        assert upcoming['status'] in ['scheduled', 'expected']
        assert upcoming['period'] and upcoming['display_date'] and event['update_note']
        if upcoming.get('date'):
            assert date.fromisoformat(upcoming['date']) > max(date.fromisoformat(model['as_of']), date.fromisoformat(event['calendar_checked_on'])), f'{ticker}: next announcement has already passed'
        assert summary['forecast_authority_sha256'] == model['forecast_authority_sha256'], f'{ticker}: stale summary'
        if model.get('forecast_run_id'):
            assert summary.get('forecast_run_id') == model['forecast_run_id'], f'{ticker}: wrong run'
        words = len(' '.join(summary['bullets']).split())
        assert 0 < words <= 150, f'{ticker}: {words} assumption words (maximum 150)'
        assert len(summary['forecast_notes'].split()) <= 70, f'{ticker}: table notes are too long'
        page = ROOT / model['overview_url'].strip('/') / 'index.html'
        old = BeautifulSoup(page.read_text('utf-8'), 'html.parser')
        table = old.select_one('table.financials')
        assert table is not None, f'{ticker}: no annual forecast table'
        columns = [x.get_text(' ', strip=True) for x in table.select('thead th')][1:]
        assert columns == model['forecast_years'], f'{ticker}: wrong forecast years'
        notes = page.parent / 'downloads/supporting_notes.txt'
        # Preserve the complete former explanation and every source URL once.
        if not notes.exists():
            assert not check, f'{ticker}: supporting notes missing'
            main = old.find('main')
            links = '\n'.join(f'{a.get_text(" ", strip=True)}: {urljoin("https://jpinv.com" + model["overview_url"], a["href"])}' for a in main.select('a[href]'))
            notes.write_text(f'{model["company_en"]} ({ticker}) — supporting notes\nResearch cutoff: {model["as_of"]}\n\n{main.get_text(" ", strip=True)}\n\nLINKS AND SOURCES\n{links}\n', 'utf-8')
        annual = str(table)
        bullets = ''.join(bullet_html(x) for x in summary['bullets'])
        related = [next(m for m in catalog if m['ticker'] == t) for t in summary.get('related_models', [])]
        related_html = '<p class="related-models">Related models: ' + ' · '.join(f'<a href="{esc(m["overview_url"])}">{esc(m["company_en"])} ({m["ticker"]})</a>' for m in related) + '</p>' if related else ''
        article = f' · <a href="{esc(model["article_url"])}">Read the article ↗</a>' if model.get('article_url') else ''
        download_note = f'<p class="note">{esc(summary["download_note"])}</p>' if summary.get('download_note') else ''
        upcoming_html = f'<div class="next-announcement"><p><strong>Next announcement:</strong> <a href="{esc(upcoming["source_url"])}">{esc(upcoming["period"])} · {esc(upcoming["display_date"])}</a> <span>({upcoming["status"]})</span></p><p>{esc(event["update_note"])}</p></div>'
        pending = f'<p class="results-update-note">Latest results: {esc(event["latest_results"]["period"])} · {esc(event["latest_results"]["released_on"])}. The forecast below predates this release; an update is in progress.</p>' if event.get('needs_results_update') else ''
        title = f'{model["company_en"]} — JII forecast model'
        body = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(model['company_en'])} forecast, key assumptions and full model downloads."><link rel="canonical" href="https://jpinv.com{model['overview_url']}"><meta property="og:url" content="https://jpinv.com{model['overview_url']}"><link rel="icon" href="/favicon.svg"><link rel="stylesheet" href="/assets/forecast-model.css?v=20261114"></head>
<body class="jii-forecast-model" data-jii-language-fallback="/compounders/"><a class="skip-link" href="#main-content">Skip to model</a><main id="main-content">
<header><a class="back-to-library" href="/en/models/">← Forecast models</a><div class="titleline"><h1>{esc(model['company_en'])} <span>{ticker}</span></h1><p>JII forecast model</p></div><p class="date">Research cutoff: <time datetime="{model['as_of']}">{model['as_of']}</time>{article}</p>{upcoming_html}{pending}</header>
<section aria-labelledby="outlook" data-model-section="forecast"><h2 id="outlook">Forecast</h2><p class="caption">{esc(summary['caption'])}</p><div class="table-wrap" tabindex="0" role="region" aria-label="Annual base-case forecast">{annual}</div><p class="swipe">Swipe sideways to view all years →</p><p class="note">{esc(summary['forecast_notes'])}</p></section>
<section aria-labelledby="assumptions" data-model-section="assumptions"><h2 id="assumptions">Key Assumptions</h2><ul class="assumption-summary">{bullets}</ul></section>
<section aria-labelledby="downloads" data-model-section="downloads"><h2 id="downloads">Downloads</h2><a class="primary-download" href="{esc(model['full_model_url'])}" download><span>Download the complete model</span><span class="filetype">ZIP ↓</span></a><p class="download-caption">Model calculations, input data and supporting notes.</p><div class="download-options"><a href="{esc(model['annual_csv_url'])}" download>Annual forecasts · CSV</a><a href="{esc(summary['data_url'])}" download>Full dataset · JSON</a><a href="downloads/supporting_notes.txt" download>Supporting notes &amp; source links · TXT</a></div>{download_note}{related_html}</section>
<footer><b>Japan Investor Interface</b><span>Dated estimates. Actual outcomes may differ.</span></footer></main><script src="/assets/nav.js?v=e804627fe1" defer></script></body></html>'''
        if check:
            current = BeautifulSoup(page.read_text('utf-8'), 'html.parser')
            assert [x.get('data-model-section') for x in current.select('main > section')] == ['forecast', 'assumptions', 'downloads'], f'{ticker}: wrong reading order'
            assert [x.get_text(' ', strip=True) for x in current.select('.assumption-summary li')] == summary['bullets'], f'{ticker}: summary differs'
            assert current.select_one('#assumptions').get_text() == 'Key Assumptions'
            assert current.select_one('.next-announcement'), f'{ticker}: next announcement missing'
            assert len(current.select('table')) == 1 and not current.select('details'), f'{ticker}: supporting research leaked into overview'
            assert page.read_text('utf-8') == body, f'{ticker}: rebuild needed'
        else:
            page.write_text(body, 'utf-8')
        for link in BeautifulSoup(body, 'html.parser').select('a[download]'):
            href = link['href']
            target = ROOT / href.lstrip('/') if href.startswith('/') else page.parent / href
            assert target.is_file(), f'{ticker}: missing download {href}'
        table_cells = [[x.get_text(' ', strip=True) for x in row.select('th,td')] for row in table.select('tr')]
        report.append(dict(ticker=ticker, company=model['company_en'], assumption_words=words, research_cutoff=model['as_of'], table_sha256=hashlib.sha256(json.dumps(table_cells, ensure_ascii=False).encode()).hexdigest(), url='https://jpinv.com' + model['overview_url']))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    print(json.dumps(build(args.check), ensure_ascii=True, indent=2))
