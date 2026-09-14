import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_PATH = path.join(ROOT, 'content', 'compounders', 'profile-data.json');
const SNAPSHOTS_PATH = path.join(ROOT, 'tools', 'compounder-hub-snapshots.json');
const SITEMAP_PATH = path.join(ROOT, 'sitemap.xml');
const data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
const snapshots = JSON.parse(fs.readFileSync(SNAPSHOTS_PATH, 'utf8'));
const snapshotsByTicker = new Map((snapshots.reports || []).map((report) => [report.ticker, report]));

function atomicWrite(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const temporary = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  const handle = fs.openSync(temporary, 'w');
  try {
    fs.writeFileSync(handle, content, 'utf8');
    fs.fsyncSync(handle);
  } finally {
    fs.closeSync(handle);
  }
  fs.renameSync(temporary, filePath);
}

function statusArticles(status) {
  return Object.values(data.articles || {})
    .filter((article) => article.slug === 'initiation' && article.publicationStatus === status)
    .sort((a, b) => (b.datePublished || '').localeCompare(a.datePublished || '') || a.ticker.localeCompare(b.ticker));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function displayDate(date, language) {
  const [year, month, day] = date.split('-').map(Number);
  if (language === 'ja') return `${year}年${month}月${day}日`;
  const monthName = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][month - 1];
  return `${monthName} ${day}, ${year}`;
}

function renderHubReportRow(article, language) {
  const report = snapshotsByTicker.get(article.ticker);
  if (!report) throw new Error(`Missing hub snapshot for current profile ${article.ticker}.`);
  const locale = language === 'en' ? 'EN' : 'JA';
  const display = report.hubDisplay?.[locale];
  if (!display) throw new Error(`Missing ${locale} hub display data for current profile ${article.ticker}.`);
  const company = data.companies?.[article.ticker];
  if (!company) throw new Error(`Missing company record for current profile ${article.ticker}.`);
  const prefix = language === 'en' ? '/en' : '';
  const labels = display.metricLabels || [];
  if (labels.length !== 4) throw new Error(`${locale} ${article.ticker}: hub row needs four metric labels.`);
  const market = String(company.securityLine?.[language] || '').split('·')[0].trim();
  const synopsis = company.description?.[language];
  const required = ['name', 'closeValue', 'marketCapValue', 'adtvValue', 'valuationValue', 'valuationContext', 'roceValue', 'roceContext'];
  for (const key of required) {
    if (!String(display[key] || '').trim()) throw new Error(`${locale} ${article.ticker}: hubDisplay.${key} is required.`);
  }
  if (!market || !synopsis) throw new Error(`${locale} ${article.ticker}: market and synopsis are required.`);
  const reportDate = displayDate(article.datePublished, language);
  const snapshotDate = displayDate(report.snapshotDate, language);
  const closeLine = language === 'en'
    ? `Last close · ${display.closeValue} · ${snapshotDate}`
    : `終値 ${display.closeValue}`;
  return `<a class="ch-report-row" href="${prefix}/compounders/${article.ticker}/initiation/" data-report-snapshot="${article.ticker}" data-snapshot-date="${report.snapshotDate}" data-market-cap-yen="${report.marketCapYen}" data-adtv60d-yen="${report.adtv60dYen}" data-roce-pct="${report.rocePct}" data-valuation-basis="${report.valuationBasis}" data-valuation-input="${report.valuationInput}" data-valuation-multiple="${report.valuationMultiple}">
  <span class="ch-report-copy">
    <span class="ch-report-meta"><time datetime="${article.datePublished}">${escapeHtml(reportDate)}</time><span>${escapeHtml(closeLine)}</span></span>
    <span class="ch-report-security"><strong>${escapeHtml(display.name)}</strong><span><b>${article.ticker}</b><i aria-hidden="true">·</i>${escapeHtml(market)}</span></span>
    <span class="ch-report-synopsis">${escapeHtml(synopsis)}</span>
  </span>
  <span class="ch-report-metrics">
    <span><small>${escapeHtml(labels[0])}</small><b>${escapeHtml(display.marketCapValue)}</b></span>
    <span><small>${escapeHtml(labels[1])}</small><b>${escapeHtml(display.adtvValue)}</b></span>
    <span class="ch-report-valuation"><small>${escapeHtml(labels[2])}</small><b>${escapeHtml(display.valuationValue)}</b><em>${escapeHtml(display.valuationContext)}</em></span>
    <span><small>${escapeHtml(labels[3])}</small><b>${escapeHtml(display.roceValue)}</b><em>${escapeHtml(display.roceContext)}</em></span>
  </span>
</a>`;
}

