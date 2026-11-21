import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'content/compounders/profile-data.json')));
const errors = [];
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const check = (ok, msg) => { if (!ok) errors.push(msg); };
check(data.retirement?.status === 'retired', 'Retirement authority is missing.');
check(Object.values(data.articles).every(a => a.publicationStatus === 'archived'), 'A report is still current.');
for (const prefix of ['', 'en/']) {
  const archive = read(`${prefix}compounders/archive/index.html`);
  const tickers = [...archive.matchAll(/class="ra-card card" data-ticker="(\d{4})"/g)].map(m => m[1]);
  check(tickers.length === Object.keys(data.articles).length && new Set(tickers).size === tickers.length, `${prefix}: missing or duplicate archived reports.`);
  check(!/EV\s*\/\s*(?:EBIT|営業利益)|class="kpi|Last close|終値|current profiles/i.test(archive), `${prefix}: stale valuation/current-coverage cards remain.`);
  for (const article of Object.values(data.articles)) {
    check(tickers.includes(article.ticker), `${prefix}: missing archive link ${article.ticker}.`);
    const page = read(`${prefix}compounders/${article.ticker}/${article.slug}/index.html`);
    check((page.match(/class="cp-archive-notice"/g) || []).length === 1, `${prefix}${article.ticker}: archive notice is missing/duplicated.`);
    check(page.includes('noindex,follow') && page.includes('data-publication-status="archived"'), `${prefix}${article.ticker}: incorrect historical status.`);
    check(!/current Compounder format|現行のCompounder Profile/.test(page), `${prefix}${article.ticker}: obsolete coverage promise remains.`);
    check(page.includes(article.datePublished), `${prefix}${article.ticker}: original publication date is missing.`);
  }
  for (const route of ['methodology', 'universe', 'profiles', 'signals']) {
    const page = read(`${prefix}compounders/${route}/index.html`);
    check(page.includes('noindex,follow') && !/<table\b|data-sec=|UNIVERSE ·/.test(page), `${prefix}${route}: obsolete active content remains.`);
  }
  const home = read(`${prefix}index.html`);
  check((home.match(/class="jh-slide"/g)||[]).length===4 && home.includes('class="jh-dots"'), `${prefix}: original four-slide carousel is missing.`);
  check(home.includes('class="jh-panel"') === !prefix, `${prefix}: disclosure panel must be Japanese-only.`);
  check(!/names watched|追跡銘柄|data-tab="reports"/.test(home), `${prefix}: retired homepage panel/report promotion remains.`);
  check(!home.includes('class="jh-people"'), `${prefix}: removed hero photograph has returned.`);
  check((home.includes('data-tab="capital"') && home.includes('data-tab="holdings"')) === !prefix, `${prefix}: news feeds must be Japanese-only.`);
  if (prefix) check(!home.includes('/en/compounders/feed/') && !home.includes('/en/compounders/active-investors/'), 'English homepage links to retired feeds.');
}
check(!/compounders\/(?:methodology|universe|profiles|signals)\//.test(read('assets/nav.js')), 'Retired links remain in shared navigation.');
check(!/watchlist_join|build_signal_pages/.test(read('.github/workflows/feed-refresh.yml')), 'The website schedule can regenerate retired outputs.');
check(read('assets/hero.js').includes('/hero.json'), 'Restored disclosure panel is disconnected.');
check(read('assets/hero.js').includes('/news.json'), 'Homepage news is no longer connected.');
check(JSON.parse(read('compounders/feed/data/news.json')).reports.length === 0, 'Archived reports remain in current news.');
const sitemap = read('sitemap.xml');
check(!/<loc>[^<]*\/compounders\/(?:methodology|universe|profiles|signals|\d{4})\//.test(sitemap), 'Retired pages remain in sitemap.xml.');
for (const file of ['_watchlist_v4_compounders.csv', 'compounders/feed/data/watchlist_signals.json']) check(!fs.existsSync(path.join(root, file)), `Retired public download remains: ${file}`);
if (errors.length) { console.error(errors.join('\n')); process.exit(1); }
console.log(`Compounders retirement: PASS (${Object.keys(data.articles).length} bilingual archived reports; homepage/news/schedules/navigation checked).`);
