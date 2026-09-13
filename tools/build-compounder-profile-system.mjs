import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderProfilePage } from './lib/compounder-profile-template.mjs';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_PATH = path.join(REPO, 'content', 'compounders', 'profile-data.json');

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

if (!fs.existsSync(DATA_PATH)) throw new Error(`Missing ${DATA_PATH}`);
const data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
const entries = Object.entries(data.articles || {}).sort(([a], [b]) => a.localeCompare(b));
let pageCount = 0;

for (const [key, article] of entries) {
  const [ticker, slug] = key.split('/');
  const company = data.companies?.[ticker];
  if (!/^\d{4}$/.test(ticker) || !slug || !company) throw new Error(`Invalid or incomplete article record: ${key}`);
  for (const language of ['ja', 'en']) {
    const relativeBody = article.body?.[language];
    if (!relativeBody) throw new Error(`Missing canonical body source for ${key}/${language}.`);
    const bodyPath = path.join(REPO, relativeBody);
    if (!fs.existsSync(bodyPath)) throw new Error(`Missing canonical body file: ${relativeBody}`);
    const bodyHtml = fs.readFileSync(bodyPath, 'utf8');
    const page = { ticker, slug, language, company, article };
    const output = path.join(REPO, language === 'en' ? 'en' : '', 'compounders', ticker, slug, 'index.html');
    atomicWrite(output, renderProfilePage(page, bodyHtml));
    pageCount += 1;
  }
}

console.log(`Compounder profile system rendered ${pageCount} pages from ${entries.length} bilingual article records.`);
console.log(`Structured data: ${path.relative(REPO, DATA_PATH)}`);
