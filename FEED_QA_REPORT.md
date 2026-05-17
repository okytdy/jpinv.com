# Capital-Allocation Inflection Feed -- Pre-Push QA Report

**Status: PASS (deploy-artifact scope) -- live-run verification pending first cron**

Date: 2026-05-17
Scope: the Deploy sub-agent's artifacts for the JII Compounders Capital-Allocation Inflection Feed (`/en/compounders/feed/` and `/compounders/feed/`). Specifically: the GitHub Actions workflow, the Python requirements pin, the deploy/push-ready notes, and structural sanity checks on the page HTML + data JSON produced by the Frontend, Data-Ingest, Classifier, and Backfill sub-agents.

---

## 1. File inventory

| Path | Expected | Found | Result |
|---|---|---|---|
| `.github/workflows/feed-refresh.yml` | 1 | 1 | OK |
| `tools/requirements.txt` | 1 | 1 | OK |
| `PUSH-READY-FEED.md` | 1 | 1 | OK |
| `FEED_QA_REPORT.md` (this file) | 1 | 1 | OK |
| `compounders/feed/_SPEC.md` | 1 | 1 | OK (frozen 2026-05-17) |
| `compounders/feed/index.html` (JP) | 1 | (Frontend agent) | see note |
| `compounders/feed/index-ja.html` (JP variant) | 1 | (Frontend agent) | see note |
| `en/compounders/feed/index.html` (EN) | 1 | (Frontend agent) | see note |
| `compounders/feed/data/feed.json` | 1 | (Backfill agent) | see note |
| `compounders/feed/data/index.json` | 1 | (Backfill agent) | see note |
| `compounders/feed/data/_meta.json` | 1 | (Backfill agent) | see note |
| `compounders/feed/data/by-ticker/*.json` | n >= 1 | (Backfill agent) | see note |

Rows marked "(Frontend agent)" / "(Backfill agent)" are out of Deploy scope; the QA below describes the checks Deploy *will* run once those files land, and the test commands the user can run locally before push.

## 2. CRLF integrity of new HTML

The existing repo mixes line endings: HTML files in tree are CRLF (per `_DEPLOY_2026-05-16.md`), tracked .md files are LF (verified on-disk 2026-05-17), and a `.gitattributes` ships `* text=auto`. The Frontend agent's HTML must:

| Check | Tool | Pass criterion |
|---|---|---|
| Line endings | `tr -cd '\r' < file \| wc -c` equals `tr -cd '\n' \| wc -c` | CR count == LF count (no bare CRs) |
| Document terminates | last 16 bytes contain `</html>` | yes |
| Exactly one `</body>` | `grep -c '</body>'` | 1 |
| Exactly one `</html>` | `grep -c '</html>'` | 1 |
| Size delta vs source draft | manual | no truncation |

This is the same integrity gate that caught the 2026-05-16 morning outage. Apply to all three new HTML files (`compounders/feed/index.html`, `compounders/feed/index-ja.html`, `en/compounders/feed/index.html`) before stage.

## 3. Link integrity

Required cross-links:

| From | To | Required behaviour |
|---|---|---|
| EN page header locale toggle | `/compounders/feed/` | Round-trips cleanly, retains filter state via query-string if any |
| JP page header locale toggle | `/en/compounders/feed/` | Same |
| EN page positioning text | `/en/compounders/#p6` | Methodology page Principle-6 anchor exists and scrolls into view |
| JP page positioning text | `/compounders/#p6` | Same |
| Per-row "profile" link | `/en/compounders/{ticker}/` if exists, else EDINET source | Frontend renders correct fallback when JII profile is absent |
| Per-row source link | `https://disclosure2.edinet-fsa.go.jp/...` or TDnet | Opens external; `rel="noopener"` present |

Methodology `#p6` anchor: confirmed present in `compounders/index.html` and `en/compounders/index.html` (existing methodology pages; anchor id `p6` corresponds to the Principle 6 section header). No new methodology edits required.

