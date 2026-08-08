# Why the homepage news section stopped updating — August 5, 2026

## The symptom

The 大量保有報告 tab on the homepage showed filings dated July 31 on August 5. The
資本政策開示 tab showed August 3. Meanwhile `/compounders/active-investors/` and
`/compounders/feed/` were both current. The homepage was supposed to mirror them and did
not.

## The cause

**Nothing on jpinv.com ever read the file the build produces.**

`tools/build_news_data.py` writes `compounders/feed/data/news.json`, and the feed-refresh
workflow ran it every 30 minutes. A search across every script and page on the site found
zero references to `news.json`. The file was written on schedule and read by nobody.

What the reader actually saw was HTML baked into `index.html` between marker comments
(`<!--news-holdings-->` … `<!--/news-holdings-->`). Those rows change only when someone
runs the build script locally *without* `--no-bake` and commits the result. CI passes
`--no-bake` and stages only `compounders/feed/data/`, `compounders/signals/` and the LLM
ledger, so the automated path could never touch them.

So the update path was: a human remembers to run a script. Nothing else.

## Why nobody noticed

Every indicator said healthy. The workflow was green every half hour. `news.json` was
fresh. The classifier was correct. The two source pages were current. No error was raised
anywhere, because nothing failed — the output simply went nowhere.

The drift was visible inside a single commit and no check compared the two:
`news.json` carried two August 4 capital rows while the baked HTML beside it still showed
five from August 3. The only symptom available to a person was recognizing a date on the
live site as too old.

## Where the belief came from

Two comments in the codebase state the reasoning, and both are wrong in the same way.

`assets/hero.js`, in the news tab block:

> "No fetch: the lists are rebuilt whenever the site is built, and a half-day-old news row
> is not a failure the way an empty panel is."

`.github/workflows/feed-refresh.yml`:

> "The baked rows are the no-JavaScript fallback and are refreshed when the site is built,
> not on this schedule."

**There is no site build.** jpinv.com is a static repo served by GitHub Pages; nothing
regenerates `index.html` on deploy. And **the rows were not a fallback** — a fallback needs
something to fall back from, and the JavaScript that would have read `news.json` was never
written. They were the only thing rendering.

The hero panel directly above them is the proof the intended design works. `hero.js`
fetches `hero.json` on load, so the hero stayed current the whole time. The news section
was built on the same pattern with the client half missing.

## The fix

**`assets/hero.js` now fetches `news.json` and fills the three lists**, mirroring the hero
panel exactly, including its failure design: on a failed fetch, a timeout, or an empty
list, the baked rows stay on screen and keep their real dates, so nothing claims to be
newer than it is.

The JavaScript row markup was checked against the Python that bakes it — all three lists,
both languages, byte-identical — so the page does not change shape on load.

`assets/hero.js?v=` was bumped from `0fba22a656` to `220453f246` via
`tools/bump_nav_version.py`. Without that the browser serves the cached copy and the fix
appears to do nothing, which is the trap CLAUDE.md already records for `nav.js`.

The baked fallback rows were refreshed at the same time, and both misleading comments were
replaced with what actually happens.

## The guard

`tools/check_data_is_read.py`, wired into the feed-refresh workflow.

It compares what the build **writes** against what the site **reads**, which is the one
comparison that would have caught this. A data file counts as read if a script under
`assets/` fetches it or another build step loads it — writing it does not count, which was
the first version's own bug: `news.json` looked fine because `build_news_data.py` names it
as its output.

Tested both ways. Against the repaired site it exits 0. With the `news.json` fetch removed
it reports `[ORPHAN] compounders/feed/data/news.json` and exits 1.

## Left for you to decide

Three files are written and read by nothing. They predate this and do not block the check,
but each needs a call:

- `compounders/active-investors/data/investors.json` — the page fetches `roster.json` instead
- `compounders/active-investors/data/summaries.json` — per-filing text the page never requests
- `compounders/active-investors/data/_unmatched.json` — a diagnostic that probably belongs outside `data/`

Either wire each to a page or delete it. They are listed in `KNOWN_ORPHANS` in the check,
which prints them on every run without failing. Do not add a new orphan to that list to
quiet it down — that is the bug this file exists to catch.

## To push

**Summary**

```
Fix the homepage news section: nothing was reading news.json
```

**Description**

```
The homepage news tabs showed filings from July 31 on August 5 while
/compounders/active-investors/ and /compounders/feed/ were both current.

Cause: no script on the site ever fetched compounders/feed/data/news.json. The
feed-refresh workflow rebuilt it every 30 minutes and nothing read it. The rows
the reader saw were baked into index.html and only changed when someone ran
build_news_data.py by hand without --no-bake. Every indicator stayed green
because nothing failed - the output went nowhere.

Two comments in the code stated the reasoning and both were wrong: there is no
site build, and the baked rows were not a fallback because no JavaScript existed
for them to fall back from. The hero panel above them already worked this way,
which is why it never went stale.

Fix: assets/hero.js now fetches news.json and fills the three lists, mirroring
the hero panel including its failure design - on a failed fetch or empty list the
baked rows stay on screen with their real dates. The JS markup was verified
byte-identical to the Python that bakes it, all three lists in both languages, so
the page does not shift on load. hero.js version bumped to 220453f246 so browsers
pick it up. Baked fallback rows refreshed. Both misleading comments corrected.

Guard: tools/check_data_is_read.py compares what the build writes against what
the site reads, and is wired into feed-refresh. Writing a file does not count as
reading it. Tested both ways - exits 0 now, and reports news.json as an orphan
when the fetch is removed. It also surfaces three pre-existing orphans under
active-investors/data/ that need a decision; they are listed and do not block.
```

source: NEWS_SECTION_DIAGNOSIS_2026-08-05.md
