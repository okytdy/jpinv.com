import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = JSON.parse(fs.readFileSync(path.join(root, 'tools/compounder-hub-snapshots.json'), 'utf8'));
const expected = new Map(source.reports.map((report) => [report.ticker, report]));
const pages = [
  ['EN', 'en/compounders/index.html'],
  ['JA', 'compounders/index.html'],
];
const metricOrder = {
  EN: ['Market cap', '60D ADTV', 'Forward EV / EBIT', 'ROCE'],
  JA: ['時価総額', '60日平均売買代金', '予想 EV / EBIT', 'ROCE'],
};
const errors = [];

function attributes(raw) {
  return Object.fromEntries(
    [...raw.matchAll(/([:\w-]+)="([^"]*)"/g)].map((match) => [match[1], match[2]]),
  );
}

function snapshots(html) {
  return [...html.matchAll(/<(article|a)\b([^>]*data-report-snapshot="[^"]+"[^>]*)>([\s\S]*?)<\/\1>/g)]
    .map((match) => ({attrs: attributes(match[2]), body: match[3]}));
}

function sameNumber(name, actual, wanted, ticker, locale) {
  const value = Number(actual);
  if (!Number.isFinite(value) || Math.abs(value - wanted) > 0.5) {
    errors.push(`${locale} ${ticker}: ${name} is ${actual}; expected ${wanted}`);
  }
}

for (const report of source.reports) {
  if (report.snapshotDate > report.reportDate) {
    errors.push(`${report.ticker}: snapshot date ${report.snapshotDate} is after report date ${report.reportDate}`);
  }
  if (report.adtvSessions !== 60) {
    errors.push(`${report.ticker}: ADTV window has ${report.adtvSessions} sessions instead of 60`);
  }
  if (report.adtvWindowEnd !== report.snapshotDate) {
    errors.push(`${report.ticker}: ADTV window ends ${report.adtvWindowEnd}; expected snapshot date ${report.snapshotDate}`);
  }
}

const sequences = [];
for (const [locale, relativePath] of pages) {
  const html = fs.readFileSync(path.join(root, relativePath), 'utf8');
  const records = snapshots(html);
  const sequence = records.map((record) => record.attrs['data-report-snapshot']);
  sequences.push(sequence);
  if (records.length !== expected.size) {
    errors.push(`${locale}: found ${records.length} snapshots; expected ${expected.size}`);
  }

  for (const record of records) {
    const ticker = record.attrs['data-report-snapshot'];
    const report = expected.get(ticker);
    if (!report) {
      errors.push(`${locale}: unexpected snapshot ${ticker}`);
      continue;
    }
    if (record.attrs['data-snapshot-date'] !== report.snapshotDate) {
      errors.push(`${locale} ${ticker}: snapshot date is ${record.attrs['data-snapshot-date']}; expected ${report.snapshotDate}`);
    }
    sameNumber('market cap', record.attrs['data-market-cap-yen'], report.marketCapYen, ticker, locale);
    sameNumber('60D ADTV', record.attrs['data-adtv60d-yen'], report.adtv60dYen, ticker, locale);
    sameNumber('ROCE', record.attrs['data-roce-pct'], report.rocePct, ticker, locale);
    sameNumber('valuation multiple', record.attrs['data-valuation-multiple'], report.valuationMultiple, ticker, locale);

    if (record.attrs['data-valuation-basis'] !== report.valuationBasis) {
      errors.push(`${locale} ${ticker}: valuation basis is ${record.attrs['data-valuation-basis']}; expected ${report.valuationBasis}`);
    }
    if (record.attrs['data-valuation-input'] !== report.valuationInput) {
      errors.push(`${locale} ${ticker}: valuation input is ${record.attrs['data-valuation-input']}; expected ${report.valuationInput}`);
    }
    if (!record.body.includes(`EV / ${report.valuationBasis}`)) {
      errors.push(`${locale} ${ticker}: visible multiple does not use EV / ${report.valuationBasis}`);
    }
    if (record.body.includes('OP / EV') || record.body.includes('EV / OP') || record.body.includes('EBIT / EV')) {
      errors.push(`${locale} ${ticker}: visible valuation includes a reciprocal or OP label`);
    }

    const labelTag = ticker === '4290' ? 'dt' : 'small';
    const labels = [...record.body.matchAll(new RegExp(`<${labelTag}>([^<]+)</${labelTag}>`, 'g'))]
      .map((match) => match[1].replace(/\s*·.*$/, ''))
      .slice(0, 4);
    if (JSON.stringify(labels) !== JSON.stringify(metricOrder[locale])) {
      errors.push(`${locale} ${ticker}: metric order is ${labels.join(', ')}; expected ${metricOrder[locale].join(', ')}`);
    }
  }
}

if (JSON.stringify(sequences[0]) !== JSON.stringify(sequences[1])) {
  errors.push(`EN/JA snapshot order differs: ${sequences[0].join(', ')} vs ${sequences[1].join(', ')}`);
}

if (errors.length) {
  console.error('COMPOUNDER HUB DATA: FAIL');
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`COMPOUNDER HUB DATA: PASS — ${source.reports.length} dated snapshots; EN/JA values and forward EV/EBIT labels agree`);
