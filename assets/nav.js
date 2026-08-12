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
  /* Every section opens a panel. `img` is the tile photo; sections without
     their own FOOTER column carry an explicit `items` list of the pages
     that belong with them. */
  var SECTIONS = [
    /* Leftmost on purpose. This is the page a cold-pitch recipient lands on,
       and it is the only one that answers "what is this company" before the
       reader has to pick a service. It carries no dropdown: it is a single
       page, and a panel would put a menu between the reader and the answer. */
    { ja: "すぐわかるJII", en: "About JII", jaHref: "/%E3%81%99%E3%81%90%E3%82%8F%E3%81%8B%E3%82%8BJII/", enHref: "/en/about-jii/",
      panel: false },
    { ja: "サービス",     en: "Services", jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/", enHref: "/en/services/",
      panel: true, img: "slot02_mendan_card" },
    { ja: "料金",         en: "Pricing",  jaHref: "/%E6%96%99%E9%87%91/",                   enHref: "/en/pricing/",
      panel: true, img: "slot01_kaiji_card",
      items: [
        { ja: "料金表",       en: "Pricing",            jaHref: "/%E6%96%99%E9%87%91/",                   enHref: "/en/pricing/" },
        { ja: "特急翻訳",     en: "Express translation", jaHref: "/%E7%89%B9%E6%80%A5%E7%BF%BB%E8%A8%B3/", enHref: "/%E7%89%B9%E6%80%A5%E7%BF%BB%E8%A8%B3/" },
        { ja: "よくある質問", en: "FAQ",                jaHref: "/faq/",                                  enHref: "/en/faq/" },
        { ja: "お問い合わせ", en: "Contact",            jaHref: "/%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B/", enHref: "/en/contact/" }
      ] },
    { ja: "会社概要",     en: "Company",  jaHref: "/%E4%BC%9A%E7%A4%BE%E6%A6%82%E8%A6%81/", enHref: "/en/company/",
      panel: true, img: "slot07_company_card",
      items: [
        { ja: "会社概要",             en: "Company profile", jaHref: "/%E4%BC%9A%E7%A4%BE%E6%A6%82%E8%A6%81/", enHref: "/en/company/" },
        { ja: "IR研修",               en: "IR training",     jaHref: "/governance/",  enHref: "/en/governance/" },
        { ja: "考察記事",             en: "Articles (JP)",   jaHref: "/articles/",    enHref: "/articles/" },
        { ja: "プライバシーポリシー", en: "Privacy policy",  jaHref: "/privacy/",     enHref: "/en/privacy/" },
        { ja: "サイトマップ",         en: "Sitemap",         jaHref: "/sitemap/",     enHref: "/en/sitemap/" }
      ] },
    { ja: "銘柄レポート", en: "Research", jaHref: "/compounders/",                          enHref: "/en/compounders/",
      panel: true, img: "free05_shoshu_card" }
  ];

  /* Look a section up by its Japanese name.
     The FOOTER below used to index SECTIONS by POSITION (SECTIONS[0],
     SECTIONS[2], SECTIONS[3]). On August 4, 2026 すぐわかるJII was inserted at
     the front of the array, which shifted every index by one and silently
     repointed all three footer columns at the wrong section heads. Nothing
     errors when that happens; the footer just renders wrong. Names do not
     shift, so the lookup is by name and it throws loudly if the name is gone.
     Do not go back to numbers. */
  function S(ja) {
    for (var i = 0; i < SECTIONS.length; i++) { if (SECTIONS[i].ja === ja) return SECTIONS[i]; }
    throw new Error("nav.js: no section named " + ja);
  }

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
    { head: S("サービス"), items: [
        { ja: "開示翻訳",   en: "Disclosure translation",  jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E9%96%8B%E7%A4%BA%E7%BF%BB%E8%A8%B3/", enHref: "/en/services/disclosure-translation/" },
        { ja: "IR通訳",     en: "IR interpretation",       jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/IR%E9%80%9A%E8%A8%B3/",                 enHref: "/en/services/ir-interpretation/" },
        { ja: "海外IR診断", en: "IR diagnosis",            jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E6%B5%B7%E5%A4%96IR%E8%A8%BA%E6%96%AD/", enHref: "/en/services/ir-diagnosis/" },
        { ja: "継続IR支援", en: "Ongoing IR support",      jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E7%B6%99%E7%B6%9AIR%E6%94%AF%E6%8F%B4/", enHref: "/en/services/ongoing-ir-support/" },
        { ja: "招集通知・有報・統合報告書翻訳", en: "AGM notice and annual report", jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/%E6%8B%9B%E9%9B%86%E9%80%9A%E7%9F%A5%E3%83%BB%E6%9C%89%E5%A0%B1%E3%83%BB%E7%B5%B1%E5%90%88%E5%A0%B1%E5%91%8A%E6%9B%B8%E7%BF%BB%E8%A8%B3/", enHref: "/en/services/annual-agm-translation/" },
        { ja: "特急翻訳",   en: "Express translation (JP)", jaHref: "/%E7%89%B9%E6%80%A5%E7%BF%BB%E8%A8%B3/",                                     enHref: "/%E7%89%B9%E6%80%A5%E7%BF%BB%E8%A8%B3/" },
        { ja: "AIと機密保持", en: "AI and confidentiality", jaHref: "/%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/AI%E3%81%A8%E6%A9%9F%E5%AF%86%E4%BF%9D%E6%8C%81/", enHref: "/en/services/ai-confidentiality/" }
      ] },
    { head: S("銘柄レポート"), items: [
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
    { head: S("会社概要"), items: [
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
    /* Japanese normally permits a line break between almost any two
       characters. That is appropriate for body copy, but it can split a
       heading in the middle of a word (リクエス / ト, for example).
       `auto-phrase` asks the browser to use natural bunsetsu boundaries.
       Section 6c supplies a word-level fallback for browsers that do not yet
       implement it. English keeps its normal wrapping rules. */
    "html[lang='ja'] :where(h1,h2,h3,h4,h5,h6){word-break:auto-phrase;line-break:strict;}",
    ".jii-no-break-word{white-space:nowrap;}",
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
    /* `align-self:stretch` + `align-items:stretch` make the <ul> and every <li>
       inside it exactly as tall as the 64px bar. That is what closes the gap
       described at .jn-pw below: the bottom edge of the hover target lands on
       the top edge of the panel, with nothing in between. Do not change either
       one back to `center` — the label stays vertically centered because each
       <li> is itself a centering flex box. */
    "#jii-nav .jn-links{flex:0 0 auto;align-self:stretch;display:flex;align-items:stretch;gap:44px;list-style:none;padding:0;margin:0 0 0 auto;}",
    /* `> li > a`, not a bare `a`. A bare descendant selector also matched every
       link INSIDE the dropdown panel, since the panel lives in the <li>, and it
       was putting the bar's 8px vertical padding on the panel's photo tile. */
    /* `line-height:20px` is here to hold the label exactly where it was.
       Making the <li> a flex box, two rules below, turns this anchor from an
       inline box into a block one, and a block box counts its line-height and
       its 8px padding toward its own height where an inline box did not. Left
       alone the label drifted about a pixel up and the gold underline a pixel
       down. 20px is the height the line box had before, so nothing moves. */
    "#jii-nav .jn-links > li > a{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:14px;letter-spacing:.05em;",
    "line-height:20px;color:var(--text,#1f2937);padding:8px 0;border-bottom:2px solid transparent;white-space:nowrap;transition:color .15s,border-color .15s;}",
    "#jii-nav .jn-links > li > a:hover{color:var(--ink,#1a2a4a);}",
    "#jii-nav .jn-links > li > a.jn-on{color:var(--ink,#1a2a4a);border-bottom-color:var(--accent,#9a7838);font-weight:500;}",
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
    /* `position:static` on purpose, so the panel below measures itself against
       #jii-nav and spans the full width of the window rather than the width of
       one label. `display:flex;align-items:center` makes the <li> fill the whole
       height of the bar while keeping its label centered — see .jn-links above. */
    "#jii-nav .jn-links > li{position:static;display:flex;align-items:center;}",
    /* WHY `top:64px` AND NOT `top:100%` — the bug fixed on August 4, 2026.
       The panel is only on screen while the CSS `:hover` on the <li> is true,
       and it vanishes the instant that stops being true. So every pixel between
       the bottom of the <li> and the top of the panel is a trap: the reader
       moves the mouse down toward a menu item, crosses that strip, the hover
       ends, and the panel closes before the click lands.

       Two separate faults put a strip there.

       First, the <li> used to be only as tall as its own text — about 25px,
       floating in the middle of a 64px bar — so roughly 19px of bar underneath
       the label belonged to no <li> at all. That is fixed above, by stretching
       the <li> to the full height of the bar.

       Second, `top:100%` measured 100% of #jii-nav, and #jii-nav is not just the
       bar. On every /compounders/ page it also contains the 46px row of section
       tabs, which pushed the panel down to y=110 and opened a 46px strip even
       once the <li> was full height. A fixed 64px is the bottom of the bar on
       every page, with or without that second row, so the panel now hangs
       directly off the bar and simply covers the tabs while it is open.

       Both numbers now come from the same NAV_H constant, so they cannot drift
       apart. If you ever change the height of the bar, change NAV_H and nothing
       else. */
    "#jii-nav .jn-pw{position:absolute;top:" + NAV_H + "px;left:0;right:0;z-index:1;display:none;",
    "background:#fff;border-top:1px solid var(--rule,#d6dee8);box-shadow:0 22px 44px rgba(15,31,58,.10);}",
    /* Two ways a panel can be open. `.jn-open` is a class that section 6b puts
       on the <li> for the mouse, and `:focus-within` covers a reader moving
       through the bar with the Tab key.

       There used to be a third, `li:hover`, and it is deliberately gone. Plain
       `:hover` is instantaneous and cannot be held or delayed, which is the
       whole difficulty section 6b exists to solve; leaving it in would have
       overridden the timing there and reopened the bug. Nothing is lost by
       removing it, because this entire bar is drawn by this script — a reader
       with JavaScript switched off has no navigation to fall back to, so there
       is no CSS-only case left to protect. */
    "@media(min-width:1001px){",
    "#jii-nav .jn-links > li:focus-within .jn-pw,",
    "#jii-nav .jn-links > li.jn-open .jn-pw{display:block;}",
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
    /* The tile: a photograph with a navy caption bar, Nikkato's own tile
       pattern. The photo zooms slightly on hover; the caption never moves. */
    "#jii-nav .jn-tile{display:block;text-decoration:none;border:1px solid var(--rule,#d6dee8);}",
    "#jii-nav .jn-timg{display:block;overflow:hidden;aspect-ratio:3/2;background:#f5f7fa;}",
    "#jii-nav .jn-timg img{width:100%;height:100%;object-fit:cover;display:block;",
    "transition:transform .6s ease;}",
    "#jii-nav .jn-tile:hover .jn-timg img{transform:scale(1.06);}",
    "#jii-nav .jn-tcap{display:flex;align-items:center;justify-content:space-between;gap:10px;",
    "background:var(--ink,#1a2a4a);padding:13px 16px;}",
    "#jii-nav .jn-tcap b{font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);font-size:13.5px;",
    "font-weight:500;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}",
    "#jii-nav .jn-tcap em{font-style:normal;font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);",
    "font-size:11.5px;color:#c9a464;white-space:nowrap;}",
    /* footer sitemap */
    /* flex rules because Compounder profile pages set body{display:flex} to
       center their column — without these the footer rendered as a dark
       column BESIDE the report instead of below it (seen August 3, 2026). */
    "body{flex-wrap:wrap;}",
    "#jii-foot{background:var(--ink,#1a2a4a);color:#cfd6e2;font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);",
    "font-size:13px;line-height:1.8;margin-top:0;flex:0 0 100%;width:100%;min-width:100%;}",
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
    /* Contact strip: a light visual bridge into the navy sitemap. The warm
       image treatment is deliberate; repeating navy here would merge the
       call to action and the footer into one undifferentiated block. */
    "#jii-contact{position:relative;overflow:hidden;flex:0 0 100%;width:100%;min-width:100%;",
    "background:#f3efe7;color:var(--text,#1f2937);font-family:var(--sans,'Noto Sans JP',system-ui,sans-serif);}",
    "#jii-contact .jfc-media{position:absolute;inset:0 0 0 48%;overflow:hidden;background:#ded7ca;}",
    "#jii-contact .jfc-media img{display:block;width:100%;height:100%;object-fit:cover;object-position:48% center;",
    "filter:saturate(.72) contrast(.96) brightness(1.03);}",
    "#jii-contact .jfc-media::after{content:'';position:absolute;inset:0;",
    "background:linear-gradient(90deg,#f3efe7 0%,rgba(243,239,231,.84) 14%,rgba(243,239,231,.12) 54%,rgba(243,239,231,.03) 100%);}",
    "#jii-contact .jfc-in{position:relative;z-index:1;max-width:1100px;min-height:330px;margin:0 auto;",
    "padding:64px 48px;display:flex;align-items:center;}",
    "#jii-contact .jfc-copy{width:48%;max-width:510px;}",
    "#jii-contact .jfc-kicker{display:block;margin-bottom:12px;font-family:var(--mono,'DM Mono',monospace);",
    "font-size:10.5px;letter-spacing:.2em;color:var(--accent,#9a7838);}",
    "#jii-contact h2{margin:0;font-family:var(--serif,'Noto Serif JP','Yu Mincho',serif);",
    "font-size:clamp(25px,2.6vw,34px);font-weight:300;line-height:1.5;letter-spacing:.03em;color:var(--ink,#1a2a4a);}",
    "#jii-contact .jfc-rule{width:32px;height:2px;margin:16px 0 20px;background:var(--accent,#9a7838);}",
    "#jii-contact p{max-width:430px;margin:0;font-size:14px;line-height:1.9;color:var(--text-mid,#4a5566);}",
    "#jii-contact .jfc-btn{display:inline-flex;align-items:center;justify-content:space-between;gap:30px;",
    "min-width:220px;margin-top:26px;padding:13px 17px 13px 20px;border:1px solid var(--ink,#1a2a4a);",
    "background:var(--ink,#1a2a4a);color:#fff;text-decoration:none;font-size:13px;letter-spacing:.04em;",
    "transition:background .2s,color .2s,transform .2s;}",
    "#jii-contact .jfc-btn::after{content:'→';color:#d4b675;font-size:15px;line-height:1;}",
    "#jii-contact .jfc-btn:hover{background:#fff;color:var(--ink,#1a2a4a);text-decoration:none;transform:translateY(-2px);}",
    /* Floating top control. The text link remains available as an aria-label,
       while the visible control is the same quiet circular gesture on every
       background and in both languages. */
    "#jii-top{position:fixed;right:clamp(16px,2.7vw,40px);bottom:clamp(16px,2.7vw,32px);z-index:95;",
    "width:48px;height:48px;border:1px solid rgba(255,255,255,.34);border-radius:50%;padding:0;",
    "background:var(--ink-mid,#172641);box-shadow:0 7px 20px rgba(15,31,58,.22);cursor:pointer;",
    "opacity:0;visibility:hidden;pointer-events:none;transform:translateY(10px);",
    "transition:opacity .2s,transform .2s,visibility .2s,background .2s;}",
    "#jii-top::before{content:'';position:absolute;left:50%;top:52%;width:9px;height:9px;",
    "border-left:1.5px solid #fff;border-top:1.5px solid #fff;transform:translate(-50%,-30%) rotate(45deg);}",
    "#jii-top.jt-visible{opacity:1;visibility:visible;pointer-events:auto;transform:translateY(0);}",
    "#jii-top:hover{background:#263b60;}",
    "#jii-top:focus-visible{outline:3px solid rgba(154,120,56,.55);outline-offset:3px;}",
    "@media(max-width:860px){#jii-foot .jf-cols{grid-template-columns:repeat(2,minmax(0,1fr));gap:26px;}}",
    "@media(max-width:700px){#jii-contact .jfc-media{position:relative;inset:auto;width:100%;height:190px;}",
    "#jii-contact .jfc-media::after{background:linear-gradient(0deg,#f3efe7 0%,rgba(243,239,231,.08) 42%);}",
    "#jii-contact .jfc-in{min-height:0;padding:38px 22px 48px;}#jii-contact .jfc-copy{width:100%;max-width:520px;}",
    "#jii-contact .jfc-btn{min-width:0;width:100%;max-width:330px;}}",
    "@media(max-width:520px){#jii-foot .jf-cols{grid-template-columns:1fr;}#jii-foot .jf-in{padding:40px 22px 26px;}",
    "#jii-foot .jf-mark{flex-direction:column;align-items:flex-start;}}",
    /* retire the old systems wherever they still exist on the page */
    "nav#main-nav,nav.mobile-menu,#cmpnav{display:none!important;}",
    "footer:has(.footer-row){display:none!important;}",
    "footer .footer-row,footer .footer-bottom{display:none!important;}",
    "@media(prefers-reduced-motion:reduce){#jii-nav *,#jii-contact *,#jii-top{transition:none!important;}}"
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
    /* The list: the section's own `items` if it declares them, otherwise
       the FOOTER column with the same head — so dropdown, footer and
       sitemap read from one source wherever they overlap. */
    var items = section.items || null;
    if (!items) {
      for (var f = 0; f < FOOTER.length; f++) {
        if (FOOTER[f].head === section) items = FOOTER[f].items;
      }
    }
    if (!items) return "";
    var links = "";
    for (var g = 0; g < items.length; g++) {
      links += '<a href="' + esc(href(items[g])) + '">' + esc(label(items[g])) + '</a>';
    }
    return '<div class="jn-pw"><div class="jn-pin">' +
      '<div class="jn-pcols">' + links + '</div>' +
      '<a class="jn-tile" href="' + esc(href(section)) + '">' +
        /* `section.img` needs BOTH /assets/photos/{img}.webp AND {img}@2x.webp to
           exist. From August 3 to August 4, 2026 サービス pointed at
           slot02_mendan_card, which had never been generated, and the panel showed
           the browser's broken-image icon to every visitor who hovered it. The
           onerror below hides the picture area so a missing file degrades to a
           caption-only tile instead of a broken icon — but that is a safety net,
           not permission to ship a missing image. Check the file exists. */
        '<span class="jn-timg"><img src="/assets/photos/' + section.img + '.webp" ' +
          'srcset="/assets/photos/' + section.img + '.webp 1x, /assets/photos/' + section.img + '@2x.webp 2x" ' +
          'alt="" loading="lazy" decoding="async" ' +
          'onerror="this.parentNode.style.display=\'none\'"></span>' +
        '<span class="jn-tcap"><b>' + esc(label(section)) + '</b>' +
        '<em>' + (isEn ? "Open →" : "詳しく見る →") + '</em></span>' +
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
        '<img src="/assets/logo-jii-wordmark.svg" alt="Japan Investor Interface" width="328" height="40" decoding="async" fetchpriority="high">' +
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
      '<div class="jf-cols">' + colsHtml + '</div>' +
      '<div class="jf-mark">' +
        '<a href="' + homeHref + '" aria-label="' + (isEn ? "JII home" : "JII トップページへ") + '">' +
          '<img src="/assets/logo-jii-wordmark-white.svg" alt="Japan Investor Interface Co., Ltd." width="328" height="40" loading="lazy" decoding="async">' +
        '</a>' +
        '<div class="jf-policy">' + policyHtml + '</div>' +
      '</div>' +
      '<div class="jf-legal">' + (isEn ? LEGAL_EN : LEGAL_JA) + '</div>' +
    '</div>';
  /* Do not append the shared contact strip when the page already supplies a
     contextual CTA or an inquiry form. One clear conversion endpoint is
     enough; the shared strip is only a fallback for pages without one. */
  var onContact = path.replace(/\/$/, "") === href(CONTACT).replace(/\/$/, "");
  var hasPageContact = document.querySelector(
    "#inquiry-form, #urgent-form, .cta-band, .cta-box, .contact-band"
  );
  if (!onContact && !hasPageContact) {
    var contactStrip = document.createElement("section");
    contactStrip.id = "jii-contact";
    contactStrip.setAttribute("aria-labelledby", "jii-contact-title");
    contactStrip.innerHTML =
      '<div class="jfc-media" aria-hidden="true">' +
        '<img src="/assets/photos/slot10_contact.webp" ' +
          'srcset="/assets/photos/slot10_contact.webp 1x, /assets/photos/slot10_contact@2x.webp 2x" ' +
          'alt="" loading="lazy" decoding="async">' +
      '</div>' +
      '<div class="jfc-in"><div class="jfc-copy">' +
        '<span class="jfc-kicker">CONTACT</span>' +
        '<h2 id="jii-contact-title">' + (isEn ? "Inquiries and quotes" : "ご相談・お見積り") + '</h2>' +
        '<div class="jfc-rule" aria-hidden="true"></div>' +
        '<p>' + (isEn
          ? "You are welcome to contact us before the scope or timing is fixed. We can arrange an NDA before materials are shared."
          : "資料や納期が決まっていなくても、ご相談いただけます。必要に応じて、資料を共有する前にNDAを締結します。") + '</p>' +
        '<a class="jfc-btn" href="' + esc(href(CONTACT)) + '">' +
          (isEn ? "Go to contact form" : "お問い合わせフォームへ") + '</a>' +
      '</div></div>';
    document.body.appendChild(contactStrip);
  }

  document.body.appendChild(foot);

  var topButton = document.createElement("button");
  topButton.id = "jii-top";
  topButton.type = "button";
  topButton.setAttribute("aria-label", isEn ? "Back to top" : "ページ上部へ戻る");
  topButton.setAttribute("title", isEn ? "Back to top" : "ページ上部へ戻る");
  document.body.appendChild(topButton);

  function syncTopButton() {
    topButton.classList.toggle("jt-visible", window.scrollY > Math.max(320, window.innerHeight * 0.5));
  }
  topButton.addEventListener("click", function () {
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
  });
  window.addEventListener("scroll", syncTopButton, { passive: true });
  syncTopButton();

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

  /* ---------- 6a. Phrase-safe Japanese headings ----------

     Chrome/Edge and current WebKit understand `word-break:auto-phrase`, which
     produces the best Japanese line breaks. Older engines ignore that value.
     For those engines, protect the words inside headings with small inline
     spans so a line can move before or after リクエスト, ガバナンス, etc., but
     never through the word itself.

     Intl.Segmenter occasionally splits one katakana loanword into several
     short pieces (ガバ / ナン / ス). Adjacent short katakana pieces are merged
     again before spans are written. Long compounds retain the larger word
     boundaries so they do not become a single unbreakable line. */
  function protectJapaneseHeadingWords() {
    if (isEn || !window.Intl || !Intl.Segmenter) return;
    if (window.CSS && CSS.supports && CSS.supports("word-break", "auto-phrase")) return;

    var segmenter = new Intl.Segmenter("ja", { granularity: "word" });
    var headings = document.querySelectorAll("h1,h2,h3,h4,h5,h6");
    var katakana = /^[\u30A0-\u30FF\u31F0-\u31FF\uFF65-\uFF9F]+$/;

    function appendWord(fragment, value) {
      var span = document.createElement("span");
      span.className = "jii-no-break-word";
      span.textContent = value;
      fragment.appendChild(span);
    }

    function appendKatakanaRun(fragment, pieces) {
      var shortRun = "";
      for (var i = 0; i < pieces.length; i++) {
        var value = pieces[i];
        if (value.length <= 3) {
          shortRun += value;
        } else {
          if (shortRun) { appendWord(fragment, shortRun); shortRun = ""; }
          appendWord(fragment, value);
        }
      }
      if (shortRun) appendWord(fragment, shortRun);
    }

    for (var h = 0; h < headings.length; h++) {
      var walker = document.createTreeWalker(headings[h], NodeFilter.SHOW_TEXT);
      var nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);

      for (var n = 0; n < nodes.length; n++) {
        var node = nodes[n];
        if (!node.nodeValue || !node.nodeValue.trim()) continue;
        if (node.parentElement && node.parentElement.closest(".jii-no-break-word,svg,script,style")) continue;

        var segments = Array.from(segmenter.segment(node.nodeValue));
        var fragment = document.createDocumentFragment();
        for (var s = 0; s < segments.length;) {
          var part = segments[s];
          if (part.isWordLike && katakana.test(part.segment)) {
            var run = [];
            while (s < segments.length && segments[s].isWordLike && katakana.test(segments[s].segment)) {
              run.push(segments[s].segment);
              s++;
            }
            appendKatakanaRun(fragment, run);
          } else {
            if (part.isWordLike) appendWord(fragment, part.segment);
            else fragment.appendChild(document.createTextNode(part.segment));
            s++;
          }
        }
        node.parentNode.replaceChild(fragment, node);
      }
    }
  }
  protectJapaneseHeadingWords();

  /* ---------- 6b. Keeping a dropdown panel open ----------

     The CSS above can open a panel on its own, and on the straight path down
     from a tab into the panel it is enough. It is not enough on the path a hand
     actually takes.

     The reason is that the row of tabs is not one solid strip. There is a 44px
     space between one tab and the next, and that space belongs to no tab at
     all. A reader who hovers 会社概要 near the right of the bar and heads for
     サイトマップ, which sits at the far left of the panel, does not travel down
     and then left in two straight moves. The hand cuts the corner. On the way
     the pointer clips one of those 44px spaces, every `:hover` in the bar goes
     false at once, and the panel is gone before the click arrives — the same
     symptom as the vertical gap fixed above, from a different hole.

     So the panel does not close the moment the pointer leaves. Leaving starts a
     180ms timer, and coming back anywhere inside the bar or the panel cancels
     it. A clipped corner is over in a few milliseconds, so the panel never
     notices. A reader who has genuinely left sees it close, slightly late,
     which nobody reads as a fault.

     Note what the pointerover handler does when the pointer is over a space
     between two tabs: `closest("li")` finds nothing, and the handler returns
     without touching anything. The open panel simply stays open. That is the
     whole repair for the gaps.

     Touch is excluded. A tap fires pointerover with no matching pointerout, so
     a touch-opened panel would stay on screen until the next tap somewhere
     else. Phones get the burger menu instead, and it is separate from this. */

  var links = nav.querySelector(".jn-links");
  var openLi = null;            /* the <li> whose panel is on screen, or null */
  var closeTimer = null;        /* pending "close what is open"               */
  var switchTimer = null;       /* pending "swap to a different tab"          */
  var pendingLi = null;         /* which tab that pending swap is aimed at.
                                   A separate variable because setTimeout gives
                                   back a plain number in a browser, so there is
                                   nothing on the timer to hang this on. */

  function cancelClose() { if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; } }
  function cancelSwitch() { if (switchTimer) { clearTimeout(switchTimer); switchTimer = null; } pendingLi = null; }

  function showPanel(li) {
    cancelClose(); cancelSwitch();
    if (openLi && openLi !== li) openLi.classList.remove("jn-open");
    openLi = li;
    li.classList.add("jn-open");
  }
  function hidePanel() {
    cancelClose(); cancelSwitch();
    if (openLi) { openLi.classList.remove("jn-open"); openLi = null; }
  }
  function hidePanelSoon() {
    cancelClose(); cancelSwitch();
    closeTimer = setTimeout(hidePanel, 180);
  }

  /* Opening the first panel is instant. Swapping to a DIFFERENT tab while one
     is already open waits 140ms, and here is why.

     Look at where things are on a 1440px window. The 会社概要 tab occupies
     x=964 to x=1023. Its first menu item sits at about x=115, roughly 850px to
     the left. Nobody travels that distance as two straight lines. The hand
     leaves the tab heading down and to the left at once, and on the way through
     the bar it passes over 料金 and サービス. Swapping on contact would hand the
     reader サービス's menu when they were already halfway to a サイトマップ link
     they could see.

     A pass costs a few tens of milliseconds. Deliberately choosing another tab
     means resting on it. 140ms tells those two apart, and is short enough that
     a deliberate move still feels immediate. */
  function showPanelSoon(li) {
    if (openLi === li) { cancelClose(); cancelSwitch(); return; }
    if (!openLi) { showPanel(li); return; }
    cancelClose();
    if (pendingLi === li) return;
    cancelSwitch();
    pendingLi = li;
    switchTimer = setTimeout(function () { switchTimer = null; pendingLi = null; showPanel(li); }, 140);
  }

  links.addEventListener("pointerover", function (e) {
    if (e.pointerType === "touch") return;
    var li = e.target.closest ? e.target.closest("li") : null;
    /* Nothing under the pointer, which happens in the 44px space between two
       tabs. Leave whatever is open alone — that is the repair for the gaps. */
    if (!li || !links.contains(li)) return;
    if (li.querySelector(".jn-pw")) showPanelSoon(li);
    else hidePanelSoon();   /* すぐわかるJII has no panel of its own */
  });
  /* pointerleave counts the panel as inside, because the panel is a descendant
     of the <li>. Moving from the tab down into the panel therefore does not
     fire this at all. It fires when the reader leaves the navigation. */
  links.addEventListener("pointerleave", function (e) {
    if (e.pointerType === "touch") return;
    hidePanelSoon();
  });
  /* A click inside the panel is followed by a page load, but a link to the
     page you are already on does not reload, and the panel would sit there. */
  links.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest(".jn-pw")) hidePanel();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hidePanel();
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
