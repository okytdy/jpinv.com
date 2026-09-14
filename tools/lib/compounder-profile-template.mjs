import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE_ORIGIN = 'https://jpinv.com';
const ROOT = path.dirname(path.dirname(path.dirname(fileURLToPath(import.meta.url))));

function navVersion() {
  const nav = fs.readFileSync(path.join(ROOT, 'assets', 'nav.js'), 'utf8');
  const versionPattern = /(assets\/(?:nav\.js|hero\.js|hero\.css)\?v=)([0-9a-zA-Z]+)/g;
  const stableSource = nav.replace(versionPattern, '$1');
  return crypto.createHash('sha256').update(stableSource).digest('hex').slice(0, 10);
}

export function escapeHtml(value = '') {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function localizedDate(isoDate, language) {
  if (!isoDate) return '';
  const date = new Date(`${isoDate}T00:00:00Z`);
  if (Number.isNaN(date.valueOf())) return isoDate;
  return new Intl.DateTimeFormat(language === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC'
  }).format(date);
}

export function articleUrl(ticker, slug, language) {
  return `${language === 'en' ? '/en' : ''}/compounders/${ticker}/${slug}/`;
}

function isArchived(article) {
  return article.publicationStatus === 'archived';
}

function renderArchiveNotice(page) {
  if (!isArchived(page.article)) return '';
  const isJa = page.language === 'ja';
  const currentProfiles = isJa ? '/compounders/profiles/' : '/en/compounders/profiles/';
  const archive = isJa ? '/compounders/archive/' : '/en/compounders/archive/';
  return `<aside class="cp-archive-notice" aria-labelledby="cp-archive-title">
  <span class="cp-archive-kicker">${isJa ? 'アーカイブ調査' : 'Archived research'}</span>
  <h2 id="cp-archive-title">${isJa ? '旧形式で公開したJII Compounder Profileです。' : 'Published under JII\'s previous Compounder format.'}</h2>
  <p>${isJa ? '本ページは公開時点の調査記録として保存しており、更新していません。JIIの現行フォーマットは、2026年9月2日公開のNJSから適用しています。' : 'This page preserves the research record as published and is not maintained. JII\'s current Compounder format begins with NJS, published on September 2, 2026.'}</p>
  <div class="cp-archive-links"><a href="${currentProfiles}">${isJa ? '現行のCompounder Profileを見る' : 'View current Compounder profiles'}</a><a href="${archive}">${isJa ? 'アーカイブ一覧' : 'Browse the archive'}</a></div>
</aside>`;
}

function renderMetric(metric) {
  const context = metric.context
    ? `<dd class="cp-metric-context">${escapeHtml(metric.context)}</dd>`
    : '';
  return `<div class="cp-key-metric"><dt>${escapeHtml(metric.label)}</dt><dd class="cp-metric-value">${escapeHtml(metric.value)}</dd>${context}</div>`;
}

export function renderProfileFooter(page) {
  const isJa = page.language === 'ja';
  const home = isJa ? '/compounders/' : '/en/compounders/';
  const method = isJa ? '/compounders/methodology/' : '/en/compounders/methodology/';
  const current = articleUrl(page.ticker, page.slug, page.language);
  const counterpart = articleUrl(page.ticker, page.slug, isJa ? 'en' : 'ja');
  return `<div class="meth"><span><a href="${home}">${isJa ? '銘柄レポート' : 'Company research'}</a> · <a href="${method}">${isJa ? '調査方針' : 'Methodology'}</a></span><span class="report-footer-locale">${isJa ? '言語' : 'Language'}: <a href="${isJa ? counterpart : current}"${isJa ? '' : ' class="current" aria-current="page"'}>EN</a> · <a href="${isJa ? current : counterpart}"${isJa ? ' class="current" aria-current="page"' : ''}>JP</a></span><span>Japan Investor Interface Co., Ltd.</span></div>`;
}

