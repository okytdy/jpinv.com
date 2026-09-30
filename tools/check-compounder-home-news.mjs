import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { reportRows, renderReportRows, homepageReportBlock } from './lib/compounder-home-news.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'content/compounders/profile-data.json'), 'utf8'));
const expected = reportRows(data);
const news = JSON.parse(fs.readFileSync(path.join(root, 'compounders/feed/data/news.json'), 'utf8'));
const errors = [];
const fields = ['ticker', 'date', 'name_jp', 'href_jp', 'name_en', 'href_en'];
if (JSON.stringify((news.reports || []).map((row) => fields.map((key) => row[key]))) !==
    JSON.stringify(expected.map((row) => fields.map((key) => row[key])))) {
  errors.push('news.json reports differ from the current publication registry.');
}
for (const [relative, language] of [['index.html', 'ja'], ['en/index.html', 'en']]) {
  const html = fs.readFileSync(path.join(root, relative), 'utf8');
  try {
    if (homepageReportBlock(html) !== renderReportRows(expected, language)) {
      errors.push(`${relative}: homepage report links, names, dates or order are stale. Run npm run build:compounder-profiles.`);
    }
  } catch (error) { errors.push(`${relative}: ${error.message}`); }
  for (const row of expected) {
    const relativePage = (language === 'en' ? row.href_en : row.href_jp).slice(1) + 'index.html';
    if (!fs.existsSync(path.join(root, relativePage))) errors.push(`${relative}: missing report target ${relativePage}.`);
  }
}
if (errors.length) {
  console.error(`HOMEPAGE COMPOUNDER FEED: FAIL\n${errors.map((error) => `- ${error}`).join('\n')}`);
  process.exit(1);
}
console.log(`HOMEPAGE COMPOUNDER FEED: PASS — ${expected.map((row) => row.ticker).join(', ')} in both homepages and news.json.`);
