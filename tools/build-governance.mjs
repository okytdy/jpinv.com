#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { marked, Renderer } from "marked";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const SOURCE = path.join(ROOT, "content", "governance", "curriculum-ja.md");
const CHECKSUM = `${SOURCE}.sha256`;
const SITE_ORIGIN = "https://jpinv.com";
const UPDATED = "2026-08-30";

const THEME_META = [
  { index: 1, slug: "foundations", period: "1990年代～2014年" },
  { index: 2, slug: "cg-code", period: "2015～2021年" },
  { index: 3, slug: "market-restructuring", period: "2022～2025年" },
  { index: 4, slug: "capital-efficiency", period: "2023年3月～現在" },
  { index: 5, slug: "frontier", period: "2024～2027年" }
];

function fail(message) {
  throw new Error(`Governance build failed: ${message}`);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}

function stripMarkdown(value) {
  return String(value)
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/[*_`>#]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function verifySource() {
  const expected = fs.readFileSync(CHECKSUM, "utf8").trim().split(/\s+/)[0].toLowerCase();
  const sourceBuffer = fs.readFileSync(SOURCE);
  const actual = crypto.createHash("sha256").update(sourceBuffer).digest("hex");
  if (expected !== actual) fail(`source checksum mismatch (expected ${expected}, received ${actual})`);
  return sourceBuffer.toString("utf8").replaceAll("\r\n", "\n");
}

function sourceOccurrences(source) {
  return [...source.matchAll(/^\*\*SOURCE URL:\*\*\s+(https:\/\/jpinv\.com\/governance\/[^\s]*)\s*$/gm)];
}

function headingBefore(source, index) {
  const found = source.lastIndexOf("\n## ", index);
  return found < 0 ? 0 : found + 1;
}

function lineEnd(source, index) {
  const found = source.indexOf("\n", index);
  return found < 0 ? source.length : found;
}

function cleanStructuralTail(markdown) {
  const lines = markdown.split("\n");
  let changed = true;
  while (changed) {
    changed = false;
    while (lines.length && !lines.at(-1).trim()) { lines.pop(); changed = true; }
    if (lines.length && lines.at(-1).trim() === "---") { lines.pop(); changed = true; }
    while (lines.length && !lines.at(-1).trim()) { lines.pop(); changed = true; }
    if (lines.length && /^# テーマ\d+：/.test(lines.at(-1).trim())) { lines.pop(); changed = true; }
  }
  return lines.join("\n").trim();
}

function parseArticles(source, occurrences) {
  const articles = [];
  for (let i = 2; i < occurrences.length; i += 1) {
    const occurrence = occurrences[i];
    const url = occurrence[1];
    const start = headingBefore(source, occurrence.index);
    const end = i + 1 < occurrences.length ? headingBefore(source, occurrences[i + 1].index) : source.length;
    const headingLine = source.slice(start, source.indexOf("\n", start));
    const title = headingLine.replace(/^##\s+/, "").trim();
    const raw = cleanStructuralTail(source.slice(lineEnd(source, occurrence.index) + 1, end));
    const payload = raw.match(/^\s*\*\*記事要約\*\*\s*\n+([\s\S]*?)\n+\*\*本文\*\*\s*\n+([\s\S]+)$/);
    if (!payload) fail(`could not parse summary and body for ${url}`);
    const pathname = new URL(url).pathname;
    const numberMatch = pathname.match(/\/(\d\.\d+)-/);
    if (!numberMatch) fail(`could not read article number from ${url}`);
    const number = numberMatch[1];
    articles.push({
      title,
      url,
      pathname,
      number,
      themeIndex: Number(number.split(".")[0]),
      summary: payload[1].trim(),
      body: cleanStructuralTail(payload[2])
    });
  }
  if (articles.length !== 27) fail(`expected 27 articles, found ${articles.length}`);
  return articles;
}

function parseThemes(source) {
  const start = source.indexOf("## テーマページ");
  const end = source.indexOf("## 全27記事", start);
  if (start < 0 || end < 0) fail("theme-page source section is missing");
  const section = source.slice(start, end);
  const matches = [...section.matchAll(/^### テーマ(\d+)：([^\n]+)\n([\s\S]*?)(?=^### テーマ\d+：|(?![\s\S]))/gm)];
  const themes = matches.map((match) => {
    const index = Number(match[1]);
    const body = match[3].trim();
    const pageHeading = body.match(/^\*\*ページ見出し:\*\*\s*(.+)$/m)?.[1]?.trim();
    const listMarker = body.indexOf("**記事一覧の見出し:**");
    if (!pageHeading || listMarker < 0) fail(`theme ${index} is incomplete`);
    const afterHeading = body.slice(body.indexOf("\n", body.indexOf("**ページ見出し:**")) + 1, listMarker).trim();
    const articleTitles = [...body.slice(listMarker).matchAll(/^-\s+(.+)$/gm)].map((item) => item[1].trim());
    const meta = THEME_META.find((item) => item.index === index);
    return {
      ...meta,
      name: match[2].trim(),
      pageHeading,
      description: afterHeading,
      articleTitles,
      pathname: `/governance/${meta.slug}/`
    };
  });
  if (themes.length !== 5) fail(`expected 5 themes, found ${themes.length}`);
  return themes;
}

function splitHeadingSections(markdown, level) {
  const prefix = "#".repeat(level);
  const expression = new RegExp(`^${prefix} ([^\\n]+)\\n([\\s\\S]*?)(?=^${prefix} |(?![\\s\\S]))`, "gm");
  return [...markdown.matchAll(expression)].map((match) => ({ heading: match[1].trim(), content: match[2].trim() }));
}

function sourceSegment(source, occurrence, nextStart) {
  return cleanStructuralTail(source.slice(lineEnd(source, occurrence.index) + 1, nextStart));
}

function parseTop(source, occurrences) {
  const markdown = sourceSegment(source, occurrences[0], headingBefore(source, occurrences[1].index));
  const sections = splitHeadingSections(markdown, 3);
  if (sections.length !== 7) fail(`expected 7 landing-page sections, found ${sections.length}`);
  return sections;
}

function parseToolbox(source, occurrences) {
  const end = source.indexOf("## テーマページ", occurrences[1].index);
  const markdown = sourceSegment(source, occurrences[1], end);
  const sections = splitHeadingSections(markdown, 3);
  if (sections.length !== 3) fail(`expected 3 toolbox sections, found ${sections.length}`);
  return sections;
}

function makeRouteResolver(articles) {
  const byNumber = new Map(articles.map((article) => [article.number, article.pathname]));
  const byTitle = articles.map((article) => ({ title: stripMarkdown(article.title), pathname: article.pathname }));
  let unresolved = 0;
  function resolve(markdown) {
    const normalized = markdown.replace(/\]\(\.\.\/\.\.\/toolbox\/ir-toolbox\.j\)/g, "](/governance/toolbox/)");
    return normalized.replace(/\[([^\]]+)\]\(\/governance\/\)/g, (full, label) => {
      const plain = stripMarkdown(label).replace(/^テーマ/, "");
      const number = plain.match(/([1-5]\.\d+)/)?.[1];
      if (number && byNumber.has(number)) return `[${label}](${byNumber.get(number)})`;
      const titleMatch = byTitle.find((item) => item.title === plain || item.title.includes(plain) || plain.includes(item.title));
      if (titleMatch) return `[${label}](${titleMatch.pathname})`;
      unresolved += 1;
      return full;
    });
  }
  resolve.unresolved = () => unresolved;
  return resolve;
}

function autolinkBareUrls(markdown) {
  return markdown.replace(/(?<!\]\()https?:\/\/[^\s<>()（）、，。]+/g, (url) => `<${url}>`);
}

function protectMermaid(markdown) {
  return markdown.replace(/```mermaid\s*\n([\s\S]*?)```/g, (_, diagram) => {
    const code = diagram.trim();
    return `<pre class="mermaid" role="img" aria-label="本文内の制度図">${escapeHtml(code)}</pre>`;
  });
}

function normalizeStrong(markdown) {
  return markdown.replace(/\*\*([^*\n]+?)\*\*/g, "<strong>$1</strong>");
}

let resolveInternalLinks = (markdown) => markdown;

function prepareMarkdown(markdown) {
  return protectMermaid(autolinkBareUrls(normalizeStrong(resolveInternalLinks(markdown))));
}

function renderMarkdown(markdown) {
  let headingNumber = 0;
  const renderer = new Renderer();
  renderer.heading = function ({ text, depth }) {
    headingNumber += 1;
    return `<h${depth} id="section-${headingNumber}">${marked.parseInline(text)}</h${depth}>\n`;
  };
  return marked.parse(prepareMarkdown(markdown), { gfm: true, breaks: false, renderer }).trim();
}

function renderInline(markdown) {
  return marked.parseInline(normalizeStrong(resolveInternalLinks(markdown.trim())), { gfm: true }).trim();
}

function firstParagraph(markdown) {
  return markdown.split(/\n\s*\n/)[0].trim();
}

function parseList(markdown, ordered = false) {
  const expression = ordered ? /^\d+\.\s+(.+)$/gm : /^-\s+(.+)$/gm;
  return [...markdown.matchAll(expression)].map((match) => match[1].trim());
}

function assetVersion(filename) {
  const content = fs.readFileSync(path.join(ROOT, "assets", filename));
  return crypto.createHash("sha256").update(content).digest("hex").slice(0, 10);
}

function navVersion() {
  const nav = fs.readFileSync(path.join(ROOT, "assets", "nav.js"), "utf8");
  const versionPattern = /(assets\/(?:nav\.js|hero\.js|hero\.css)\?v=)([0-9a-zA-Z]+)/g;
  const stableSource = nav.replace(versionPattern, "$1");
  return crypto.createHash("sha256").update(stableSource).digest("hex").slice(0, 10);
}

function commonHead({ title, description, pathname, type = "WebPage", schema = {} }) {
  const canonical = `${SITE_ORIGIN}${pathname}`;
  const english = `${SITE_ORIGIN}/en${pathname}`;
  const cssVersion = assetVersion("governance.css");
  const schemaPayload = {
    "@context": "https://schema.org",
    "@type": type,
    name: title,
    description,
    url: canonical,
    inLanguage: "ja",
    isPartOf: { "@type": "WebSite", name: "Japan Investor Interface", url: `${SITE_ORIGIN}/` },
    ...schema
  };
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <meta name="description" content="${escapeAttr(description)}">
  <link rel="canonical" href="${canonical}">
  <link rel="alternate" hreflang="ja" href="${canonical}">
  <link rel="alternate" hreflang="en" href="${english}">
  <link rel="alternate" hreflang="x-default" href="${canonical}">
  <meta property="og:title" content="${escapeAttr(title)}">
  <meta property="og:description" content="${escapeAttr(description)}">
  <meta property="og:url" content="${canonical}">
  <meta property="og:type" content="${type === "Article" ? "article" : "website"}">
  <meta property="og:image" content="${SITE_ORIGIN}/og/jii-default.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="${SITE_ORIGIN}/og/jii-default.png">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests; block-all-mixed-content">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500&amp;family=Noto+Sans+JP:wght@300;400;500;600&amp;family=DM+Mono:wght@400;500&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/governance.css?v=${cssVersion}">
  <script type="application/ld+json">${JSON.stringify(schemaPayload).replaceAll("</", "<\\/")}</script>
</head>`;
}

function commonScripts() {
  return `  <script src="/assets/governance.js?v=${assetVersion("governance.js")}" defer></script>
  <script src="/assets/nav.js?v=${navVersion()}" defer></script>`;
}

function breadcrumbs(items) {
  const nodes = [`<a href="/">ホーム</a>`];
  for (const item of items) {
    nodes.push(item.href ? `<a href="${item.href}">${escapeHtml(item.label)}</a>` : `<span aria-current="page">${escapeHtml(item.label)}</span>`);
  }
  return `<nav class="gov-wrap gov-crumbs" aria-label="パンくず">${nodes.join('<span class="sep">/</span>')}</nav>`;
}

function pageShell(head, main, scripts = commonScripts()) {
  return `${head}
<body>
  <a class="gov-skip" href="#main-content">本文へ移動</a>
${main}
${scripts}
</body>
</html>
`;
}

function parseLandingThemes(section) {
  return parseList(section.content, true).map((line, index) => {
    const match = line.match(/^\*\*(.+?):\*\*\s*(.+)$/);
    if (!match) fail(`could not parse landing theme ${index + 1}`);
    return { label: match[1], description: match[2], meta: THEME_META[index] };
  });
}

function parseLandingQuiz(section) {
  const questions = splitHeadingSections(section.content, 4);
  const correct = ["b", "d", "a"];
  return questions.map((question, index) => {
    const options = parseList(question.content);
    const explanation = question.content.match(/^\*\*解説:\*\*\s*(.+)$/m)?.[1];
    const questionText = firstParagraph(question.content);
    if (options.length !== 4 || !explanation) fail(`could not parse landing quiz question ${index + 1}`);
    return { ...question, questionText, options, explanation, correct: correct[index] };
  });
}

function renderLanding(top) {
  const hero = top[0];
  const overview = top[1];
  const stats = parseList(overview.content).map((line) => {
    const match = line.match(/^\*\*(.+?):\*\*\s*(.+)$/);
    if (!match) fail("could not parse landing statistic");
    return { value: match[1], label: match[2] };
  });
  const themes = parseLandingThemes(top[2]);
  const quiz = parseLandingQuiz(top[4]);
  const uses = parseList(top[5].content, true).map((line) => {
    const match = line.match(/^\*\*(.+?):\*\*\s*(.+)$/);
    if (!match) fail("could not parse curriculum use case");
    return { title: match[1], body: match[2] };
  });
  const description = stripMarkdown(firstParagraph(hero.content));
  const head = commonHead({
    title: `${hero.heading}｜JII`,
    description,
    pathname: "/governance/",
    type: "Course",
    schema: {
      provider: { "@type": "Organization", name: "Japan Investor Interface Co., Ltd.", url: `${SITE_ORIGIN}/` },
      isAccessibleForFree: true,
      numberOfCredits: 27
    }
  });
  const main = `  <main id="main-content" class="governance-page" tabindex="-1">
    ${breadcrumbs([{ label: "ガバナンス改革講座" }])}
    <section class="gov-hero" aria-labelledby="hero-title">
      <div class="gov-wrap">
        <span class="gov-kicker">IR実務講座</span>
        <h1 id="hero-title">${escapeHtml(hero.heading)}</h1>
        <p>${renderInline(firstParagraph(hero.content))}</p>
        <nav class="gov-local" aria-label="ページ内メニュー"><a href="#curriculum">5つのテーマ</a><a href="#toolbox">IRツールボックス</a><a href="#check">理解度チェック</a><a href="#howto">目的別の使い方</a></nav>
      </div>
    </section>
    <section class="gov-section" aria-labelledby="overview-title">
      <div class="gov-wrap">
        <div class="gov-section-head"><div><span class="gov-kicker">講座の全体像</span><h2 id="overview-title">${escapeHtml(overview.heading)}</h2></div><p>${renderInline(firstParagraph(overview.content))}</p></div>
        <div class="gov-stats">${stats.map((item) => `<div class="gov-stat"><strong>${escapeHtml(item.value)}</strong><span>${renderInline(item.label)}</span></div>`).join("")}</div>
      </div>
    </section>
    <section id="curriculum" class="gov-section gov-section--soft" aria-labelledby="curriculum-title">
      <div class="gov-wrap">
        <div class="gov-section-head"><div><span class="gov-kicker">カリキュラム</span><h2 id="curriculum-title">${escapeHtml(top[2].heading)}</h2></div><p>${renderInline(firstParagraph(top[2].content))}</p></div>
        <nav class="gov-themes" aria-label="講座テーマ">${themes.map((item, index) => `<a class="gov-theme-card" href="/governance/${item.meta.slug}/"><span class="gov-theme-no">${String(index + 1).padStart(2, "0")}</span><span class="gov-theme-title"><strong>${escapeHtml(item.label.split("（")[0])}</strong><span>${escapeHtml(item.label.match(/（(.+)）/)?.[1] || item.meta.period)}</span></span><p>${renderInline(item.description)}</p><span class="gov-theme-arrow">テーマへ →</span></a>`).join("")}</nav>
      </div>
    </section>
    <section id="toolbox" class="gov-section" aria-labelledby="toolbox-title">
      <div class="gov-wrap"><div class="gov-toolbox-callout"><span>実務資料</span><div><h2 id="toolbox-title">${escapeHtml(top[3].heading)}</h2><p>${renderInline(firstParagraph(top[3].content))}</p></div><a href="/governance/toolbox/">ツールボックスを開く →</a></div></div>
    </section>
    <section id="check" class="gov-section gov-section--navy" aria-labelledby="check-title">
      <div class="gov-wrap">
        <div class="gov-section-head"><div><span class="gov-kicker">理解度チェック</span><h2 id="check-title">${escapeHtml(top[4].heading)}</h2></div><p>${renderInline(firstParagraph(top[4].content))}</p></div>
        <div id="governance-quiz" class="gov-quiz">${quiz.map((question, index) => `<article class="gov-question" data-correct="${question.correct}"><span class="gov-question-no">${escapeHtml(question.heading)}</span><h3>${renderInline(question.questionText)}</h3><div class="gov-options">${question.options.map((option, optionIndex) => `<button type="button" class="gov-option" data-option="${String.fromCharCode(97 + optionIndex)}">${renderInline(option)}</button>`).join("")}</div><p class="gov-explain"><strong>解説:</strong> ${renderInline(question.explanation)}</p></article>`).join("")}<p class="gov-score" aria-live="polite">スコア: <strong><span id="governance-quiz-score">0</span> / 3</strong></p></div>
      </div>
    </section>
    <section id="howto" class="gov-section" aria-labelledby="howto-title">
      <div class="gov-wrap"><div class="gov-section-head"><div><span class="gov-kicker">読み方</span><h2 id="howto-title">${escapeHtml(top[5].heading)}</h2></div></div><div class="gov-use-grid">${uses.map((item, index) => `<article class="gov-use"><i>${String(index + 1).padStart(2, "0")}</i><h3>${escapeHtml(item.title)}</h3><p>${renderInline(item.body)}</p></article>`).join("")}</div></div>
    </section>
    <section class="gov-section gov-section--soft" aria-labelledby="training-title">
      <div class="gov-wrap gov-training"><div><span class="gov-kicker">IR担当者研修</span><h2 id="training-title">${escapeHtml(top[6].heading)}</h2></div><div><p>${renderInline(firstParagraph(top[6].content))}</p><a class="gov-contact-link" href="/%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B/">IR研修について相談する →</a></div></div>
    </section>
  </main>`;
  return pageShell(head, main);
}

function renderTheme(theme, articles) {
  const themeArticles = articles.filter((article) => article.themeIndex === theme.index);
  if (themeArticles.length !== theme.articleTitles.length) fail(`theme ${theme.index} article-count mismatch`);
  const description = stripMarkdown(theme.description);
  const head = commonHead({
    title: `${theme.pageHeading}（テーマ${theme.index}）｜JII ガバナンス改革講座`,
    description,
    pathname: theme.pathname
  });
  const main = `  <main id="main-content" class="governance-page" tabindex="-1">
    ${breadcrumbs([{ label: "ガバナンス改革講座", href: "/governance/" }, { label: theme.pageHeading }])}
    <section class="theme-hero" aria-labelledby="theme-title"><div class="gov-wrap"><div class="theme-hero-inner"><span class="theme-eyebrow">テーマ ${theme.index} · ${escapeHtml(theme.period)}</span><h1 id="theme-title">${escapeHtml(theme.pageHeading)}</h1><p class="lede">${renderInline(theme.description)}</p><div class="theme-meta"><span>記事数: <strong>${themeArticles.length}</strong></span><span>期間: <strong>${escapeHtml(theme.period)}</strong></span></div></div></div></section>
    <section class="theme-list" aria-labelledby="article-list-title"><div class="gov-wrap gov-measure"><h2 id="article-list-title">本テーマの記事一覧</h2>${themeArticles.map((article, index) => `<a class="theme-article" href="${article.pathname}"><span class="theme-article-no">${article.number}</span><span class="theme-article-title">${escapeHtml(theme.articleTitles[index])}</span><span class="theme-article-arrow">記事を読む →</span></a>`).join("")}</div></section>
  </main>`;
  return pageShell(head, main);
}

function renderToolbox(toolbox) {
  const title = toolbox[0].heading;
  const summary = firstParagraph(toolbox[0].content);
  const body = `${toolbox[1].heading ? `### ${toolbox[1].heading}\n\n${toolbox[1].content}` : toolbox[1].content}\n\n### ${toolbox[2].heading}\n\n${toolbox[2].content}`;
  const description = stripMarkdown(summary);
  const pathname = "/governance/toolbox/";
  const head = commonHead({ title: `${title}｜JII`, description, pathname });
  const main = `  <main id="main-content" class="governance-page" tabindex="-1">
    ${breadcrumbs([{ label: "ガバナンス改革講座", href: "/governance/" }, { label: "IRツールボックス" }])}
    <header class="post-header"><div class="gov-wrap"><div class="post-header-inner"><span class="post-eyebrow">中核資料 · 随時更新</span><h1 class="post-title">${escapeHtml(title)}</h1><p class="post-summary">${renderInline(summary)}</p><div class="post-meta"><span>収録分野: <strong>9</strong></span><span>一次資料: <strong>約50点以上</strong></span><span>更新: <strong>${UPDATED}</strong></span></div></div></div></header>
    <section class="post-body toolbox-body"><div class="gov-wrap"><article class="post-content">${renderMarkdown(body)}</article><div class="post-language"><a href="/en/governance/toolbox/">English version →</a></div></div></section>
  </main>`;
  return pageShell(head, main);
}

function readingMinutes(markdown) {
  const count = stripMarkdown(markdown).replace(/\s/g, "").length;
  return Math.max(4, Math.ceil(count / 500));
}

function renderArticle(article, index, articles, themes) {
  const theme = themes.find((item) => item.index === article.themeIndex);
  const description = stripMarkdown(article.summary);
  const head = commonHead({
    title: `${article.title}｜JII ガバナンス改革講座`,
    description,
    pathname: article.pathname,
    type: "Article",
    schema: {
      headline: article.title,
      dateModified: UPDATED,
      author: { "@type": "Organization", name: "Japan Investor Interface Co., Ltd." },
      publisher: { "@type": "Organization", name: "Japan Investor Interface Co., Ltd.", url: `${SITE_ORIGIN}/` }
    }
  });
  const previous = articles[index - 1];
  const next = articles[index + 1];
  const navItems = [];
  if (previous) navItems.push(`<a class="post-nav-link prev" href="${previous.pathname}"><div class="post-nav-dir">← 前の記事</div><div class="post-nav-title">${escapeHtml(previous.title)}</div></a>`);
  else navItems.push(`<a class="post-nav-link prev" href="${theme.pathname}"><div class="post-nav-dir">← テーマ概要</div><div class="post-nav-title">${escapeHtml(theme.pageHeading)}</div></a>`);
  if (next) navItems.push(`<a class="post-nav-link next" href="${next.pathname}"><div class="post-nav-dir">次の記事 →</div><div class="post-nav-title">${escapeHtml(next.title)}</div></a>`);
  else navItems.push(`<a class="post-nav-link next" href="/governance/toolbox/"><div class="post-nav-dir">次に読む →</div><div class="post-nav-title">IRツールボックス</div></a>`);
  const main = `  <main id="main-content" class="governance-page" tabindex="-1">
    ${breadcrumbs([{ label: "ガバナンス改革講座", href: "/governance/" }, { label: theme.pageHeading, href: theme.pathname }, { label: `記事 ${article.number}` }])}
    <header class="post-header"><div class="gov-wrap"><div class="post-header-inner"><span class="post-eyebrow">テーマ ${article.themeIndex} · 記事 ${article.number}</span><h1 class="post-title">${escapeHtml(article.title)}</h1><p class="post-summary">${renderInline(article.summary)}</p><div class="post-meta"><span>テーマ: <strong>${escapeHtml(theme.pageHeading)}</strong></span><span>読了目安: <strong>${readingMinutes(article.body)}分</strong></span><span>更新: <strong>${UPDATED}</strong></span></div></div></div></header>
    <section class="post-body"><div class="gov-wrap"><article class="post-content">${renderMarkdown(article.body)}</article><nav class="post-nav" aria-label="前後の記事">${navItems.join("")}</nav><div class="post-language"><a href="/en${article.pathname}">English version →</a></div></div></section>
  </main>`;
  return pageShell(head, main);
}

function writePage(pathname, html) {
  const relative = pathname.replace(/^\//, "");
  const destination = path.join(ROOT, relative, "index.html");
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, html, "utf8");
}

function decodeEntities(value) {
  return value
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_, code) => String.fromCodePoint(Number.parseInt(code, 16)))
    .replaceAll("&amp;", "&")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"')
    .replaceAll("&#39;", "'");
}

