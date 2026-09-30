import fs from 'node:fs';
import path from 'node:path';

export function reportRows(data) {
  return Object.values(data.articles || {})
    .filter((article) => article.slug === 'initiation' && article.publicationStatus === 'current')
    .sort((a, b) => b.datePublished.localeCompare(a.datePublished) || a.ticker.localeCompare(b.ticker))
    .slice(0, 5)
    .map((article) => {
      const company = data.companies?.[article.ticker];
      if (!company?.name?.ja || !company?.name?.en || !/^\d{4}-\d{2}-\d{2}$/.test(article.datePublished)) {
        throw new Error(`Incomplete homepage report metadata for ${article.ticker}.`);
      }
      return {
        ticker: article.ticker, date: article.datePublished,
        name_jp: company.name.ja, href_jp: `/compounders/${article.ticker}/initiation/`,
        name_en: company.name.en, href_en: `/en/compounders/${article.ticker}/initiation/`,
      };
    });
}

function escapeHtml(value) {
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
}

export function renderReportRows(rows, language) {
  const en = language === 'en';
  return rows.map((row) => `<li><a href="${escapeHtml(en ? row.href_en : row.href_jp)}"><span class="nw-date">${row.date.replaceAll('-', '.')}</span><span class="nw-tag">${en ? 'Report' : '銘柄レポート'}</span><span class="nw-tx"><b>${row.ticker}</b> ${escapeHtml(en ? row.name_en : row.name_jp)}</span></a></li>`).join('');
}

export function homepageReportBlock(html) {
  const matches = [...html.matchAll(/<!--news-reports-->([\s\S]*?)<!--\/news-reports-->/g)];
  if (matches.length !== 1) throw new Error('Homepage must contain exactly one news-reports marker pair.');
  return matches[0][1];
}

function atomicWrite(file, content) {
  const temporary = `${file}.${process.pid}.tmp`;
  const handle = fs.openSync(temporary, 'w');
  try { fs.writeFileSync(handle, content, 'utf8'); fs.fsyncSync(handle); }
  finally { fs.closeSync(handle); }
  fs.renameSync(temporary, file);
}

export function buildHomepageReports(root, data) {
  const rows = reportRows(data);
  const newsFile = path.join(root, 'compounders/feed/data/news.json');
  const payload = JSON.parse(fs.readFileSync(newsFile, 'utf8'));
  const pages = [['index.html', 'ja'], ['en/index.html', 'en']].map(([relative, language]) => {
    const file = path.join(root, relative);
    const html = fs.readFileSync(file, 'utf8');
    homepageReportBlock(html);
    return [file, html.replace(/<!--news-reports-->[\s\S]*?<!--\/news-reports-->/,
      `<!--news-reports-->${renderReportRows(rows, language)}<!--/news-reports-->`)];
  });
  // The publication build refreshes its report list while retaining the other news tabs.
  payload.reports = rows;
  atomicWrite(newsFile, `${JSON.stringify(payload, null, 1)}\n`);
  for (const [file, html] of pages) atomicWrite(file, html);
  console.log(`Homepage report feed built: ${rows.map((row) => row.ticker).join(', ')} (JA + EN + news.json).`);
}
