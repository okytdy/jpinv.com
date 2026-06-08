#!/usr/bin/env python3
"""
wire_universe_signals.py -- Decorate the universe (watchlist) pages with a clickable
capital-allocation SIGNAL badge on every name that has signals on file.

Client-side enhancer driven by compounders/feed/data/watchlist_signals.json, so the
badges stay current as the feed cron appends new signals -- no page rebuild needed.
Injects (idempotently, marker-guarded) into BOTH:
    compounders/universe/index.html       (JP)
    en/compounders/universe/index.html     (EN)
  1) a .sig-badge / #sig-legend CSS rule before </style>
  2) a <p id="sig-legend"> just before <table id="universe">
  3) the enhancer <script> just before </body>
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["compounders/universe/index.html", "en/compounders/universe/index.html"]
MARKER = "<!-- sig-wire v1 -->"

CSS = """
  .sig-badge { font-family:var(--mono); font-size:10.5px; letter-spacing:0.04em; color:var(--accent-deep); border-bottom:1px solid var(--accent); padding-bottom:1px; white-space:nowrap; margin-left:7px; }
  .sig-badge:hover { color:var(--ink-mid); border-color:var(--ink-mid); }
  tr.has-signal .cell-name { font-weight:400; }
  #sig-legend { display:none; font-family:var(--mono); font-size:11px; letter-spacing:0.04em; color:var(--text-dim); margin:0 0 12px; }
  #sig-legend a { color:var(--accent-deep); border-bottom:1px solid var(--accent); }
"""

SCRIPT = """
<script>
/* sig-wire: decorate watchlist rows with capital-allocation signal badges */
(function(){
  "use strict";
  var EN = location.pathname.indexOf("/en/") === 0;
  var SIGROOT = EN ? "/en/compounders/signals/" : "/compounders/signals/";
  function t(en, ja){ return EN ? en : ja; }
  fetch("/compounders/feed/data/watchlist_signals.json", {cache:"no-store"})
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if (!d || !d.names) return;
      var map = {};
      d.names.forEach(function(n){ map[n.ticker] = { c:n.signal_count, latest:(n.latest&&n.latest.date)||"" }; });
      var rows = document.querySelectorAll("#universe tbody tr");
      Array.prototype.forEach.call(rows, function(tr){
        var tkEl = tr.querySelector(".cell-tk"), nmEl = tr.querySelector(".cell-name");
        if (!tkEl || !nmEl) return;
        var code = (tkEl.textContent || "").trim();
        var info = map[code];
        if (!info) return;
        if (nmEl.querySelector(".sig-badge")) return;
        var a = document.createElement("a");
        a.className = "sig-badge";
        a.href = SIGROOT + code + "/";
        a.textContent = "\\u25C9 " + info.c;
        var title = EN
          ? (info.c + " capital-allocation signal" + (info.c>1?"s":"") + " on file \\u00B7 latest " + info.latest)
          : ("\\u8CC7\\u672C\\u653F\\u7B56\\u30B7\\u30B0\\u30CA\\u30EB " + info.c + "\\u4EF6 \\u00B7 \\u6700\\u65B0 " + info.latest);
        a.setAttribute("title", title);
        a.setAttribute("aria-label", title);
        nmEl.appendChild(document.createTextNode(" "));
        nmEl.appendChild(a);
        tr.classList.add("has-signal");
      });
      var lg = document.getElementById("sig-legend");
      if (lg) {
        lg.innerHTML = t(
          "\\u25C9 = capital-allocation signals on file \\u2014 click a badge for the name\\u2019s signal log, or see the <a href=\\"/en/compounders/signals/\\">full signal log</a>.",
          "\\u25C9 = \\u8CC7\\u672C\\u653F\\u7B56\\u30B7\\u30B0\\u30CA\\u30EB\\u306E\\u8A18\\u9332\\u3042\\u308A \\u2014 \\u30D0\\u30C3\\u30B8\\u3092\\u30AF\\u30EA\\u30C3\\u30AF\\u3067\\u9298\\u67C4\\u5225\\u30ED\\u30B0\\u3078\\u3001\\u307E\\u305F\\u306F<a href=\\"/compounders/signals/\\">\\u30B7\\u30B0\\u30CA\\u30EB\\u4E00\\u89A7</a>\\u3078\\u3002"
        );
        lg.style.display = "";
      }
    })
    .catch(function(){});
})();
</script>
"""

def inject(path):
    full = os.path.join(ROOT, path)
    s = open(full, encoding="utf-8").read()
    if MARKER in s:
        return "skip (already wired)"
    # 1) CSS before </style>
    if "</style>" in s:
        s = s.replace("</style>", CSS + "</style>", 1)
    # 2) legend before the table
    if '<table id="universe">' in s:
        s = s.replace('<table id="universe">', '<p id="sig-legend"></p>\n  <table id="universe">', 1)
    # 3) script + marker before </body>
    s = s.replace("</body>", MARKER + "\n" + SCRIPT + "\n</body>", 1)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    return "wired"

for p in PAGES:
    print(f"{p}: {inject(p)}")