export function renderProfileHeader(page) {
  const { ticker, slug, language, company, article } = page;
  const isJa = language === 'ja';
  const home = isJa ? '/compounders/' : '/en/compounders/';
  const homeLabel = isJa ? '銘柄レポート' : 'Company research';
  const companyLabel = isJa ? '企業' : 'Company';
  const typeLabel = article.type || homeLabel;
  const securityLine = company.securityLine?.[language] || ticker;
  const name = company.name?.[language] || company.name?.en || company.name?.ja || ticker;
  const altLanguage = isJa ? 'en' : 'ja';
  const altName = company.name?.[altLanguage] || '';
  const description = company.description?.[language] || '';
  const title = article.title?.[language] || name;
  const deck = article.deck?.[language] || '';
  const metrics = article.metrics?.[language] || [];
  const metaParts = [typeLabel, securityLine].filter(Boolean);

  const date = article.datePublished
    ? `<time class="cp-publication-date" datetime="${escapeHtml(article.datePublished)}">${escapeHtml(localizedDate(article.datePublished, language))}</time>`
    : '';
  const deckHtml = deck ? `<p class="cp-profile-deck">${escapeHtml(deck)}</p>` : '';
  const altHtml = altName && altName !== name
    ? `<p class="cp-company-alt" lang="${altLanguage}">${escapeHtml(altName)}</p>`
    : '';
  const descriptionHtml = description
    ? `<p class="cp-company-description">${escapeHtml(description)}</p>`
    : '';
  const metricHtml = metrics.length
    ? `<div class="cp-key-metrics" aria-label="${isJa ? '主要指標' : 'Key metrics'}"><dl class="cp-metric-count-${Math.min(metrics.length, 6)}">${metrics.slice(0, 6).map(renderMetric).join('')}</dl></div>`
    : '';
  const dateLine = date ? `      ${date}\n` : '';
  const deckLine = deckHtml ? `      ${deckHtml}\n` : '';
  const altLine = altHtml ? `      ${altHtml}\n` : '';
  const descriptionLine = descriptionHtml ? `      ${descriptionHtml}\n` : '';

  return `<header class="cp-profile-header" data-profile-shell="1">
  <div class="cp-profile-header__inner">
    <div class="cp-research-summary">
      <a class="cp-breadcrumb" href="${home}">${homeLabel}</a>
      <p class="cp-meta-line">${metaParts.map((part) => `<span>${escapeHtml(part)}</span>`).join('')}</p>
${dateLine}      <h1 class="cp-profile-title">${escapeHtml(title)}</h1>
${deckLine}    </div>
    <div class="cp-company-summary">
      <p class="cp-company-label">${companyLabel}</p>
      <h2 class="cp-company-name">${escapeHtml(name)}</h2>
${altLine}${descriptionLine}    </div>
  </div>
  ${metricHtml}
</header>`;
}

export function inlinePageData(page) {
  const data = {
    ticker: page.ticker,
    slug: page.slug,
    language: page.language,
    secondaryMetrics: (page.article.secondaryMetrics?.[page.language] || []).slice(0, 4),
    related: page.related || []
  };
  return JSON.stringify(data).replaceAll('<', '\\u003c');
}

