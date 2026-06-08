#!/usr/bin/env python3
"""
unwire_profile_signallog.py -- Reverse of wire_profile_signallog.py. Removes the
client-side "Capital-allocation signal log" block (the id="sig-log" section, the
siglog-wire script, and the .siglog/#sig-log CSS) from every profile it was injected
into. The signal-log concept is retired (2026-06-09).
"""
import os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def strip(path):
    if not os.path.exists(path): return "missing"
    s = open(path, encoding="utf-8").read()
    if "siglog-wire" not in s and 'id="sig-log"' not in s:
        return "none"
    # 1) the placeholder section
    s = re.sub(r'<section class="section" id="sig-log"[^>]*></section>\s*', '', s)
    # 2) the script block (marker -> </script>)
    s = re.sub(r'<!-- siglog-wire v1 -->\s*<script>.*?</script>\s*', '', s, flags=re.DOTALL)
    # 3) the injected CSS rules (any selector containing sig-log / siglog)
    s = re.sub(r'\n  [^\n{}]*sig-?log[^\n{}]*\{[^}]*\}', '', s)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    return "stripped"

targets = set()
for base in ("compounders", "en/compounders"):
    for p in glob.glob(os.path.join(ROOT, base, "*", "index.html")):
        tk = os.path.basename(os.path.dirname(p))
        if re.match(r'^[0-9]{4}$', tk):
            targets.add(p)
done = {}
for p in sorted(targets):
    r = strip(p)
    if r in ("stripped",):
        done[os.path.relpath(p, ROOT)] = r
print(f"stripped signal-log from {len(done)} files:")
for k in sorted(done): print("  ", k)
