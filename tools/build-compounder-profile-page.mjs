import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { renderProfilePage } from './lib/compounder-profile-template.mjs';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA_PATH = path.join(REPO, 'content', 'compounders', 'profile-data.json');

function argument(name) {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : '';
}

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

const ticker = argument('ticker');
const slug = argument('slug') || 'initiation';
const language = argument('lang');
const bodyPath = argument('body');

if (!/^\d{4}$/.test(ticker) || !['en', 'ja'].includes(language) || !bodyPath) {
  throw new Error('Usage: node tools/build-compounder-profile-page.mjs --ticker 1234 --slug initiation --lang en|ja --body path/to/body.html');
}
if (!fs.existsSync(DATA_PATH)) throw new Error(`Missing ${DATA_PATH}`);
const data = JSON.parse(fs.readFileSync(DATA_PATH, 'utf8'));
const company = data.companies[ticker];
const article = data.articles[`${ticker}/${slug}`];
if (!company) throw new Error(`Add company data for ${ticker} to content/compounders/profile-data.json first.`);
if (!article) throw new Error(`Add article data for ${ticker}/${slug} to content/compounders/profile-data.json first.`);

const resolvedBody = path.resolve(process.cwd(), bodyPath);
const bodyHtml = `${fs.readFileSync(resolvedBody, 'utf8').trim()}\n`;
const page = { ticker, slug, language, company, article };
const relativeBody = path.posix.join('content', 'compounders', 'articles', ticker, slug, `${language}.html`);
const canonicalBody = path.join(REPO, relativeBody);
const output = path.join(REPO, language === 'en' ? 'en' : '', 'compounders', ticker, slug, 'index.html');
const rendered = renderProfilePage(page, bodyHtml);
article.body ||= {};
article.body[language] = relativeBody;
atomicWrite(canonicalBody, bodyHtml);
atomicWrite(DATA_PATH, `${JSON.stringify(data, null, 2)}\n`);
atomicWrite(output, rendered);
console.log(`Built ${path.relative(REPO, output)} and stored its canonical body at ${relativeBody}.`);