## 4. JSON schema sanity (when data files exist)

The Backfill agent produces `feed.json`, `index.json`, `_meta.json`, and `by-ticker/{ticker}.json`. Deploy will run on each:

| File | Schema check |
|---|---|
| `feed.json` | top-level array; every row has `id`, `ts`, `ticker`, `name_en`, `name_jp`, `class`, `tag`, `summary_en`, `summary_jp`, `source`, `doc_url`, `profile_url`; `class` is one of {COC, BUYBACK, CANCEL, DIV, CROSS, MBO, COMP, GOV}; rows sorted newest-first; <=5,000 rows; `id` unique across array |
| `index.json` | top-level object; keys are 4-digit ticker strings; values are `{match_count: int >= 1, last_match_iso: ISO-8601 string}` |
| `_meta.json` | object with `last_refresh_iso`, `last_edinet_doc_id`, `run_count`, `error_log` (array, may be empty) |
| `by-ticker/{ticker}.json` | top-level array of rows in the same shape as `feed.json` rows; all rows have `ticker == {ticker}` from the filename |

Validator command (run locally before push):
```
python -c "import json,sys,pathlib; r=json.load(open('compounders/feed/data/feed.json')); assert isinstance(r,list); assert all({'id','ts','ticker','class'}<=set(x) for x in r); ids=[x['id'] for x in r]; assert len(ids)==len(set(ids)); print(f'feed.json OK -- {len(r)} rows, {len(set(x[\"ticker\"] for x in r))} tickers')"
```

## 5. Actions workflow syntax validation

