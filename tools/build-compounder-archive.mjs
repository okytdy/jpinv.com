import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_PATH = path.join(ROOT, 'content', 'compounders', 'profile-data.json');
const SITEMAP_PATH = path.join(ROOT, 'sitemap.xml');
const data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));

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

function statusTickers(status) {
  return Object.values(data.articles || {})
    .filter((article) => article.slug === 'initiation' && article.publicationStatus === status)
    .sort((a, b) => (b.datePublished || '').localeCompare(a.datePublished || '') || a.ticker.localeCompare(b.ticker))
    .map((article) => article.ticker);
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

function renderHubCurrentSection(language) {
  const isEn = language === 'en';
  const prefix = isEn ? '/en' : '';
  return `<section class="ch-reports" id="reports" aria-labelledby="ch-reports-title">
  <div class="wrap">
    <header class="ch-section-title">
      <h2 id="ch-reports-title">${isEn ? 'Current profiles' : '現行の銘柄分析'}</h2>
      <a href="${prefix}/compounders/profiles/">${isEn ? 'Current library' : '現行版一覧'} <span aria-hidden="true">→</span></a>
    </header>
    <div class="ch-series-note">
      <span>${isEn ? 'CURRENT FORMAT · SINCE SEPTEMBER 2026' : '現行フォーマット · 2026年9月開始'}</span>
      <h3>${isEn ? 'The current Compounder series begins with NJS.' : '現行のCompounderシリーズはNJSから始まります。'}</h3>
      <p>${isEn ? 'Earlier company research remains available as a dated, unmaintained record in the archive.' : 'それ以前の企業調査は、公開時点の記録としてアーカイブに保存しています。内容は更新していません。'}</p>
      <div><a href="${prefix}/compounders/profiles/">${isEn ? 'View current profiles' : '現行の銘柄分析を見る'}</a><a href="${prefix}/compounders/archive/">${isEn ? 'Browse archived research' : 'アーカイブ調査を見る'}</a></div>
    </div>
    <div class="ch-report-list" aria-live="polite"></div>
  </div>
</section>`;
}

const currentTickers = statusTickers('current');
const archivedTickers = statusTickers('archived');
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
  atomicWrite(hubPath, hubHtml.replace(reportSection, renderHubCurrentSection(language)));
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
const currentArticles = Object.values(data.articles || {})
  .filter((article) => article.publicationStatus === 'current' && article.slug === 'initiation')
  .sort((a, b) => a.ticker.localeCompare(b.ticker));
const generatedEntries = [
  ...currentArticles.flatMap((article) => [profileEntry(article, 'ja'), profileEntry(article, 'en')]),
  archiveEntry('ja'),
  archiveEntry('en'),
].join('\n');
sitemap = sitemap.replace(/\s*<\/urlset>\s*$/, `\n${generatedEntries}\n</urlset>\n`);
atomicWrite(SITEMAP_PATH, sitemap);

console.log(`Compounder archive built: ${currentTickers.length} current and ${archivedTickers.length} archived bilingual profiles.`);
console.log(`Gallery cards available: JA ${allCards.get('ja')}; EN ${allCards.get('en')}.`);