function extractCards(html) {
  const cards = new Map();
  for (const match of html.matchAll(/<a\b(?=[^>]*\bclass="[^"]*\bcard\b[^"]*")(?=[^>]*\bdata-ticker="([^"]+)")[^>]*>[\s\S]*?<\/a>/g)) {
    cards.set(match[1], match[0]);
  }
  return cards;
}

function replaceCards(html, tickers, cards) {
  const rendered = tickers.map((ticker) => {
    const card = cards.get(ticker);
    if (!card) throw new Error(`Missing gallery card for ${ticker}.`);
    return `      ${card.trim()}`;
  }).join('\n\n');
  const pattern = /<div class="grid" id="profile-grid">[\s\S]*?<\/div>\s*<div class="empty-state"/;
  if (!pattern.test(html)) throw new Error('Profile gallery grid boundary was not found.');
  return html.replace(pattern, `<div class="grid" id="profile-grid">\n\n${rendered}\n\n  </div>\n\n  <div class="empty-state"`);
}

function setControlsVisibility(html, visible) {
  return html.replace(/<div class="controls"(?: hidden)?/, `<div class="controls"${visible ? '' : ' hidden'}`);
}

function profileEntry(article, language) {
  const prefix = language === 'en' ? '/en' : '';
  const pathName = `${prefix}/compounders/${article.ticker}/initiation/`;
  const counterpartPrefix = language === 'en' ? '' : '/en';
  const counterpart = `${counterpartPrefix}/compounders/${article.ticker}/initiation/`;
  const canonical = `https://jpinv.com${pathName}`;
  const ja = language === 'ja' ? canonical : `https://jpinv.com${counterpart}`;
  const en = language === 'en' ? canonical : `https://jpinv.com${counterpart}`;
  const lastmod = article.dateModified || article.datePublished || data.archive.archivedOn;
  return `  <url><loc>${canonical}</loc><lastmod>${lastmod}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority><xhtml:link rel="alternate" hreflang="ja" href="${ja}" /><xhtml:link rel="alternate" hreflang="en" href="${en}" /><xhtml:link rel="alternate" hreflang="x-default" href="${en}" /></url>`;
}

function archiveEntry(language) {
  const prefix = language === 'en' ? '/en' : '';
  const canonical = `https://jpinv.com${prefix}/compounders/archive/`;
  const ja = 'https://jpinv.com/compounders/archive/';
  const en = 'https://jpinv.com/en/compounders/archive/';
  return `  <url><loc>${canonical}</loc><lastmod>${data.archive.archivedOn}</lastmod><changefreq>yearly</changefreq><priority>0.4</priority><xhtml:link rel="alternate" hreflang="ja" href="${ja}" /><xhtml:link rel="alternate" hreflang="en" href="${en}" /><xhtml:link rel="alternate" hreflang="x-default" href="${en}" /></url>`;
}

function renderHubCurrentSection(language, reportArticles) {
  const isEn = language === 'en';
  const prefix = isEn ? '/en' : '';
  const body = reportArticles.length
    ? `<div class="ch-report-list" aria-live="polite">
${reportArticles.map((article) => renderHubReportRow(article, language)).join('\n')}
    </div>`
    : `<div class="ch-series-note">
      <span>${isEn ? 'CURRENT FORMAT · SINCE SEPTEMBER 2026' : '2026年9月以降のレポート'}</span>
      <h3>${isEn ? 'The current Compounder series begins with NJS.' : '銘柄レポートはNJSから掲載しています。'}</h3>
      <p>${isEn ? 'Earlier company research remains available as a dated, unmaintained record in the archive.' : 'それ以前の企業調査は、公開時点の記録としてアーカイブに保存しています。内容は更新していません。'}</p>
      <div><a href="${prefix}/compounders/profiles/">${isEn ? 'View current profiles' : '銘柄レポートを見る'}</a><a href="${prefix}/compounders/archive/">${isEn ? 'Browse archived research' : 'アーカイブ調査を見る'}</a></div>
    </div>
    <div class="ch-report-list" aria-live="polite"></div>`;
  return `<section class="ch-reports" id="reports" aria-labelledby="ch-reports-title">
  <div class="wrap">
    <header class="ch-section-title">
      <h2 id="ch-reports-title">${isEn ? 'Current profiles' : '銘柄レポート'}</h2>
      <a href="${prefix}/compounders/profiles/">${isEn ? 'Current library' : '銘柄レポート一覧'} <span aria-hidden="true">→</span></a>
    </header>
    ${body}
  </div>
</section>`;
}

