#!/usr/bin/env python3
"""
wire_universe_signals.py (v2) -- Turn the universe (watchlist) STATUS column into a
"Latest Signal" column.

Each watched row's last cell now shows the latest capital-allocation signal type with a
dated hyperlink to that name's signal log (/compounders/signals/{ticker}/). Names with no
signals show an em dash. The Active/Near-miss status stays on the row (data-status) so the
SHOW filter buttons keep working; it's just no longer the visible column.

Client-side enhancer driven by compounders/feed/data/watchlist_signals.json (stays current
as the cron appends). Idempotent: strips any prior v1 (badge) or v2 injection first.
Applies to compounders/universe/index.html and en/compounders/universe/index.html.
"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["compounders/universe/index.html", "en/compounders/universe/index.html"]
MARKER = "<!-- sig-wire v2 -->"

CSS = """
  .cell-latest-sig { white-space:nowrap; }
  .cell-latest-sig .ls-class { display:block; font-family:var(--mono); font-size:11px; letter-spacing:0.06em; color:var(--ink-mid); }
  .cell-latest-sig .ls-date { font-family:var(--mono); font-size:11px; color:var(--accent-deep); border-bottom:1px solid var(--accent); }
  .cell-latest-sig .ls-date:hover { color:var(--ink-mid); border-color:var(--ink-mid); }
  .cell-latest-sig .ls-none { color:var(--text-dim); }
"""

SCRIPT = """
<script>
/* sig-wire v2: STATUS column -> Latest Signal (type + dated link to the name's signal log) */
(function(){
  "use strict";
  var EN = location.pathname.indexOf("/en/") === 0;
  var SIGROOT = EN ? "/en/compounders/signals/" : "/compounders/signals/";
  function esc(x){ return (""+(x==null?"":x)).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  // Rename the last header cell (the old STATUS column).
  var ths = document.querySelectorAll("#universe thead th");
  if (ths.length) { ths[ths.length-1].textContent = EN ? "Latest Signal" : "最新シグナル"; }
  fetch("/compounders/feed/data/watchlist_signals.json", {cache:"no-store"})
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if (!d || !d.names) return;
      var map = {};
      d.names.forEach(function(n){ if (n.latest) map[n.ticker] = { cls:(EN ? n.latest.class_en : n.latest.class_jp), date:n.latest.date }; });
      var rows = document.querySelectorAll("#universe tbody tr");
      Array.prototype.forEach.call(rows, function(tr){
        var tkEl = tr.querySelector(".cell-tk"), cell = tr.querySelector(".cell-status");
        if (!tkEl || !cell) return;
        var tk = (tkEl.textContent || "").trim();
        var info = map[tk];
        cell.className = "cell-status cell-latest-sig";
        if (info) {
          cell.innerHTML = '<span class="ls-class">' + esc(info.cls) + '</span>'
                         + '<a class="ls-date" href="' + SIGROOT + tk + '/">' + esc(info.date) + '</a>';
        } else {
          cell.innerHTML = '<span class="ls-none">—</span>';
        }
      });
    })
    .catch(function(){});
})();
</script>
"""

def strip_prior(s: str) -> str:
    # remove prior script blocks (v1 and v2)
    s = re.sub(r'<!-- sig-wire v[12] -->\s*<script>.*?</script>\s*', '', s, flags=re.DOTALL)
    # remove the v1 legend element
    s = re.sub(r'\s*<p id="sig-legend"></p>', '', s)
    # remove injected CSS rules (v1 badge/legend + any prior v2)
    s = re.sub(r'\n  [^\n{}]*(?:sig-badge|sig-legend|has-signal|cell-latest-sig|ls-class|ls-date|ls-none)[^\n{}]*\{[^}]*\}', '', s)
    return s

def inject(path):
    full = os.path.join(ROOT, path)
    s = open(full, encoding="utf-8").read()
    s = strip_prior(s)
    if "</style>" in s:
        s = s.replace("</style>", CSS + "</style>", 1)
    s = s.replace("</body>", MARKER + "\n" + SCRIPT + "\n</body>", 1)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    return "wired (Latest Signal column)"

for p in PAGES:
    print(f"{p}: {inject(p)}")
