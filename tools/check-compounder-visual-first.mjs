import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const roots = [path.join(root, "en", "compounders"), path.join(root, "compounders")];
const pages = [];

for (const languageRoot of roots) {
  if (!fs.existsSync(languageRoot)) continue;
  for (const entry of fs.readdirSync(languageRoot, { withFileTypes: true })) {
    if (!entry.isDirectory() || !/^\d{4}$/.test(entry.name)) continue;
    const page = path.join(languageRoot, entry.name, "initiation", "index.html");
    if (!fs.existsSync(page)) continue;
    const html = fs.readFileSync(page, "utf8");
    if (html.includes("/assets/compounder-research.css")) pages.push({ page, html });
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
for (const { page, html } of pages) {
  const failures = [];
  exactly(html, "/assets/compounder-research.css", 1, "research stylesheet", failures);
  exactly(html, "/assets/compounder-research.js", 1, "research script", failures);
  exactly(html, "/assets/share-bar.js", 1, "share-bar script", failures);
  exactly(html, "/assets/nav.js", 1, "shared navigation", failures);
  exactly(html, 'class="investability-item"', 4, "investability cells", failures);
  atLeast(html, 'class="research-section', 5, "research sections", failures);
  atLeast(html, 'class="section-label"', 5, "section labels", failures);
  exactly(html, 'class="underwriting-panel"', 1, "underwriting panel", failures);
  exactly(html, 'class="chart-wrap"', 1, "price chart", failures);
  exactly(html, 'class="loop-panel"', 1, "economic-mechanism visual", failures);
  atLeast(html, 'class="question-card"', 2, "decisive-question cards", failures);
  exactly(html, 'class="valuation-matrix"', 1, "valuation matrix", failures);
  exactly(html, 'class="source-shelf"', 1, "source shelf", failures);
  exactly(html, 'class="share-bar"', 1, "shared share bar", failures);
  exactly(html, 'class="publication-note"', 1, "publication note", failures);
  exactly(html, 'class="meth"', 1, "methodology/language footer", failures);
  exactly(html, "</main>", 1, "main close", failures);

  for (const forbidden of ["profile-essay", "share-panel", "profile-footer", "compounders-nav.js", 'id="main-nav"']) {
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
