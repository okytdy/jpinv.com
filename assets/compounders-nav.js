/* ===================================================================
   JII Compounders — shared top tab navigation.
   Self-injecting: one <script src="/assets/compounders-nav.js" defer> per
   page renders a sticky horizontal tab bar (Universe · Profiles ·
   Active Investors · Signals Feed · Contact), auto-detecting the
   language (/en/ vs root) and the active tab from the URL. No dependencies.
   Edit the `tabs` array below to rename / reorder / add tabs in one place.
   =================================================================== */
(function () {
  "use strict";
  if (document.getElementById("cmpnav")) return;
  var p = location.pathname;
  var isEn = /^\/en(\/|$)/.test(p);
  var P = isEn ? "/en" : "";

  var tabs = [
    { k: "universe", en: "Universe",         ja: "ユニバース",       href: P + "/compounders/universe/" },
    { k: "profiles", en: "Profiles",         ja: "銘柄分析",         href: P + "/compounders/profiles/" },
    { k: "active",   en: "New 5% Disclosures", ja: "大量保有報告",       href: P + "/compounders/active-investors/" },
    { k: "signals",  en: "Signals Feed",     ja: "資本政策開示",     href: P + "/compounders/feed/" },
    { k: "contact",  en: "Contact",          ja: "お問い合わせ",     href: isEn ? "/en/contact/" : "/contact/" }
  ];

  var isLanding = /^\/(en\/)?compounders\/?$/.test(p);
  if (isLanding) {
    var anchors = { profiles: "#sec-profiles" };
    for (var ai = 0; ai < tabs.length; ai++) {
      if (anchors[tabs[ai].k]) tabs[ai].href = anchors[tabs[ai].k];
    }
  }

  function activeKey() {
    if (/\/compounders\/profiles\//.test(p)) return "profiles";
    if (/\/compounders\/active-investors\//.test(p)) return "active";
    if (/\/compounders\/feed\//.test(p)) return "signals";
    if (/\/compounders\/universe\//.test(p)) return "universe";
    if (/\/contact\//.test(p)) return "contact";
    // an individual profile page /compounders/{ticker}/ -> Profiles
    if (/\/compounders\/[0-9A-Za-z]{3,5}\/?$/.test(p.replace(/^\/en/, ""))) return "profiles";
    return "";  // the compounders landing — no tab highlighted
  }
  var ak = activeKey();
  var home = P + "/compounders/";
  var toEn = isEn ? p : ("/en" + p);
  var toJa = isEn ? (p.replace(/^\/en/, "") || "/") : p;

  var css =
    ".cmpnav{position:fixed;top:0;left:0;right:0;z-index:1000;background:#fff;border-bottom:1px solid var(--rule,#d6dee8);" +
    "font-family:var(--sans,system-ui,sans-serif);}" +
    ".cmpnav-in{max-width:1320px;margin:0 auto;padding:0 28px;display:flex;align-items:center;justify-content:space-between;gap:10px;height:54px;}" +
    ".cmpnav-brand{display:flex;align-items:center;gap:10px;text-decoration:none;flex:0 0 auto;}" +
    ".cmpnav-mark{font-family:var(--serif,Georgia,serif);font-size:20px;font-weight:300;color:var(--ink-mid,#172641);letter-spacing:.04em;}" +
    ".cmpnav-pipe{color:var(--accent,#b08a4a);margin:0 2px;font-weight:200;}" +
    ".cmpnav-wm{font-family:var(--mono,monospace);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-soft,#304466);}" +
    ".cmpnav-tabs{display:contents;}" +
    "@media(max-width:1100px){.cmpnav-tab{padding:8px 8px;font-size:12.5px;}}" +
    ".cmpnav-tab{font-family:var(--sans,sans-serif);font-size:13px;color:var(--text-mid,#4a5566);text-decoration:none;" +
    "padding:8px 13px;white-space:nowrap;border-bottom:2px solid transparent;transition:color .15s,border-color .15s;}" +
    ".cmpnav-tab:hover{color:var(--ink,#1a2a4a);}" +
    ".cmpnav-on{color:var(--ink-mid,#172641);border-bottom-color:var(--accent,#b08a4a);font-weight:500;}" +
    ".cmpnav-lang{font-family:var(--mono,monospace);font-size:11px;letter-spacing:.08em;display:flex;gap:6px;align-items:center;color:var(--text-dim,#7a8290);flex:0 0 auto;}" +
    ".cmpnav-lang a{color:var(--text-dim,#7a8290);text-decoration:none;}.cmpnav-lang a:hover{color:var(--ink,#1a2a4a);}" +
    ".cmpnav-cur{color:var(--ink-mid,#172641)!important;font-weight:600;}" +
    ".cmpnav-burger{display:none;background:none;border:none;font-size:20px;color:var(--ink-mid,#172641);cursor:pointer;padding:6px;}" +
    ".cmpnav-tab:focus-visible,.cmpnav-brand:focus-visible,.cmpnav-lang a:focus-visible{outline:2px solid var(--accent,#b08a4a);outline-offset:2px;}" +
    "@media(max-width:860px){.cmpnav-in{justify-content:flex-start;gap:14px;}.cmpnav-burger{display:block;margin-left:auto;order:3;}.cmpnav-wm{display:none;}" +
    ".cmpnav-lang{order:2;margin-left:auto;}" +
    ".cmpnav-tabs{order:4;display:none;position:absolute;top:54px;left:0;right:0;background:#fff;" +
    "border-bottom:1px solid var(--rule,#d6dee8);flex-direction:column;align-items:stretch;padding:6px 0;box-shadow:0 12px 24px rgba(15,31,58,.08);}" +
    ".cmpnav-tabs.cmpnav-open{display:flex;}.cmpnav-tabs{gap:0;}.cmpnav-tab{padding:13px 28px;border-bottom:none;}" +
    ".cmpnav-on{border-bottom:none;border-left:3px solid var(--accent,#b08a4a);}}" +
    "html{scroll-behavior:smooth;}" +
    "#sec-profiles,#sec-links{scroll-margin-top:64px;}" +
    "@media(prefers-reduced-motion:reduce){.cmpnav-tab{transition:none;}html{scroll-behavior:auto;}}" +
    "/* retire the duplicate logo/home-link below the sticky nav */" +
    ".hero-brand,.crumb,.masthead-inner .brand-home-link{display:none!important;}";
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[c];}); }
  var tabsHtml = "";
  for (var i = 0; i < tabs.length; i++) {
    var t = tabs[i], on = t.k === ak;
    tabsHtml += '<a class="cmpnav-tab' + (on ? ' cmpnav-on' : '') + '" href="' + t.href + '"' +
      (on ? ' aria-current="page"' : '') + '>' + esc(isEn ? t.en : t.ja) + '</a>';
  }
  var html = '<div class="cmpnav-in">' +
    '<a class="cmpnav-brand" href="' + home + '" aria-label="JII Compounders home">' +
    '<span class="cmpnav-mark">J<span class="cmpnav-pipe">|</span>I</span>' +
    '<span class="cmpnav-wm">Compounders</span></a>' +
    '<div class="cmpnav-tabs" id="cmpnav-tabs">' + tabsHtml + '</div>' +
    '<div class="cmpnav-lang"><a' + (isEn ? ' class="cmpnav-cur"' : '') + ' href="' + esc(toEn) + '" lang="en">EN</a>' +
    '<span>·</span><a' + (!isEn ? ' class="cmpnav-cur"' : '') + ' href="' + esc(toJa) + '" lang="ja">JP</a></div>' +
    '<button class="cmpnav-burger" aria-label="Menu" aria-expanded="false">&#9776;</button>';

  var nav = document.createElement("nav");
  nav.id = "cmpnav"; nav.className = "cmpnav";
  nav.setAttribute("aria-label", isEn ? "Compounders sections" : "コンパウンダーズ");
  nav.innerHTML = html;
  document.body.insertBefore(nav, document.body.firstChild);
  document.body.style.paddingTop = "54px";

  var burger = nav.querySelector(".cmpnav-burger");
  var tabsEl = nav.querySelector("#cmpnav-tabs");
  burger.addEventListener("click", function () {
    var open = tabsEl.classList.toggle("cmpnav-open");
    burger.setAttribute("aria-expanded", open ? "true" : "false");
  });
})();
