import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const roots = [path.join(root, "en", "compounders"), path.join(root, "compounders")];
const pages = [];
const profileCss = fs.readFileSync(path.join(root, "assets", "compounder-profile.css"), "utf8");

const cssFailures = [];
const sectionLabelRule = profileCss.match(/\.compounder-profile \.section-num,\s*\.compounder-profile \.section-label\s*\{([^}]*)\}/);
if (!sectionLabelRule || !/display:\s*block\b/.test(sectionLabelRule[1]) || !/margin:\s*0 0 12px\b/.test(sectionLabelRule[1]) || !/font:\s*600 14px\/1\.45 var\(--cp-sans\)/.test(sectionLabelRule[1])) {
  cssFailures.push("shared section labels must remain block-level with the readable 14px hierarchy and 12px separation");
}
const narrativeQuestionRule = profileCss.match(/\.compounder-profile \.narrative-phase \.question-card\s*\{([^}]*)\}/);
if (!narrativeQuestionRule || !/padding:\s*26px 28px 30px\b/.test(narrativeQuestionRule[1]) || !/border-top:\s*3px solid var\(--cp-gold\)/.test(narrativeQuestionRule[1]) || !/box-shadow:\s*none\b/.test(narrativeQuestionRule[1])) {
  cssFailures.push("narrative decisive-question boxes must retain balanced internal spacing and the quiet gold top rule");
}
const narrativeOpenerRule = profileCss.match(/\.compounder-profile \.narrative-phase \.phase-opener\s*\{([^}]*)\}/);
if (!narrativeOpenerRule || !/margin:\s*0 0 28px\b/.test(narrativeOpenerRule[1]) || !/padding:\s*0 0 22px\b/.test(narrativeOpenerRule[1]) || !/border-bottom:\s*1px solid var\(--cp-rule\)/.test(narrativeOpenerRule[1])) {
  cssFailures.push("narrative box openers must preserve their lower inset and divider spacing");
}

for (const languageRoot of roots) {
  if (!fs.existsSync(languageRoot)) continue;
  for (const entry of fs.readdirSync(languageRoot, { withFileTypes: true })) {
    if (!entry.isDirectory() || !/^\d{4}$/.test(entry.name)) continue;
    const page = path.join(languageRoot, entry.name, "initiation", "index.html");
    if (!fs.existsSync(page)) continue;
    const html = fs.readFileSync(page, "utf8");
    if (html.includes("/assets/compounder-profile.css")) pages.push({ page, html });
  }
}

if (pages.length === 0) {
  throw new Error("No visual-first Compounder pages found.");
}

const exact = (html, needle) => html.split(needle).length - 1;
const atLeast = (html, needle, count, label, failures) => {
  const found = exact(html, needle);
  if (found < count) failures.push(`${label}: expected at least ${count}, found ${found}`);
};
const exactly = (html, needle, count, label, failures) => {
  const found = exact(html, needle);
  if (found !== count) failures.push(`${label}: expected ${count}, found ${found}`);
};

let failed = false;
if (cssFailures.length) {
  failed = true;
  console.error("FAIL assets/compounder-profile.css");
  for (const failure of cssFailures) console.error(`  - ${failure}`);
}
for (const { page, html } of pages) {
  const failures = [];
  const isMembraneProfile = html.includes('data-conviction-membrane="2.0"');
  exactly(html, "/assets/compounder-profile.css", 1, "canonical profile stylesheet", failures);
  exactly(html, "/assets/compounder-profile.js", 1, "canonical profile script", failures);
  exactly(html, "/assets/share-bar.js", 1, "share-bar script", failures);
  exactly(html, "/assets/nav.js", 1, "shared navigation", failures);
  exactly(html, 'class="compounder-profile"', 1, "canonical profile root", failures);
  exactly(html, 'class="cp-profile-header"', 1, "canonical profile header", failures);
  exactly(html, 'class="cp-key-metrics"', 1, "data-driven key metrics", failures);
  exactly(html, 'data-compounder-profile="1"', 1, "profile system marker", failures);
  if (isMembraneProfile) {
    exactly(html, 'data-conviction-membrane="2.0"', 1, "Conviction Membrane marker", failures);
    exactly(html, 'data-conviction-role="title"', 1, "title-conviction role", failures);
    exactly(html, 'data-conviction-role="valuation"', 1, "valuation-conviction role", failures);
    exactly(html, 'data-conviction-role="risks"', 1, "affirmative-risks role", failures);
    exactly(html, 'data-conviction-role="observable"', 1, "observable-confirmation role", failures);
    const synthesisRoles = exact(html, 'data-conviction-role="master"') + exact(html, 'data-conviction-role="forecast"');
    if (synthesisRoles < 1) failures.push("conviction traversal: expected at least one master or forecast role");
    atLeast(html, 'class="research-section', 4, "research sections", failures);
    atLeast(html, 'class="section-label"', 4, "section labels", failures);
    exactly(html, 'data-compounder-chart', 1, "price chart", failures);
    for (const retired of ['class="question-card"', 'class="ct-card"', 'class="scn-card bear"', 'class="scn-card base"', 'class="scn-card bull"']) {
      exactly(html, retired, 0, `retired analytical block ${retired}`, failures);
    }
    if (/>(?:\s|<[^>]+>)*(?:BULL|BEAR)(?:\s|<[^>]+>)*</i.test(html)) {
      failures.push("retired BULL/BEAR publication label");
    }
    for (const match of html.matchAll(/<[^>]*class="[^"]*section-label[^"]*"[^>]*>([\s\S]*?)<\/[^>]+>/gi)) {
      if (match[1].includes("?")) failures.push("section heading poses a research question");
    }
    for (const match of html.matchAll(/<(?:section|div)\b[^>]*class="[^"]*research-section[^"]*"[^>]*>/gi)) {
      const tag = match[0];
      if (!tag.includes("data-card-ids=") && !tag.includes('data-reader-orientation="true"')) {
        failures.push("research section lacks data-card-ids or reader-orientation marker");
      }
    }
  } else {
    atLeast(html, '<section', 4, "article sections", failures);
    exactly(html, '<h1 class="cp-profile-title"', 1, "single research H1", failures);
  }
  exactly(html, 'class="share-bar"', 1, "shared share bar", failures);
  exactly(html, 'class="meth"', 1, "methodology/language footer", failures);
  exactly(html, "</main>", 1, "main close", failures);

  for (const forbidden of ["profile-essay", "share-panel", "profile-footer", "compounders-nav.js", 'id="main-nav"', "simple-profile", "prestige-profile", "/assets/profile.css", "/assets/compounder-research.css", 'id="v2-inflections"']) {
    if (html.includes(forbidden)) failures.push(`forbidden fallback markup: ${forbidden}`);
  }

  const relative = path.relative(root, page).replaceAll(path.sep, "/");
  if (failures.length) {
    failed = true;
    console.error(`FAIL ${relative}`);
    for (const failure of failures) console.error(`  - ${failure}`);
  } else {
    console.log(`PASS ${relative}`);
  }
}

if (failed) process.exit(1);
console.log(`Visual-first Compounder check passed: ${pages.length} pages.`);