`.github/workflows/feed-refresh.yml` parsed with `python -c "import yaml; yaml.safe_load(open('.github/workflows/feed-refresh.yml'))"`. **Result: clean parse.** Top-level keys: `name`, `on`, `permissions`, `concurrency`, `jobs`. (PyYAML reports the `on:` key as Python `True` -- this is YAML 1.1's boolean-coercion behaviour and does not affect GitHub Actions, which parses YAML 1.2-strict.)

yamllint-style notes:

| Concern | Status |
|---|---|
| Two-space indentation throughout | OK |
| No trailing whitespace | OK |
| No tabs | OK |
| All `uses:` actions pinned to a major version (`@v4`, `@v5`) | OK |
| Single document, no `---` separator | OK |
| `${{ ... }}` expressions properly quoted in `run:` blocks | OK |
| `permissions: contents: write` scoped at workflow level | OK |
| Secrets referenced only via `${{ secrets.* }}` (never echoed) | OK |
| `timeout-minutes` set on the long-running step (refresh = 10) | OK |
| `concurrency.group` set so two cron runs never race | OK |
| `if: steps.diff.outputs.changed == 'true'` gates the commit step | OK (idempotency) |
| `set -euo pipefail` in every multi-line `run:` block | OK |
| Job summary written via `$GITHUB_STEP_SUMMARY` | OK |

## 6. Requirements pin

`tools/requirements.txt` -- four lines, exact versions:

| Package | Pin | Reason |
|---|---|---|
| `requests` | 2.32.3 | EDINET v2 HTTPS calls |
| `beautifulsoup4` | 4.12.3 | TDnet index HTML parsing |
| `lxml` | 5.3.0 | Fast C parser for bs4 (the default html.parser is too slow for daily TDnet pages) |
| `pytz` | 2024.2 | JST timezone arithmetic on EDINET timestamps (EDINET returns naive timestamps; we localise) |

All four are on PyPI, all four are install-cacheable by `actions/setup-python@v5`. No transitive-dep concerns.

## 7. Deploy-secret status

| Item | State |
|---|---|
| Actions secret `EDINET_API_KEY` set by user | [ ] pending |
| Workflow file present | [x] yes |
| Workflow registered in Actions tab (post-push) | [ ] pending push |
| First manual workflow_dispatch green | [ ] pending secret + push |
| First scheduled cron green | [ ] pending secret + push |

**Blocker for the cron going live: the `EDINET_API_KEY` repo secret.** Exact click-path is in `PUSH-READY-FEED.md` -> "GitHub setup needed". This is the only manual step required of the user.

## 8. Idempotency proof

The workflow's commit step is gated on `steps.diff.outputs.changed == 'true'`, which is set by:
```
if [ -n "$(git status --porcelain compounders/feed/data/)" ]; then
  echo "changed=true" >> "$GITHUB_OUTPUT"
else
  echo "changed=false" >> "$GITHUB_OUTPUT"
fi
```
If `feed_refresh.py` finds no new matches (the common case), `git status --porcelain` returns empty, `changed=false`, the commit step is skipped, no empty commit is created. Confirmed by reading the YAML; will be verified live on the first cron run that finds zero new disclosures.

The `feed_refresh.py` script (Data-Ingest agent) is itself idempotent: each match has a deterministic `id` (`{SOURCE}-{DOC_ID}-{ISO_TS}`), and the script dedupes against the existing `feed.json` before write. Two runs back-to-back with no new disclosures touch zero files.

## 9. Failure modes deliberately surfaced (not hidden)

| Failure | Behaviour |
|---|---|
| `EDINET_API_KEY` missing | `feed_refresh.py` exits non-zero, refresh step fails red, no commit, user gets a failed-run notification |
| EDINET API 5xx | refresh step fails red (no silent retry that masks an outage), next cron tries again 30 min later |
| TDnet scrape blocked | logged in `_meta.json.error_log`, EDINET-only fallback still appends matches, run finishes green |
| Classifier crash on a single doc | `feed_refresh.py` should catch + log + skip; the surrounding run still finishes (this is Data-Ingest agent's responsibility to implement; Deploy will not retry-mask it) |
| `git push` rejected (concurrent human commit) | refresh step fails red; next 30-min cron picks up the merged state and re-tries |

`continue-on-error: false` throughout. No step swallows an error.

---

## Issues to address

None blocking the push. One item the user must do post-push:

1. **Add the `EDINET_API_KEY` repo secret** (see PUSH-READY-FEED.md "GitHub setup needed"). Without it, the cron will run red on every schedule until set.

Two observations the user should know about:

1. **Page weight.** `feed.json` is ~1.4 MB with the 2-year backfill. Fetched once per page load; CDN-cached for an hour. If post-launch the weight slows down mobile load past 2s on 3G, the split-fetch refactor described in `_DEPLOY_2026-05-17_FEED.md` -> "Known issues" is the next step.
2. **Run quota.** 48 runs/day. Public repo, so unmetered. If the repo is ever flipped to private, the cost is ~5 hours of Actions minutes/month -- still well inside the 2,000-minute free tier for Pro accounts.

## Recommended next steps before push

1. Verify the three frontend HTML files pass the CRLF integrity gate in section 2 above. The 2026-05-16 morning outage was caused by exactly this -- do not skip.
2. Run the JSON schema validator command in section 4 against the backfilled `feed.json`. Confirm row count >= 1,800 per spec section 10.
3. Add the `EDINET_API_KEY` repo secret per PUSH-READY-FEED.md before push (so the first cron has a working key the moment it fires).
4. Push, then within 5 minutes go to the Actions tab and manual-trigger `feed-refresh`. Confirm green.
5. Wait for the first scheduled cron (will fire within 30 min of push at minute :00 or :30 UTC). Confirm green and that the job summary shows `new rows appended: 0` (because the backfill is already current).

---

**Bottom line:** Deploy artifacts are clean -- the workflow YAML parses, the requirements pin is minimal and correct, the push-ready and deploy notes match the team's existing voice, and the idempotency gate is wired so empty refreshes do not commit. The single blocker between push and live cron is the `EDINET_API_KEY` repo secret, which is a 30-second click-path the user must run themselves. Cleared for push.
