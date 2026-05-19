# PUSH-READY · Capital-Allocation Inflection Feed (v1.1)

**Date:** 2026-05-19
**Repo:** jpinv.com on GitHub · branch `main`
**Status:** Live data path unblocked. Sample-data contamination removed. One-click backfill workflow added. Ready to push.

---

## What changed since v1 (2026-05-17)

The v1 ship-doc (`PUSH-READY-FEED.md`) called out two human-action bottlenecks before live data could flow:

1. **EDINET_API_KEY in GitHub Secrets** → **resolved**. Key is saved to the repo's Actions secrets.
2. **First backfill run** → **resolved with a one-click workflow** (see below) so no local Python execution is required.

Plus two silent bugs the prior QA missed:

- `compounders/feed/data/feed.json` and `index.json` were committed in a JSON-truncated state (mid-string cutoff at row ~280). The page silently rendered the empty-state placeholder. **Fixed:** reset to valid empty placeholders. The cron will populate them on first run.
- `compounders/feed/index.html` and `en/compounders/feed/index.html` had also been silently truncated by past sync activity (closing JS lopped off). **Fixed:** restored from git HEAD.

## Files in this push (delta vs v1)

```
NEW   .github/workflows/feed-backfill.yml      ← workflow_dispatch only, 730-day default, parameterised
NEW   tools/validate_feed.py                   ← stdlib-only schema validator, all SPEC §4 invariants
NEW   compounders/feed/_V2_DESIGN.md           ← v2 design doc: decks (ship), IR (next quarter), transcripts (punt)

MOD   tools/feed_refresh.py                    ← added FEED_BACKFILL_LOOKBACK_DAYS env override (bounds 30..1095)
MOD   compounders/feed/data/feed.json          ← reset from corrupted/sample to []
MOD   compounders/feed/data/index.json         ← reset from corrupted/sample to {}
MOD   compounders/feed/data/_meta.json         ← reset to mode=awaiting_first_real_run, run_count=0
MOD   compounders/feed/data/by-ticker/2917.json  ← reset to [] (was corrupted)
MOD   compounders/feed/data/by-ticker/409A.json  ← reset to [] (was corrupted)
MOD   compounders/feed/index.html              ← restored from git HEAD (had been truncated on disk)
MOD   en/compounders/feed/index.html           ← restored from git HEAD (had been truncated on disk)
```

The other 60-odd `M` files showing up in `git status` (articles/, compounders/4*, en/governance/, etc.) **are pre-existing dirty changes in your working tree, not part of this push.** If you don't want them shipped, commit only the paths above.

## Validation gate

```
$ python tools/validate_feed.py
validate_feed: data_dir = .../compounders/feed/data
  feed.json rows checked:        0
  index.json keys checked:       0
  by-ticker/*.json files checked: 66
PASS: every checked file conforms to _SPEC.md Section 4.
```

## Your three remaining moves (the one mile I can't drive)

### Move 1 — Push these changes to `main`

```
cd "C:\Users\okuya\OneDrive\Desktop\JII\3 Pipeline\5 Assets\Website\jpinv.com"
git add .github/workflows/feed-backfill.yml \
        tools/validate_feed.py \
        tools/feed_refresh.py \
        compounders/feed/_V2_DESIGN.md \
        compounders/feed/index.html \
        en/compounders/feed/index.html \
        compounders/feed/data/feed.json \
        compounders/feed/data/index.json \
        compounders/feed/data/_meta.json \
        compounders/feed/data/by-ticker/2917.json \
        compounders/feed/data/by-ticker/409A.json
git commit -m "feed v1.1: unblock live pipeline + add backfill workflow + reset corrupted samples"
git push
```

### Move 2 — Trigger the backfill (one click)

1. Go to `https://github.com/okytdy/jpinv.com/actions/workflows/feed-backfill.yml`
2. Click "Run workflow"
3. Set `lookback_days` (default 730 = 2 years per spec; pick something like 90 if you want faster confirmation)
4. Click the green "Run workflow" button
5. Watch it. Expected: ~10–60 min depending on lookback. It commits the populated JSON when it finishes.

After this finishes, `/compounders/feed/` will show real rows.

### Move 3 — Regenerate the EDINET API key (security)

The key you pasted into chat earlier is now in conversation logs and should be treated as burned.

1. Log back into EDINET → API key page
2. Click regenerate (or issue new)
3. Update the `EDINET_API_KEY` secret in your jpinv.com repo Settings → Secrets and variables → Actions
4. The cron will pick it up on its next 30-min tick — no other action needed

---

## What's automatic from this point

- Every 30 minutes, `feed-refresh.yml` polls EDINET (today + yesterday) and TDnet, classifies, appends new matches, commits.
- New rows show up on `/compounders/feed/` and `/en/compounders/feed/` within ~60s of each commit.
- The 8-class taxonomy (COC, BUYBACK, CANCEL, DIV, CROSS, MBO, COMP, GOV) and the exclusion list (短信, 月次, splits, option grants) are frozen per `_SPEC.md`.

## What's deliberately out of scope (see `_V2_DESIGN.md`)

- **Briefing decks** — design done, build next. ~1–2 weeks calendar.
- **Integrated reports** — design done, build the quarter after. Acquisition is the wall, not classification.
- **Transcript Q&As** — punted. Licensing risk dwarfs the engineering. Revisit Q4.

---

**Bottom line:** the live disclosure feed will start producing real, searchable-by-ticker rows on jpinv.com the moment you finish Move 1 and Move 2 above. Move 3 is housekeeping.
