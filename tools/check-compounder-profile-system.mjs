import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderProfilePage } from './lib/compounder-profile-template.mjs';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_PATH = path.join(REPO, 'content', 'compounders', 'profile-data.json');
const PROFILE_CSS = fs.readFileSync(path.join(REPO, 'assets', 'compounder-profile.css'), 'utf8');
const data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
const failures = [];
const bodySources = new Set();
let pageCount = 0;
const requiredSemanticComponents = [
  'cat-meta', 'cat-num', 'cat-viz', 'cat-viz-bar-fill', 'cat-viz-bar-label',
  'cat-viz-bar-row', 'cat-viz-bar-track', 'cat-viz-bar-val', 'cat-viz-cap',
  'cat-viz-label', 'scn-delta', 'scn-driver-head', 'scn-drivers', 'scn-mult',
  'sotp', 'sotp-foot', 'sotp-head', 'sotp-name', 'sotp-row', 'share-head',
  'lead-grid', 'segment-snapshot', 'segment-snapshot-title', 'underwriting-table',
  'thesis-points', 'loop-num', 'margin-chart', 'margin-fill', 'margin-row',
  'margin-track', 'plan-comparison', 'plan-comparison-grid', 'plan-comparison-head',
  'capital-visual', 'ev-bar', 'balance-list', 'valuation-basis', 'valuation-matrix',
  'question-head', 'question-heading', 'question-index', 'question-body',
  'promise-chain', 'promise-step', 'price-cost-bridge', 'bridge-step',
  'divergence-card', 'divergence-grid', 'margin-history', 'margin-year',
  'revenue-bar', 'campus-visual', 'campus-numbers', 'utilization-ramp',
  'ramp-track', 'ramp-fill', 'ramp-marker', 'market-grid', 'market-facts',
  'ev-bridge', 'ev-piece', 'sotp-range', 'range-line', 'range-point',
  'current-marker', 'profile-table', 'watch-list'
];
const nonVisualClassHooks = new Set([
  'lbl', 'share-cp', 'share-em', 'share-x', 'new',
  'external-ai-profile-copy', 'explainer-fig'
]);

function exact(html, pattern) {
  return (html.match(pattern) || []).length;
}

function plain(value) {
  return value.replace(/<[^>]+>/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\s+/g, ' ').trim();
}

function fail(page, message) {
  failures.push(`${page}: ${message}`);
}

