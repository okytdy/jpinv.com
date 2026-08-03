/* ===================================================================
   jpinv.com — THE navigation. One file for the whole site.

   Replaces two older systems:
     1. the <nav id="main-nav"> block that was pasted into 97 pages
     2. assets/compounders-nav.js, which drew a separate bar with its own
        brand and no route back to the main site

   Include on every page with one line, where the version is a hash of this
   file stamped by tools/bump_nav_version.py:
     <script src="/assets/nav.js?v=HASH" defer></script>

   AFTER ANY EDIT TO THIS FILE, RUN tools/bump_nav_version.py. Without it the
   browser keeps serving the copy it already cached and the site looks
   unchanged.

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

  /* The top bar. Four sections, in the order a first-time visitor needs
     them: what we do, what it costs, who we are, what we publish. */
  /* `panel` names the FOOTER column (by head) whose items open in a
     dropdown under the bar, Nikkato-style. 料金 and 会社概要 are single
     pages, so they stay plain links. */
  var SECTIONS = [
    { ja: "サービス",     en: "Services", jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/", enHref: "/en/services/", panel: true,
      tag: { ja: "英文開示から面談まで", en: "Disclosure to the meeting" } },
    { ja: "料金",         en: "Pricing",  jaHref: "/%E6%96%99%E9%87%91/",                   enHref: "/en/pricing/" },
    { ja: "会社概要",     en: "Company",  jaHref: "/%E4%BC%9A%E7%A4%BE%E6%A6%82%E8%A6%81/", enHref: "/en/company/" },
    { ja: "銘柄レポート", en: "Research", jaHref: "/compounders/",                          enHref: "/en/compounders/", panel: true,
      tag: { ja: "日本株を、日英で読み解く", en: "Japanese equities, in both languages" } }
  ];

  /* Reachable, but not from the top bar. These appear in the mobile menu
     and in the footer. IR研修 and FAQ live here because a visitor who has
     never heard of JII does not need either one to decide anything. */
  var SECONDARY = [
    { ja: "IR研修", en: "IR Training", jaHref: "/governance/", enHref: "/en/governance/" },
    { ja: "FAQ",    en: "FAQ",         jaHref: "/faq/",        enHref: "/en/faq/" }
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

  /* ---------- 1b. THE FOOTER SITEMAP. Same idea: edit here only. ----------
     One column per section. The column head is the section's own landing
     page; the items under it are the pages inside that section.

     The footer is a navigational summary, not a complete index. IR研修 has
     34 pages and 銘柄レポート has 32 profiles; listing all of them here
     would bury the sections that sell. The complete index is /sitemap/. */

  var FOOTER = [
    { head: SECTIONS[0], items: [
        { ja: "開示翻訳",   en: "Disclosure translation",  jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E9%96%8B%E7%A4%BA%E7%BF%BB%E8%A8%B3/", enHref: "/en/services/disclosure-translation/" },
        { ja: "IR通訳",     en: "IR interpretation",       jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/IR%E9%80%9A%E8%A8%B3/",                 enHref: "/en/services/ir-interpretation/" },
        { ja: "海外IR診断", en: "IR diagnosis",            jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E6%B5%B7%E5%A4%96IR%E8%A8%BA%E6%96%AD/", enHref: "/en/services/ir-diagnosis/" },
        { ja: "継続IR支援", en: "Ongoing IR support",      jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E7%B6%99%E7%B6%9AIR%E6%94%AF%E6%8F%B4/", enHref: "/en/services/ongoing-ir-support/" },
        { ja: "招集通知・有報・統合報告書翻訳", en: "AGM notice and annual report", jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E6%8B%9B%E9%9B%86%E9%80%9A%E7%9F%A5%E3%83%BB%E6%9C%89%E5%A0%B1%E3%83%BB%E7%B5%B1%E5%90%88%E5%A0%B1%E5%91%8A%E6%9B%B8%E7%BF%BB%E8%A8%B3/", enHref: "/en/services/annual-agm-translation/" },
        { ja: "特急翻訳",   en: "Express translation (JP)", jaHref: "/%E7%89%B9%E6%80%A5%E7%BF%BB%E8%A8%B3/",                                     enHref: "/%E7%89%B9%E6%80%A5%E7%BF%BB%E8%A8%B3/" },
        { ja: "AIと機密保持", en: "AI and confidentiality", jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/AI%E3%81%A8%E6%A9%9F%E5%AF%86%E4%BF%9D%E6%8C%81/", enHref: "/en/services/ai-confidentiality/" }
      ] },
    { head: SECTIONS[3], items: [
        { ja: "銘柄分析",           en: "Profiles",         jaHref: "/compounders/profiles/",          enHref: "/en/compounders/profiles/" },
        { ja: "銘柄スクリーニング", en: "Universe",         jaHref: "/compounders/universe/",          enHref: "/en/compounders/universe/" },
        { ja: "資本政策開示",       en: "Capital actions",  jaHref: "/compounders/feed/",              enHref: "/en/compounders/feed/" },
        { ja: "大量保有報告",       en: "5% filings",       jaHref: "/compounders/active-investors/",  enHref: "/en/compounders/active-investors/" },
        { ja: "着眼点",             en: "Methodology",      jaHref: "/compounders/methodology/",       enHref: "/en/compounders/methodology/" }
        /* シグナルログ (/compounders/signals/) is deliberately NOT listed here.
           It is a per-name history, not a destination: a reader reaches one
           name's log by clicking that name's Latest Signal cell on the universe
           page. The two market-wide feeds above are the destinations. The signal
           log still appears in full on /sitemap/. Decided by Teddy, August 3, 2026. */
      ] },
    { head: SECONDARY[0], items: [
        { ja: "改革の起源",     en: "Origins of reform",   jaHref: "/governance/foundations/",          enHref: "/en/governance/foundations/" },
        { ja: "コードの時代",   en: "The code era",        jaHref: "/governance/cg-code/",              enHref: "/en/governance/cg-code/" },
        { ja: "市場区分の見直し", en: "Market restructuring", jaHref: "/governance/market-restructuring/", enHref: "/en/governance/market-restructuring/" },
        { ja: "資本効率革命",   en: "Capital efficiency",  jaHref: "/governance/capital-efficiency/",   enHref: "/en/governance/capital-efficiency/" },
        { ja: "最前線",         en: "The frontier",        jaHref: "/governance/frontier/",             enHref: "/en/governance/frontier/" },
        { ja: "IRツールボックス", en: "IR toolbox",        jaHref: "/governance/toolbox/",              enHref: "/en/governance/toolbox/" }
      ] },
    { head: SECTIONS[2], items: [
        { ja: "料金",         en: "Pricing",  jaHref: "/%E6%96%99%E9%87%91/", enHref: "/en/pricing/" },
        { ja: "お問い合わせ", en: "Contact",  jaHref: CONTACT.jaHref,         enHref: CONTACT.enHref },
        { ja: "よくある質問", en: "FAQ",      jaHref: "/faq/",                enHref: "/en/faq/" },
        { ja: "考察記事",     en: "Articles (JP)", jaHref: "/articles/",      enHref: "/articles/" }
      ] }
  ];

  var POLICY = [
    { ja: "プライバシーポリシー", en: "Privacy policy", jaHref: "/privacy/", enHref: "/en/privacy/" },
    { ja: "サイトマップ",         en: "Sitemap",        jaHref: "/sitemap/", enHref: "/en/sitemap/" }
  ];

  var LEGAL_JA = "© Japan Investor Interface Co., Ltd.｜代表取締役 屋山テディ｜大阪府大阪市北区梅田1丁目2番2号 大阪駅前第2ビル 12-12";
  var LEGAL_EN = "© Japan Investor Interface Co., Ltd.｜Representative Director Teddy Okuyama｜Osaka Ekimae Dai-2 Bldg. 12-12, 1-2-2 Umeda, Kita-ku, Osaka";

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
    /* Full-bleed like Nikkato: logo hard left, sections centered in the
       space that is left, language and the contact block hard right. */
    "#jii-nav .jn-bar{height:" + NAV_H + "px;display:flex;align-items:center;padding:0 0 0 40px;}",
    "#jii-nav a{text-decoration:none;color:inherit;}",
    "#jii-nav .jn-logo{flex:0 0 auto;display:flex;align-items:center;}",
    "#jii-nav .jn-logo img{display:block;height:32px;width:auto;}",
    "#jii-nav .jn-logo .jn-logo-sm{display:none;height:30px;}",
    /* Links sit against the right group, not centered. Centering leaves a
       gap on both sides of them; Nikkato has one gap, after the logo. */
    "#jii-nav .jn-links{flex:0 0 auto;display:flex;align-items:center;gap:44px;list-style:none;padding:0;margin:0 0 0 auto;}",
    "#jii-nav .jn-links a{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:14px;letter-spacing:.05em;",
    "color:var(--text,#1f2937);padding:8px 0;border-bottom:2px solid transparent;white-space:nowrap;transition:color .15s,border-color .15s;}",
    "#jii-nav .jn-links a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-links a.jn-on{color:var(--ink,#1a2a4a);border-bottom-color:var(--accent,#9a7838);font-weight:500;}",
    "#jii-nav .jn-right{display:flex;align-items:stretch;flex:0 0 auto;height:100%;}",
    "#jii-nav .jn-lang{font-family:var(--mono,'DM Mono',monospace);font-size:11.5px;letter-spacing:.1em;color:var(--text-dim,#5f6875);",
    "display:flex;align-items:center;gap:7px;padding:0 32px 0 48px;}",
    "#jii-nav .jn-lang a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-lang .jn-cur{color:var(--ink,#1a2a4a);font-weight:600;}",
    "#jii-nav .jn-cta{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:13px;letter-spacing:.06em;",
    "background:var(--ink,#1a2a4a);color:#fff;display:flex;align-items:center;padding:0 34px;white-space:nowrap;transition:background .15s;}",
    "#jii-nav .jn-cta:hover{background:var(--accent,#9a7838);}",
    "#jii-nav .jn-burger{display:none;background:none;border:none;cursor:pointer;padding:8px;margin-left:auto;margin-right:22px;}",
    "#jii-nav .jn-burger span{display:block;width:22px;height:1.5px;background:var(--ink,#1a2a4a);margin:5px 0;transition:transform .2s,opacity .2s;}",
    /* section sub-tabs */
    "#jii-nav .jn-sub{border-top:1px solid var(--rule,#d6dee8);background:var(--bg-soft,#fafbfc);}",
    "#jii-nav .jn-sub-in{height:" + SUB_H + "px;padding:0 40px;display:flex;align-items:center;gap:26px;overflow-x:auto;}",
    "#jii-nav .jn-sub a{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:12.5px;color:var(--text-mid,#4a5566);",
    "padding:5px 0;border-bottom:2px solid transparent;white-space:nowrap;}",
    "#jii-nav .jn-sub a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-sub a.jn-on{color:var(--ink,#1a2a4a);border-bottom-color:var(--accent,#9a7838);font-weight:500;}",
    /* mobile */
    "#jii-nav .jn-menu{display:none;flex-direction:column;background:#fff;border-top:1px solid var(--rule,#d6dee8);padding:8px 0 18px;",
    "box-shadow:0 14px 28px rgba(15,31,58,.08);max-height:calc(100vh - " + NAV_H + "px);overflow-y:auto;}",
    "#jii-nav .jn-menu.jn-open{display:flex;}",
    "#jii-nav .jn-menu a{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:15px;color:var(--ink,#1a2a4a);padding:14px 40px;}",
    "#jii-nav .jn-menu .jn-menu-sub{font-size:13px;color:var(--text-mid,#4a5566);padding-left:58px;}",
    "#jii-nav .jn-menu .jn-menu-rule{border-top:1px solid var(--rule,#d6dee8);margin:8px 40px;}",
    /* This must come after ".jn-menu a", which is more specific than
       ".jn-cta" and was painting the contact button's text navy on navy —
       it rendered as an empty dark block. */
    "#jii-nav .jn-menu a.jn-cta{color:#fff;margin:16px 40px 0;justify-content:center;padding:15px 0;}",
    "@media(max-width:1000px){#jii-nav .jn-links,#jii-nav .jn-right .jn-cta{display:none;}#jii-nav .jn-burger{display:block;}",
    "#jii-nav .jn-right{margin-left:auto;order:2;}#jii-nav .jn-burger{order:3;margin-left:0;}",
    "#jii-nav .jn-lang{padding:0 4px 0 0;}}",
    "@media(min-width:1001px){#jii-nav .jn-menu{display:none!important;}}",
    "@media(max-width:760px){#jii-nav .jn-bar{padding-left:22px;}#jii-nav .jn-sub-in{padding:0 22px;}#jii-nav .jn-burger{margin-right:12px;}}",
    "@media(max-width:560px){#jii-nav .jn-logo img{display:none;}#jii-nav .jn-logo .jn-logo-sm{display:block;}}",
    /* ---- dropdown panels (desktop only) ----
       Nikkato's pattern: hover a section, a full-width white panel opens
       with the page list on the left and a visual tile on the right.
       White with a hairline top rule and a soft shadow — the panel is a
       sheet of paper under the bar, not a second dark block. The tile is
       navy so the panel carries the same two colors as the site: paper
       and ink, with gold only as the accent. */
    "#jii-nav .jn-links > li{position:static;}",
    "#jii-nav .jn-pw{position:absolute;top:100%;left:0;right:0;display:none;",
    "background:#fff;border-top:1px solid var(--rule,#d6dee8);box-shadow:0 22px 44px rgba(15,31,58,.10);}",
    "@media(min-width:1001px){",
    "#jii-nav .jn-links > li:hover .jn-pw,#jii-nav .jn-links > li:focus-within .jn-pw{display:block;}",
    "}",
    "#jii-nav .jn-pin{max-width:1100px;margin:0 auto;padding:38px 48px 42px;",
    "display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:52px;}",
    "#jii-nav .jn-pcols{display:grid;grid-template-columns:1fr 1fr;gap:0 44px;align-content:start;}",
    "#jii-nav .jn-pcols a{display:block;font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);",
    "font-size:13.5px;color:var(--text,#1f2937);padding:11px 2px;border-bottom:1px solid var(--rule,#d6dee8);",
    "transition:color .15s;position:relative;}",
    "#jii-nav .jn-pcols a::after{content:'→';position:absolute;right:4px;color:var(--accent,#9a7838);",
    "opacity:0;transition:opacity .15s;}",
    "#jii-nav .jn-pcols a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-pcols a:hover::after{opacity:1;}",
    "#jii-nav .jn-tile{display:flex;flex-direction:column;justify-content:center;gap:12px;",
    "background:var(--ink,#1a2a4a);padding:30px 32px;text-decoration:none;transition:background .15s;}",
    "#jii-nav .jn-tile:hover{background:var(--ink-mid,#172641);}",
    "#jii-nav .jn-tile b{font-family:var(--serif,'Noto Serif JP',serif);font-size:19px;font-weight:400;",
    "color:#fff;line-height:1.5;}",
    "#jii-nav .jn-tile i{font-style:normal;font-family:var(--mono,'DM Mono',monospace);font-size:10.5px;",
    "letter-spacing:.18em;color:#c9a464;}",
    "#jii-nav .jn-tile s{text-decoration:none;font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);",
    "font-size:12px;color:rgba(255,255,255,.75);}",
    "#jii-nav .jn-tile em{font-style:normal;font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);",
    "font-size:12px;color:#c9a464;margin-top:6px;}",
    /* footer sitemap */
    "#jii-foot{background:var(--ink,#1a2a4a);color:#cfd6e2;font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);",
    "font-size:13px;line-height:1.8;margin-top:0;}",
    "#jii-foot a{color:#cfd6e2;text-decoration:none;}",
    "#jii-foot a:hover{color:#fff;text-decoration:underline;}",
    "#jii-foot .jf-in{max-width:1100px;margin:0 auto;padding:56px 48px 30px;}",
    "#jii-foot .jf-cols{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:32px;}",
    "#jii-foot .jf-head{display:block;color:#fff;font-size:13.5px;font-weight:500;letter-spacing:.05em;",
    "padding-bottom:11px;margin-bottom:12px;border-bottom:1px solid rgba(255,255,255,.18);}",
    "#jii-foot ul{list-style:none;margin:0;padding:0;}",
    "#jii-foot li{margin-bottom:7px;font-size:12.5px;line-height:1.6;}",
    "#jii-foot li a{color:rgba(255,255,255,.72);}",
    "#jii-foot .jf-mark{margin-top:44px;padding-top:26px;border-top:1px solid rgba(255,255,255,.14);",
    "display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:18px;}",
    "#jii-foot .jf-mark img{height:26px;width:auto;display:block;}",
    "#jii-foot .jf-policy{display:flex;gap:22px;flex-wrap:wrap;font-size:12px;}",
    "#jii-foot .jf-legal{margin-top:20px;font-family:var(--mono,'DM Mono',monospace);font-size:11px;",
    "letter-spacing:.06em;color:rgba(255,255,255,.5);line-height:1.8;}",
    "#jii-foot .jf-top{display:block;text-align:right;font-size:11.5px;color:rgba(255,255,255,.6);padding-bottom:22px;}",
    "@media(max-width:860px){#jii-foot .jf-cols{grid-template-columns:repeat(2,minmax(0,1fr));gap:26px;}}",
    "@media(max-width:520px){#jii-foot .jf-cols{grid-template-columns:1fr;}#jii-foot .jf-in{padding:40px 22px 26px;}",
    "#jii-foot .jf-mark{flex-direction:column;align-items:flex-start;}}",
    /* retire the old systems wherever they still exist on the page */
    "nav#main-nav,nav.mobile-menu,#cmpnav{display:none!important;}",
    "footer:has(.footer-row){display:none!important;}",
    "footer .footer-row,footer .footer-bottom{display:none!important;}",
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

  function panelFor(section) {
    /* The panel's list is the FOOTER column with the same head, so the
       dropdown, the footer and the sitemap can never disagree. */
    var col = null;
    for (var f = 0; f < FOOTER.length; f++) {
      if (FOOTER[f].head === section) col = FOOTER[f];
    }
    if (!col) return "";
    var links = "";
    for (var g = 0; g < col.items.length; g++) {
      links += '<a href="' + esc(href(col.items[g])) + '">' + esc(label(col.items[g])) + '</a>';
    }
    return '<div class="jn-pw"><div class="jn-pin">' +
      '<div class="jn-pcols">' + links + '</div>' +
      '<a class="jn-tile" href="' + esc(href(section)) + '">' +
        '<i>' + esc(isEn ? section.ja : section.en).toUpperCase() + '</i>' +
        '<b>' + esc(label(section)) + '</b>' +
        '<s>' + esc(section.tag ? (isEn ? section.tag.en : section.tag.ja) : "") + '</s>' +
        '<em>' + (isEn ? "Open →" : "トップページへ →") + '</em>' +
      '</a>' +
    '</div></div>';
  }

  for (var i = 0; i < SECTIONS.length; i++) {
    var s = SECTIONS[i], h = href(s), on = isActive(h);
    linksHtml += '<li><a href="' + esc(h) + '"' + (on ? ' class="jn-on" aria-current="page"' : '') + '>' + esc(label(s)) + '</a>' +
                 (s.panel ? panelFor(s) : '') + '</li>';
    menuHtml += '<a href="' + esc(h) + '">' + esc(label(s)) + '</a>';
  }

  if (inCompounders) {
    for (var j = 0; j < SUBTABS.length; j++) {
      var t = SUBTABS[j];
      menuHtml += '<a class="jn-menu-sub" href="' + esc((isEn ? "/en" : "") + t.path) + '">' + esc(isEn ? t.en : t.ja) + '</a>';
    }
  }

  menuHtml += '<div class="jn-menu-rule"></div>';
  for (var m = 0; m < SECONDARY.length; m++) {
    menuHtml += '<a href="' + esc(href(SECONDARY[m])) + '">' + esc(label(SECONDARY[m])) + '</a>';
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
    /* A <div>, not a <nav>, on purpose. site.css carries
         nav:not(#main-nav):not(.mobile-menu){ … display:block … }
       which matched this element, outranked "#jii-nav .jn-menu" on
       specificity, and left the mobile menu permanently open with its items
       flowing in rows instead of a column. role="navigation" keeps the
       semantics without the collision. */
    '<div class="jn-menu" id="jii-nav-menu" role="navigation" aria-label="' +
      (isEn ? "Mobile navigation" : "モバイルナビゲーション") + '">' + menuHtml + '</div>';

  var nav = document.createElement("header");
  nav.id = "jii-nav";
  nav.setAttribute("role", "navigation");
  nav.setAttribute("aria-label", isEn ? "Main navigation" : "メインナビゲーション");
  nav.innerHTML = html;
  document.body.insertBefore(nav, document.body.firstChild);

  /* ---------- 4b. The footer sitemap ---------- */

  var colsHtml = "";
  for (var c1 = 0; c1 < FOOTER.length; c1++) {
    var col = FOOTER[c1], itemsHtml = "";
    for (var c2 = 0; c2 < col.items.length; c2++) {
      itemsHtml += '<li><a href="' + esc(href(col.items[c2])) + '">' + esc(label(col.items[c2])) + '</a></li>';
    }
    colsHtml += '<div><a class="jf-head" href="' + esc(href(col.head)) + '">' + esc(label(col.head)) +
                '</a><ul>' + itemsHtml + '</ul></div>';
  }

  var policyHtml = "";
  for (var c3 = 0; c3 < POLICY.length; c3++) {
    policyHtml += '<a href="' + esc(href(POLICY[c3])) + '">' + esc(label(POLICY[c3])) + '</a>';
  }

  var foot = document.createElement("footer");
  foot.id = "jii-foot";
  foot.innerHTML =
    '<div class="jf-in">' +
      '<a class="jf-top" href="#">' + (isEn ? "Back to top ↑" : "上へ戻る ↑") + '</a>' +
      '<div class="jf-cols">' + colsHtml + '</div>' +
      '<div class="jf-mark">' +
        '<a href="' + homeHref + '" aria-label="' + (isEn ? "JII home" : "JII トップページへ") + '">' +
          '<img src="/assets/logo-jii-wordmark-white.svg" alt="Japan Investor Interface Co., Ltd." width="282" height="40" loading="lazy" decoding="async">' +
        '</a>' +
        '<div class="jf-policy">' + policyHtml + '</div>' +
      '</div>' +
      '<div class="jf-legal">' + (isEn ? LEGAL_EN : LEGAL_JA) + '</div>' +
    '</div>';
  document.body.appendChild(foot);

  foot.querySelector(".jf-top").addEventListener("click", function (e) {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

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
  /* Close on a link tap. Navigation closes it anyway, but a same-page
     anchor would otherwise leave the panel covering what it jumped to. */
  menu.addEventListener("click", function (e) {
    if (e.target.closest("a")) setOpen(false);
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
