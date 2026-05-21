# PUSH-READY · Capital-Allocation Inflection Feed (v1)

> **HISTORICAL SNAPSHOT** — preserved as-shipped. The EDINET integration described below was removed on 2026-05-21 (commit `2a11a02`) after diagnostic logging proved it had been a silent no-op since day one (docType 350 was 大量保有報告書, not CG reports; CG reports actually flow via TDnet; other docTypes had no body content for matchers). For current pipeline architecture see `compounders/feed/_SPEC.md` History entry.

**Date:** 2026-05-17
**Repo:** jpinv.com on GitHub · branch `main`
**Status:** Code complete. Two human-action bottlenecks before live data flows. Page renders today against sample data.
**Spec:** `compounders/feed/_SPEC.md`

---

## What this ships

A new section of jpinv.com under `/compounders/feed/` (JP) and `/en/compounders/feed/` (EN) — a live, filterable feed of only the TDnet/EDINET disclosures that indicate a capital-allocation inflection (cost-of-capital awareness statements, buybacks ≥1% of S/O, material dividend changes, treasury cancellations, cross-shareholding unwinds, take-private events, ROIC/ROCE-linked comp revisions, and governance-code flips on the capital-policy principles).

Reader-facing behaviour: reverse-chronological list with 8 class chips (default all on), ticker search box with autocomplete, per-ticker drill-down to the full 2-year back-catalogue for that name, deep-links to source disclosures (EDINET viewer / TDnet PDF) and to the matching JII Compounder Profile when one exists.

Architecture: GitHub Actions cron every 30 min runs the Python pipeline, writes JSON into `compounders/feed/data/`, commits and pushes. GitHub Pages serves the JSON; the page is a thin client-side renderer. Zero new infra.

## Files added (new — all additive)

```
compounders/feed/_SPEC.md                     ← canonical build spec, committed for reference
compounders/feed/index.html                   ← JP page (30,314 B, CRLF, trailer verified)
compounders/feed/data/feed.json               ← sample data (30 rows), real until backfill
compounders/feed/data/index.json              ← ticker search index, 25 tickers
compounders/feed/data/_meta.json              ← refresh metadata; flagged sample_data_pending_backfill
compounders/feed/data/by-ticker/{ticker}.json ← 25 files, one per ticker with matches
en/compounders/feed/index.html                ← EN page (30,001 B, CRLF, trailer verified)

tools/classifier.py                           ← 8-class Principle-6 taxonomy, 16/16 tests pass
tools/edinet_client.py                        ← FSA EDINET API client (stub-mode when no key)
tools/tdnet_scraper.py                        ← TDnet HTML scraper, polite rate-limit
tools/feed_refresh.py                         ← orchestrator script, called by Actions cron
tools/requirements.txt                        ← pinned: requests, beautifulsoup4, lxml, pytz

.github/workflows/feed-refresh.yml            ← cron */30, workflow_dispatch, idempotent commits
```

## Files modified

None. The build is entirely additive — easy revert if needed.

## How it works (in plain English)

1. The GitHub Actions cron fires every 30 minutes. It runs `tools/feed_refresh.py`.
2. The script pulls today's EDINET disclosures (free FSA API) and today's TDnet HTML index. Each disclosure gets normalised into a uniform dict and passed to `classifier.classify()`.
3. The classifier rejects anything in the exclusion list (earnings, monthly sales, splits, option grants) and tests each surviving disclosure against the 8 Principle-6 classes. Matches are tagged and returned; non-matches drop silently.
4. New matches are deduped against `feed.json` by deterministic `id`, appended, and `index.json` plus the affected `by-ticker/{ticker}.json` files are regenerated.
5. If anything actually changed, the workflow commits with message `feed: refresh @ {run_id}` and pushes. GitHub Pages serves the updated JSON within ~60 seconds. The page itself does not need to be rebuilt — only its data files change.

## Two human-action bottlenecks before this goes fully live

### 1. EDINET API key (blocks live EDINET data; TDnet still flows without it)

