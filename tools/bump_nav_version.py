#!/usr/bin/env python3
"""
Stamp assets/nav.js with a version derived from its own contents, and rewrite
that version into every file that loads it.

WHY THIS EXISTS. Every page loads the navigation as

    <script src="/assets/nav.js?v=325f02a804" defer></script>

The browser caches that URL. If nav.js changes but the `?v=` does not, the
browser keeps serving the copy it already has, and the site appears not to have
changed at all. That happened on August 3, 2026: nav.js was edited five times
while the version string stayed at 20260803, so the deployed pages kept
rendering the first version.

Using a hash of the file removes the judgement call. Change nav.js, run this,
and every page points at a URL that has never been requested before.

    python3 tools/bump_nav_version.py

Run it after ANY edit to assets/nav.js, before committing.
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAV = os.path.join(ROOT, "assets", "nav.js")

# Every asset that is loaded by URL and therefore cached by the browser.
# Add a file here the moment it starts being loaded with a ?v= query.
VERSIONED = ["nav.js", "hero.js", "hero.css"]

# Files outside the site tree that also carry a tag.
EXTERNAL = [
    os.path.join(ROOT, "tools", "build_signal_pages.py"),
    os.path.join(ROOT, "tools", "build_sitemap_page.py"),
]

PATTERN = re.compile(
    r"(assets/(?:%s)\?v=)([0-9a-zA-Z]+)" % "|".join(re.escape(n) for n in VERSIONED))


def walk_site():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        for name in files:
            # .js is included because assets/compounders-nav.js is a shim that
            # loads nav.js by URL and therefore carries the version too.
            if name.endswith((".html", ".py", ".md", ".js")):
                yield os.path.join(base, name)


def main():
    if not os.path.exists(NAV):
        sys.exit("assets/nav.js not found")
    # Hash every versioned asset together, with any version strings stripped
    # out first, so that a version written into a file's own header comment
    # cannot change the hash and send this into a loop where every run
    # produces a different answer. One shared version keeps it simple: edit
    # any of them and every page picks up all of them.
    blob = ""
    for name in VERSIONED:
        p = os.path.join(ROOT, "assets", name)
        if os.path.exists(p):
            blob += PATTERN.sub(r"\1", open(p, encoding="utf-8").read())
    version = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:10]

    roots = sys.argv[1:]
    changed = 0
    scanned = 0
    paths = list(walk_site()) + EXTERNAL
    if roots:
        paths = [p for p in paths
                 if any(os.path.relpath(p, ROOT).replace(os.sep, "/").startswith(r) for r in roots)]
    for path in paths:
        if os.path.abspath(path) == os.path.abspath(NAV):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if "assets/nav.js?v=" not in text:
            continue
        scanned += 1
        new = PATTERN.sub(lambda m: m.group(1) + version, text)
        if new != text:
            open(path, "w", encoding="utf-8").write(new)
            changed += 1

    print(f"nav.js version: {version}")
    print(f"files carrying the tag: {scanned}")
    print(f"files rewritten: {changed}")
    if changed == 0 and scanned:
        print("(already up to date)")
    return version


if __name__ == "__main__":
    main()
