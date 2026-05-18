const fs = require('node:fs');
const path = require('node:path');

const rootDir = path.resolve(__dirname, '..');
const distDir = path.join(rootDir, 'dist');

const publicEntries = [
  'index.html',
  'index-ja.html',
  'index-en.html',
  'CNAME',
  'robots.txt',
  'sitemap.xml',
  'favicon.ico',
  'favicon.svg',
  'favicon-16x16.png',
  'favicon-32x32.png',
  'apple-touch-icon.png',
  'logo.svg',
  'assets',
  'og',
  'availability',
  'articles',
  'compounders',
  'en',
  'faq',
  'お問い合わせ',
  'サービス',
  '会社概要',
  '料金'
];

fs.rmSync(distDir, { recursive: true, force: true });
fs.mkdirSync(distDir, { recursive: true });

for (const entry of publicEntries) {
  const source = path.join(rootDir, entry);
  if (!fs.existsSync(source)) continue;

  fs.cpSync(source, path.join(distDir, entry), {
    recursive: true,
    errorOnExist: false,
    force: true
  });
}

console.log(`Built static site into ${path.relative(rootDir, distDir)}/`);
