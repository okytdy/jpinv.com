/* ===================================================================
   Acceptance test for the jpinv.com dropdown navigation.

   WHAT IT CHECKS. It opens a real Chrome, hovers each tab in the top bar,
   moves a real pointer along the two paths a hand actually takes, and then
   requires that the menu item under the pointer receives the click. If the
   panel has closed on the way, the click hits nothing and the trial fails.

   The two paths:
     1. straight down out of the tab, then across to the item
     2. the corner cut — a single diagonal from the tab to the item, which is
        what a hand does when the item is 800px to the left

   WHY IT EXISTS. On August 4, 2026 the panel opened on hover and could not be
   clicked: it disappeared the moment the pointer left the tab. The cause was
   geometric, and geometry is exactly what a person reading the CSS cannot see.
   Reading the file found nothing wrong twice. Measuring found it in one run:
   the hover target was 26px tall inside a 64px bar, so a 19px strip of bar sat
   under the label belonging to no tab, and crossing it closed the panel. On
   /compounders/ pages the strip was 66px because the panel measured itself
   against the whole header, section tabs included.

   It runs against both builds so the failure itself is proved, not assumed —
   a gate that has never failed has never been tested. Point BASE at a copy of
   nav.js from before a change and the BEFORE column should fail.

   SETUP (nothing here is committed — puppeteer is a local dev dependency):
       mkdir -p /tmp/navtest && cd /tmp/navtest && npm i puppeteer
       node tools/test_nav_dropdown.js            # runs from the repo root

   Optional: BASE=/path/to/old/nav.js node tools/test_nav_dropdown.js
   =================================================================== */
const path = require("path");
const fs = require("fs");
const http = require("http");
const url = require("url");

const PUPPETEER = process.env.PUPPETEER_PATH || "/tmp/navtest/node_modules/puppeteer";
const puppeteer = require(PUPPETEER);

const ROOT = path.dirname(__dirname);          /* the site root */
const BASE = process.env.BASE || null;         /* optional known-bad nav.js */
const PORT = 8737;

/* Pages: one plain page, and one inside /compounders/, because that section
   adds a second row to the header and used to move the panel with it. */
const PAGES = [
  { name: "plain page  /会社概要/", path: "/%E4%BC%9A%E7%A4%BE%E6%A6%82%E8%A6%81/" },
  { name: "compounder  /compounders/profiles/", path: "/compounders/profiles/" }
];
const PATHS = ["straight down, then across", "corner cut, straight at the item"];

const TYPES = { ".html":"text/html;charset=utf-8", ".js":"text/javascript;charset=utf-8",
  ".css":"text/css;charset=utf-8", ".svg":"image/svg+xml", ".webp":"image/webp",
  ".png":"image/png", ".jpg":"image/jpeg", ".json":"application/json", ".woff2":"font/woff2" };

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(url.parse(req.url).pathname);
  let f = path.join(ROOT, p);
  try { if (fs.statSync(f).isDirectory()) f = path.join(f, "index.html"); } catch (e) {}
  fs.readFile(f, (e, d) => {
    if (e) { res.writeHead(404); return res.end("not found"); }
    res.writeHead(200, { "Content-Type": TYPES[path.extname(f)] || "application/octet-stream" });
    res.end(d);
  });
});
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function openPage(browser, pagePath, useBase) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  if (useBase) {
    await page.setRequestInterception(true);
    page.on("request", r => r.continue(
      /\/assets\/nav\.js/.test(r.url()) ? { url: "http://127.0.0.1:" + PORT + "/__base_nav.js" } : {}));
  }
  await page.goto("http://127.0.0.1:" + PORT + pagePath, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#jii-nav .jn-links > li .jn-pw", { timeout: 20000 });
  /* Swallow the navigation so one page can serve every trial, and record which
     link the click actually reached. That is the thing being measured. */
  await page.evaluate(() => {
    window.__hit = null;
    document.addEventListener("click", e => {
      const a = e.target.closest && e.target.closest("a");
      if (a) window.__hit = a.getAttribute("href");
      e.preventDefault();
    }, true);
  });
  return page;
}

