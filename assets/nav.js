/* ===================================================================
   jpinv.com — THE navigation. One file for the whole site.

   Replaces two older systems:
     1. the <nav id="main-nav"> block that was pasted into 97 pages
     2. assets/compounders-nav.js, which drew a separate bar with its own
        brand and no route back to the main site

   Include on every page with:
     <script src="/assets/nav.js?v=20260803" defer></script>

   To change the navigation anywhere on jpinv.com, edit the SECTIONS array
   below. Nothing else needs to be touched.

   Safety: if a page still carries the old pasted <nav id="main-nav">,
   this script hides it, so a page can never show two bars during rollout.

   Created August 3, 2026.
   =================================================================== */
(function () {
  "use strict";
  if (document.getElementById("jii-nav")) return;

  /* ---------- 1. THE NAVIGATION. Edit here and nowhere else. ---------- */

  var SECTIONS = [
    { ja: "サービス",     en: "Services",    jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/", enHref: "/en/services/" },
    { ja: "料金",         en: "Pricing",     jaHref: "/%E6%96%99%E9%87%91/",                   enHref: "/en/pricing/" },
    { ja: "銘柄レポート", en: "Research",    jaHref: "/compounders/",                          enHref: "/en/compounders/" },
    { ja: "IR研修",       en: "IR Training", jaHref: "/governance/",                           enHref: "/en/governance/" },
    { ja: "会社概要",     en: "Company",     jaHref: "/%E4%BC%9A%E7%A4%BE%E6%A6%82%E8%A6%81/", enHref: "/en/company/" },
    { ja: "FAQ",          en: "FAQ",         jaHref: "/faq/",                                  enHref: "/en/faq/" }
  ];

  var CONTACT = { ja: "お問い合わせ", en: "Contact",
                  jaHref: "/%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B/", enHref: "/en/contact/" };

  /* The Compounders section keeps its own row of tabs, shown only inside
     /compounders/. These are the tabs the old compounders-nav.js drew. */
  var SUBTABS = [
    { k: "methodology", ja: "着眼点",             en: "Methodology",  path: "/compounders/methodology/" },
    { k: "profiles",    ja: "銘柄分析",           en: "Profiles",     path: "/compounders/profiles/" },
    { k: "universe",    ja: "銘柄スクリーニング", en: "Universe",     path: "/compounders/universe/" },
    { k: "signals",     ja: "資本政策開示",       en: "Capital Actions", path: "/compounders/feed/" },
    { k: "disclosures", ja: "大量保有報告",       en: "5% Filings",   path: "/compounders/active-investors/" }
  ];

  /* ---------- 2. Where are we? ---------- */

  var path = location.pathname;
  var isEn = /^\/en(\/|$)/.test(path);
  var inCompounders = /^\/(en\/)?compounders(\/|$)/.test(path);
  var L = isEn ? "en" : "ja";
  var homeHref = isEn ? "/en/" : "/";

  function label(o) { return isEn ? o.en : o.ja; }
  function href(o) { return isEn ? o.enHref : o.jaHref; }

  /* The other language's version of THIS page.
     Every page that has one declares it in <link rel="alternate" hreflang>.
     Pages without one fall back to the other language's home page. */
  function counterpart() {
    var want = isEn ? "ja" : "en";
    var el = document.querySelector('link[rel="alternate"][hreflang="' + want + '"]');
    if (el && el.getAttribute("href")) {
      try { return new URL(el.getAttribute("href"), location.origin).pathname; }
      catch (e) { /* fall through */ }
    }
    /* A noindex page (404, the availability page) has no counterpart to
       construct, so send the reader to the other language's home page. */
    if (document.querySelector('meta[name="robots"][content*="noindex"]')) {
      return isEn ? "/" : "/en/";
    }
    if (isEn) { return path.replace(/^\/en/, "") || "/"; }
    return "/en" + path;
  }

  function isActive(p) {
    if (!p || p === "/" || p === "/en/") return false;
    return path === p || path.indexOf(p) === 0 ||
           decodeURIComponent(path).indexOf(decodeURIComponent(p)) === 0;
  }

  /* ---------- 3. Styles. Self-contained, so this works on pages that
       load site.css and on pages that load only profile.css. ---------- */

  var NAV_H = 64, SUB_H = 46;

  var css = [
    "#jii-nav{position:fixed;top:0;left:0;right:0;z-index:1000;background:rgba(255,255,255,.97);",
    "backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--rule,#d6dee8);}",
    "#jii-nav .jn-bar{height:" + NAV_H + "px;max-width:1100px;margin:0 auto;padding:0 48px;display:flex;align-items:center;gap:18px;}",
    "#jii-nav a{text-decoration:none;color:inherit;}",
    "#jii-nav .jn-logo{flex:0 0 auto;display:flex;align-items:center;}",
    "#jii-nav .jn-logo img{display:block;height:34px;width:auto;}",
    "#jii-nav .jn-logo .jn-logo-sm{display:none;height:30px;}",
    "#jii-nav .jn-links{display:flex;align-items:center;gap:26px;margin-left:auto;list-style:none;padding:0;}",
    "#jii-nav .jn-links a{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:13px;letter-spacing:.04em;",
    "color:var(--text,#1f2937);padding:6px 0;border-bottom:2px solid transparent;white-space:nowrap;transition:color .15s,border-color .15s;}",
    "#jii-nav .jn-links a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-links a.jn-on{color:var(--ink,#1a2a4a);border-bottom-color:var(--accent,#9a7838);font-weight:500;}",
    "#jii-nav .jn-right{display:flex;align-items:center;gap:14px;flex:0 0 auto;}",
    "#jii-nav .jn-lang{font-family:var(--mono,'DM Mono',monospace);font-size:11px;letter-spacing:.1em;color:var(--text-dim,#5f6875);display:flex;gap:5px;}",
    "#jii-nav .jn-lang a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-lang .jn-cur{color:var(--ink,#1a2a4a);font-weight:600;}",
    "#jii-nav .jn-cta{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:12.5px;letter-spacing:.05em;",
    "background:var(--ink,#1a2a4a);color:#fff;padding:10px 20px;white-space:nowrap;}",
    "#jii-nav .jn-cta:hover{background:var(--ink-mid,#172641);}",
    "#jii-nav .jn-burger{display:none;background:none;border:none;cursor:pointer;padding:8px;margin-left:auto;}",
    "#jii-nav .jn-burger span{display:block;width:22px;height:1.5px;background:var(--ink,#1a2a4a);margin:5px 0;transition:transform .2s,opacity .2s;}",
    /* section sub-tabs */
    "#jii-nav .jn-sub{border-top:1px solid var(--rule,#d6dee8);background:var(--bg-soft,#fafbfc);}",
    "#jii-nav .jn-sub-in{height:" + SUB_H + "px;max-width:1100px;margin:0 auto;padding:0 48px;display:flex;align-items:center;gap:22px;overflow-x:auto;}",
    "#jii-nav .jn-sub a{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:12.5px;color:var(--text-mid,#4a5566);",
    "padding:5px 0;border-bottom:2px solid transparent;white-space:nowrap;}",
    "#jii-nav .jn-sub a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-sub a.jn-on{color:var(--ink,#1a2a4a);border-bottom-color:var(--accent,#9a7838);font-weight:500;}",
    /* mobile */
    "#jii-nav .jn-menu{display:none;flex-direction:column;background:#fff;border-top:1px solid var(--rule,#d6dee8);padding:8px 0 18px;",
    "box-shadow:0 14px 28px rgba(15,31,58,.08);max-height:calc(100vh - " + NAV_H + "px);overflow-y:auto;}",
    "#jii-nav .jn-menu.jn-open{display:flex;}",
    "#jii-nav .jn-menu a{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:15px;color:var(--ink,#1a2a4a);padding:14px 32px;}",
    "#jii-nav .jn-menu .jn-menu-sub{font-size:13px;color:var(--text-mid,#4a5566);padding-left:48px;}",
    "#jii-nav .jn-menu .jn-cta{margin:14px 32px 0;text-align:center;}",
    "@media(max-width:1120px){#jii-nav .jn-links,#jii-nav .jn-right .jn-cta{display:none;}#jii-nav .jn-burger{display:block;}",
    "#jii-nav .jn-right{margin-left:auto;order:2;}#jii-nav .jn-burger{order:3;margin-left:0;}}",
    "@media(min-width:1121px){#jii-nav .jn-menu{display:none!important;}}",
    "@media(max-width:760px){#jii-nav .jn-bar,#jii-nav .jn-sub-in{padding:0 22px;}}",
    "@media(max-width:560px){#jii-nav .jn-logo img{display:none;}#jii-nav .jn-logo .jn-logo-sm{display:block;}}",
    /* retire the old systems wherever they still exist on the page */
    "nav#main-nav,nav.mobile-menu,#cmpnav{display:none!important;}",
    "@media(prefers-reduced-motion:reduce){#jii-nav *{transition:none!important;}}"
  ].join("");

  /* Compounder profile pages carry their own logo and breadcrumb inside the
     masthead. The bar above now provides the route home, so those stay
     hidden to avoid two logos stacked on top of each other. */
  if (inCompounders) {
    css += ".hero-brand,.crumb,.masthead-inner .brand-home-link{display:none!important;}";
  }

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  /* ---------- 4. Build it ---------- */

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c];
    });
  }

  var other = counterpart();
  var linksHtml = "", menuHtml = "";

  for (var i = 0; i < SECTIONS.length; i++) {
    var s = SECTIONS[i], h = href(s), on = isActive(h);
    linksHtml += '<li><a href="' + esc(h) + '"' + (on ? ' class="jn-on" aria-current="page"' : '') + '>' + esc(label(s)) + '</a></li>';
    menuHtml += '<a href="' + esc(h) + '">' + esc(label(s)) + '</a>';
  }

  if (inCompounders) {
    for (var j = 0; j < SUBTABS.length; j++) {
      var t = SUBTABS[j];
      menuHtml += '<a class="jn-menu-sub" href="' + esc((isEn ? "/en" : "") + t.path) + '">' + esc(isEn ? t.en : t.ja) + '</a>';
    }
  }

  menuHtml += '<a href="' + esc(isEn ? "/" : "/en/") + '" lang="' + (isEn ? "ja" : "en") + '">' + (isEn ? "日本語" : "English") + '</a>';
  menuHtml += '<a class="jn-cta" href="' + esc(href(CONTACT)) + '">' + esc(label(CONTACT)) + '</a>';

  var subHtml = "";
  if (inCompounders) {
    var P = isEn ? "/en" : "";
    subHtml += '<div class="jn-sub"><div class="jn-sub-in">';
    subHtml += '<a href="' + P + '/compounders/"' + (path.replace(/\/$/, "") === (P + "/compounders").replace(/\/$/, "") ? ' class="jn-on"' : '') + '>' +
               esc(isEn ? "Overview" : "概要") + '</a>';
    for (var k = 0; k < SUBTABS.length; k++) {
      var tb = SUBTABS[k], hp = P + tb.path;
      var act = path.indexOf(hp) === 0 ||
                (tb.k === "profiles" && /\/compounders\/[0-9A-Za-z]{3,5}\//.test(path));
      subHtml += '<a href="' + esc(hp) + '"' + (act ? ' class="jn-on" aria-current="page"' : '') + '>' + esc(isEn ? tb.en : tb.ja) + '</a>';
    }
    subHtml += '</div></div>';
  }

  var html =
    '<div class="jn-bar">' +
      '<a class="jn-logo" href="' + homeHref + '" aria-label="' + (isEn ? "JII home" : "JII トップページへ") + '">' +
        '<img src="/assets/logo-jii-wordmark.svg" alt="Japan Investor Interface" width="282" height="40" decoding="async" fetchpriority="high">' +
        '<img class="jn-logo-sm" src="/assets/logo-jii-monogram.svg" alt="Japan Investor Interface" width="32" height="32" decoding="async">' +
      '</a>' +
      '<ul class="jn-links" role="list">' + linksHtml + '</ul>' +
      '<div class="jn-right">' +
        '<span class="jn-lang" aria-label="' + (isEn ? "Language switcher" : "言語切替") + '">' +
          '<a' + (!isEn ? ' class="jn-cur" aria-current="page"' : '') + ' href="' + esc(isEn ? other : path) + '" lang="ja">JP</a>' +
          '<span aria-hidden="true">·</span>' +
          '<a' + (isEn ? ' class="jn-cur" aria-current="page"' : '') + ' href="' + esc(isEn ? path : other) + '" lang="en">EN</a>' +
        '</span>' +
        '<a class="jn-cta" href="' + esc(href(CONTACT)) + '">' + esc(label(CONTACT)) + '</a>' +
      '</div>' +
      '<button class="jn-burger" aria-label="Menu" aria-expanded="false" aria-controls="jii-nav-menu"><span></span><span></span><span></span></button>' +
    '</div>' +
    subHtml +
    '<nav class="jn-menu" id="jii-nav-menu" aria-label="' + (isEn ? "Mobile navigation" : "モバイルナビゲーション") + '">' + menuHtml + '</nav>';

  var nav = document.createElement("header");
  nav.id = "jii-nav";
  nav.setAttribute("role", "navigation");
  nav.setAttribute("aria-label", isEn ? "Main navigation" : "メインナビゲーション");
  nav.innerHTML = html;
  document.body.insertBefore(nav, document.body.firstChild);

  /* ---------- 5. Reserve space ----------
     Pages that load site.css already leave room for a 64px fixed bar.
     Pages that do not (every Compounder profile) need it added here. */
  var hasSiteCss = !!document.querySelector('link[href*="site.css"]');
  if (!hasSiteCss) {
    document.body.style.paddingTop = (NAV_H + (inCompounders ? SUB_H : 0)) + "px";
  } else if (inCompounders) {
    document.body.style.paddingTop = SUB_H + "px";
  }

  /* ---------- 6. Behavior ---------- */

  var burger = nav.querySelector(".jn-burger");
  var menu = nav.querySelector("#jii-nav-menu");

  function setOpen(open) {
    menu.classList.toggle("jn-open", open);
    burger.setAttribute("aria-expanded", String(open));
  }
  burger.addEventListener("click", function () {
    setOpen(!menu.classList.contains("jn-open"));
  });
  document.addEventListener("click", function (e) {
    if (!nav.contains(e.target)) setOpen(false);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setOpen(false);
  });

  /* Older pages call toggleMenu() from inline onclick handlers. Keep the
     name alive so those never throw after the old markup is removed. */
  if (typeof window.toggleMenu !== "function") {
    window.toggleMenu = function () { setOpen(!menu.classList.contains("jn-open")); };
  }

  window.addEventListener("scroll", function () {
    nav.style.boxShadow = window.scrollY > 40 ? "0 1px 14px rgba(15,31,58,.07)" : "none";
  }, { passive: true });
})();
