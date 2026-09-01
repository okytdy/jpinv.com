import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const recentReportCount = 5;
const locales = [
  {
    name: 'EN',
    hub: 'en/compounders/index.html',
    profiles: 'en/compounders/profiles/index.html',
  },
  {
    name: 'JA',
    hub: 'compounders/index.html',
    profiles: 'compounders/profiles/index.html',
  },
];

function attributes(raw) {
  return Object.fromEntries(
    [...raw.matchAll(/([:\w-]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function anchors(html) {
  return [...html.matchAll(/<a\b([^>]*)>([\s\S]*?)<\/a>/g)].map((match) => ({
    attrs: attributes(match[1]),
    body: match[2],
  }));
}

function hasClass(anchor, className) {
  return (anchor.attrs.class || '').split(/\s+/).includes(className);
}

function readLocale(config) {
  const hub = fs.readFileSync(path.join(root, config.hub), 'utf8');
  const profiles = fs.readFileSync(path.join(root, config.profiles), 'utf8');
  const profileCards = anchors(profiles)
    .filter((anchor) => hasClass(anchor, 'card') && anchor.attrs['data-ticker'])
    .map((anchor) => ({
      ticker: anchor.attrs['data-ticker'],
      date: anchor.attrs['data-date'],
      href: anchor.attrs.href,
    }));
  const hero = anchors(hub).find((anchor) => hasClass(anchor, 'ch-read-link'));
  const heroDate = hub.match(/<div class="ch-lead-topline">[\s\S]*?<time datetime="([^"]+)"/);
  const reportRows = anchors(hub)
    .filter((anchor) => hasClass(anchor, 'ch-report-row'))
    .map((anchor) => ({
      ticker: anchor.attrs['data-report-snapshot'],
      date: anchor.body.match(/<time datetime="([^"]+)"/)?.[1],
      href: anchor.attrs.href,
    }));
  return {
    config,
    profileCards,
    hero: hero ? {href: hero.attrs.href, date: heroDate?.[1]} : null,
    reportRows,
  };
}

const results = locales.map(readLocale);
const errors = [];
for (const result of results) {
  const {name} = result.config;
  if (result.profileCards.length < recentReportCount + 1) {
    errors.push(`${name}: profile library has only ${result.profileCards.length} dated cards`);
    continue;
  }
  for (let index = 1; index < result.profileCards.length; index += 1) {
    if (result.profileCards[index - 1].date < result.profileCards[index].date) {
      errors.push(`${name}: profile cards are not in descending date order at ${result.profileCards[index].ticker}`);
      break;
    }
  }
  const latest = result.profileCards[0];
  if (!result.hero) {
    errors.push(`${name}: featured-report link or date is missing`);
  } else {
    if (result.hero.href !== latest.href) errors.push(`${name}: featured report is ${result.hero.href}; latest profile is ${latest.href}`);
    if (result.hero.date !== latest.date) errors.push(`${name}: featured date is ${result.hero.date}; latest profile date is ${latest.date}`);
  }
  if (result.reportRows.length !== recentReportCount) {
    errors.push(`${name}: expected ${recentReportCount} New reports rows, found ${result.reportRows.length}`);
  }
  const expectedRows = result.profileCards.slice(1, recentReportCount + 1);
  for (let index = 0; index < expectedRows.length; index += 1) {
    const expected = expectedRows[index];
    const actual = result.reportRows[index];
    if (!actual) continue;
    if (actual.href !== expected.href || actual.ticker !== expected.ticker || actual.date !== expected.date) {
      errors.push(
        `${name}: New reports row ${index + 1} is ${actual.ticker || '?'} ${actual.date || '?'} ${actual.href || '?'}; expected ${expected.ticker} ${expected.date} ${expected.href}`,
      );
    }
  }
  const visibleTickers = [latest.ticker, ...result.reportRows.map((row) => row.ticker)];
  if (new Set(visibleTickers).size !== visibleTickers.length) errors.push(`${name}: featured and New reports contain a duplicate ticker`);
}

const [en, ja] = results;
const enSequence = [en.profileCards[0], ...en.reportRows].map((entry) => `${entry?.ticker}:${entry?.date}`);
const jaSequence = [ja.profileCards[0], ...ja.reportRows].map((entry) => `${entry?.ticker}:${entry?.date}`);
if (JSON.stringify(enSequence) !== JSON.stringify(jaSequence)) {
  errors.push(`EN/JA featured and New reports sequences differ: ${enSequence.join(', ')} vs ${jaSequence.join(', ')}`);
}

if (errors.length) {
  console.error('COMPOUNDER HUB RECENCY: FAIL');
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`COMPOUNDER HUB RECENCY: PASS — featured ${en.profileCards[0].ticker}; New reports ${en.reportRows.map((row) => row.ticker).join(', ')}`);
