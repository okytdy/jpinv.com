import fs from 'node:fs';
import path from 'node:path';

const origin = 'https://jpinv.com';
const esc = (s = '') => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const date = (iso, lang) => new Intl.DateTimeFormat(lang === 'ja' ? 'ja-JP' : 'en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${iso}T00:00:00Z`));

function shell(lang, route, title, description, body, noindex = false) {
  const prefix = lang === 'en' ? '/en' : '';
  return `<!DOCTYPE html>
<html lang="${lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} | JII</title><meta name="description" content="${esc(description)}">
${noindex ? '<meta name="robots" content="noindex,follow">' : ''}
<link rel="canonical" href="${origin}${prefix}/compounders/${route}">
<link rel="alternate" hreflang="ja" href="${origin}/compounders/${route}"><link rel="alternate" hreflang="en" href="${origin}/en/compounders/${route}"><link rel="alternate" hreflang="x-default" href="${origin}/en/compounders/${route}">
<meta property="og:title" content="${esc(title)} | JII"><meta property="og:description" content="${esc(description)}"><meta property="og:url" content="${origin}${prefix}/compounders/${route}"><meta property="og:type" content="website"><meta property="og:image" content="${origin}/og/jii-default${lang === 'en' ? '-en' : ''}.png">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500&family=Noto+Sans+JP:wght@400;500;600&family=DM+Mono&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css?v=20260831c"><link rel="stylesheet" href="/assets/research-archive.css?v=20261119"><script src="/assets/nav.js?v=retired20261119" defer></script><script src="/assets/locale-switcher.js" defer></script>
</head><body><main id="main-content" tabindex="-1">${body}</main><script src="/assets/research-archive.js?v=20261119" defer></script></body></html>\n`;
}

export function buildRetiredResearch(root, data) {
  if (data.retirement?.status !== 'retired') throw new Error('Research retirement is not configured.');
  const retired = data.retirement.retiredOn;
  const articles = Object.values(data.articles).sort((a, b) => b.datePublished.localeCompare(a.datePublished) || a.ticker.localeCompare(b.ticker));
  if (articles.some(a => a.publicationStatus !== 'archived')) throw new Error('A retired research series cannot have current articles.');
  const write = (relative, text) => { const file = path.join(root, relative); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, text); };
  for (const lang of ['ja', 'en']) {
    const en = lang === 'en';
    const prefix = en ? '/en' : '';
    const base = en ? 'en/compounders' : 'compounders';
    const title = en ? 'Research archive' : '調査レポート・アーカイブ';
    const description = en ? 'Previously published JII company research, preserved as dated records. These reports are no longer maintained.' : '過去に公開したJIIの企業調査を、公開時点の記録として保存しています。現在は更新していません。';
    const intro = `<header class="ra-head"><div class="wrap"><p class="ra-kicker">JAPAN INVESTOR INTERFACE</p><h1>${title}</h1><p>${description}</p></div></header>`;
    const note = en ? `JII Compounders, its methodology and screening universe were retired on ${date(retired, lang)}. The reports below reflect the information, prices and analysis available on their stated dates and do not describe JII’s current research approach.` : `JII Compoundersの調査方針とスクリーニング・銘柄一覧は、${date(retired, lang)}をもって公開・更新を終了しました。以下のレポートは、記載された日付時点の情報・株価・分析に基づくものであり、現在のJIIの調査方針を示すものではありません。`;
    const cards = articles.map(a => {
      const c = data.companies[a.ticker];
      return `<a class="ra-card card" data-ticker="${a.ticker}" data-date="${a.datePublished}" data-search="${esc(`${a.ticker} ${c.name.ja} ${c.name.en}`.toLowerCase())}" href="${prefix}/compounders/${a.ticker}/${a.slug}/"><div class="ra-card-meta"><span>${a.ticker}</span><span>${en ? 'Archived' : 'アーカイブ'}</span></div><h2>${esc(c.name[lang])}</h2><p class="ra-sector">${esc(c.securityLine?.[lang] || '')}</p><p class="ra-description">${esc(c.description?.[lang] || '')}</p><p class="ra-date">${en ? 'Published' : '公開日'} <time datetime="${a.datePublished}">${date(a.datePublished, lang)}</time></p></a>`;
    }).join('\n');
    const archiveBody = `${intro}<section class="ra-main"><div class="wrap"><aside class="ra-note">${note}</aside><div class="ra-tools"><label>${en ? 'Find a report' : 'レポートを探す'}<input id="archive-search" type="search" placeholder="${en ? 'Company or ticker' : '会社名・証券コード'}"></label><label>${en ? 'Sort' : '並べ替え'}<select id="archive-sort"><option value="latest">${en ? 'Publication date' : '公開日の新しい順'}</option><option value="ticker">${en ? 'Ticker' : '証券コード順'}</option></select></label><p id="archive-count" aria-live="polite">${articles.length} ${en ? 'reports' : '件'}</p></div><div class="ra-grid" id="archive-grid">${cards}</div><p id="archive-empty" hidden>${en ? 'No matching reports.' : '該当するレポートはありません。'}</p></div></section>`;
    write(`${base}/archive/index.html`, shell(lang, 'archive/', title, description, archiveBody));
    const landing = `${intro}<section class="ra-main"><div class="wrap ra-intro"><p>${note}</p><a class="btn btn-primary" href="${prefix}/compounders/archive/">${en ? `Browse ${articles.length} archived reports` : `${articles.length}件のアーカイブを見る`}</a><p class="ra-current">${en ? 'Current English research is published through' : '現在の英文調査は'} <a href="https://japaninterface.substack.com/">Japan Investor Interface on Substack</a>${en ? '.' : 'で公開しています。'}</p></div></section>`;
    write(`${base}/index.html`, shell(lang, '', title, description, landing));
    for (const route of ['profiles/', 'methodology/', 'universe/']) {
      const what = en ? { 'profiles/': 'Current profiles', 'methodology/': 'Research methodology', 'universe/': 'Screening universe and watchlist' }[route] : { 'profiles/': '現行の銘柄分析', 'methodology/': '調査方針', 'universe/': 'スクリーニング・銘柄一覧' }[route];
      const retiredTitle = en ? `${what} — retired` : `${what}の公開・更新は終了しました`;
      write(`${base}/${route}index.html`, shell(lang, route, retiredTitle, description, `<header class="ra-head"><div class="wrap"><p class="ra-kicker">JAPAN INVESTOR INTERFACE</p><h1>${retiredTitle}</h1></div></header><section class="ra-main"><div class="wrap ra-intro"><p>${note}</p><a class="btn btn-primary" href="${prefix}/compounders/archive/">${en ? 'Browse archived research' : '調査アーカイブを見る'}</a></div></section>`, true));
      if (!en && route === 'methodology/' && fs.existsSync(path.join(root, base, 'methodology/ja/index.html'))) {
        write(`${base}/methodology/ja/index.html`, fs.readFileSync(path.join(root, base, 'methodology/index.html'), 'utf8'));
      }
    }
    const signalsRoot = path.join(root, base, 'signals');
    const signalRoutes = ['signals/', ...fs.readdirSync(signalsRoot, { withFileTypes: true }).filter(p => p.isDirectory()).map(p => `signals/${p.name}/`)];
    for (const route of signalRoutes) {
      const title = en ? 'Watchlist signal log — retired' : '銘柄一覧の開示履歴は公開・更新を終了しました';
      const text = en ? 'The Compounders watchlist and its company signal logs were retired on 19 November 2026. Market-wide capital-allocation disclosures remain available in the news feed.' : 'Compoundersの銘柄一覧と銘柄別の開示履歴は、2026年11月19日をもって公開・更新を終了しました。市場全体の資本政策開示は、引き続きニュースフィードでご覧いただけます。';
      write(`${base}/${route}index.html`, shell(lang, route, title, text, `<header class="ra-head"><div class="wrap"><h1>${title}</h1></div></header><section class="ra-main"><div class="wrap ra-intro"><p>${text}</p><a class="btn btn-primary" href="${prefix}/compounders/feed/">${en ? 'Capital-allocation news' : '資本政策開示ニュースを見る'}</a></div></section>`, true));
    }
  }
  // Retired tools and individual historical reports are deliberately absent from the sitemap.
  let sitemap = fs.readFileSync(path.join(root, 'sitemap.xml'), 'utf8');
  sitemap = sitemap.replace(/\s*<url>[\s\S]*?<\/url>/g, block => {
    const loc = block.match(/<loc>([^<]+)<\/loc>/)?.[1] || '';
    return /\/compounders\/(?:methodology|profiles|universe|signals)(?:\/|$)/.test(loc) || /\/compounders\/\d{4}\//.test(loc) ? '' : block;
  });
  fs.writeFileSync(path.join(root, 'sitemap.xml'), sitemap);
  console.log(`Retired research built: ${articles.length} dated bilingual reports; methodology, universe and watchlist logs retired.`);
}
