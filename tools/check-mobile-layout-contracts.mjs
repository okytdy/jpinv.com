import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");
const failures = [];

function requireMatch(source, pattern, message) {
  if (!pattern.test(source)) failures.push(message);
}

function routeFile(url) {
  const pathname = decodeURIComponent(new URL(url).pathname);
  if (pathname === "/") return "index.html";
  return path.join(pathname.replace(/^\/+|\/+$/g, ""), "index.html");
}

const sitemap = read("sitemap.xml");
const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);

for (const url of urls) {
  const relativePath = routeFile(url);
  const absolutePath = path.join(root, relativePath);
  if (!fs.existsSync(absolutePath)) {
    failures.push(`${url}: no local ${relativePath}`);
    continue;
  }
  const html = fs.readFileSync(absolutePath, "utf8");
  requireMatch(
    html,
    /<meta\s+name=["']viewport["'][^>]*content=["'][^"']*width=device-width/i,
    `${relativePath}: missing a device-width viewport`,
  );
  requireMatch(
    html,
    /\/assets\/(?:nav|compounders-nav)\.js(?:\?v=[^"']+)?/i,
    `${relativePath}: missing the shared navigation loader`,
  );
}

const heroCss = read("assets/hero.css");
requireMatch(
  heroCss,
  /@media\s*\(max-width:760px\)[\s\S]*?html\[lang=["']ja["']\]\s+\.nw-in\s*\{[^}]*grid-template-columns\s*:\s*minmax\(0,1fr\)/,
  "assets/hero.css: the Japanese news grid lacks its mobile single-column override",
);

const navJs = read("assets/nav.js");
requireMatch(
  navJs,
  /renderedHeight\s*=\s*Math\.ceil\(nav\.getBoundingClientRect\(\)\.height\)/,
  "assets/nav.js: fixed navigation space is not based on the rendered mobile header height",
);
requireMatch(
  navJs,
  /\.curriculum \.post-content table\{display:block!important;[^}]*overflow-x:auto!important/,
  "assets/nav.js: legacy governance tables are not confined to a mobile scroll region",
);
requireMatch(
  navJs,
  /\.curriculum \.post-list-row\{grid-template-columns:50px minmax\(0,1fr\)!important/,
  "assets/nav.js: legacy governance index rows lack a shrinkable mobile content column",
);
requireMatch(
  navJs,
  /@media\(max-width:420px\)\{html\[lang='ja'\] \.jp-keep\{display:inline;white-space:normal;/,
  "assets/nav.js: Japanese no-break phrases cannot relax on narrow phones",
);

for (const relativePath of [
  "compounders/universe/index.html",
  "en/compounders/universe/index.html",
]) {
  const html = read(relativePath);
  requireMatch(
    html,
    /\.universe-table\s*\{[^}]*display:block[^}]*overflow-x:auto/s,
    `${relativePath}: wide universe tables are not confined to a mobile scroll region`,
  );
}

for (const relativePath of [
  "compounders/feed/index.html",
  "en/compounders/feed/index.html",
]) {
  const html = read(relativePath);
  requireMatch(
    html,
    /\.row-class\s*\{[^}]*white-space:normal[^}]*overflow-wrap:anywhere/s,
    `${relativePath}: long disclosure labels cannot wrap on mobile`,
  );
}

if (failures.length) {
  console.error(`Mobile layout contract check failed (${failures.length}):`);
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`Mobile layout contracts OK: ${urls.length} published routes, both languages, and all wide-content surfaces.`);