async function trial(page, tabName, mode) {
  await page.mouse.move(5, 700); await sleep(260);   /* start clear of the bar */
  const g = await page.evaluate(t => {
    document.querySelectorAll("li[data-probe]").forEach(x => delete x.dataset.probe);
    window.__hit = null;
    const li = [...document.querySelectorAll("#jii-nav .jn-links > li")]
      .find(x => x.querySelector("a").textContent.trim() === t);
    li.dataset.probe = "1";
    const r = li.getBoundingClientRect();
    return { cx: r.left + r.width / 2, cy: r.top + r.height / 2 };
  }, tabName);
  await page.mouse.move(g.cx, g.cy); await sleep(220);

  const pw = await page.evaluate(() => {
    const li = document.querySelector("li[data-probe]"), el = li.querySelector(".jn-pw");
    const r = el.getBoundingClientRect(), a = el.querySelector(".jn-pcols a"), ar = a.getBoundingClientRect();
    return { top: r.top, gap: Math.round((r.top - li.getBoundingClientRect().bottom) * 10) / 10,
             ix: ar.left + ar.width / 2, iy: ar.top + ar.height / 2,
             text: a.textContent.trim(), href: a.getAttribute("href") };
  });

  const legs = mode === PATHS[0] ? [[g.cx, pw.top + 26], [pw.ix, pw.iy]] : [[pw.ix, pw.iy]];
  let from = { x: g.cx, y: g.cy };
  for (const [tx, ty] of legs) {
    const N = 14;
    for (let i = 1; i <= N; i++) {
      await page.mouse.move(from.x + (tx - from.x) * i / N, from.y + (ty - from.y) * i / N);
      await sleep(4);
    }
    from = { x: tx, y: ty };
  }
  await page.mouse.click(pw.ix, pw.iy); await sleep(30);
  const hit = await page.evaluate(() => window.__hit);
  const ok = hit === pw.href;
  return { ok, gap: pw.gap, panelTop: pw.top,
    verdict: ok ? "PASS  clicked " + pw.text
                : "FAIL  " + (hit ? "click hit " + hit + " instead of " + pw.href
                                  : "panel gone, click hit nothing") };
}

(async () => {
  /* serve the known-bad nav.js at a fixed path when one was supplied */
  if (BASE) {
    const body = fs.readFileSync(BASE);
    server.on("request", () => {});
    const orig = server.listeners("request")[0];
    server.removeAllListeners("request");
    server.on("request", (req, res) => {
      if (url.parse(req.url).pathname === "/__base_nav.js") {
        res.writeHead(200, { "Content-Type": "text/javascript;charset=utf-8" });
        return res.end(body);
      }
      orig(req, res);
    });
  }
  await new Promise(r => server.listen(PORT, "127.0.0.1", r));

  const browser = await puppeteer.launch({ args: ["--no-sandbox", "--disable-dev-shm-usage"] });
  const builds = BASE ? [{ label: "BEFORE  " + BASE, base: true },
                         { label: "AFTER   assets/nav.js", base: false }]
                      : [{ label: "assets/nav.js", base: false }];
  let failures = 0;

  for (const b of builds) {
    console.log("\n============ " + b.label + " ============");
    for (const pg of PAGES) {
      const page = await openPage(browser, pg.path, b.base);
      console.log("\n  " + pg.name);
      const tabs = await page.evaluate(() =>
        [...document.querySelectorAll("#jii-nav .jn-links > li")]
          .filter(li => li.querySelector(".jn-pw"))
          .map(li => li.querySelector("a").textContent.trim()));
      let shown = false;
      for (const t of tabs) for (const m of PATHS) {
        const r = await trial(page, t, m);
        if (!shown) {
          console.log("    vertical gap between tab and panel: " + r.gap +
                      "px  (panel top y=" + r.panelTop + ")");
          shown = true;
        }
        console.log("      " + t.padEnd(8) + " | " + m.padEnd(32) + " | " + r.verdict);
        if (!r.ok && !b.base) failures++;
      }
      await page.close();
    }
  }
  await browser.close(); server.close();
  console.log("\n" + (failures ? "FAILED: " + failures + " trial(s) on the current nav.js"
                                : "OK: every tab is clickable on both paths"));
  process.exit(failures ? 1 : 0);
})();