export function renderProfilePage(page, bodyHtml) {
  if (/<h1\b/i.test(bodyHtml)) {
    throw new Error('Article body must not contain an H1; the profile shell owns the single page H1.');
  }
  if (/<(?:html|head|body|main|article|style|script)\b/i.test(bodyHtml) || /<link\b[^>]*rel=["']stylesheet["']/i.test(bodyHtml)) {
    throw new Error('Article body must contain research content only; the profile shell owns document structure and styles.');
  }
  if (/\sstyle\s*=/i.test(bodyHtml)) {
    throw new Error('Article body must not contain inline styles; add reusable styling to the canonical profile stylesheet.');
  }
  const { ticker, slug, language, company, article } = page;
  const isJa = language === 'ja';
  const urlPath = articleUrl(ticker, slug, language);
  const counterpart = articleUrl(ticker, slug, isJa ? 'en' : 'ja');
  const canonical = `${SITE_ORIGIN}${urlPath}`;
  const counterpartUrl = `${SITE_ORIGIN}${counterpart}`;
  const title = article.title?.[language] || company.name?.[language] || ticker;
  const documentTitle = article.documentTitle?.[language] || `${title} | JII Compounders`;
  const ogTitle = article.ogTitle?.[language] || title;
  const description = article.metaDescription?.[language]
    || article.deck?.[language]
    || company.description?.[language]
    || '';
  const ogDescription = article.ogDescription?.[language] || description;
  const imageAlt = article.ogImageAlt?.[language]
    || (isJa ? `JII Compounders 銘柄レポート · ${ticker}` : `JII Compounders company research · ${ticker}`);
  const dateModified = article.dateModified || article.datePublished || '';
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: title,
    datePublished: article.datePublished,
    dateModified,
    inLanguage: language,
    author: { '@type': 'Organization', name: 'Japan Investor Interface Co., Ltd.' },
    publisher: { '@type': 'Organization', name: 'Japan Investor Interface Co., Ltd.' },
    mainEntityOfPage: canonical
  };
  const rootAttrs = [
    'class="compounder-profile"',
    'data-compounder-profile="1"',
    `data-profile-ticker="${escapeHtml(ticker)}"`,
    `data-profile-article="${escapeHtml(slug)}"`,
    `data-publication-status="${isArchived(article) ? 'archived' : 'current'}"`
  ];
  if (article.convictionMembrane) rootAttrs.push(`data-conviction-membrane="${escapeHtml(article.convictionMembrane)}"`);

  return `<!DOCTYPE html>
<html lang="${language}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>${escapeHtml(documentTitle)}</title>
  <meta name="description" content="${escapeHtml(description)}">
${isArchived(article) ? '  <meta name="robots" content="noindex,follow">\n' : ''}  <link rel="canonical" href="${canonical}">
  <link rel="alternate" hreflang="en" href="${isJa ? counterpartUrl : canonical}">
  <link rel="alternate" hreflang="ja" href="${isJa ? canonical : counterpartUrl}">
  <link rel="alternate" hreflang="x-default" href="${isJa ? counterpartUrl : canonical}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="${escapeHtml(ogTitle)}">
  <meta property="og:description" content="${escapeHtml(ogDescription)}">
  <meta property="og:url" content="${canonical}">
  <meta property="og:image" content="${SITE_ORIGIN}/og/compounders/${escapeHtml(ticker)}.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="${escapeHtml(imageAlt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="${SITE_ORIGIN}/og/compounders/${escapeHtml(ticker)}.png">
  <meta name="twitter:image:alt" content="${escapeHtml(imageAlt)}">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="shortcut icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <script src="/assets/locale-switcher.js" defer></script>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500&amp;family=Noto+Sans+JP:wght@300;400;500;600&amp;family=DM+Mono:wght@400;500&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/site.css?v=20260831c">
  <link rel="stylesheet" href="/assets/compounder-profile.css?v=20260913b">
  <script type="application/ld+json">${JSON.stringify(jsonLd)}</script>
  <script type="application/json" id="compounder-profile-data">${inlinePageData(page)}</script>
</head>
<body>
<a class="skip-link" href="#main-content">${isJa ? '本文へ移動' : 'Skip to main content'}</a>
<main id="main-content" tabindex="-1">
<article ${rootAttrs.join(' ')}>
${renderProfileHeader(page)}
${renderArchiveNotice(page)}
${bodyHtml.trim()}
${renderProfileFooter(page)}
</article>
</main>
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
<script src="/assets/compounder-profile.js?v=20260913"></script>
<script src="/assets/share-bar.js"></script>
<script src="/assets/nav.js?v=${navVersion()}" defer></script>
</body>
</html>
`;
}