for (const language of ['ja', 'en']) {
  const root = path.join(REPO, language === 'en' ? 'en' : '', 'compounders');
  for (const tickerEntry of fs.readdirSync(root, { withFileTypes: true })) {
    if (!tickerEntry.isDirectory() || !/^\d{4}$/.test(tickerEntry.name)) continue;
    const ticker = tickerEntry.name;
    const tickerRoot = path.join(root, ticker);
    for (const articleEntry of fs.readdirSync(tickerRoot, { withFileTypes: true })) {
      if (!articleEntry.isDirectory()) continue;
      const slug = articleEntry.name;
      const file = path.join(tickerRoot, slug, 'index.html');
      if (!fs.existsSync(file)) continue;
      pageCount += 1;
      const page = path.relative(REPO, file).replaceAll('\\', '/');
      const html = fs.readFileSync(file, 'utf8');
      const article = data.articles[`${ticker}/${slug}`];
      const company = data.companies[ticker];
      if (!company) fail(page, 'missing company data');
      if (!article) fail(page, 'missing article data');
      const relativeBody = article?.body?.[language];
      const expectedBody = path.posix.join('content', 'compounders', 'articles', ticker, slug, `${language}.html`);
      const bodyFile = relativeBody ? path.join(REPO, relativeBody) : '';
      if (!relativeBody) fail(page, 'missing canonical content-source path');
      if (relativeBody && relativeBody !== expectedBody) fail(page, `content source must use the canonical path ${expectedBody}`);
      if (relativeBody && bodySources.has(relativeBody)) fail(page, `content source is reused by another page: ${relativeBody}`);
      if (relativeBody) bodySources.add(relativeBody);
      if (relativeBody && !fs.existsSync(bodyFile)) fail(page, `canonical content source does not exist: ${relativeBody}`);
      if (relativeBody && fs.existsSync(bodyFile)) {
        const bodyHtml = fs.readFileSync(bodyFile, 'utf8');
        if (/<(?:html|head|body|main|article|h1|style|script)\b/i.test(bodyHtml)) fail(page, 'content source contains shell, H1, style, or script markup');
        if (/\sstyle\s*=/i.test(bodyHtml)) fail(page, 'content source contains inline presentation');
        if (/△/.test(bodyHtml)) fail(page, 'uses the accounting triangle glyph instead of a true minus sign');
        for (const classMatch of bodyHtml.matchAll(/\bclass=["']([^"']+)["']/g)) {
          for (const className of classMatch[1].trim().split(/\s+/)) {
            if (!className || className.startsWith('cp-u-') || nonVisualClassHooks.has(className)) continue;
            if (!PROFILE_CSS.includes(`.${className}`)) fail(page, `content class ${className} has no canonical visual contract`);
          }
        }
        for (const match of bodyHtml.matchAll(/\bcp-u-([a-f0-9]{12})\b/g)) {
          if (!PROFILE_CSS.includes(`.cp-u-${match[1]}{`)) fail(page, `content utility cp-u-${match[1]} is missing from the canonical profile CSS`);
        }
        try {
          const expected = renderProfilePage({ ticker, slug, language, company, article }, bodyHtml);
          if (expected !== html) fail(page, 'published page is stale; rebuild from the canonical data and content source');
        } catch (error) {
          fail(page, `content source cannot be rendered: ${error.message}`);
        }
      }
      if (exact(html, /\/assets\/compounder-profile\.css(?:\?[^"']*)?/g) !== 1) fail(page, 'must load the canonical profile stylesheet exactly once');
      if (exact(html, /\/assets\/site\.css(?:\?[^"']*)?/g) !== 1) fail(page, 'must load the global JII stylesheet exactly once');
      if (/\/assets\/(?:profile|compounder-research|prestige-4290)\.css/.test(html)) fail(page, 'loads an obsolete profile stylesheet');
      if (/<style\b[^>]*id=["']v2-inflections["']/.test(html)) fail(page, 'contains a duplicated legacy component stylesheet');
      if (/<style\b/i.test(html)) fail(page, 'contains a page-local stylesheet instead of the canonical profile CSS');
      if (/\sstyle\s*=/i.test(html)) fail(page, 'contains inline presentation instead of the canonical profile CSS');
      if (exact(html, /\/assets\/compounder-profile\.js(?:\?[^"']*)?/g) !== 1) fail(page, 'must load the canonical profile script exactly once');
      if (exact(html, /\/assets\/share-bar\.js(?:\?[^"']*)?/g) !== 1) fail(page, 'must load the shared share-bar script exactly once');
      if (/\/assets\/compounder-research\.js/.test(html)) fail(page, 'loads the obsolete research script');
      if (exact(html, /\/assets\/nav\.js(?:\?[^"']*)?/g) !== 1) fail(page, 'must load shared navigation exactly once');
      if (/compounders-nav\.js|id=["']main-nav["']/.test(html)) fail(page, 'contains duplicated navigation');
      if (exact(html, /\/assets\/locale-switcher\.js(?:\?[^"']*)?/g) !== 1) fail(page, 'must load the shared locale switcher exactly once');
      const executableInline = (html.match(/<script\b(?![^>]*\bsrc=)[^>]*>[\s\S]*?<\/script>/gi) || []).filter((script) => {
        return !/\btype=["']application\/(?:ld\+json|json)["']/i.test(script);
      });
      if (executableInline.length) fail(page, 'contains page-local executable JavaScript');
      if (/class=["'][^"']*\breport-locale\b/.test(html)) fail(page, 'contains the redundant in-header language selector');
      if (!/<article\b[^>]*class=["']compounder-profile["'][^>]*data-compounder-profile=["']1["']/.test(html)) fail(page, 'missing canonical article root');
      if (/class=["'][^"']*\b(?:simple-profile|prestige-profile|research-profile)\b/.test(html)) fail(page, 'retains a page-generation variant class');
      if (exact(html, /<header\b[^>]*class=["']cp-profile-header["']/g) !== 1) fail(page, 'must render one canonical profile header');
      if (exact(html, /<h1\b/g) !== 1) fail(page, 'must contain exactly one H1');
      if (!/<h2\b/.test(html)) fail(page, 'contains no H2 research hierarchy');
      if (!new RegExp(`data-profile-ticker=["']${ticker}["']`).test(html)) fail(page, 'ticker route and page data disagree');
      if (!new RegExp(`data-profile-article=["']${slug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}["']`).test(html)) fail(page, 'article route and page data disagree');
      if (exact(html, /\bdata-compounder-chart\b/g) !== 1) fail(page, 'must contain exactly one canonical chart container');
      if (/\b(?:const|var)\s+CHART_DATA\s*=/.test(html)) fail(page, 'embeds duplicated chart data or chart runtime');
      const chartPath = article?.chartData;
      if (!chartPath) fail(page, 'article record has no chart-data path');
      if (chartPath && !html.includes(`data-chart-src="${chartPath}"`)) fail(page, 'chart container and article chart-data record disagree');
      if (chartPath) {
        const chartFile = path.join(REPO, chartPath.replace(/^\//, ''));
        if (!fs.existsSync(chartFile)) fail(page, `chart data does not exist: ${chartPath}`);
        else {
          try {
            const chart = JSON.parse(fs.readFileSync(chartFile, 'utf8'));
            for (const key of ['candles', 'topix_rebased', 'sma60', 'volume']) {
              if (!Array.isArray(chart[key]) || chart[key].length === 0) fail(page, `chart data is missing ${key}`);
            }
            if ('source' in chart || 'topix_source' in chart || 'built_by' in chart) fail(page, 'chart data exposes internal source or tool metadata');
            if ('peak' in chart || 'trough' in chart) fail(page, 'chart data uses ambiguous legacy marker names');
          } catch (error) {
            fail(page, `chart data is invalid JSON: ${error.message}`);
          }
        }
      }
      if (exact(html, /class=["'][^"']*\bshare-bar(?=\s|["'])/g) !== 1) fail(page, 'must contain exactly one shared share bar');
      const disclosureCount = exact(html, /class=["'][^"']*\bdisclaimer(?=\s|["'])/g)
        + exact(html, /class=["'][^"']*\bpublication-note(?=\s|["'])/g);
      if (disclosureCount !== 1) fail(page, 'must contain exactly one disclaimer or publication note');
      if (article?.title?.[language]) {
        const h1 = plain((html.match(/<h1\b[^>]*class=["']cp-profile-title["'][^>]*>([\s\S]*?)<\/h1>/i) || [,''])[1]);
        if (!h1) fail(page, 'profile title is empty');
      }
      if ((article?.metrics?.[language] || []).length < 3) fail(page, 'structured Key Metrics has fewer than three available fields');
      for (const image of html.match(/<img\b[^>]*>/gi) || []) {
        if (!/\balt=["'][^"']*["']/.test(image)) fail(page, 'image lacks alt text infrastructure');
      }
      if (exact(html, /<link\b[^>]*rel=["']canonical["']/g) !== 1) fail(page, 'canonical link count is not one');
      if (exact(html, /hreflang=["']en["']/g) !== 1 || exact(html, /hreflang=["']ja["']/g) !== 1) fail(page, 'bilingual alternate links are incomplete');
    }
  }
}

if (pageCount === 0) failures.push('No Compounder research pages found.');
if (pageCount % 2 !== 0) failures.push(`Expected bilingual pairs, found ${pageCount} pages.`);
if (pageCount !== Object.keys(data.articles || {}).length * 2) failures.push('Published profile count and structured article registry disagree.');
if (bodySources.size !== pageCount) failures.push('Canonical body sources are missing or reused.');
if (/!important/i.test(PROFILE_CSS)) failures.push('Canonical profile CSS contains !important.');
for (const component of requiredSemanticComponents) {
  if (!PROFILE_CSS.includes(`.${component}`)) failures.push(`Canonical profile CSS is missing the ${component} component contract.`);
}
for (const relative of ['en/compounders/index.html', 'en/compounders/profiles/index.html']) {
  const file = path.join(REPO, relative);
  const visibleText = plain(fs.readFileSync(file, 'utf8'));
  if (/(?:^|\W)Y(?=\d)/.test(visibleText)) failures.push(`${relative}: contains ASCII Y where a yen symbol is required.`);
}

if (failures.length) {
  console.error(`Compounder profile system: FAIL (${failures.length})`);
  failures.forEach((message) => console.error(`- ${message}`));
  process.exit(1);
}

console.log(`Compounder profile system: PASS (${pageCount} pages; ${pageCount / 2} bilingual article pairs).`);
