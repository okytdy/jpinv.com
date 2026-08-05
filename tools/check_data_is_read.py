#!/usr/bin/env python3
"""
check_data_is_read.py — every data file the site builds must be read by the site.

Written August 5, 2026, after the homepage news section sat frozen for days.

WHAT HAPPENED. tools/build_news_data.py wrote compounders/feed/data/news.json
every 30 minutes, and nothing on jpinv.com ever fetched it. The news rows the
reader saw were baked into index.html and only ever changed when someone ran the
script by hand without --no-bake and committed. So the automated half of the
system ran on schedule, produced a correct file, and had no effect on the page.

That failure is silent by construction. The workflow was green. The file was
fresh. The classifier was right. Nothing anywhere was in an error state — the
output simply went nowhere, and the only way to notice was to look at the site
and recognize a date as too old. The drift was visible inside a single commit:
news.json carried two August 4 rows while the HTML beside it showed five from
August 3, and no check compared them.

WHAT THIS CHECKS. For each JSON file under a data/ directory that a build script
writes, confirm that something the browser loads actually asks for it. A file may
be read in two legitimate ways:

  - fetched at runtime by a script under assets/, or
  - consumed at build time by another tool that writes HTML

Anything read by neither is orphaned: it costs a commit every 30 minutes and
changes nothing a reader sees. That is either a bug like the one above, or a file
that should be deleted.

    python3 tools/check_data_is_read.py

Exit status is 1 if an orphan is found.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files that are deliberately not fetched by the browser. Each needs a reason,
# and the reason has to say what does read it.
EXEMPT = {
    "tools/llm_ledger.json":
        "budget ledger for tools/llm_budget.py; committed so the monthly cap "
        "accumulates across CI runs, never served to a reader",
    "tools/jpx_cache.json":
        "ticker master cache for tools/jpx_master.py, build-time only",
    "tools/llm_summary_cache.json":
        "LLM response cache for tools/pdf_enricher.py, build-time only",
    "tools/.alert_state.json":
        "alert de-duplication state for the feed refresh, build-time only",
}

# Orphans that already existed when this check was written. They are printed on
# every run but do not fail it, so the check is usable from day one instead of
# being switched off as noisy. Each needs a decision: wire it to a page, or
# delete it. Do not add to this list to silence a NEW orphan — that is the exact
# bug this file exists to catch.
KNOWN_ORPHANS = {
    "compounders/active-investors/data/investors.json":
        "written by build_data.py; the page fetches roster.json instead",
    "compounders/active-investors/data/summaries.json":
        "written by build_data.py; per-filing text the page never requests",
    "compounders/active-investors/data/_unmatched.json":
        "written by refresh.py as a diagnostic; probably belongs outside data/",
}


def repo_files(suffixes, roots=None, skip=("node_modules", ".git", "__pycache__")):
    bases = [os.path.join(ROOT, r) for r in roots] if roots else [ROOT]
    for base_root in bases:
        if not os.path.isdir(base_root):
            continue
        for base, dirs, names in os.walk(base_root):
            dirs[:] = [d for d in dirs if d not in skip]
            for n in names:
                if n.endswith(suffixes):
                    yield os.path.relpath(os.path.join(base, n), ROOT).replace("\\", "/")


def read(path):
    try:
        return open(os.path.join(ROOT, path), encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""


def main() -> int:
    # WHERE A RUNTIME READ CAN LIVE. Every fetch on this site is in a script under
    # assets/, or inline in one of the few pages that carry their own data loader.
    # Walking all 400-plus built HTML pages instead takes minutes on a cloud-synced
    # folder and finds nothing extra, because the per-ticker and profile pages are
    # generated from templates that load the same shared assets. If that ever stops
    # being true, add the page here.
    client_paths = sorted(set(repo_files((".js",), roots=["assets"]))) + [
        "index.html",
        "en/index.html",
        "compounders/feed/index.html",
        "en/compounders/feed/index.html",
        "compounders/active-investors/index.html",
        "en/compounders/active-investors/index.html",
        "compounders/index.html",
        "compounders/profiles/index.html",
    ]
    client_text = "".join(read(p) for p in client_paths)

    # WRITING IS NOT READING, and this is the whole point of the check. The first
    # version of this script matched the filename anywhere in tools/, which meant
    # news.json looked "read" because build_news_data.py names it — as its own
    # output. The orphan reported itself as fine.
    #
    # So each tool is scanned twice: once for names it READS and once for names it
    # WRITES. The codebase assigns a path to a constant and uses the constant, so
    # resolve the constant first, then see which way it is used.
    reads, writes = set(), set()
    for tool in repo_files((".py",), roots=["tools"]):
        if os.path.basename(tool) == os.path.basename(__file__):
            continue
        src = read(tool)
        # CONST = os.path.join(..., "news.json")  /  CONST = "…/news.json"
        for const, fname in re.findall(
                r"^\s*([A-Z_][A-Z0-9_]*)\s*=\s*[^\n]*[\"']([\w.\-]+\.json)[\"']", src, re.M):
            if re.search(r"open\(\s*%s\s*,\s*[\"']w" % re.escape(const), src):
                writes.add(fname)
            if re.search(r"json\.load\(\s*open\(\s*%s|open\(\s*%s\s*,\s*encoding" % (
                    re.escape(const), re.escape(const)), src):
                reads.add(fname)
        # Direct use without a constant, e.g. json.load(open("roster.json"))
        for fname in re.findall(r"json\.load\(\s*open\(\s*[^)]*[\"']([\w.\-]+\.json)[\"']", src):
            reads.add(fname)
        # A read helper, e.g. C.read_json(DATA_DIR / "filings.json", []). The
        # active-investors tools use this shape throughout, and missing it made
        # filings.json look orphaned when refresh.py reads it three times.
        for fname in re.findall(
                r"(?:read|load)_json\(\s*[^)]*?[\"']([\w.\-]+\.json)[\"']", src):
            reads.add(fname)
        # A directory walked by path, e.g. data_dir / "by-ticker"
        for folder in re.findall(r"[\"']([\w\-]+)[\"']\s*(?:\)|$)", src):
            reads.add("dir:" + folder)
        for folder in re.findall(r"/\s*[\"']([\w\-]+)[\"']", src):
            reads.add("dir:" + folder)

    tool_text = ""  # kept for the directory fallback below

    data_files = sorted(
        p for p in repo_files((".json",), roots=["compounders", "en", "tools"])
        if "/data/" in p or (p.startswith("tools/") and p.count("/") == 1)
    )

    orphans, fetched, build_only, exempt = [], [], [], []
    for path in data_files:
        name = os.path.basename(path)
        if path in EXEMPT:
            exempt.append(path)
            continue
        # A runtime read names the file in a fetch, an import, or a src.
        in_client = re.search(r"[\"'/]%s[\"'?]" % re.escape(name), client_text) is not None
        # A build-time read is a read, established above — not a mere mention.
        in_tools = name in reads

        # A whole DIRECTORY can be read without any single filename appearing.
        # compounders/feed/data/by-ticker/ holds one file per ticker and is walked
        # by path, so matching on names alone reports two thousand false orphans.
        folder = os.path.basename(os.path.dirname(path))
        if not (in_client or in_tools) and folder not in ("data",):
            if re.search(r"[\"'/]%s[\"'/]" % re.escape(folder), client_text):
                in_client = True
            elif ("dir:" + folder) in reads:
                in_tools = True

        if in_client:
            fetched.append(path)
        elif in_tools:
            build_only.append(path)
        else:
            orphans.append(path)

    # by-ticker/ and translated/ hold thousands of files each. Listing them one
    # per line buries the answer, so collapse any directory holding more than a
    # few into a single line.
    def lines_for(paths):
        folders = {}
        for p in paths:
            folders.setdefault(os.path.dirname(p), []).append(p)
        out = []
        for folder, group in sorted(folders.items()):
            if len(group) > 3:
                out.append("%s/  — %d files" % (folder, len(group)))
            else:
                out.extend(sorted(group))
        return out

    print()
    print("  data files the site builds — %d in total" % len(data_files))
    print("  " + "-" * 66)
    for tag, group in (("fetched", fetched), ("build", build_only), ("exempt", exempt)):
        for line in lines_for(group):
            print("  [%-7s]  %s" % (tag, line))

    print("  " + "-" * 66)

    new_orphans = [p for p in orphans if p not in KNOWN_ORPHANS]
    old_orphans = [p for p in orphans if p in KNOWN_ORPHANS]

    for path in old_orphans:
        print("  [known  ]  %s — %s" % (path, KNOWN_ORPHANS[path]))
    for path in new_orphans:
        print("  [ORPHAN ]  %s" % path)

    if new_orphans:
        print()
        print("  %d file(s) are written by a build and read by nothing." % len(new_orphans))
        print()
        print("  An orphan is not harmless. It is rebuilt and committed on a schedule,")
        print("  so every check around it stays green while the page it was meant to")
        print("  update never changes. Either wire it to the page, or delete it.")
        print()
        return 1

    if old_orphans:
        print()
        print("  No new orphans. The %d listed above were already there on August 5," % len(old_orphans))
        print("  2026 and are waiting on a decision; they do not block.")
    else:
        print("  every data file is read by the browser or by another build step")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