function comparableText(value) {
  return decodeEntities(String(value))
    .replace(/<script[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?<\/style>/gi, "")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/https?:\/\/[^\s<>"'()（）、，。]+/g, "")
    .replace(/<[^>]+>/g, "")
    .replace(/[`*_>#|\-]/g, "")
    .replace(/\s+/g, "");
}

function assertContentParity(article, html) {
  const rendered = comparableText(html);
  let inFence = false;
  for (const sourceLine of `${article.summary}\n${article.body}`.split("\n")) {
    if (sourceLine.trim().startsWith("```")) { inFence = !inFence; continue; }
    if (inFence || /^\s*(?:---|\|?\s*:?-{3,})/.test(sourceLine) || !sourceLine.trim()) continue;
    const lineContent = sourceLine.replace(/^\s*(?:>\s*)?(?:[-*+]|\d+\.)\s+/, "");
    const expected = comparableText(renderInline(lineContent));
    if (expected.length >= 14 && !rendered.includes(expected)) {
      fail(`${article.pathname} is missing source text: ${stripMarkdown(sourceLine).slice(0, 80)}`);
    }
  }
  const sourceH2 = (article.body.match(/^##\s+/gm) || []).length;
  const sourceH3 = (article.body.match(/^###\s+/gm) || []).length;
  const htmlH2 = (html.match(/<h2\b/g) || []).length;
  const htmlH3 = (html.match(/<h3\b/g) || []).length;
  if (sourceH2 !== htmlH2 || sourceH3 !== htmlH3) {
    fail(`${article.pathname} heading parity failed (${sourceH2}/${sourceH3} source, ${htmlH2}/${htmlH3} HTML)`);
  }
  const sourceTables = (article.body.match(/^\|\s*:?-{3,}/gm) || []).length;
  const htmlTables = (html.match(/<table>/g) || []).length;
  if (sourceTables !== htmlTables) fail(`${article.pathname} table parity failed (${sourceTables} source, ${htmlTables} HTML)`);
}

function assertGovernanceLinks(pathname, html) {
  for (const match of html.matchAll(/href="([^"]+)"/g)) {
    const href = decodeEntities(match[1]);
    if (!href.startsWith("/governance/") && !href.startsWith("/en/governance/")) continue;
    const linkedPath = new URL(href, SITE_ORIGIN).pathname;
    const destination = path.join(ROOT, linkedPath.replace(/^\//, ""), "index.html");
    if (!fs.existsSync(destination)) fail(`${pathname} links to missing page ${linkedPath}`);
  }
}

function validateBuild(articles) {
  const expectedPages = ["/governance/", "/governance/toolbox/", ...THEME_META.map((theme) => `/governance/${theme.slug}/`), ...articles.map((article) => article.pathname)];
  if (expectedPages.length !== 34) fail(`expected 34 generated pages, found ${expectedPages.length}`);
  let mermaidCount = 0;
  let genericLinks = 0;
  for (const pathname of expectedPages) {
    const html = fs.readFileSync(path.join(ROOT, pathname.replace(/^\//, ""), "index.html"), "utf8");
    if (!html.includes("<main id=\"main-content\"")) fail(`${pathname} has no main content`);
    if (!html.includes(`<link rel="canonical" href="${SITE_ORIGIN}${pathname}">`)) fail(`${pathname} has an incorrect canonical URL`);
    mermaidCount += (html.match(/class="mermaid"/g) || []).length;
    genericLinks += (html.match(/href="\/governance\/"/g) || []).length;
    if (/\*\*|```mermaid|\]\(https?:\/\//.test(html)) fail(`${pathname} contains unrendered Markdown`);
    if (/<pre class="mermaid">[\s\S]*?<pre>|&lt;\/pre&gt;/.test(html)) fail(`${pathname} contains malformed Mermaid markup`);
    if ((html.match(/<h1\b/g) || []).length !== 1) fail(`${pathname} must contain exactly one h1`);
    const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map((match) => match[1]);
    if (new Set(ids).size !== ids.length) fail(`${pathname} contains duplicate IDs`);
    const schema = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)?.[1];
    if (!schema) fail(`${pathname} has no structured data`);
    JSON.parse(schema);
    assertGovernanceLinks(pathname, html);
  }
  articles.forEach((article) => {
    const html = fs.readFileSync(path.join(ROOT, article.pathname.replace(/^\//, ""), "index.html"), "utf8");
    assertContentParity(article, html);
  });
  if (mermaidCount !== 13) fail(`expected 13 Mermaid diagrams, found ${mermaidCount}`);
  if (genericLinks > 140) fail("unexpected number of curriculum-home links");
  if (resolveInternalLinks.unresolved() !== 0) fail(`${resolveInternalLinks.unresolved()} related-article links could not be resolved`);
  console.log(`Validated ${expectedPages.length} pages, 27 articles, and ${mermaidCount} Mermaid diagrams.`);
}

function main() {
  const source = verifySource();
  const occurrences = sourceOccurrences(source);
  if (occurrences.length !== 29) fail(`expected 29 source URLs, found ${occurrences.length}`);
  const articles = parseArticles(source, occurrences);
  const themes = parseThemes(source);
  resolveInternalLinks = makeRouteResolver(articles);
  const top = parseTop(source, occurrences);
  const toolbox = parseToolbox(source, occurrences);

  writePage("/governance/", renderLanding(top));
  writePage("/governance/toolbox/", renderToolbox(toolbox));
  themes.forEach((theme) => writePage(theme.pathname, renderTheme(theme, articles)));
  articles.forEach((article, index) => writePage(article.pathname, renderArticle(article, index, articles, themes)));
  validateBuild(articles);
}

main();
