#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const ignoredDirectories = new Set([".git", "node_modules", "research"]);

function walk(directory) {
  const files = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...walk(absolute));
    else files.push(absolute);
  }
  return files;
}

function relative(absolute) {
  return path.relative(root, absolute).split(path.sep).join("/");
}

function routeForFile(file) {
  const rel = relative(file);
  if (rel === "index.html") return "/";
  return `/${rel.replace(/index\.html$/, "")}`;
}

function fileForPathname(pathname) {
  let decoded;
  try {
    decoded = decodeURIComponent(pathname);
  } catch {
    decoded = pathname;
  }
  const rel = decoded.replace(/^\/+/, "");
  if (!rel) return "index.html";
  if (rel.endsWith("/")) return `${rel}index.html`;
  if (path.posix.extname(rel)) return rel;
  return `${rel}/index.html`;
}

const publicFiles = walk(root);
const fileSet = new Set(publicFiles.map(relative));
const htmlFiles = publicFiles.filter(
  (file) => file.endsWith(".html") && !path.basename(file).includes(".bak"),
);
const redirects = new Set();
const bodies = new Map();
for (const file of htmlFiles) {
  const body = fs.readFileSync(file, "utf8");
  bodies.set(file, body);
  if (/<meta[^>]+http-equiv=["']?refresh/i.test(body)) redirects.add(routeForFile(file));
}

const issues = [];
const seen = new Set();
function report(kind, source, target) {
  const key = `${kind}\0${source}\0${target}`;
  if (seen.has(key)) return;
  seen.add(key);
  issues.push({ kind, source, target });
}

for (const file of htmlFiles) {
  const body = bodies.get(file);
  const sourceRoute = routeForFile(file);
  const source = relative(file);
  const targets = [
    ...Array.from(body.matchAll(/<a\b[^>]*\bhref\s*=\s*["']([^"']+)["'][^>]*>/gi), (match) => match[1]),
    ...Array.from(body.matchAll(/\bdata-share-url\s*=\s*["']([^"']+)["']/gi), (match) => match[1]),
  ];
  for (const raw of targets) {
    if (!raw || raw.startsWith("#") || /^(?:mailto:|tel:|javascript:|data:)/i.test(raw)) continue;
    let url;
    try {
      url = new URL(raw, `https://jpinv.com${sourceRoute}`);
    } catch {
      report("invalid URL", source, raw);
      continue;
    }
    if (url.hostname !== "jpinv.com") continue;
    const targetFile = fileForPathname(url.pathname);
    if (!fileSet.has(targetFile)) {
      report("missing internal target", source, raw);
      continue;
    }
    const targetRoute = routeForFile(path.join(root, ...targetFile.split("/")));
    if (redirects.has(targetRoute)) report("internal link uses redirect", source, raw);
  }
}

const sitemapPath = path.join(root, "sitemap.xml");
const sitemap = fs.readFileSync(sitemapPath, "utf8");
const locations = Array.from(sitemap.matchAll(/<loc>([^<]+)<\/loc>/g), (match) => match[1]);
for (const location of locations) {
  const url = new URL(location);
  const targetFile = fileForPathname(url.pathname);
  if (!fileSet.has(targetFile)) {
    report("sitemap target missing", "sitemap.xml", location);
    continue;
  }
  const file = path.join(root, ...targetFile.split("/"));
  const body = bodies.get(file) ?? fs.readFileSync(file, "utf8");
  if (/<meta[^>]+http-equiv=["']?refresh/i.test(body)) {
    report("sitemap target redirects", "sitemap.xml", location);
  }
  const canonical = body.match(/<link(?=[^>]*\brel=["']canonical["'])(?=[^>]*\bhref=["']([^"']+)["'])[^>]*>/i)?.[1];
  if (!canonical || new URL(canonical, location).href !== url.href) {
    report("sitemap canonical mismatch", "sitemap.xml", `${location} -> ${canonical ?? "missing"}`);
  }
}

if (issues.length) {
  console.error(`Indexing check failed with ${issues.length} issue(s):`);
  for (const issue of issues) console.error(`- ${issue.kind}: ${issue.source} -> ${issue.target}`);
  process.exitCode = 1;
} else {
  console.log(`Indexing check passed: ${htmlFiles.length} HTML files and ${locations.length} sitemap URLs.`);
}
