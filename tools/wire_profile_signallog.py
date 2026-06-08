#!/usr/bin/env python3
"""
wire_profile_signallog.py -- Add a 'Capital-allocation signal log' block to each
PUBLISHED Compounder Profile that has signals, closing the signal->post loop.

Client-side block driven by watchlist_signals.json (stays current; leaves the
profile's static structure + validation gates untouched). Injects idempotently
into compounders/{tk}/index.html and en/compounders/{tk}/index.html, before the
share-bar, for every name with profile_exists && signal_count>0.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "compounders", "feed", "data", "watchlist_signals.json")
MARKER = "<!-- siglog-wire v1 -->"

CSS = """
  #sig-log[hidden] { display:none; }
  .siglog { margin-top:8px; }
  .siglog-row { display:flex; gap:14px; align-items:baseline; flex-wrap:wrap; padding:11px 0; border-bottom:1px solid var(--rule-soft); }
  .siglog-date { font-family:var(--mono); font-size:12px; color:var(--text-dim); min-width:94px; }
  .siglog-chip { font-family:var(--mono); font-size:10px; letter-spacing:0.12em; text-transform:uppercase; padding:2px 7px; border:1px solid var(--accent); color:var(--accent-deep); background:var(--accent-soft); white-space:nowrap; }
  .siglog-tag { font-family:var(--sans); font-size:13px; color:var(--ink-mid); }
  .siglog-more { margin-top:16px; }
  .siglog-more a { font-family:var(--mono); font-size:11px; letter-spacing:0.14em; text-transform:uppercase; color:var(--accent-deep); border-bottom:1px solid var(--accent); padding-bottom:1px; }
"""

SCRIPT = """
<script>
/* siglog-wire: render this name's capital-allocation signal log from the live feed join */
(function(){
  "use strict";
  var EN = location.pathname.indexOf("/en/") === 0;
  var parts = location.pathname.split("/").filter(Boolean);
  var ci = parts.indexOf("compounders");
  var tk = ci >= 0 ? parts[ci+1] : null;
  if (!tk || !/^[0-9A-Za-z]{3,4}$/.test(tk)) return;
  function esc(x){ return (""+(x==null?"":x)).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c]; }); }
  fetch("/compounders/feed/data/watchlist_signals.json", {cache:"no-store"})
    .then(function(r){ return r.ok ? r.json() : null; })
    .then(function(d){
      if (!d || !d.names) return;
      var n = null;
      for (var i=0;i<d.names.length;i++){ if (d.names[i].ticker === tk){ n = d.names[i]; break; } }
      if (!n || !n.signals || !n.signals.length) return;
      var sec = document.getElementById("sig-log");
      if (!sec) return;
      var rows = n.signals.slice(0,6).map(function(s){
        var chip = EN ? s.class_en : s.class_jp;
        var tag  = EN ? s.tag_en : s.tag_jp;
        return '<div class="siglog-row"><span class="siglog-date">'+esc(s.date)+'</span>'
             + '<span class="siglog-chip">'+esc(chip)+'</span>'
             + '<span class="siglog-tag">'+esc(tag||"")+'</span></div>';
      }).join("");
      var href = (EN?"/en":"")+"/compounders/signals/"+tk+"/";
      var more = EN ? ("View the full signal log ("+n.signal_count+") \\u2192")
                    : ("\\u30B7\\u30B0\\u30CA\\u30EB\\u30ED\\u30B0\\u5168"+n.signal_count+"\\u4EF6\\u3092\\u898B\\u308B \\u2192");
      var title = EN ? "Capital-allocation signal log" : "\\u8CC7\\u672C\\u653F\\u7B56\\u30B7\\u30B0\\u30CA\\u30EB\\u30ED\\u30B0";
      var num = EN ? "SIGNAL LOG" : "\\u30B7\\u30B0\\u30CA\\u30EB\\u30ED\\u30B0";
      var lede = EN ? "The capital-policy disclosures this profile is built on, newest first \\u2014 the signals that put this name on the watchlist."
                    : "\\u672C\\u30EC\\u30DD\\u30FC\\u30C8\\u306E\\u80CC\\u666F\\u306B\\u3042\\u308B\\u8CC7\\u672C\\u653F\\u7B56\\u958B\\u793A\\uFF08\\u65B0\\u3057\\u3044\\u9806\\uFF09\\u3002";
      sec.innerHTML = '<div class="section-head"><span class="section-num">'+num+'</span>'
        + '<h2 class="section-title">'+title+'</h2>'
        + '<p class="section-sub">'+lede+'</p></div>'
        + '<div class="siglog">'+rows+'</div>'
        + '<p class="siglog-more"><a href="'+href+'">'+more+'</a></p>';
      sec.hidden = false;
    })
    .catch(function(){});
})();
</script>
"""

def inject(path):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full): return "missing"
    s = open(full, encoding="utf-8").read()
    if MARKER in s: return "skip"
    if "</style>" in s:
        s = s.replace("</style>", CSS + "</style>", 1)
    sec = '<section class="section" id="sig-log" hidden></section>\n'
    if '<section class="share-bar"' in s:
        s = s.replace('<section class="share-bar"', sec + '<section class="share-bar"', 1)
    elif '<section class="disclaimer"' in s:
        s = s.replace('<section class="disclaimer"', sec + '<section class="disclaimer"', 1)
    else:
        return "no-anchor"
    s = s.replace("</body>", MARKER + "\n" + SCRIPT + "\n</body>", 1)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    return "wired"

payload = json.load(open(DATA, encoding="utf-8"))
targets = [n["ticker"] for n in payload["names"] if n["profile_exists"] and n["signal_count"] > 0]
print("published names with signals:", " ".join(targets))
for tk in targets:
    for path in (f"compounders/{tk}/index.html", f"en/compounders/{tk}/index.html"):
        print(f"  {path}: {inject(path)}")