const currentArticles = statusArticles('current');
const archivedArticles = statusArticles('archived');
const currentTickers = currentArticles.map((article) => article.ticker);
const archivedTickers = archivedArticles.map((article) => article.ticker);
const currentHubRows = currentArticles.slice(1, 6);
const allCards = new Map();

for (const language of ['ja', 'en']) {
  const prefix = language === 'en' ? 'en' : '';
  const currentPath = path.join(ROOT, prefix, 'compounders', 'profiles', 'index.html');
  const archivePath = path.join(ROOT, prefix, 'compounders', 'archive', 'index.html');
  const currentHtml = fs.readFileSync(currentPath, 'utf8');
  const archiveHtml = fs.readFileSync(archivePath, 'utf8');
  const localizedCards = new Map([...extractCards(archiveHtml), ...extractCards(currentHtml)]);
  for (const ticker of [...currentTickers, ...archivedTickers]) {
    if (!localizedCards.has(ticker)) throw new Error(`${language}: no gallery card found for ${ticker}.`);
  }
  atomicWrite(currentPath, setControlsVisibility(replaceCards(currentHtml, currentTickers, localizedCards), currentTickers.length > 1));
  atomicWrite(archivePath, replaceCards(archiveHtml, archivedTickers, localizedCards));
  const hubPath = path.join(ROOT, prefix, 'compounders', 'index.html');
  const hubHtml = fs.readFileSync(hubPath, 'utf8');
  const reportSection = /<section class="ch-reports" id="reports"[\s\S]*?<\/section>/;
  if (!reportSection.test(hubHtml)) throw new Error(`${language}: current-report section was not found.`);
  atomicWrite(hubPath, hubHtml.replace(reportSection, renderHubCurrentSection(language, currentHubRows)));
  allCards.set(language, localizedCards.size);
}

let sitemap = fs.readFileSync(SITEMAP_PATH, 'utf8');
const articleTickers = new Set(Object.values(data.articles || {}).map((article) => article.ticker));
sitemap = sitemap.replace(/\s*<url>[\s\S]*?<\/url>/g, (block) => {
  const location = block.match(/<loc>([^<]+)<\/loc>/)?.[1];
  if (!location) return block;
  if (/^https:\/\/jpinv\.com\/(?:en\/)?compounders\/archive\/$/.test(location)) return '';
  const profile = location.match(/^https:\/\/jpinv\.com\/(?:en\/)?compounders\/([^/]+)\/([^/]+)\/$/);
  if (profile && articleTickers.has(profile[1]) && profile[2] === 'initiation') return '';
  return block;
});
const sitemapCurrentArticles = Object.values(data.articles || {})
  .filter((article) => article.publicationStatus === 'current' && article.slug === 'initiation')
  .sort((a, b) => a.ticker.localeCompare(b.ticker));
const generatedEntries = [
  ...sitemapCurrentArticles.flatMap((article) => [profileEntry(article, 'ja'), profileEntry(article, 'en')]),
  archiveEntry('ja'),
  archiveEntry('en'),
].join('\n');
sitemap = sitemap.replace(/\s*<\/urlset>\s*$/, `\n${generatedEntries}\n</urlset>\n`);
atomicWrite(SITEMAP_PATH, sitemap);

console.log(`Compounder archive built: ${currentTickers.length} current and ${archivedTickers.length} archived bilingual profiles.`);
console.log(`Gallery cards available: JA ${allCards.get('ja')}; EN ${allCards.get('en')}.`);
