import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'content', 'compounders', 'profile-data.json'), 'utf8'));
const failures = [];

function read(relative) {
  return fs.readFileSync(path.join(ROOT, relative), 'utf8');
}

function cardTickers(html) {
  return [...html.matchAll(/<a\b(?=[^>]*\bclass="[^"]*\bcard\b[^"]*")(?=[^>]*\bdata-ticker="([^"]+)")[^>]*>/g)].map((match) => match[1]);
}

function reportTickers(html) {
  return [...html.matchAll(/<a\b(?=[^>]*\bclass="[^"]*\bch-report-row\b[^"]*")(?=[^>]*\bdata-report-snapshot="([^"]+)")[^>]*>/g)].map((match) => match[1]);
}

const articles = Object.values(data.articles || {}).filter((article) => article.slug === 'initiation');
const current = articles.filter((article) => article.publicationStatus === 'current').map((article) => article.ticker).sort();
const archived = articles.filter((article) => article.publicationStatus === 'archived').map((article) => article.ticker).sort();

if (!data.archive?.currentFormatTicker || !data.archive?.currentFormatStart || !data.archive?.archivedOn) {
  failures.push('Archive configuration is incomplete.');
}
const currentByDate = articles
  .filter((article) => article.publicationStatus === 'current')
  .sort((a, b) => (a.datePublished || '').localeCompare(b.datePublished || '') || a.ticker.localeCompare(b.ticker));
if (!currentByDate.length || currentByDate[0].ticker !== data.archive.currentFormatTicker) {
  failures.push(`Current-format series begins with ${currentByDate[0]?.ticker || 'nothing'}; expected ${data.archive?.currentFormatTicker || 'configured ticker'}.`);
}
if (currentByDate[0]?.datePublished !== data.archive.currentFormatStart) {
  failures.push(`Current-format start is ${currentByDate[0]?.datePublished || 'missing'}; expected ${data.archive.currentFormatStart}.`);
}
for (const article of articles) {
  const expectedStatus = article.datePublished >= data.archive.currentFormatStart ? 'current' : 'archived';
  if (article.publicationStatus !== expectedStatus) {
    failures.push(`${article.ticker}: ${article.datePublished} is ${article.publicationStatus}; expected ${expectedStatus} from the current-format boundary.`);
  }
}
if (current.length + archived.length !== articles.length) failures.push('Every initiation article must be current or archived.');

for (const language of ['ja', 'en']) {
  const prefix = language === 'en' ? 'en/' : '';
  for (const article of articles) {
    const relative = `${prefix}compounders/${article.ticker}/initiation/index.html`;
    const html = read(relative);
    const isArchived = article.publicationStatus === 'archived';
    const noticeCount = (html.match(/class="cp-archive-notice"/g) || []).length;
    const noindexCount = (html.match(/<meta name="robots" content="noindex,follow">/g) || []).length;
    const status = html.match(/data-publication-status="([^"]+)"/)?.[1];
    if (status !== article.publicationStatus) failures.push(`${relative}: rendered status is ${status || 'missing'}.`);
    if (isArchived && noticeCount !== 1) failures.push(`${relative}: archived page must have one notice.`);
    if (isArchived && noindexCount !== 1) failures.push(`${relative}: archived page must be noindex,follow.`);
    if (!isArchived && noticeCount !== 0) failures.push(`${relative}: current page has an archive notice.`);
    if (!isArchived && noindexCount !== 0) failures.push(`${relative}: current page is noindex.`);
  }

  const currentPage = read(`${prefix}compounders/profiles/index.html`);
  const archivePage = read(`${prefix}compounders/archive/index.html`);
  const currentCards = cardTickers(currentPage).sort();
  const archiveCards = cardTickers(archivePage).sort();
  if (JSON.stringify(currentCards) !== JSON.stringify(current)) failures.push(`${language}: current gallery is ${currentCards.join(', ')}.`);
  if (JSON.stringify(archiveCards) !== JSON.stringify(archived)) failures.push(`${language}: archive gallery has ${archiveCards.length} of ${archived.length} profiles.`);
  const hiddenControls = /<div class="controls"[^>]*\bhidden\b/;
  if (current.length < 2 && !hiddenControls.test(currentPage)) failures.push(`${language}: single-profile gallery controls must be hidden.`);
  if (hiddenControls.test(archivePage)) failures.push(`${language}: archive gallery controls must remain available.`);
  if (/name="robots"[^>]*noindex/i.test(archivePage)) failures.push(`${language}: archive landing page must remain indexable.`);
  if (!archivePage.includes(`https://jpinv.com/${prefix}compounders/archive/`)) failures.push(`${language}: archive canonical is missing.`);

  const hub = read(`${prefix}compounders/index.html`);
  const rows = reportTickers(hub);
  if (rows.some((ticker) => !current.includes(ticker))) failures.push(`${language}: hub New reports contains archived tickers: ${rows.join(', ')}.`);
  const heroTicker = hub.match(/<article class="ch-lead"[^>]*data-report-snapshot="([^"]+)"/)?.[1];
  if (!current.includes(heroTicker)) failures.push(`${language}: hub hero ${heroTicker || 'missing'} is not current.`);
}

const sitemap = read('sitemap.xml');
const locations = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
if (new Set(locations).size !== locations.length) failures.push('sitemap.xml contains duplicate locations.');
for (const ticker of archived) {
  if (locations.some((location) => new RegExp(`/(?:en/)?compounders/${ticker}/initiation/$`).test(location))) {
    failures.push(`sitemap.xml: archived profile ${ticker} remains listed.`);
  }
}
for (const ticker of current) {
  for (const prefix of ['', 'en/']) {
    const wanted = `https://jpinv.com/${prefix}compounders/${ticker}/initiation/`;
    if (!locations.includes(wanted)) failures.push(`sitemap.xml: missing current profile ${wanted}.`);
  }
}
for (const prefix of ['', 'en/']) {
  const wanted = `https://jpinv.com/${prefix}compounders/archive/`;
  if (locations.filter((location) => location === wanted).length !== 1) failures.push(`sitemap.xml: archive landing must appear exactly once: ${wanted}.`);
}

if (failures.length) {
  console.error(`Compounder archive: FAIL (${failures.length})`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(`Compounder archive: PASS (${current.length} current; ${archived.length} archived; ${articles.length * 2} profile pages checked).`);