The `EdinetClient` runs in stub mode (warns, yields nothing) until you set `EDINET_API_KEY`. To unblock:

1. Register for free at https://disclosure2.edinet-fsa.go.jp/weee0010.aspx — takes ~5 minutes, key is emailed within 24 hours.
2. In the jpinv.com GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**. Name: `EDINET_API_KEY`. Value: the key from the email.
3. Manually run the workflow once: **Actions tab → feed-refresh → Run workflow**. It should commit one new batch (or 0 if no qualifying disclosures since the last run).
4. Then run the one-shot 2-year backfill locally (the cron only does incremental): from `/5 Assets/Website/jpinv.com/`, `EDINET_API_KEY=xxx FEED_MODE=backfill python3 tools/feed_refresh.py`. Takes ~2–4 hours because of EDINET's 3.5-sec rate limit. Result is one commit with ~1,500–2,500 rows depending on hit rate.

### 2. Local git index corruption (blocks push, predates this build)

When the orchestrator ran `git status` in your cloned repo, the output was `error: bad index file sha1 signature; fatal: index file corrupt`. This is **independent of today's work** — it would block any push regardless. Fix in one command before opening GitHub Desktop:

1. Close GitHub Desktop.
2. From a terminal in the repo root: `rm .git/index && git reset` — regenerates the index from HEAD without touching the working tree (no file changes are lost).
3. Reopen GitHub Desktop. The Changes tab should now show the additive files from this build cleanly.

## Verification checklist after push

- [ ] `EDINET_API_KEY` secret set in repo Settings.
- [ ] Visit `https://jpinv.com/en/compounders/feed/` — page loads, sample 30 rows render with all 8 class chips.
- [ ] Toggle a chip off — only that class disappears from the list.
- [ ] Type `4776` in search — feed filters to 3 Cybozu rows; clicking `← Back to all` restores the full list.
- [ ] Click the ticker link `4776` in a row — same drill-down behaviour.
- [ ] Click "Read the JII Compounder Profile" on a Cybozu row — lands on `/en/compounders/4776/`.
- [ ] Click the EN/JP toggle in the footer — lands on the same page in the other language.
- [ ] Actions tab → feed-refresh shows scheduled runs every 30 min.
- [ ] First manual run with key set commits a new batch (or no-ops cleanly if no new matches).

## Rollback

If anything is wrong post-push:

```bash
git revert <commit_sha>
git push
```

The build is purely additive — reverting removes the feed entirely with no impact on anything else on jpinv.com.

## Known limitations (deliberate, see `_SPEC.md` Section 9)

- No email / RSS / Substack push of new matches. Read-only page.
- No sentiment scoring or confidence display. Binary match-or-not.
- No login or per-user filtering.
- TDnet body extraction is title-only (no PDF parsing). Buyback rows where size isn't in the title fall back to `Buyback · size TBC` tag — still surfaced, but the precise % / yen needs the EDINET document. A follow-up sprint could add lazy PDF parsing for matched TDnet rows.
- The 2-year backfill is a one-shot manual run, not part of the cron. The cron only does incremental from this point forward.

## What was deliberately not built (v1 scope discipline)

Anything in Section 9 of `_SPEC.md`. If you want any of them in v2, write a new spec section first and re-orchestrate.

---

**Co-built by:** Cowork orchestrator + Classifier / Frontend / Deploy / Data-Ingest / Sample-Feed sub-agents.
**Pre-flight QA:** classifier 16/16 tests pass, pipeline end-to-end runs clean in stub mode, both HTML files CRLF-clean with valid `</body></html>` trailers, YAML parses, JSON schemas validated, methodology `#p6` anchor exists on both EN and JP.
**Bottlenecks surfaced:** (1) classifier file had 2,171 trailing NUL bytes — fixed in-session. (2) EDINET key not yet registered — pipeline runs in stub mode until you set the secret. (3) local `.git/index` corrupt — one-command fix above.
